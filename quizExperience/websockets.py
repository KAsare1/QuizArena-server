import os
import sys
from fastapi import APIRouter, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any, Optional
from Question_answering.RoundOne.FundamentalConcepts import QAMLRoundOne
import asyncio

multiplayer = APIRouter()

# Determine base path (handles both normal execution and PyInstaller mode)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Access Round_1.json from AIAgent/Agent.py
json_path = os.path.join(base_path, "Question_answering", "RoundOne", "Round_1.json")  # Script's directory

json_path = os.path.normpath(json_path)  # Normalize for cross-platform compatibility

# Use the dynamically generated path
questions = QAMLRoundOne(json_path)


class ConnectionManager:
    def __init__(self):
        self.active_rooms: Dict[str, List[WebSocket]] = {}
        self.room_questions: Dict[str, List[Dict[str, Any]]] = {}
        self.room_timers: Dict[str, int] = {}  # Timer for each room
        self.room_hosts: Dict[str, WebSocket] = {}  # Host for each room
        self.room_active_contestants: Dict[str, int] = {}  # Active contestant for each room
        self.room_transcripts: Dict[str, str] = {}
        self.room_answers: Dict[str, List[Dict[str, Any]]] = {}
        self.room_current_question: Dict[str, int] = {}
        self.room_states: Dict[str, Dict[str, Any]] = {}
        self.room_timer_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        
        if room not in self.active_rooms:
            self.active_rooms[room] = []
            self.room_questions[room] = self.load_questions()
            self.room_timers[room] = 30  # Initialize timer
            self.room_active_contestants[room] = 0  # Start with contestant 0
            self.room_hosts[room] = websocket  # First user is the host
            self.room_answers[room] = []  # Initialize answers list for room
            self.room_current_question[room] = 0 
            self.room_states[room] = {
                "current_question": 0,
                "total_questions": len(self.room_questions[room]["questions"])
            }
            self.room_timer_tasks[room] = asyncio.create_task(self.start_timer(room))

        self.active_rooms[room].append(websocket)

        # Send initial state to the newly connected user (only current question)
        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "current_question_index": self.room_current_question[room],
                "current_question": self.room_questions[room]["questions"][self.room_current_question[room]],
                "timer": self.room_timers[room],
                "active_contestant": self.room_active_contestants[room],
                "previous_answers": self.room_answers[room]
            }
        })

        # Retrieve the current question to broadcast to other users
        current_question = self.room_questions[room]["questions"][self.room_current_question[room]]
        
        # Notify other users about the new connection with the current question
        await self.broadcast(room, {
            "type": "question_update",
            "data": {
                "current_question_index": self.room_current_question[room],
                "question": current_question,
                "timer": self.room_timers[room],
                "active_contestant": self.room_active_contestants[room]
            }
        })

    async def handle_next_question(self, room: str):
        """Move to the next question and broadcast it to all clients"""
        if room in self.active_rooms:
            total_questions = self.room_states[room]["total_questions"]
            if self.room_current_question[room] < total_questions - 1:
                self.room_current_question[room] += 1
                self.room_states[room]["current_question"] = self.room_current_question[room]
                self.room_active_contestants[room] = 0  # Reset to the first contestant

                # Retrieve the next question
                current_question = self.room_questions[room]["questions"][self.room_current_question[room]]
                await self.broadcast(room, {
                    "type": "question_update",
                    "data": {
                        "current_question_index": self.room_current_question[room],
                        "question": current_question,
                        "timer": self.room_timers[room],
                        "active_contestant": self.room_active_contestants[room]
                    }
                })
            else:
                # No more questions, end the game
                await self.broadcast(room, {
                    "type": "game_over",
                    "data": {
                        "message": "The game has ended."
                    }
                })

    async def handle_answer_submission(self, room: str, data: dict):
        """Handle when a contestant submits their answer"""
        if room in self.active_rooms:
            # Store the answer
            self.room_answers[room].append({
                "contestant": data["contestant"],
                "answer": data["answer"],
                "correct": data["correct"],
                "question_index": self.room_current_question[room]
            })

            # Clear transcript and reset timer
            self.room_transcripts[room] = ""
            self.room_timers[room] = 30

            # Move to the next contestant or question
            if self.room_active_contestants[room] < len(self.active_rooms[room]) - 1:
                self.room_active_contestants[room] += 1
                await self.broadcast(room, {
                    "type": "next_contestant",
                    "data": {
                        "active_contestant": self.room_active_contestants[room],
                    }
                })
            else:
                # All contestants have answered, move to the next question
                await self.handle_next_question(room)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_rooms:
            self.active_rooms[room].remove(websocket)
            if not self.active_rooms[room]:
                # Clean up room data but keep room_states if needed
                del self.active_rooms[room]
                del self.room_questions[room]
                del self.room_timers[room]
                del self.room_hosts[room]
                del self.room_active_contestants[room]
                del self.room_current_question[room]
            elif websocket == self.room_hosts[room]:
                self.room_hosts[room] = self.active_rooms[room][0]
                asyncio.create_task(self.broadcast(room, {
                    "type": "new_host",
                    "data": {
                        "message": "A new host has been elected."
                    }
                }))

    async def broadcast(self, room: str, message: dict):
        if room in self.active_rooms:
            for connection in self.active_rooms[room]:
                await connection.send_json(message)

    def load_questions(self) -> List[Dict[str, Any]]:
        try:
            questions_data = questions.get_quiz_questions()
            return {"questions": questions_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def start_timer(self, room: str):
        """Manage the timer for a room and handle question flow"""
        try:
            while room in self.active_rooms:
                await asyncio.sleep(1)
                
                # Safeguard: If the room's timer isn't set, exit the loop.
                if room not in self.room_timers:
                    print(f"Room {room} not found in room_timers, stopping timer.")
                    break
                
                if self.room_timers[room] > 0:
                    self.room_timers[room] -= 1
                    await self.broadcast(room, {
                        "type": "timer",
                        "data": {
                            "timer": self.room_timers[room],
                        }
                    })
                else:
                    self.room_timers[room] = 30  # Reset timer
                    if self.room_active_contestants[room] < len(self.active_rooms[room]) - 1:
                        self.room_active_contestants[room] += 1
                        await self.broadcast(room, {
                            "type": "next_contestant",
                            "data": {
                                "active_contestant": self.room_active_contestants[room],
                            }
                        })
                    else:
                        await self.handle_next_question(room)
        except Exception as e:
            print(f"Error in start_timer: {e}")


    async def update_transcript(self, room: str, transcript: str):
        """Update and broadcast transcript changes"""
        if room in self.active_rooms:
            self.room_transcripts[room] = transcript
            await self.broadcast(room, {
                "type": "transcript_update",
                "data": {
                    "transcript": transcript,
                    "active_contestant": self.room_active_contestants[room]
                }
            })

manager = ConnectionManager()

@multiplayer.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        # If this websocket is the host, start the timer task (it may already be running)
        if websocket == manager.room_hosts[room]:
            asyncio.create_task(manager.start_timer(room))

        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "transcript_update":
                await manager.update_transcript(room, data["data"]["transcript"])
            elif data["type"] == "answer_submitted":
                await manager.handle_answer_submission(room, data["data"])
            elif data["type"] == "next_question":
                await manager.handle_next_question(room)
            else:
                await manager.broadcast(room, data)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
