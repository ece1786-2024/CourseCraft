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

class ResponseGeneratorAgent:
    def __init__(self, max_tokens=4096):
        self.model_id = "gpt-3.5-turbo"  
        self.max_tokens = max_tokens
        self.max_context_length = 16385  # Context length limit for the model

        # Initialize the tokenizer for the model
        self.tokenizer = tiktoken.encoding_for_model(self.model_id)
        
        # the 
        self.sys_prompt = """ 
        You are a specialized assistant at the University of Toronto, helping new students select courses 
        based on their requirements and a list of course information retrieved by a RAG system. 
        The RAG retrieved course info will contain several parts:
            1. The course code and the course name
            2. The course description
            3. The course prerequisites 
            4. The course offerings
            5. The meeting sections

        Your task is to analyze the RAG retrieved course information and recommend the most relevant courses 
        based on the user's expressed interests, requirements, department/division, faculty, campus and goals provided earlier in the conversation.

        **Important Guidelines for Recommendations:**
        1. **Prioritize Relevance**:
            - Focus on courses that align with the user's academic interests, skill level, and stated goals.
            - If the user is a beginner, prioritize introductory or foundational courses.
            - Include courses that match the user's preferences for specific topics, skills, or career goals.

        2. **Diversify Recommendations**:
            - Recommend courses across different areas that align with the user's interests to give them a range of options.

        3. **Deduplicate and Filter Irrelevant Courses**:
            - Avoid recommending duplicate or overlapping courses.
            - Exclude courses that don't match the user's requirements (e.g., courses with prerequisites the user doesn’t meet).

        4. **JSON-Formatted Output**:
            - Your recommendation must strictly follow this JSON format:
            **Example Format:**
            [
                {
                    "course_code": "CSC108",
                    "name": "Introduction to Computer Programming",
                    "department": "Computer Science",
                    "division": "Faculty of Arts & Science",
                    "description": "Programming in a language such as Python. Elementary data types, lists, maps. Program structure: control flow, functions, classes, objects, methods. Algorithms and problem solving. Searching, sorting, and complexity. Unit testing. Floating-point numbers and numerical computation. No prior programming experience required. NOTE: You may take CSC148H1 after CSC108H1. You may not take CSC108H1 in the same term as, or after taking, any of CSC110Y1/CSC111H1/CSC120H1/CSC148H1.",
                    "prerequisites": "None",
                    "exclusions": "CSC148, CSC150",
                    "campus": "St. George",
                    "section_code": "F",
                    "meeting_sections": ["Lecture: Mon/Wed/Fri 10-11 AM", "Tutorial: Thu 2-3 PM"]
                },
                {
                    More recommended courses here
                }
            ]

        5. **Weight Course Features**:
            - Give higher priority to courses with:
                - A good match to the user's requirements.
                - If the user mentions about prerequisites and exlucions or corequisites, extract those courses first.
                - Make sure the campus is the same as the user's campus.

        6. **Output Rules**:
            - Strictly output all course recommendations in a JSON format for each course.
            - Do not include any explanations or additional text outside the JSON structure.
            - Ensure all fields in the JSON format are included for each recommended course.

        Use this approach to provide the user with the most relevant, useful, and personalized recommendations based on their preferences.

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
    

    def generate_response(self, user_query, retrieved_courses):
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

        # Add truncated user query and retrieved courses to the conversation
        self.messages.append({
            "role": "user",
            "content": f"""
            User Query: {truncated_user_query}
            Retrieved Courses: {retrieved_courses}
            Now starts your recommendations.
            """
        })

        try:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=self.messages,
                max_tokens=self.max_tokens,
                temperature=1
            )
            return response.choices[0].message.content
        except Exception as e:
            print("Error during response generation:", str(e))
            return "Sorry, I couldn't generate a response at this time."



if __name__ == "__main__":
    agent = ResponseGeneratorAgent()
    user_query = "I'm a first-year student interested in introductory computer science courses."
    retrieved_courses = [
        #"Course: CSC108 - Introduction to Computer Programming\nDescription: An introduction to programming using Python.",
        #"Course: CSC148 - Introduction to Computer Science\nDescription: Basic data structures and algorithms.",
        """This course MIE369H1 - 'Introduction to Artificial Intelligence' is offered by the N/A department in the N/A.
                Course Description: Introduction to Artificial Intelligence. Search. Constraint Satisfaction. Propositional and First-order Logic Knowledge Representation. Representing Uncertainty (Bayesian networks). Rationality and (Sequential) Decision Making under Uncertainty. Reinforcement Learning. Weak and Strong AI, AI as Engineering, Ethics and Safety in AI.
                Understanding the course code: MIE369H1: The first three letters represent the department (MIE),
                and the section code N/A indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: MIE250H1/ECE244H1/ECE345H1/CSC263H1/CSC265H1, MIE236H1/ECE286H1/ECE302H1
                Exclusions: No exclusions
                This course is offered at the N/A campus during these sessions: N/A.
                Meeting Sections: N/A
        """
    ]
    response = agent.generate_response(user_query, retrieved_courses)
    print("\nGenerated Response:\n", response)