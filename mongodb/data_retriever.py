import faiss
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from weights_decider import decide_weights_with_llm
import time

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)

def decide_weights(query):
    weights = decide_weights_with_llm(query)
    # weights = {"name": 0.0, "description": 1.0, "prerequisites": 0.0}
    return weights

def retrieve_courses_from_db(query, model, num_results=10):
    if model is None:
        print("Model is not provided.")
        return []

    try:
        print("Connecting to MongoDB...")
        # Connect to MongoDB
        db = client['university_courses']
        courses_collection = db['courses']
        meeting_sections_collection = db['meeting_sections']

        # Encode the user's query
        print("Encoding the user query...")
        try:
            query_embedding = model.encode(query, device='cpu', convert_to_numpy=True, num_workers=0).reshape(1, -1)
            print("Query encoded successfully.")
        except Exception as e:
            print(f"Error encoding query: {e}")
            return []

        # Decide weights for hybrid approach
        print("Deciding weights for hybrid approach...")
        weights = decide_weights(query)
        print(f"Weights: {weights}")

        # Retrieve all courses with embeddings
        print("Retrieving courses from database...")
        try:
            docs = list(courses_collection.find(
                {"name_embedding": {"$exists": True}, "description_embedding": {"$exists": True}},
                {
                    "_id": 0,
                    "course_id": 1,
                    "course_code": 1,
                    "name": 1,
                    "description": 1,
                    "prerequisites": 1,
                    "name_embedding": 1,
                    "description_embedding": 1,
                    "prerequisites_embedding": 1,
                }
            ))
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
                name_emb = np.array(doc.get("name_embedding", []), dtype="float32")
                desc_emb = np.array(doc.get("description_embedding", []), dtype="float32")
                prereq_emb = np.array(doc.get("prerequisites_embedding", []), dtype="float32")

                # Combine embeddings using dynamic weights
                combined_emb = (
                    weights["name"] * name_emb +
                    weights["description"] * desc_emb +
                    weights["prerequisites"] * prereq_emb
                )

                combined_embeddings.append(combined_emb)
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
                meeting_sections_str = ''
                for ms in meeting_sections:
                    try:
                        times_str = ''
                        for time in ms.get('times', []):
                            day = time.get('day', '')
                            start = time.get('start', '')
                            end = time.get('end', '')
                            location = time.get('location', '')
                            times_str += f"Day {day}, {start}-{end} at {location}; "
                        ms_info = (
                            f"Section: {ms.get('section_code', '')}, "
                            f"Type: {ms.get('type', '')}, "
                            f"Instructors: {', '.join(ms.get('instructors', []))}, "
                            f"Times: {times_str.strip('; ')}, "
                            f"Size: {ms.get('size', 0)}, "
                            f"Enrolment: {ms.get('enrolment', 0)}, "
                            f"Notes: {ms.get('notes', '')}"
                        )
                        meeting_sections_str += ms_info + '\n'
                    except Exception as e:
                        print(f"Error processing meeting section: {e}")
                        continue

                # Create a string representation of the course
                course_string = (
                    f"Course Code: {course.get('course_code', '')}\n"
                    f"Name: {course.get('name', '')}\n"
                    f"Description: {course.get('description', '')}\n"
                    f"Prerequisites: {course.get('prerequisites', '')}\n"
                    f"Meeting Sections:\n{meeting_sections_str}"
                )

                # Append to results
                retrieved_courses.append(course_string)
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
    try:
        import torch.multiprocessing as mp
        mp.set_start_method('spawn', force=True)
    except RuntimeError:
        pass  # Start method has already been set

    # Load pre-trained Sentence-BERT model
    print("Loading SentenceTransformer model...")
    try:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device="cpu")
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        exit()

    # User query
    query = "I want to take machine learning courses and I'm only considering Computer Science courses. For example, introduction to machine learning, deep learning, and reinforcement learning."

    # Measure start time
    start_time = time.time()

    # Retrieve similar courses
    results = retrieve_courses_from_db(query, model=model)

    # Measure end time
    end_time = time.time()

    # Calculate and print the elapsed time
    elapsed_time = end_time - start_time
    print(f"Time taken to retrieve courses: {elapsed_time:.2f} seconds")

    # Print the list of formatted strings
    for result in results:
        print(result)
        print('---')  # Separator between courses

