import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def decide_weights_with_llm(query):
    """
    Use an LLM to dynamically decide weights for fields based on the query.

    Args:
        query (str): The user query.

    Returns:
        dict: A dictionary of weights for each field.
    """
    prompt = f"""
    You are an intelligent assistant tasked with determining the importance of specific fields for retrieving relevant courses.

    **Query:** "{query}"

    Your task:
    - Assign weights to the following fields based on their relevance to the given query:
    - Name
    - Description
    - Prerequisites

    **Response Format:**
    - The response must be a valid JSON object.
    - The JSON object should have the keys: "name", "description", "prerequisites".
    - The values must be floating-point numbers representing weights, and the weights must sum to exactly 1.
    - Output strictly the JSON object with no additional text or explanation. ollow exactly the format shown below. Your output should start from "{" and end with "}", make sure ```json is not included in the response.

    **Example of a valid response:**
    {{
        "name": 0.3,
        "description": 0.5,
        "prerequisites": 0.2
    }}

    Now generate the JSON object based on the query.
    """

    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.7
        )
        # Extract JSON-like response
        model_output = response.choices[0].message.content.strip()
        print(model_output)
        weights = eval(response.choices[0].message.content.strip())
        
        # Validate weights sum to 1
        if not isinstance(weights, dict) or not sum(weights.values()) == 1.0:
            raise ValueError("Invalid weights returned from LLM.")
        
        return weights
    except Exception as e:
        print(f"Error with LLM response: {e}")
        # Fallback weights if LLM fails
        return {"name": 0.3, "description": 0.5, "prerequisites": 0.2}

# Example usage
query = "I am looking for courses that focus on financial mathematics, actuarial science, or investment-related topics."
weights = decide_weights_with_llm(query)
print("Weights decided by LLM:", weights)
