import json
import os
import sys
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import random
from Question_answering.RoundOne.FundamentalConcepts import QAMLRoundOne


AI_agent_app = APIRouter()

# ---------------------------
# Pydantic Models
# ---------------------------
class Question(BaseModel):
    sn: int
    has_preamble: bool
    preamble_text: Optional[str]
    question_text: str
    has_question_figure: bool
    has_answer_figure: bool
    correct_answer: str
    calculations_present: bool
    subject: str

class NormalDifficultyInput(BaseModel):
    difficulty: str  # "easy", "intermediate", "hard"
    questions: List[Question]

class NormalDifficultyOutput(BaseModel):
    sn: int
    bot_answer: str
    is_correct: bool 

class CustomDifficultyInput(BaseModel):
    question: Question
    user_correct_count: int    
    bot_correct_count: int     

class CustomDifficultyOutput(BaseModel):
    sn: int
    bot_answer: str
    is_correct: bool


class QuestionBank:
    def __init__(self, file_path: str):
        # Open the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        # Convert the raw data to our internal format
        self.questions = []

        # Create subject-based indices for faster lookup
        self.subject_questions = {}
        for q in self.questions:
            subject = q['subject']
            if subject not in self.subject_questions:
                self.subject_questions[subject] = []
            self.subject_questions[subject].append(q)

    def get_wrong_answer(self, current_question: Question) -> str:
        """
        Get a wrong answer from the question bank for the given question.
        The wrong answer will be from the same subject but from a different question.
        """
        subject = current_question.subject
        subject_questions = self.subject_questions.get(subject, [])
        
        # Filter out the current question and questions with similar text
        current_question_text = current_question.question_text.lower()
        current_preamble = (current_question.preamble_text or "").lower()
        
        possible_answers = []
        for q in subject_questions:
            # Skip if it's the same question
            if q['question'].lower() == current_question_text:
                continue
                
            # Skip if it's too similar (part of the same preamble)
            if current_preamble and q['preamble'] and current_preamble == q['preamble'].lower():
                continue
                
            possible_answers.append(q['answer'])
        
        if possible_answers:
            return random.choice(possible_answers)
        else:
            # Fallback if no suitable answer is found
            return f"No answer available for this {subject} question."



if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Access Round_1.json from AIAgent/Agent.py
json_path = os.path.join(base_path, "RoundOne", "Round_1.json")
json_path = os.path.normpath(json_path)

# Use the dynamically generated path
question_bank = QuestionBank(json_path)

# ---------------------------
# Global Reinforcement Tracking for Custom Difficulty
# ---------------------------
class CustomAgentPerformance:
    def __init__(self):
        self.user_correct_count = 0
        self.bot_correct_count = 0
        self.bot_accuracy_probability = 0.5

    def update(self, user_correct: bool, bot_correct: bool):
        if user_correct:
            self.user_correct_count += 1
        if bot_correct:
            self.bot_correct_count += 1
        diff = self.user_correct_count - self.bot_correct_count
        self.bot_accuracy_probability = 0.5 + 0.1 * diff
        self.bot_accuracy_probability = max(0.05, min(0.95, self.bot_accuracy_probability))

custom_performance = CustomAgentPerformance()

# ---------------------------
# Helper Function to Generate an Answer
# ---------------------------
def generate_answer(question: Question, should_be_correct: bool) -> str:
    if should_be_correct:
        return QAMLRoundOne.convert_latex_to_plain_text(question.correct_answer)
    else:
        if question.calculations_present:
            try:
                correct_value = float(question.correct_answer)
                offset = correct_value * random.uniform(0.1, 0.3)
                wrong_value = correct_value + offset
                return f"{wrong_value:.2f}"
            except ValueError:
                return "42"
        else:
            if question.subject.lower() == "biology":
                if "compare" in question.question_text.lower() or "distinguish" in (question.preamble_text or "").lower():
                    parts = question.correct_answer.split("whereas")
                    if len(parts) == 2:
                        return f"{parts[1].strip()}, whereas {parts[0].strip()}"
                    
                common_bio_terms = ["cell membrane", "cytoplasm", "nucleus", "mitochondria", 
                                  "chloroplast", "cell wall", "vacuole"]
                return f"The {random.choice(common_bio_terms)} is responsible for this process"
            
            return f"Incorrect answer for {question.subject} question."

# ---------------------------
# API Endpoint for Normal Difficulty
# ---------------------------
@AI_agent_app.post("/normal", response_model=List[NormalDifficultyOutput])
def normal_difficulty(input_data: NormalDifficultyInput):
    # Define the percentage of questions to be answered correctly for each difficulty
    difficulty_correct_percentages = {
        "easy": 0.8,  # 80% correct answers
        "intermediate": 0.5,  # 50% correct answers
        "hard": 0.2,  # 20% correct answers
    }
    
    difficulty = input_data.difficulty.lower()
    if difficulty not in difficulty_correct_percentages:
        raise HTTPException(status_code=400, detail="Invalid difficulty level.")
    
    # Calculate how many questions should be answered correctly
    total_questions = len(input_data.questions)
    correct_count = round(total_questions * difficulty_correct_percentages[difficulty])
    
    # Create a list of indices and randomly select which questions to answer correctly
    all_indices = list(range(total_questions))
    correct_indices = set(random.sample(all_indices, correct_count))
    
    # Generate answers
    results = []
    for i, question in enumerate(input_data.questions):
        if i in correct_indices:
            answer = question.correct_answer
            is_correct = True  # Bot's answer is correct
        else:
            answer = question_bank.get_wrong_answer(question)
            is_correct = False  # Bot's answer is incorrect
            
        results.append(NormalDifficultyOutput(
            sn=question.sn,
            bot_answer=answer,
            is_correct=is_correct  # Include whether the answer is correct
        ))
    
    return results

# ---------------------------
# API Endpoint for Custom Difficulty
# ---------------------------
@AI_agent_app.post("/custom", response_model=CustomDifficultyOutput)
def custom_difficulty(input_data: CustomDifficultyInput):
    # Calculate how likely the bot should be to give a correct answer
    score_difference = input_data.user_correct_count - input_data.bot_correct_count
    
    # If user is doing better than bot (positive difference), bot should try harder
    # If bot is doing better than user (negative difference), bot should make more mistakes
    bot_accuracy_probability = 0.5 + (0.1 * score_difference)
    
    # Keep probability between 5% and 95%
    bot_accuracy_probability = max(0.05, min(0.95, bot_accuracy_probability))
    
    # Decide whether to give correct or wrong answer
    should_answer_correctly = random.random() < bot_accuracy_probability
    
    # Generate the answer
    if should_answer_correctly:
        answer = input_data.question.correct_answer
        is_correct = True  # Bot's answer is correct
    else:
        answer = question_bank.get_wrong_answer(input_data.question)
        is_correct = False  # Bot's answer is incorrect
    
    return CustomDifficultyOutput(
        sn=input_data.question.sn,
        bot_answer=answer,
        is_correct=is_correct  # Include whether the answer is correct
    )