# import google.generativeai as genai
# from fastapi import UploadFile, File
# from fastapi import APIRouter
# import os
# import nest_asyncio



# genai.configure(api_key='AIzaSyBHGgND_IpLd67G1lA_vkwyiBDnx3aNY4U')


# def generate_questions_from_pdf(pdf_file_path):
#     # Load the generative model
#     model = genai.GenerativeModel("gemini-1.5-flash")
    
#     # Upload the PDF file
#     sample_pdf = genai.upload_file(pdf_file_path)
    
#     # Define the task for generating questions
#     task = """
#     Your task is to analyze a provided PDF file and generate around 10 questions based on its content. 
#     The questions should be formatted as a JSON array, with each question represented as an object with the following keys:

#     - "S/N": The serial number of the question.
#     - "Has Preamble": Indicate whether the question has a preamble or context (Yes/No).
#     - "Preamble Text": If the question has a preamble, provide the preamble text here.
#     - "Question": The actual question text.
#     - "Question has figure": Indicate whether the question refers to a figure or image (Yes/No).
#     - "Answer has figure": Indicate whether the answer requires a figure or image (Yes/No).
#     - "Answer": The answer to the question.
#     - "calculations present": Indicate whether the answer involves calculations (Yes/No).
#     - "Subject": The subject or topic of the question.

#     Here are the steps to follow:

#     1. Read the provided PDF file carefully:
#     <PDF_FILE>{$PDF_FILE}</PDF_FILE>

#     2. As you read through the content, identify potential areas or topics that could be used to generate questions. 
#        Consider the following guidelines for generating questions:
#         - Questions should be based on the information presented in the PDF and should not require external knowledge.
#         - Questions should cover a range of topics and difficulty levels.
#         - Questions can be multiple-choice, true/false, fill-in-the-blank, or open-ended.
#         - Some questions may require calculations or refer to figures or images in the PDF.

#     3. For each question you generate, create a JSON object following the specified format. 
#        Assign a unique serial number (S/N) to each question, and provide the appropriate values for the other keys based on the question's characteristics.

#     4. Once you have generated around 10 questions, compile them into a JSON array.

#     5. Output ONLY the final JSON array:

#     [
#     {
#     "S/N": 1,
#     "Has Preamble": "Yes/No",
#     "Preamble Text": "...",
#     "Question": "...",
#     "Question has figure": "Yes/No",
#     "Answer has figure": "Yes/No",
#     "Answer": "...",
#     "calculations present": "Yes/No",
#     "Subject": "..."
#     },
#     {
#     "S/N": 2,
#     ...
#     },
#     ...
#     ]
#     """
    
#     # Generate the content based on the PDF
#     response = model.generate_content([task, sample_pdf])
    
#     # Return the JSON response
#     return response.text


# # Define the folder where PDF files will be saved
# BOOKS_FOLDER = "books"

# # Ensure the 'books' directory exists
# if not os.path.exists(BOOKS_FOLDER):
#     os.makedirs(BOOKS_FOLDER)


# nest_asyncio.apply()

# # Initialize the FastAPI app
# new_questions = APIRouter()

# @new_questions.post("/generate-questions/")
# async def generate_questions(file: UploadFile = File(...)):
#     # Define the path to save the PDF in the 'books' folder
#     file_location = os.path.join(BOOKS_FOLDER, file.filename)
    
#     # Save the uploaded file in the 'books' directory
#     with open(file_location, "wb") as f:
#         content = await file.read()
#         f.write(content)
    
#     # Generate the questions from the saved PDF
#     result = generate_questions_from_pdf(file_location)
    
#     # Return the result as JSON
#     return {"questions": result}