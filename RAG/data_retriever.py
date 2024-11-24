import faiss
import numpy as np
from pymongo import MongoClient
# from weights_decider import decide_weights_with_llm
import time
from openai import OpenAI
from dotenv import load_dotenv
from mongodb.db_store import extract_lecture_meeting_sections
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI()

MONGO_URI = os.getenv('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)

# def decide_weights(query):
#     weights = decide_weights_with_llm(query)
#     # weights = {"name": 0.0, "description": 1.0, "prerequisites": 0.0, "division_department": 0.0}
#     return weights

def retrieve_courses_from_db(query, num_results=19):
    try:
        print("Connecting to MongoDB...")
        # Connect to MongoDB
        db = mongo_client['uoft_courses']
        courses_collection = db['courses']
        meeting_sections_collection = db['meeting_sections']

        # Encode the user's query
        print("Encoding the user query...")
        try:
            query_embedding = openai_client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = query_embedding.data[0].embedding
            query_embedding = np.array(query_embedding, dtype="float32").reshape(1, -1)
            print("Query encoded successfully.")
        except Exception as e:
            print(f"Error encoding query: {e}")
            return []

        # Decide weights for hybrid approach
        # print("Deciding weights for hybrid approach...")
        # weights = decide_weights(query)
        # print(f"Weights: {weights}")

        # Retrieve all courses with embeddings
        print("Retrieving courses from database...")
        try:
            docs = list(courses_collection.find({}, {  # No filter, include all documents
                "_id": 0,
                "course_id": 1,
                "course_code": 1,
                "name": 1,
                "description": 1,
                "prerequisites": 1,
                "embedding": 1,
                "department": 1,
                "division": 1,
                "exclusions": 1,
                "campus": 1,
                "section_code": 1,
            }))
        except Exception as e:
            print(f"Error retrieving courses from database: {e}")
            return []

        if not docs:
            print("No courses with embeddings found in the database.")
            return []

        # Prepare embeddings and course references for FAISS search
        combined_embeddings = []
        all_courses = []

        for doc in docs:
            try:
                # Retrieve embeddings for each field
                # name_emb = np.array(doc.get("name_embedding", []), dtype="float32")
                # desc_emb = np.array(doc.get("description_embedding", []), dtype="float32")
                # prereq_emb = np.array(doc.get("prerequisites_embedding", []), dtype="float32")
                # div_emb = np.array(doc.get("division_department_embedding", []), dtype="float32")

                # # Combine embeddings using dynamic weights
                # combined_emb = (
                #     weights["name"] * name_emb +
                #     weights["description"] * desc_emb +
                #     weights["prerequisites"] * prereq_emb +
                #     weights["division_department"] * div_emb
                # )

                # combined_embeddings.append(combined_emb)
                combined_embeddings.append(doc.get("embedding", []))
                all_courses.append(doc)
            except Exception as e:
                print(f"Error processing document {doc.get('course_id', 'unknown')}: {e}")
                continue

        # Convert combined embeddings to numpy array
        try:
            combined_embeddings = np.vstack(combined_embeddings)
        except ValueError as e:
            print(f"Error stacking embeddings: {e}")
            return []

        if combined_embeddings.size == 0:
            print("No valid embeddings found for the courses.")
            return []

        # Initialize FAISS index for vector search
        try:
            index = faiss.IndexFlatL2(combined_embeddings.shape[1])
            index.add(combined_embeddings)
        except Exception as e:
            print(f"Error initializing FAISS index: {e}")
            return []

        # Perform vector search for the top 'num_results' similar courses
        try:
            D, I = index.search(query_embedding, num_results)
        except Exception as e:
            print(f"Error during FAISS search: {e}")
            return []

        # Retrieve the most similar courses
        retrieved_courses = []
        course_ids_seen = set()

        for idx in I[0]:
            try:
                course = all_courses[idx]

                # Avoid duplicate courses in results
                if course['course_id'] in course_ids_seen:
                    continue

                # Retrieve the meeting_sections for this course
                meeting_sections = list(meeting_sections_collection.find({'course_id': course['course_id']}))

                # Build a string representation of the meeting_sections
                meeting_info = '\n'.join(extract_lecture_meeting_sections(course['course_id'], meeting_sections))

                # Create the combined text
                combined_text = """This course {code} - '{name}' is offered by the {department} department in the {division}.
                Course Description: {description}
                Understanding the course code: {code}: The first three letters represent the department ({department_code}),
                and the section code {section_code} indicates when it's offered - 'F' means Fall semester (September-December),
                'S' means Winter semester (January-April), and 'Y' means full year course.
                Prerequisites required: {prerequisites}
                Exclusions: {exclusions}
                This course is offered at the {campus} campus during these sessions: {sessions}.
                Meeting Sections: {meeting_info}
                """.format(
                    code=course.get('course_code', 'N/A'),
                    name=course.get('name', 'N/A'),
                    department=course.get('department', 'N/A'),
                    division=course.get('division', 'N/A'),
                    description=course.get('description', 'N/A'),
                    department_code=course.get('course_code', 'N/A')[:3],
                    section_code=course.get('section_code', 'N/A'),
                    prerequisites=course.get('prerequisites', 'No prerequisites'),
                    exclusions=course.get('exclusions', 'No exclusions'),
                    campus=course.get('campus', 'N/A'),
                    sessions=', '.join(course.get('sessions', [])) or 'N/A',
                    meeting_info=meeting_info or 'N/A'
                )

                retrieved_courses.append(combined_text)
                course_ids_seen.add(course['course_id'])

                # Limit the number of results
                if len(retrieved_courses) >= num_results:
                    break
            except Exception as e:
                print(f"Error processing course {idx}: {e}")
                continue

        return retrieved_courses

    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

if __name__ == '__main__':
    # Set multiprocessing start method
    # try:
    #     import torch.multiprocessing as mp
    #     mp.set_start_method('spawn', force=True)
    # except RuntimeError:
    #     pass  # Start method has already been set

    # User query
    query = """
    Refined User Query: The student is interested in an introductory course in machine learning and AI at the University of Toronto's St. George campus. They prefer an entry-level course, focusing on broad concepts of ML and AI without specific experience in mathematics or programming prerequisites. The student is keen on exploring various aspects of machine learning, possibly including neural networks, natural language processing, and robotics, with an eye towards applying this knowledge in a versatile career setting. They have expressed an openness to foundational learning and potential exploration of AI's diverse applications.

    Possible guesses on courses: 
    - Introduction to Machine Learning, Computer Science Department, St. George Campus, Faculty of Arts & Science. This course might cover the basics of supervised and unsupervised learning, decision trees, regression models, and introductory neural networks. There might be initial discussion of real-world applications such as image and speech recognition.
    - AI Fundamentals, Computer Science Department, St. George Campus, Faculty of Arts & Science. This course could delve into foundational AI concepts, including problem-solving, search algorithms, basic natural language processing, and an overview of AI development history and ethical implications.
    - Basics of Data Science and AI, Institute of Data Science, St. George Campus, Faculty of Arts & Science. This course might offer an introduction to data handling, basic statistical analysis, machine learning libraries, and AI applications across various fields.
    - Foundations of Neural Networks, Computer Science Department, St. George Campus, Faculty of Arts & Science. While being a bit more focused, this course might introduce neural network architectures, training algorithms, and early applications.

    These courses would provide a solid starting ground for a comprehensive understanding of machine learning and AI, preparing you for more advanced topics later on.
    """
    # Measure start time
    start_time = time.time()

    # Retrieve similar courses
    results = retrieve_courses_from_db(query)

    # Measure end time
    end_time = time.time()

    # Calculate and print the elapsed time
    elapsed_time = end_time - start_time
    print(f"Time taken to retrieve courses: {elapsed_time:.2f} seconds")

    # Print the list of formatted strings
    for result in results:
        print(result)
        print('---')  # Separator between courses

