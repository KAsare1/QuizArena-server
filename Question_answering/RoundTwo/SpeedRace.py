import pandas as pd
import random
import re
from difflib import SequenceMatcher



class QAMLRoundTwo:
    def __init__(self, questions_file_path):
        self.questions_file_path = questions_file_path
        self.questions = self.load_questions()
    
    def load_questions(self):
        return pd.read_json(self.questions_file_path)
    
    def preprocess_answer(self, answer):
        answer = answer.lower()
        answer = re.sub(r'[^\w\s]', '', answer)
        answer = answer.strip()
        return answer
    
    def is_correct(self, user_answer, correct_answer, threshold=0.8):
        user_answer = self.preprocess_answer(user_answer)
        correct_answer = self.preprocess_answer(correct_answer)
        
        if user_answer == correct_answer:
            return True
        
        similarity = SequenceMatcher(None, user_answer, correct_answer).ratio()
        return similarity >= threshold
    
    
    def categorize_by_subject(self):
        subjects = {}
        for _, question in self.questions.iterrows():
            subject = question['Subject']
            if subject not in subjects:
                subjects[subject] = []
            subjects[subject].append(question.to_dict())
        return subjects
    
    def handle_preamble_questions(self, subject_questions):
        preamble_groups = {}
        standalone_questions = []
        
        for question in subject_questions:
            if question["Has Preamble"] == "Yes":
                preamble_text = question["Preamble Text"]
                if preamble_text not in preamble_groups:
                    preamble_groups[preamble_text] = []
                preamble_groups[preamble_text].append(question)
            else:
                standalone_questions.append(question)
        
        return preamble_groups, standalone_questions
    
    def select_questions(self, preamble_groups, standalone_questions, count_per_subject):
        selected_questions = []

        for group in preamble_groups.values():
            random.shuffle(group)
            selected_questions.extend(group[:count_per_subject])

        random.shuffle(standalone_questions)
        selected_questions.extend(standalone_questions[:count_per_subject])

        return selected_questions[:count_per_subject * len(preamble_groups) + count_per_subject]

    
    def get_quiz_questions(self):
        categorized = self.categorize_by_subject()
        final_selection = []
        
        for subject, subject_questions in categorized.items():
            preamble_groups, standalone_questions = self.handle_preamble_questions(subject_questions)
            selected = self.select_questions(preamble_groups, standalone_questions, 6)
            final_selection.extend(selected)
        
        random.shuffle(final_selection)
        
        return final_selection