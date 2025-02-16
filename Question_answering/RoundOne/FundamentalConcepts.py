import pandas as pd
import random
import re
import math
from difflib import SequenceMatcher
from pylatexenc.latex2text import LatexNodes2Text
import json
import os


# genai.configure(api_key='AIzaSyBHGgND_IpLd67G1lA_vkwyiBDnx3aNY4U')

class QAMLRoundOne:
    def __init__(self, questions_file_path):
        self.questions_file_path = questions_file_path
        self.questions = self.load_questions()
    
    def load_questions(self):
        try:
            return pd.read_json(self.questions_file_path)
        except Exception as e:
            print(f"Error loading questions: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of error
    
    def preprocess_answer(self, answer):
        answer = answer.lower()
        answer = re.sub(r'[^\w\s]', '', answer)
        answer = answer.strip()
        return answer
    
    def is_correct_refined(self, user_answer, correct_answer, threshold=0.4):
        user_answer = self.preprocess_answer(user_answer)
        correct_answer = self.preprocess_answer(correct_answer)
        
        if user_answer == correct_answer:
            return True
        
        similarity = SequenceMatcher(None, user_answer, correct_answer).ratio()
        return similarity >= threshold
    
    # def is_correct(self, user_answer, correct_answer):
    #     task = f"""
    #     You will be acting as a virtual quizmistress, analyzing a user's answer to a question and providing a score from 0-3 based on how correct or incorrect the user's answer is compared to the actual correct answer.

    #     Here are the steps you should follow:

    #     1. You will receive two inputs: {user_answer} and {correct_answer}. Compare the {user_answer} to the {correct_answer}.

    #     2. Based on this comparison, determine a score from 0-3 using the following criteria:
    #     - 3: The {user_answer} is essentially the same as the {correct_answer}, with only very minor differences like phrasing or word choice.
    #     - 2: The {user_answer} contains the core concepts of the {correct_answer} but is missing some key details or has some incorrect information.
    #     - 1: The {user_answer} shows some basic understanding of the topic but is largely incorrect or missing most of the key points in the {correct_answer}.
    #     - 0: The {user_answer} is completely wrong or unrelated to the {correct_answer}.

    #     3. Provide a brief reason explaining why you assigned that particular score. The reason should justify the score based on how the {user_answer} compares to the {correct_answer}.

    #     4. Output your response in the following format:
        
    #         <reason for score>Your explanation here</reason for score>
    #         <score>The numeric score from 0-3</score>

    #     Do not include any other text in your output besides the reason and score inside their respective XML tags. Follow the format exactly.
    #     """

    #     # Load the model
    #     model = genai.GenerativeModel("gemini-1.5-flash")

    #     # Send the task to the model to generate content
    #     response = model.generate_content([task])

    #     # Print the response to check output format
    #     print(response.text)

    #     # Example to handle the XML-style output
    #     try:
    #         # Extract the reason and score from the response using XML tags
    #         reason = response.text.split("<reason for score>")[1].split("</reason for score>")[0]
    #         score = int(response.text.split("<score>")[1].split("</score>")[0])

    #         # Return the extracted reason and score
    #         return {"reason": reason, "score": score}

    #     except IndexError:
    #         # Handle parsing errors
    #         return {"error": "Failed to parse the response"}


    
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
    
    def select_questions(self, preamble_groups, standalone_questions, count):
        selected_questions = []
        
        random.shuffle(standalone_questions)
        
        for question in standalone_questions:
            if len(selected_questions) < count:
                selected_questions.append(question)
        
        preamble_list = list(preamble_groups.values())
        random.shuffle(preamble_list)
        
        for group in preamble_list:
            if len(selected_questions) + len(group) <= count:
                selected_questions.extend(group)
        
        return selected_questions
    
    def sanitize_questions(self, questions):
        """
        Recursively checks and replaces any NaN, Infinity, or -Infinity
        values with zero or another placeholder in the questions data.
        """
        if isinstance(questions, float):
            if math.isnan(questions) or math.isinf(questions):
                return 0.0  # Replace invalid float with a placeholder
        elif isinstance(questions, dict):
            return {key: self.sanitize_questions(value) for key, value in questions.items()}
        elif isinstance(questions, list):
            return [self.sanitize_questions(item) for item in questions]
        return questions
    
    def convert_latex_to_plain_text(self, questions):
        """
        Convert LaTeX-formatted text in the 'Question' and 'Answer' fields of the dataset to plain text.

        :param data: List of dictionaries containing the dataset
        :return: Updated dataset with LaTeX content converted to plain text
        """
        # Initialize LaTeX to text converter
        latex_to_text_converter = LatexNodes2Text()

        # Process each entry in the dataset
        for entry in questions:
            # Convert the LaTeX 'Question' field to plain text
            latex_question = entry.get("Question", "")
            plain_question = latex_to_text_converter.latex_to_text(latex_question)
            entry["Question"] = plain_question

            # Convert the LaTeX 'Answer' field to plain text
            latex_answer = entry.get("Answer", "")
            plain_answer = latex_to_text_converter.latex_to_text(latex_answer)
            entry["Answer"] = plain_answer

        return questions

    def get_quiz_questions(self):
        categorized = self.categorize_by_subject()
        final_selection = []
        
        for subject, subject_questions in categorized.items():
            preamble_groups, standalone_questions = self.handle_preamble_questions(subject_questions)
            selected = self.select_questions(preamble_groups, standalone_questions, 6)
            final_selection.extend(selected)
        
        random.shuffle(final_selection)
        final_selection = self.convert_latex_to_plain_text(final_selection)
        
        return self.sanitize_questions(final_selection)
