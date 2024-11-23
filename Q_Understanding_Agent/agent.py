import openai
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

# Set the API key for OpenAI
openai.api_key = api_key

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
    {"role": "system", "content": (
        "You are an academic advisor specializing in course selection and academic planning at the University of Toronto. "
        "Your role is to assist students in navigating their academic journey, with a focus on selecting the most suitable courses.\n\n"
        "Your primary task is to engage with students to gather detailed information about their academic background, career goals, future plans, and personal interests. "
        "Use this information to infer what courses the student might be interested in, but do not reveal these guesses to the student. Instead, craft a refined query that "
        "encapsulates what the student is looking for, enriched with contextual details. Make sure the conversation lasts for at least 3 turns, and you should gain as much information "
        "as possible to describe the interests the user has and include a rich description in the refined user query. For guesses course suggestions, be more general, and provide as much "
        "possible guesses as you can. However, you should say exact course name and division, department, campus information you guessed. Take a deep breath, make sure that before you return "
        "the final output, you have to notify the user and once the user confirmed, you can return it. The final output should follow the exact format as, Refined User Query: ..., Possible guesses "
        "on courses: .... No other texts should be included in the final output, and make sure you ask the user to get the final output before you return them, no matter what the user say previously. "
        "Ask the user to say specific key words so that you know when to return the final output, for example you can say, \"I'm ready to give you some course suggestions, just say 'generate' when you are ready\", "
        "something like that. If the user is not ready, then proceed with the conversation again to understand the user more, you can ask the user again later on to see if they are ready.\n\n"
        "In the final output:\n\n"
        "Refined User Query: Describe student's needs as detailed as possible, providing enough context to guide the retrieval process.\n"
        "Course Suggestions: Include potential course recommendations from UofT's current offerings. These should be described in detail (course name, department, campus, division, course description, instructors, etc.) "
        "to enhance the relevance of retrieval from the RAG model. Especially for course descriptions, you have to be as detailed as you can, you have to say what exact concepts each course teaches and what might be some possible "
        "pre-requisites associated with this course. For example, for a course CSC413 at UofT, the description should be something like this: An introduction to neural networks and deep learning. Backpropagation and automatic differentiation. "
        "Architectures: convolutional networks and recurrent neural networks. Methods for improving optimization and generalization. Neural networks for unsupervised and reinforcement learning. Understanding the course code: CSC413H5: The first three letters "
        "represent the department (CSC), and the section code N/A, 'S' means Winter semester (January-April), and 'Y' means full year course. Prerequisites required: CSC311H5 or CSC411H5.\n\n"
        "Make sure your possible course guesses do not mention course code. As you interact with the student, adapt your communication style to be empathetic and relatable, ensuring you gain as much information as possible. Once you feel confident that you have gathered sufficient "
        "details, end the conversation and provide your final output. Your goal is to ensure the refined query serves as the most effective input for the RAG pipeline to retrieve the best possible matches from the database. Once you returned your final output, do not say anything else other than the final output."
    )},
    {"role": "system", "content": f"The user's resume:\n{resume_text}"}
]

print("Hello! I’m here to help you with course recommendations. Let’s start by understanding your academic background and goals.")

try:
    while True:
        # Generate a single question
        question_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation_history,
            max_tokens=2048,
            temperature=1
        )
        
        response = question_response.choices[0].message.content.strip()
        print(f"Assistant: {response}")
        
        # Get user input
        user_response = input("User: ").strip()
        
        # Exit condition
        if user_response.lower() == "generate":
            print("Generating your refined query and possible course suggestions...")
            break
        elif user_response.lower() in {"exit", "quit"}:
            print("Thank you for the conversation. Ending now.")
            exit(0)

        # Add user response to conversation history
        conversation_history.append({"role": "assistant", "content": response})
        conversation_history.append({"role": "user", "content": user_response})

except Exception as e:
    print(f"Error during API interaction: {e}")
    exit(1)

# Generate the final refined query
try:
    refined_query_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history + [
            {"role": "user", "content": (
                "Based on the user's resume and the conversation, generate the final output as a detailed refined query."
            )}
        ],
        max_tokens=2048,
        temperature=1
    )
    refined_query = refined_query_response.choices[0].message.content.strip()
    print("\nRefined Query:")
    print(refined_query)

    # Format the refined query with new lines
    formatted_query = "\n\n".join(
        f"{line.strip()}" for line in refined_query.split(". ") if line.strip()
    )

    # Write the formatted refined query to a text file
    with open("refined_query.txt", "w") as file:
        file.write(f"Refined Query:\n\n{formatted_query}\n")
    print("Refined query saved to 'refined_query.txt'.")

except Exception as e:
    print(f"Error generating the refined query: {e}")
    exit(1)
