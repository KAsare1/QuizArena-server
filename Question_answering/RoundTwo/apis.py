import os
import sys
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import nest_asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .SpeedRace import QAMLRoundTwo

nest_asyncio.apply()

# Initialize the FastAPI app
second_round_app = APIRouter()


if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

json_path = os.path.join(base_path, "RoundTwo", "Round_2.json")
json_path = os.path.normpath(json_path)

# Use the dynamically generated path
round_one = QAMLRoundTwo(json_path)


class AnswerCheckRequest(BaseModel):
    user_answer: str
    correct_answer: str


@second_round_app.get("/quiz")
def get_quiz_questions():
    questions = round_one.get_quiz_questions()
    return questions


@second_round_app.post("/check-answer")
def check_answer(request: AnswerCheckRequest):
    user_answer = request.user_answer
    correct_answer = request.correct_answer
    
    if round_one.is_correct(user_answer, correct_answer):
        return {"result": "Correct"}
    else:
        return {"result": "Incorrect"}


@second_round_app.get("/")
async def root():
    return {"message": "Hello from the Quiz API"}
