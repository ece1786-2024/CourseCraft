from openai import OpenAI
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY is not set in the environment variables.")
    exit(1)

client = OpenAI(api_key=api_key)
resume_file_path = "test_resume.pdf" 
try:
    reader = PdfReader(resume_file_path)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text()
except Exception as e:
    print(f"Error reading the PDF file: {e}")
    exit(1)

# TODO: to be improved
prompt = """
Based on the following resume and the user's interest in becoming an AI engineer, suggest four to five courses that will help with their career goal, and explain why those suggested courses are important:
{resume_text}
"""

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that give suggestions about course recommendation."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.7
    )

except Exception as e:
    print("Error during API call: {}".format(e))

    exit(1)

output_text = response.choices[0].message.content.strip()

output_file = "AI_course_suggestions.txt"
try:
    with open(output_file, "w") as file:
        file.write(output_text)
    print("Response saved to {}".format(output_file))

except Exception as e:
    print("Error saving the response to {}: {}".format(output_file, e))

