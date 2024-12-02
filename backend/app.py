from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
import sys
import json

uploaded_resumes = {}

# Add the parent directory (where `RAG` is located) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.data_retriever_pinecone import retrieve_courses_from_db
from JSONGeneratorAgent import JSONGeneratorAgent
from TextRecommendationAgent import TextRecommendationAgent

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

app = Flask(__name__)
CORS(app)

# In-memory storage for conversation history
conversations = {}

system_prompt = """
        You are a general academic advisor at the University of Toronto, assisting first-year students with course selection and program guidance. Your goal is to gather information to provide personalized course and program recommendations based on the student's interests, skills, and experiences.

        **Your Role and Objectives:**

        1. **Introduction:**
        - Begin the conversation by informing the student that you're collecting information to provide personalized course and program recommendations.
        - **Example Message:**
            ```
            Hello! 😊 I'm here to help you select courses and explore programs that align with your interests and goals. Please share any information about your passions, skills, or experiences to help me provide the best suggestions for your studies.
            ```
        - **Resume Upload:**
            - Let the student know they can upload their resume to help tailor recommendations.
            - **Example Message:**
            ```
            If you'd like, you can upload your resume to help me better understand your background and provide more personalized recommendations.
            ```

        2. **Information Gathering:**
        - Ask open-ended questions to learn about the student's interests, academic goals, department, campus, faculty, and any specific constraints on courses or programs.
        - **Ask One Question at a Time:** Ensure each question is concise and focused.
        - **Behavior Guidelines:**
            - **Patient Inquiry:** Allow the student ample time to respond.
            - **Open-Ended Questions:** Encourage detailed answers.
            - **Avoid Recommending or Predicting Interests:** Do not recommend courses or predict areas of interest, even if asked.
            - **Guide Towards 'generate':** Encourage the student to type 'generate' when they're ready to receive recommendations.
            - **Focus on Information Gathering:** Do not initiate recommendations.

        3. **Understanding Student Needs:**
        - Help the student clarify their thoughts by asking relevant questions.
        - **Example Questions:**
            - "What subjects or activities have you enjoyed in the past?"
            - "Are there any particular skills you'd like to develop during your first year?"
            - "Do you have interests outside academics you'd like to explore through your courses?"
            - "How do you feel about your current program choice? Are there aspects you're excited or unsure about?"

        4. **Concluding Information Gathering:**
        - **From Round 3 Onwards:** Inform the student they can type 'generate' to receive their personalized course recommendations.
        - **Example Message:**
            ```
            If you feel you've shared enough information, you can type 'generate' to receive your personalized course recommendations.
            ```

        **Additional Guidelines:**

        - **Tone and Style:**
        - Maintain a friendly, empathetic, and approachable demeanor.
        - Use simple language for clarity.

        - **Listening and Responding:**
        - Acknowledge the student's responses before asking the next question.
        - **Example:**
            ```
            That's great that you're interested in environmental science! 🌿 What other areas are you curious about?
            ```

        - **Consistency:**
        - Keep track of the conversation to ensure relevance in your questions.

        **Summary:**
        Your primary role is to engage the student in a supportive dialogue, patiently gathering information to provide 
        tailored course and program recommendations. Do not recommend courses or predict interests during this phase. Instead, 
        guide the student to type 'generate' when they're ready to receive recommendations, focusing solely on information gathering. 
        Always prioritize the student's comfort and ensure the conversation is open, friendly, and student-centered.

        """

