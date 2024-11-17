from openai import OpenAI
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()

# Validate OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY is not set in the environment variables.")
    exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Parse resume
resume_file_path = "test_resume.pdf"  # Replace with your file path
try:
    reader = PdfReader(resume_file_path)
    resume_text = ""
    for page in reader.pages:
        resume_text += page.extract_text()
except Exception as e:
    print(f"Error reading the PDF file: {e}")
    exit(1)

# Initialize conversation history
conversation_history = [
    {"role": "system", "content": "You are an assistant that asks questions one at a time to understand a user's skills, interests, and goals for course recommendations."},
    {"role": "system", "content": f"The user's resume:\n{resume_text}"}
]

print("Hello! Let’s start by understanding your interests. I’ll ask you one question at a time.")

try:
    while True:
        # Generate a single question
        question_response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history + [
                {"role": "assistant", "content": "What question should I ask next to better understand the user?"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        question = question_response.choices[0].message.content.strip()
        print(f"Assistant: {question}")
        
        # Get user input
        user_response = input("You: ").strip()
        
        # Exit condition
        if user_response.lower() in {"exit", "quit"}:
            print("Thank you for the conversation! Let me summarize the information gathered.")
            break
        
        # Add user response to conversation history
        conversation_history.append({"role": "assistant", "content": question})
        conversation_history.append({"role": "user", "content": user_response})

except Exception as e:
    print(f"Error during API interaction: {e}")
    exit(1)

# Generate the final refined query
try:
    refined_query_response = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation_history + [
            {"role": "assistant", "content": "Based on the user's resume and the conversation, generate a refined query that can aid in course searching and selection. The query should summarize the user's goals, interests, and needs for courses."}
        ],
        max_tokens=300,
        temperature=0.7
    )
    refined_query = refined_query_response.choices[0].message.content.strip()
    print("\nRefined Query:")
    print(refined_query)

except Exception as e:
    print(f"Error generating the refined query: {e}")
    exit(1)
