import os
from groq import Groq
from dotenv import load_dotenv
from mongodb.data_retriever import retrieve_courses_from_db

# Load API key from .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

class ResponseGeneratorAgent:
    def __init__(self, max_tokens=10000):
        self.model_id = "llama3-70b-8192"
        self.client = client
        self.max_tokens = max_tokens
        self.start_prompt = f""" 
            You are a specialized assistant at the University of Toronto, helping new students navigate studies, campus life, and courses. Use the RAG system as your primary source of factual knowledge, while exercising judgment to ensure that the information provided is relevant to the user's situation.

            Guidelines:
            Use Retrieved Knowledge: Always rely on RAG for facts, but carefully evaluate the relevance of the retrieved information. Only provide course details and suggestions that align with the user's background and needs (e.g., recommend beginner courses to first-year students). Filter out the extracted information that may not be suitable or helpful based on the user's context and do not mention them.
            Persona-Driven Responses: Use your persona's background and experience to personalize your responses, guiding conversations with appropriate context and expertise.
            Communication Style: Adapt your style according to your persona. Be empathetic, relatable, and explain university-specific terms in simple language.
            Clarification and Honesty: If something is unclear, ask politely for clarification. If a question is outside your scope, direct the student to additional resources or services.
        """

        self.messages = [{"role": "system", "content": self.start_prompt}]

    def generate_response(self, user_query, retrieved_courses):
        """
        Generate a response based on user query and retrieved courses.

        Args:
            user_query (str): The refined query from the Query Understanding Agent.
            retrieved_courses (list): List of retrieved courses with descriptions.

        Returns:
            str: The generated response.
        """
        self.messages.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=self.messages
            )
            print("Response generated successfully.")
            return response.choices[0].message.content
        except Exception as e:
            print("Error during response generation:", str(e))
            return "Sorry, I couldn't generate a response at this time."

# Main function to test the agent
if __name__ == "__main__":
    agent = ResponseGeneratorAgent()

    # Example input
    user_query = "I'm a first-year student interested in introductory computer science courses."
    retrieved_courses = [
        "Course: CSC108 - Introduction to Computer Programming\nDescription: An introduction to programming using Python.",
        "Course: CSC148 - Introduction to Computer Science\nDescription: Basic data structures and algorithms.",
    ]

    # Prepare the system and user messages
    prompt = f"""
    You are a specialized assistant at the University of Toronto, helping new students navigate studies, campus life, and courses. Use the RAG system as your primary source of factual knowledge, while exercising judgment to ensure that the information provided is relevant to the user's situation.

    User Query: {user_query}
    Retrieved Courses: {retrieved_courses}

    Generate a concise and informative recommendation for the user.
    """

    # Generate response
    response = agent.generate_response(prompt, retrieved_courses) # Response generation with RAG
    # response = agent.generate_response(user_query, retrieved_courses) # Response generation without RAG
    print("\nGenerated Response:\n", response)
