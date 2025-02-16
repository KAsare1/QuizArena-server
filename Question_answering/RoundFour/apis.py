import os
import sys
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from .TrueOrFalse import QAMLRoundFour

fourth_round_app = APIRouter()

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

json_path = os.path.join(base_path, "RoundFour", "Round_4.json")
json_path = os.path.normpath(json_path)

# Use the dynamically generated path
round_four = QAMLRoundFour(json_path)

class AnswerCheckRequest(BaseModel):
    user_answer: str
    correct_answer: str

@fourth_round_app.get("/quiz")
def get_quiz_questions():
    questions = round_four.get_quiz_questions()
    return questions


@fourth_round_app.post("/check-answer")
def check_answer(request: AnswerCheckRequest):
    user_answer = request.user_answer
    correct_answer = request.correct_answer
    
    if round_four.is_correct(user_answer, correct_answer):
        return {"result": "Correct"}
    else:
        return {"result": "Incorrect"}

