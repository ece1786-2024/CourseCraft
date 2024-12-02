import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
from JSONGeneratorAgent import JSONGeneratorAgent

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY is not set in the environment variables.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

class TextRecommendationAgent:
    def __init__(self, max_tokens=1000):
        self.model_id = "gpt-4o"
        self.max_tokens = max_tokens
        self.max_context_length = 16383  # Context length limit for the model

        # Initialize the tokenizer for the model
        self.tokenizer = tiktoken.encoding_for_model(self.model_id)

        # System prompt for the text-based recommendations agent
        self.sys_prompt = """ 
            You are a specialized assistant at the University of Toronto, helping new students select courses based on their requirements and a list of recommended courses provided in JSON format. The JSON contains detailed course information, including:

            1. **Course code and course name**
            2. **Course description**
            3. **Course prerequisites**
            4. **Course offerings**
            5. **Meeting sections**
            6. **Available sessions**

            Your task is to analyze the provided JSON-formatted course recommendations and generate text-based recommendations to present to the user.

            ---

            **Important Guidelines for Recommendations:**

            1. **Use the Provided Courses:**

            - Only use the courses from the provided JSON data for your recommendations.
            - Ensure that all courses in your text-based recommendations come from this data.

            2. **Prioritize Relevance:**

            - Focus on courses that align with the user's academic interests, skill level, and stated goals.
            - Highlight how each course matches the user's preferences.

            3. **Consider Sessions:**

            - Mention the session availability for each course in user-friendly terms (e.g., "Fall 2024" instead of "20249").

            4. **Concise Text-Based Output:**

            - Present your recommendations in **text format**, using **point form**.
            - For each course, **provide a brief description of why it suits the user**, including session availability.
            - Be **concise** and focus on the key reasons each course is a good fit.

            5. **Friendly and Helpful Tone:**

            - Use a friendly and approachable tone in your recommendations.
            - Ensure the language is clear and easy to understand.

            6. **Output Rules:**

            - **Do not include any additional text or explanations outside the point-form recommendations.**
            - Present the recommendations in the following format:

            **Example Format:**

            **CSC108: Introduction to Computer Programming**
                - Ideal for beginners interested in programming.
                - No prior experience required; covers fundamental concepts in Python.
                - Offered in **Fall 2024** at the **St. George** campus, aligning with your campus and session preferences.

            **MAT135: Calculus I**
                - Great for strengthening mathematical foundations.
                - Essential for various science and engineering programs.
                - Available in **Winter 2025**, fitting your schedule.
            ---

            Use this approach to provide the user with the most relevant, useful, and personalized recommendations based on their preferences. Ensure that your recommendations are clear, friendly, and helpful.
        """

        self.messages = [{"role": "system", "content": self.sys_prompt}]

    def calculate_token_count(self, content):
        """Calculate the token count for a given string."""
        return len(self.tokenizer.encode(content))

    def truncate_content(self, content, remaining_token_budget):
        """
        Truncate the content to fit within the remaining token budget.
        """
        content_tokens = self.tokenizer.encode(content)
        if len(content_tokens) > remaining_token_budget:
            # Keep only the tokens that fit within the budget
            truncated_tokens = content_tokens[:remaining_token_budget]
            return self.tokenizer.decode(truncated_tokens)
        return content

    def generate_text_recommendations(self, course_json):
        # Calculate token usage for system and course_json
        system_tokens = self.calculate_token_count(self.sys_prompt)
        course_json_tokens = self.calculate_token_count(course_json)

        if course_json == "[]":
            return "It seems there are no course recommendations available at the moment."

        # Reserve tokens for the assistant's output
        reserved_for_output = self.max_tokens

        # Calculate the remaining token budget
        remaining_token_budget = (
            self.max_context_length - system_tokens - course_json_tokens - reserved_for_output
        )

        if remaining_token_budget <= 0:
            raise ValueError("Not enough token budget for system prompt and course JSON.")

        # Truncate course_json if necessary
        truncated_course_json = self.truncate_content(course_json, remaining_token_budget)

        # Add the course_json to the conversation
        self.messages.append({
            "role": "user",
            "content": f"""
            Here are the recommended courses in JSON format:
            {truncated_course_json}
            Please generate the text-based recommendations based on these courses.
            """
        })

        try:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=self.messages,
                max_tokens=self.max_tokens,
                temperature=1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("Error during text recommendation generation:", str(e))
            return "Sorry, I couldn't generate the text recommendations at this time."
        
# Example usage
if __name__ == "__main__":
    # Assuming you have user_query and retrieved_courses from earlier in your code

    # Initialize the JSON generator agent
    json_agent = JSONGeneratorAgent(max_tokens=4096)

    user_query = "I'm a first-year student interested in introductory computer science courses."
    retrieved_courses = []

    # Generate the JSON recommendations
    course_json = json_agent.generate_json_recommendations(user_query, retrieved_courses)

    # Initialize the text recommendation agent
    text_agent = TextRecommendationAgent(max_tokens=4096)

    # Generate the text-based recommendations
    text_recommendations = text_agent.generate_text_recommendations(course_json)

    # Now you can use `course_json` for your frontend UI components
    # And present `text_recommendations` to the user
    print(text_recommendations)
