import os
from dotenv import load_dotenv
from openai import OpenAI

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
        
        # the 
        self.sys_prompt = """ 
        You are a specialized assistant at the University of Toronto, helping new students select courses based 
        on their requirements and a list of course info retrieved by a RAG system. 
        The RAG retrieved course info will contain several parts:
            1. The course code and the course name
            2. The course description
            3. The course prerequisites 
            4. The course offerings
            5. The meeting sections

        Use the RAG retrieved course info as your primary source of factual knowledge. Your generated recommendation
        should roughly follow the following format:
            1. Start with a friendly greeting and a concise summary of the user need based on the user query.
            2. Then start recommending courses one by one based on the five parts presented in RAG retrieved 
            course info. Based on the user need and the course info, explain why each course is recommended.
            3. Summarize the recommended courses and come up with an overall summary for the learning path.
            4. Finish up by another friendly message and prompt for more instructions.
            
        Always follow these rules:
            1. Don't reveal info about the RAG system.
            2. Be professional, friendly, curious, and helpful.
            3. **Ensure that each course description follows the specified example format below:**
            **Example Format:**
            ```
            [
                {
                    "course_code": "CSC108",
                    "name": "Introduction to Computer Programming",
                    "department": "Computer Science",
                    "division": "Faculty of Arts & Science",
                    "description": "An introduction to programming using Python...",
                    "prerequisites": "None",
                    "exclusions": "CSC148, CSC150",
                    "campus": "St. George",
                    "section_code": "F",
                    "meeting_sections": ["Lecture: Mon/Wed/Fri 10-11 AM", "Tutorial: Thu 2-3 PM"]
                }
            ]  
            ```
            You must strictly follow this format for each course you recommend.
            
        **Summary:**
        Your primary role is to engage new students in a supportive and informative dialogue, patiently eliciting the necessary
        information to provide tailored course recommendations. Always prioritize the student's comfort and understanding, ensuring that 
        the conversation remains open and student-centered.
        """
        self.messages = [{"role": "system", "content": self.sys_prompt}]

    def generate_response(self, user_query, retrieved_courses):
        # Add user query and retrieved courses to the conversation
        self.messages.append({
            "role": "user",
            "content": f"""
            User Query: {user_query}
            Retrieved Courses: {retrieved_courses}
            Now starts your recommendations.
            """
        })

        try:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=self.messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            #print("Response generated successfully.")
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
