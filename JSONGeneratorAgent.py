import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set in the environment variables.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

class JSONGeneratorAgent:
    def __init__(self, max_tokens=4096):
        self.model_id = "gpt-4o"
        self.max_tokens = max_tokens
        self.max_context_length = 16383  # Context length limit for the model

        # Initialize the tokenizer for the model
        self.tokenizer = tiktoken.encoding_for_model(self.model_id)

        # System prompt for the JSON generator agent
        self.sys_prompt = """ 
            You are a specialized assistant at the University of Toronto, helping new students select courses based on their refined queries. 
            The user has provided a clear set of interests, requirements, and constraints. You also have a list of relevant courses retrieved 
            by a RAG system. These courses contain essential details such as course codes, names, descriptions, prerequisites, session 
            offerings, and meeting sections. Each session code indicates when a course runs: "20249" for Fall 2024, "20251" for Winter 2025, 
            and "20249, 20251" for a year-long offering.

            Your task is to choose only from the given retrieved courses and recommend those that best match the user’s expressed goals. 
            Pay close attention to prerequisites and ensure that the user can meet them. If the user wants introductory or foundational 
            classes, highlight basic-level courses. If the user has specified a session preference, recommend only courses running in 
            those sessions. If the user prefers online or in-person courses, respect that choice as well. Make sure to consider what 
            the user wants to learn, such as specific technologies or skill sets, and ensure the recommended courses align with these desires.

            When selecting courses, give priority to those that fit the user’s academic interests, skill level, and campus choice. 
            If the user mentions department or division preferences, choose courses from those areas. If multiple courses are suitable, 
            pick a diverse range that covers different topics or skill sets. Avoid duplicates and exclude any that fail to meet prerequisites 
            or run outside the chosen sessions. If the user is exploring new fields, include courses that broaden their perspective without 
            straying from their stated goals.

            In short, recommend a set of courses that reflect the user’s refined query. Honor their preferences for session timing, 
            in-person or online delivery, department or division, and required skill level. Ensure the final selection is balanced, 
            relevant, and helpful to the user’s educational path.

            **JSON-Formatted Output**:

            - Your recommendations must strictly follow this JSON format:
            [
                {
                    "course_code": "CSC108",
                    "name": "Introduction to Computer Programming",
                    "department": "Computer Science",
                    "division": "Faculty of Arts & Science",
                    "description": "Programming in a language such as Python. Elementary data types, lists, maps...",
                    "prerequisites": "None",
                    "exclusions": "CSC148, CSC150",
                    "campus": "St. George",
                    "section_code": "F",
                    "sessions": "20249",
                    "meeting_sections": ["Lecture: Mon/Wed/Fri 10-11 AM", "Tutorial: Thu 2-3 PM"]
                },
                {
                    // More recommended courses here
                }
            ]

            NOTE: You must generate the output in strict JSON array format, adhering to the following rules: The response must start with [ and end with ]. 
            It must strictly conform to the JSON array format with no extra text, headers, or annotations. Markdown syntax such as ```json or ``` is strictly prohibited.
            - Correct Example:
                [
                    {"key": "value"},
                    {"key": "value"}
                ]

            - Incorrect Example:
                ```json
                [    
                    {"key": "value"},    
                    {"key": "value"}
                ]
                ```

            **Output Rules**:

            - Strictly output all course recommendations in the specified JSON format.
            - Ensure all fields in the JSON format are included for each recommended course. The "..." in the description should be replaced with the actual course description.
            - Make sure all recommended courses come only from the provided retrieved courses. Do not hallucinate or create new courses. 
            - Aim to provide at least 5-6 recommended courses that best match the user's needs.
            """
        self.messages = [{"role": "system", "content": self.sys_prompt}]

    def calculate_token_count(self, content):
        """Calculate the token count for a given string."""
        return len(self.tokenizer.encode(content))

    def truncate_user_query(self, user_query, remaining_token_budget):
        """
        Truncate the user query to fit within the remaining token budget.
        """
        user_query_tokens = self.tokenizer.encode(user_query)
        if len(user_query_tokens) > remaining_token_budget:
            # Keep only the tokens that fit within the budget
            truncated_tokens = user_query_tokens[:remaining_token_budget]
            return self.tokenizer.decode(truncated_tokens)
        return user_query

    def generate_json_recommendations(self, user_query, retrieved_courses):
        # Calculate token usage for system and retrieved courses
        system_tokens = self.calculate_token_count(self.sys_prompt)
        retrieved_courses_tokens = self.calculate_token_count(str(retrieved_courses))

        # Reserve tokens for the assistant's output
        reserved_for_output = self.max_tokens

        # Calculate the remaining token budget for the user query
        remaining_token_budget = (
            self.max_context_length - system_tokens - retrieved_courses_tokens - reserved_for_output
        )

        if remaining_token_budget <= 0:
            raise ValueError("Not enough token budget for system prompt and retrieved courses.")

        # Truncate user query if necessary
        truncated_user_query = self.truncate_user_query(user_query, remaining_token_budget)

        if retrieved_courses == []:
            return 'No courses were retrieved from the RAG system.'

        self.messages.append({
            "role": "user",
            "content": f"""
            User Query: {truncated_user_query} 
            Retrieved Courses: {retrieved_courses} 
            Now starts your recommendations. 
            """
        })

        try:
            output_json = client.chat.completions.create(
                model=self.model_id,
                messages=self.messages
            )
            return output_json.choices[0].message.content.strip()
        
        except Exception as e:
            print("Error during JSON generation:", str(e))
            return "Sorry, I couldn't generate the JSON recommendations at this time."