def generate_final_output(refined_query, retrieved_courses):
    # Generate the final output using the refined query and retrieved courses
    print("Generating final output...")
    json_agent = JSONGeneratorAgent(max_tokens=4096)
    text_agent = TextRecommendationAgent(max_tokens=4096)
    
    course_json = json_agent.generate_json_recommendations(refined_query, retrieved_courses)
    text_recommendations = text_agent.generate_text_recommendations(course_json)
    return course_json, text_recommendations

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    user_id = data.get('userId')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({'error': 'Missing userId or message'}), 400

    # Initialize conversation history for the user if not exists
    if user_id not in conversations:
        system_messages = [{'role': 'system', 'content': system_prompt}]

        # Check if the user has uploaded a resume
        if user_id in uploaded_resumes:
            system_messages.append(
                {"role": "system", "content": f"The user's resume:\n{uploaded_resumes[user_id]}"}
            )
        # else:
        #     system_messages.append(
        #         {"role": "system", "content": "No resume was uploaded for this user."}
        #     )
        
        conversations[user_id] = system_messages

    # Add user message to conversation history
    conversations[user_id].append({'role': 'user', 'content': message})
    
    try:
        # Call OpenAI API with conversation history
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=conversations[user_id],
        )

        bot_message = response.choices[0].message.content.strip()

        # Add assistant response to conversation history
        conversations[user_id].append({'role': 'assistant', 'content': bot_message})

        # Check if the conversation should end
        conversation_end_triggers = ['generate']
        conversation_ended = False

        if any(trigger in message.lower() for trigger in conversation_end_triggers):
            conversation_ended = True

            # Generate the refined query based on the conversation
            refined_query_prompt = """
                Based on the conversation, generate a detailed and precise user query. 
                The query should reflect all of the student's interests, goals, preferences, and any constraints they have 
                mentioned. Be sure to explicitly state whether or not the student has provided information about campus, 
                department, faculty, or any specific hard constraints, as this information is crucial for filtering in 
                subsequent steps. The query should be written in the third person and include all useful information the 
                student has provided.

                Example of the desired format:
                The student is interested in an introductory course in machine learning and AI at the University of 
                Toronto's St. George campus. They prefer an entry-level course, focusing on broad concepts of ML and AI 
                without specific experience in mathematics or programming prerequisites. The student is keen on exploring 
                various aspects of machine learning, possibly including neural networks, natural language processing, and 
                robotics, with an eye towards applying this knowledge in a versatile career setting. They have expressed an 
                openness to foundational learning and potential exploration of AI's diverse applications.
            """
            refined_query_response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': refined_query_prompt},
                    *conversations[user_id],
                ]
            )
            refined_query = refined_query_response.choices[0].message.content.strip()

            print(refined_query)

            # Generate a filter for retrieving courses based on the refined query
            filter_prompt = """
                You are a system designed to generate a filter for database searches. Based on the refined user query and the user’s conversation history, create a filter in JSON format that will retrieve relevant courses from the database.

                ### Filter Requirements:
                1. **Department**: Select the department that best matches the user’s interests or goals. You must strictly use one of the following valid department values:
                - None
                - ASDN: Arts and Science, Office of the Dean
                - African Studies Centre
                - Arts & Science Internship Program
                - Arts & Science Internship Program - Year 2
                - Arts & Science Internship Program - Year 3
                - Canadian Institute for Theoretical Astrophysics
                - Centre for Caribbean Studies
                - Centre for Criminology and Sociolegal Studies
                - Centre for Diaspora & Transnational Studies
                - Centre for Drama, Theatre and Performance Studies
                - Centre for Entrepreneurship
                - Centre for Ethics
                - Centre for European and Eurasian Studies
                - Centre for Industrial Relations and Human Resources
                - Centre for Study of United States
                - Centre for Teaching and Learning (UTSC)
                - Cinema Studies Institute
                - Contemporary East and Southeast Asian Studies
                - Cross-Disciplinary Programs Office
                - Department for the Study of Religion
                - Department of Anatomy and Cell Biology
                - Department of Anthropology
                - Department of Anthropology (UTSC)
                - Department of Art History
                - Department of Astronomy and Astrophysics
                - Department of Biochemistry
                - Department of Biological Sciences (UTSC)
                - Department of Biology
                - Department of Cell and Systems Biology
                - Department of Chemical Engineering and Applied Chemistry
                - Department of Chemical and Physical Sciences
                - Department of Chemistry
                - Department of Civil and Mineral Engineering
                - Department of Classics
                - Department of Computer Science
                - Department of Earth Sciences
                - Department of East Asian Studies
                - Department of Ecology and Evolutionary Biology
                - Department of Economics
                - Department of English
                - Department of English (UTSC)
                - Department of English and Drama
                - Department of French
                - Department of Geography and Planning
                - Department of Geography, Geomatics and Environment
                - Department of Germanic Languages & Literatures
                - Department of Global Development Studies (UTSC)
                - Department of Health and Society (UTSC)
                - Department of Historical Studies
                - Department of History
                - Department of Human Geography (UTSC)
                - Department of Immunology
                - Department of Italian Studies
                - Department of Laboratory Medicine and Pathobiology
                - Department of Language Studies
                - Department of Language Studies (UTSC)
                - Department of Linguistics
                - Department of Management
                - Department of Management (UTSC)
                - Department of Materials Science and Engineering
                - Department of Mathematical and Computational Sciences
                - Department of Mathematics
                - Department of Mechanical & Industrial Engineering
                - Department of Molecular Genetics
                - Department of Near & Middle Eastern Civilizations
                - Department of Nutritional Sciences
                - Department of Pharmacology
                - Department of Philosophy
                - Department of Philosophy (UTSC)
                - Department of Physics
                - Department of Physiology
                - Department of Political Science
                - Department of Political Science (UTSC)
                - Department of Psychology
                - Department of Psychology (UTSC)
                - Department of Slavic and East European Languages & Cultures
                - Department of Sociology
                - Department of Sociology (UTSC)
                - Department of Spanish and Portuguese
                - Department of Statistical Sciences
                - Department of Visual Studies
                - Dept. of Arts, Culture & Media (UTSC)
                - Dept. of Computer & Mathematical Sci (UTSC)
                - Dept. of Historical & Cultural Studies (UTSC)
                - Dept. of Physical & Environmental Sci (UTSC)
                - Division of Engineering Science
                - Edward S. Rogers Sr. Dept. of Electrical & Computer Engin.
                - Engineering First Year Office
                - Faculty of Applied Science & Engineering
                - Faculty of Arts and Science
                - Faculty of Kinesiology and Physical Education
                - Faculty of Music
                - Human Biology Program
                - Indigenous Studies - Arts & Science
                - Innis College
                - Inst for Studies in Transdisciplinary Engin Educ & Practice
                - Inst. for the History & Philosophy of Science & Technology
                - Institute for Management and Innovation
                - Institute for the Study of University Pedagogy
                - Institute of Biomedical Engineering
                - Institute of Communication and Culture
                - Jewish Studies
                - John H. Daniels Faculty of Architecture, Landscape, & Design
                - Munk School of Global Affairs and Public Policy
                - New College
                - Ontario Institute for Studies in Education/Univ. of Toronto
                - Rotman Commerce
                - School of Environment
                - Sexual Diversity Studies
                - South Asian Studies
                - St. Michael's College
                - Trinity College
                - University College
                - Victoria College
                - Women and Gender Studies Institute
                - Woodsworth College

                2. **Campus**: Select the campus that matches the user’s preferences. Use one of the following valid campus values:
                - Centennial College
                - Off Campus
                - Scarborough
                - Sheridan College
                - St. George
                - University of Toronto at Mississauga

                ### Expected Output Format:
                The output must be strictly in JSON format, such as:
                {
                    "department": {"$eq": "Department of Computer Science"},
                    "campus": {"$eq": "St. George"}
                }

                ### Notes:
                1. The output must be strictly in JSON format without any additional text or explanation.
                2. Do not include any additional text such as ``` json ``` or ``` { } ``` in the output, start with {}.

                The filter should include:
                1. **Department**: Use the department that best matches the user's stated interests or goals. If the user has not specified a department, default to "No Department information."
                2. **Campus**: Use the campus that aligns with the user's preferences. If no campus is mentioned, default to "St. George."
                3. Ensure that the filter is structured for a MongoDB query using `$eq` for equality matching.
            """
            filter_response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': filter_prompt},
                    *conversations[user_id]
                ]
            )

            filter = filter_response.choices[0].message.content.strip()
            print(filter_response)

            try:
                filter_dict = json.loads(filter)
            except json.JSONDecodeError as e:
                print("Error parsing JSON:", e)
                filter_dict = {
                    "department": {
                        "$in": [
                            "Centennial College",
                            "Off Campus",
                            "Scarborough",
                            "Sheridan College",
                            "St. George",
                            "University of Toronto at Mississauga"
                        ]
                    }
                }

            # Retrieve courses from the database based on the refined query
            retrieved_courses = retrieve_courses_from_db(refined_query, filter_dict)

            # Generate the final output using the refined query and retrieved courses
            course_json, text_recommendations = generate_final_output(refined_query, retrieved_courses)

            # Clear the conversation history
            del conversations[user_id]

            # Return the final output to the frontend
            return jsonify({
                'response': text_recommendations,
                'finalOutput': course_json,
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


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    user_id = request.form.get('userId')
    if 'resume' not in request.files or not user_id:
        return jsonify({'error': 'No file or userId provided'}), 400

    file = request.files['resume']

    # Save the file to a desired location
    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, f"{user_id}_{file.filename}")
    file.save(file_path)

    # Process the resume
    resume_text = ''
    try:
        # Check the file extension
        if file.filename.lower().endswith('.pdf'):
            # Read and extract text from the PDF file
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    resume_text += page.extract_text()
        else:
            return jsonify({'error': 'Unsupported file type. Please upload a PDF file.'}), 400
    except Exception as e:
        print(f"Error reading resume file: {e}")
        return jsonify({'error': 'Failed to read resume file.'}), 500

    # Optionally limit the amount of text to prevent exceeding context length
    max_resume_length = 2000  # Adjust as needed
    if len(resume_text) > max_resume_length:
        resume_text = resume_text[:max_resume_length] + '...'

    # Append the resume text to the user's conversation history
    if user_id in conversations:
        conversation_history = conversations[user_id]
    else:
        # Initialize conversation history if it doesn't exist
        conversation_history = [
            {"role": "system", "content": system_prompt}
        ]
        conversations[user_id] = conversation_history

    # Append the resume text as a user message
    conversation_history.append({"role": "user", "content": f"My resume:\n{resume_text}"})

    return jsonify({'message': 'Resume uploaded and processed successfully.'}), 200


    
if __name__ == '__main__':
    app.run(port=5000, debug=True)
