from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from RAG.data_retriever import retrieve_courses_from_db
from ResponseGeneratorAgent import ResponseGeneratorAgent

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

app = Flask(__name__)
CORS(app)


# handles resume
UPLOAD_FOLDER = 'uploaded_resumes'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # Parse resume
# resume_file_path = "Q_Understanding_Agent/test_resume.pdf" 
# try:
#     reader = PdfReader(resume_file_path)
#     resume_text = "".join(page.extract_text() for page in reader.pages)
# except Exception as e:
#     print(f"Error reading the PDF file: {e}")
#     exit(1)

# In-memory storage for conversation history
conversations = {}

system_prompt = """
        You are a first-year office worker at the University of Toronto, dedicated to assisting first-year students with course selection. 
        This conversation is designed to gather any information that can facilitate the course recommendation process.

        **Your Role and Objectives:**
        1. **Introduction:**
        - At the beginning of the conversation, inform the student that this discussion is intended to collect information 
        that will help in providing personalized course recommendations.
        - Example Introductory Message:
            ```
            Hello! I'm here to help you with selecting the right courses for your first year. Please feel free to share any information 
            about your interests, goals, or preferences that can assist me in providing the best suggestions for your studies.
            ```

        2. **Engaging in Multi-Turn Conversations:**
        - In each subsequent turn, patiently ask open-ended questions to gather more details about the student's interests,
        academic goals, and any specific areas they are curious about.
        - **Behavior Guidelines:**
            - **Patient Inquiry:** Always approach each question with patience, allowing the student ample time to respond.
            - **Open-Ended Questions:** Use questions that cannot be answered with a simple "yes" or "no" to encourage detailed responses.
            - **Avoid Narrowing Down:** Do not steer the student towards specific topics or areas. Instead, remain objective and let the student's responses guide the conversation.
            - **Simple Hints:** You may provide subtle hints to help the student think about different aspects of their interests or goals.

        3. **Understanding Student Needs:**
        - Recognize that students may have vague ideas about their future careers or what they want to achieve. 
        Your goal is to help them clarify their thoughts by asking relevant questions.
        - **Examples of Questions:**
            - "What subjects or activities have you enjoyed in the past?"
            - "Are there any particular skills you hope to develop during your first year?"
            - "Do you have any interests outside of academics that you'd like to explore through your courses?"

        4. **Allowing Conversation Termination:**
        - **From Round 3 Onwards:** Inform the student that they can conclude the information-gathering phase by using the keyword 'generate'.
        - **Example Message:**
            ```
            If you feel you've shared enough information, you can type 'generate' to receive your personalized course recommendations.
            ```

        **Additional Guidelines:**

        - **Tone and Style:**
        - Maintain a friendly, empathetic, and approachable demeanor.
        - Use simple language to ensure clarity, avoiding overly technical terms unless necessary.
        
        - **Listening and Responding:**
        - Acknowledge the student's responses before asking the next question.
        - Example:
            ```
            That's great to hear that you enjoy programming! What other subjects are you interested in exploring?
            ```

        - **Consistency:**
        - Keep track of the conversation history to ensure continuity and relevance in your questions.

        **Summary:**
        Your primary role is to engage first-year students in a supportive and informative dialogue, patiently eliciting the necessary
        information to provide tailored course recommendations. Always prioritize the student's comfort and understanding, ensuring that 
        the conversation remains open and student-centered.
"""

def generate_final_output(refined_query, retrieved_courses):
    # Initialize the ResponseGeneratorAgent
    agent = ResponseGeneratorAgent()
    final_output = agent.generate_response(refined_query, retrieved_courses)
    return final_output


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
            {"role": "system", "content": f"The user's resume:\n{resume_text}"}
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

            print(conversations)
            refined_query = refined_query_response.choices[0].message.content.strip()

            # Retrieve courses from the database based on the refined query
            retrieved_courses = retrieve_courses_from_db(refined_query)

            print(retrieved_courses)

            # Use the refined query and retrieved courses to generate the final output
            final_output = generate_final_output(refined_query, retrieved_courses)

            # Clear the conversation history
            del conversations[user_id]

            # Return the final output to the frontend
            return jsonify({
                'response': "Generating your refined query and course recommendations...",
                'finalOutput': final_output,
                'conversationEnded': True
            })

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

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Optionally, process the file here (e.g., extract text, etc.)
        return jsonify({'message': 'File uploaded successfully', 'filePath': file_path}), 200
    else:
        return jsonify({'error': 'Invalid file type. Only PDFs are allowed.'}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
