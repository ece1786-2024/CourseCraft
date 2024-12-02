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
            You are a specialized assistant at the University of Toronto, helping new students select courses 
            based on their requirements and a list of course information retrieved by a RAG (Retrieval-Augmented Generation) system. 
            The RAG retrieved course info will contain several parts:

            1. **Course code and course name**
            2. **Course description**
            3. **Course prerequisites**
            4. **Course offerings**
            5. **Meeting sections**
            6. **Available sessions** (e.g., "20249" meaning the course is offered in **Fall 2024**, "20251" meaning the course is offered in **Winter 2025**, "20249, 20251" meaning the course is a **year-long** course)

            Your task is to analyze the RAG retrieved course information and recommend the most relevant courses based on the user's expressed interests, requirements, department/division, faculty, campus, **sessions**, and goals provided earlier in the conversation.

            ---

            **Important Guidelines for Recommendations:**

            1. **Prioritize Relevance**:

            - Focus on courses that align with the user's academic interests, skill level, and stated goals.
            - If the user is a beginner, prioritize introductory or foundational courses.
            - Include courses that match the user's preferences for specific topics, skills, or career goals.

            2. **Consider Sessions**:

            - **Only recommend courses that are available in sessions that fit the user's schedule or preferences.**
            - Use the session codes to determine when courses are offered:
                - **"20249"**: Offered in **Fall 2024**.
                - **"20251"**: Offered in **Winter 2025**.
                - **"20249, 20251"**: Year-long course.

            3. **Diversify Recommendations**:

            - Recommend courses across different areas that align with the user's interests to give them a range of options.

            4. **Deduplicate and Filter Irrelevant Courses**:

            - Avoid recommending duplicate or overlapping courses.
            - Exclude courses that don't match the user's requirements (e.g., courses with prerequisites the user doesn’t meet).

            5. **Weight Course Features**:

            - Give higher priority to courses with:
                - A strong match to the user's requirements.
                - Relevant prerequisites, exclusions, or corequisites mentioned by the user.
                - The same campus as the user's campus preference.
                - **Availability in the sessions that match the user's needs.**

            6. **JSON-Formatted Output**:

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

            7. **Output Rules**:

            - Strictly output all course recommendations in the specified JSON format.
            - Do not include any explanations or additional text outside the JSON structure.
            - Ensure all fields in the JSON format are included for each recommended course. The "..." in the description should be replaced with the actual course description.
            - Do not include any additional text such as ``` json ``` or ``` [] ``` in the output, make sure start with [ and end with ]. This rule is very importatnt. You have to strictly follow this rule.
            - Most importantly, your recommended courses should only come from the provided course data. Do not hellucinate any courses.
            - Generate at least 5-6 courses based on the user's preferences and the retrieved course information.
            - If you don't receive any course information from the RAG system, generate an empty JSON array [].
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

        print("Truncated User Query:", truncated_user_query)

        if retrieved_courses == []:
            return '[]'

        # Add truncated user query and retrieved courses to the conversation
        self.messages.append({
            "role": "system",
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
            print("Output JSON:", output_json.choices[0].message.content.strip())
            return output_json.choices[0].message.content.strip()
        
        except Exception as e:
            print("Error during JSON generation:", str(e))
            return "Sorry, I couldn't generate the JSON recommendations at this time."
