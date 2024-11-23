from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

app = Flask(__name__)
CORS(app)

# In-memory storage for conversation history
conversations = {}

system_prompt = """
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
"""
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    user_id = data.get('userId')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({'error': 'Missing userId or message'}), 400

    # Initialize conversation history for the user if not exists
    if user_id not in conversations:
        conversations[user_id] = [
            {'role': 'system', 'content': system_prompt},
        ]

    # Add user message to conversation history
    conversations[user_id].append({'role': 'user', 'content': message})

    try:
        # Call OpenAI API with conversation history
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=conversations[user_id],
        )

        bot_message = response.choices[0].message.content.strip()

        # Add assistant response to conversation history
        conversations[user_id].append({'role': 'assistant', 'content': bot_message})

        # Check if the conversation should end
        conversation_end_triggers = ['done', "that's all", 'thank you', 'thanks', 'generate']
        conversation_ended = False

        if any(trigger in message.lower() for trigger in conversation_end_triggers):
            conversation_ended = True

            # Generate the refined query based on the conversation
            refined_query_response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'Based on the conversation, generate a concise and precise query suitable for searching a course database. The query should reflect the user’s interests and requirements.'},
                    *conversations[user_id],
                ],
            )

            refined_query = refined_query_response.choices[0].message.content.strip()

            # Clear the conversation history
            del conversations[user_id]

            return jsonify({'response': bot_message, 'refinedQuery': refined_query, 'conversationEnded': True})

        return jsonify({'response': bot_message, 'conversationEnded': False})

    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    data = request.get_json()
    user_id = data.get('userId')

    if user_id in conversations:
        del conversations[user_id]

    return jsonify({'message': 'Conversation reset.'})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
