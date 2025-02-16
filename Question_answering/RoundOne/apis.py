import os
import sys
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import nest_asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from .FundamentalConcepts import QAMLRoundOne

nest_asyncio.apply()

# Initialize the FastAPI app
first_round_app = APIRouter()



if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

json_path = os.path.join(base_path, "RoundOne", "Round_1.json")
json_path = os.path.normpath(json_path)

# Use the dynamically generated path
round_one = QAMLRoundOne(json_path)

class AnswerCheckRequest(BaseModel):
    user_answer: str
    correct_answer: str


@first_round_app.get("/quiz")
def get_quiz_questions():
    try:
        questions = round_one.get_quiz_questions()
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @first_round_app.post("/check-answer")
# def check_answer(request: AnswerCheckRequest):
#     user_answer = request.user_answer
#     correct_answer = request.correct_answer    

#     # Call the `is_correct` method to compare the user's answer and get the result
#     result = round_one.is_correct(user_answer, correct_answer)

#     # Return the result as the response
#     return result

@first_round_app.post("/check-answer-sec")
def check_answer(request: AnswerCheckRequest):
    user_answer = request.user_answer
    correct_answer = request.correct_answer
    
    # Call your is_correct_refined function to compare answers
    if round_one.is_correct_refined(user_answer, correct_answer):
        return {"result": "Correct", "points": 3}  # Return points for correct answers
    else:
        return {"result": "Incorrect", "points": 0}  # Return 0 points for incorrect answers



@first_round_app.get("/")
async def root():
    return {"message": "Hello from the Quiz API"}
