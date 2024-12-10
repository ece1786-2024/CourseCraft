import os
import sys
import time
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

print(sys.path)

from mongodb.db_store import extract_lecture_meeting_sections


# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
MONGO_URI = os.getenv('MONGO_URI')

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Name of the Pinecone index
INDEX_NAME = "course-embeddings"

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['uoft_courses']
courses_collection = db['courses']
meeting_sections_collection = db['meeting_sections']

def sanitize_metadata_field(value, default_value):
    if not value or value in [None, [], '', 'null']:
        return default_value
    return value


def upsert_embeddings_to_pinecone():
    print("Upserting embeddings to Pinecone...")
    index = pc.Index(INDEX_NAME)

    batch_size = 100
    docs = list(courses_collection.find({}, {
        "_id": 0,
        "course_id": 1,
        "course_code": 1,
        "section_code": 1,
        "department": 1,
        "campus": 1,
        "division": 1,
        "description": 1,
        "prerequisites": 1,
        "exclusions": 1,
        "sessions": 1,
    }))

    # Prepare and upsert embeddings in batches
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        texts = []
        ids = []
        metadata_list = []
        for doc in batch:
            try:
                # Extract fields, substituting defaults as needed
                course_id = str(doc.get('course_id', 'N/A'))
                course_code = doc.get('course_code', 'N/A')
                name = doc.get('name', 'N/A')
                section_code = doc.get('section_code', 'N/A')
                department = doc.get('department', 'N/A')
                campus = doc.get('campus', 'N/A')
                division = doc.get('division', 'N/A')
                description = doc.get('description', 'N/A')
                prerequisites = doc.get('prerequisites', 'No prerequisites')
                if not prerequisites or prerequisites in [None, [], 'null']:
                    prerequisites = 'No prerequisites'
                if not prerequisites:
                    prerequisites = 'No prerequisites'
                exclusions = doc.get('exclusions', 'No exclusions')
                if not exclusions or exclusions in [None, [], 'null']:
                    exclusions = 'No exclusions'
                sessions = ', '.join(doc.get('sessions', [])) or 'N/A'

                # Retrieve the meeting_sections for this course
                meeting_sections = list(meeting_sections_collection.find({'course_id': doc['course_id']}))

                # Build a string representation of the meeting_sections
                meeting_info = '\n'.join(extract_lecture_meeting_sections(doc['course_id'], meeting_sections))

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
                    code=doc.get('course_code', 'N/A'),
                    name=doc.get('name', 'N/A'),
                    department=doc.get('department', 'N/A'),
                    division=doc.get('division', 'N/A'),
                    description=doc.get('description', 'N/A'),
                    department_code=doc.get('course_code', 'N/A')[:3],
                    section_code=doc.get('section_code', 'N/A'),
                    prerequisites=doc.get('prerequisites', 'No prerequisites'),
                    exclusions=doc.get('exclusions', 'No exclusions'),
                    campus=doc.get('campus', 'N/A'),
                    sessions=', '.join(doc.get('sessions', [])) or 'N/A',
                    meeting_info=meeting_info or 'N/A'
                )
                texts.append(combined_text)
                ids.append(course_id)

                # Prepare metadata
                metadata = {
                    "course_id": course_id,
                    "course_code": sanitize_metadata_field(course_code, "No Course Code"),
                    "name": sanitize_metadata_field(name, "No Course Name"),
                    "department": sanitize_metadata_field(department, "No Department Information"),
                    "division": sanitize_metadata_field(division, "No Division Information"),
                    "campus": sanitize_metadata_field(campus, "No Campus Information"),
                    "section_code": sanitize_metadata_field(section_code, "No Section Code"),
                    "prerequisites": sanitize_metadata_field(prerequisites, "No Prerequisites"),
                    "exclusions": sanitize_metadata_field(exclusions, "No Exclusions"),
                    "sessions": sanitize_metadata_field(sessions, "No Session Information"),
                    "meeting_info": sanitize_metadata_field(meeting_info, "No Meeting Information"),
                    "description": sanitize_metadata_field(description, "No Description Available")
                }
                metadata_list.append(metadata)

            except Exception as e:
                print(f"Error processing document {doc.get('course_id', 'unknown')}: {e}")
                continue

        # Generate embeddings for the batch
        if texts:
            try:
                # Generate embeddings using OpenAI API
                embeddings_response = openai.embeddings.create(
                    input=texts,
                    model="text-embedding-ada-002"
                )
                embeddings = [data_point.embedding for data_point in embeddings_response.data]

                # Prepare vectors for upsert, including metadata if needed
                vectors = []
                for idx, embedding in enumerate(embeddings):
                    vector = {
                        "id": ids[idx],
                        "values": embedding,
                        "metadata": metadata_list[idx]
                    }
                    vectors.append(vector)

                # Upsert vectors into Pinecone
                index.upsert(vectors=vectors)
            except Exception as e:
                print(f"Error generating embeddings: {e}")
                continue
    print("Upsert to Pinecone completed.")


def retrieve_courses_from_db(query, filter, num_results=10):
    try:
        print("Encoding the user query...")
        try:
            query_response = openai.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_embedding = query_response.data[0].embedding
            print("Query encoded successfully.")
        except Exception as e:
            print(f"Error encoding query: {e}")
            return []

        # Initialize Pinecone index
        index = pc.Index(INDEX_NAME)

        # Perform similarity search in Pinecone
        print("Querying Pinecone for similar courses...")
        search_response = index.query(
            vector=query_embedding,
            top_k=num_results,
            include_metadata=True,
            filter=filter
        )

        # Retrieve course IDs from the search results
        retrieved_ids = [match['id'] for match in search_response['matches']]

        print(f"Retrieved {len(retrieved_ids)} course IDs from Pinecone.")

        # Fetch course details from MongoDB
        retrieved_courses = []
        course_ids_seen = set()

        for course_id in retrieved_ids:
            if course_id in course_ids_seen:
                continue
            try:
                course = courses_collection.find_one({"course_id": course_id}, {
                    "_id": 0,
                    "course_id": 1,
                    "course_code": 1,
                    "name": 1,
                    "description": 1,
                    "prerequisites": 1,
                    "department": 1,
                    "division": 1,
                    "exclusions": 1,
                    "campus": 1,
                    "section_code": 1,
                    "sessions": 1
                })

                if not course:
                    continue
                
                print(f"{course['course_code']: <10} - {course['name']}")
                # Retrieve the meeting_sections for this course
                meeting_sections = list(meeting_sections_collection.find({'course_id': course_id}, {"_id":0}))

                # Convert meeting_sections into desired string format
                def format_meeting_section(ms):
                    instructors = ', '.join(ms.get('instructors', []))
                    # Format times
                    times_str = []
                    for t in ms.get('times', []):
                        day = t.get('day', 'N/A')
                        start = t.get('start', 'N/A')
                        end = t.get('end', 'N/A')
                        location = t.get('location', 'N/A')
                        times_str.append(f"Day {day}, {start}-{end} at {location}")
                    times_str = ', '.join(times_str)

                    return f"Section: {ms.get('section_code','N/A')}, Type: {ms.get('type','N/A')}, Instructors: {instructors}, Times: {times_str}, Class Size: {ms.get('size','N/A')}"

                meeting_sections_str = [format_meeting_section(ms) for ms in meeting_sections if ms.get('type') == "Lecture"]

                # Create the final course object in the desired format
                final_course = {
                    "course_code": course.get("course_code", "N/A"),
                    "name": course.get("name", "N/A"),
                    "department": course.get("department", "N/A"),
                    "division": course.get("division", "N/A"),
                    "description": course.get("description", "N/A"),
                    "prerequisites": course.get("prerequisites", "No prerequisites") or "No prerequisites",
                    "exclusions": course.get("exclusions", "No exclusions") or "No exclusions",
                    "campus": course.get("campus", "N/A"),
                    "section_code": course.get("section_code", "N/A"),
                    "sessions": ', '.join(course.get("sessions", [])) if course.get("sessions") else "N/A",
                    "meeting_sections": meeting_sections_str
                }

                retrieved_courses.append(final_course)
                course_ids_seen.add(course_id)

                if len(retrieved_courses) >= num_results:
                    break
            except Exception as e:
                print(f"Error processing course {course_id}: {e}")
                continue
        
        # Print the retrieved courses
        for idx, course in enumerate(retrieved_courses):
            print(f"Course {idx + 1}: {course}")
            print("\n")
        return retrieved_courses

    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

if __name__ == '__main__':
    # upsert_embeddings_to_pinecone()

    # User query
    query = """
        Refined User Query: The student is interested in an introductory course in machine learning and AI at 
        the University of Toronto's St. George campus. They prefer an entry-level course, focusing on broad concepts 
        of ML and AI without specific experience in mathematics or programming prerequisites. The student is keen 
        on exploring various aspects of machine learning, possibly including neural networks, natural language 
        processing, and robotics, with an eye towards applying this knowledge in a versatile career setting. 
        They have expressed an openness to foundational learning and potential exploration of AI's diverse applications.
    """

    # Filter to restrict search results to a specific campus
    filter = {
        "department": {"$eq": "Department of Computer Science"},
        "campus": {"$eq": "St. George"}
    }

    # Measure start time
    start_time = time.time()

    # Retrieve similar courses
    results = retrieve_courses_from_db(query, filter, num_results=10)
    print(f"Retrieved {len(results)} courses:")

    # Measure end time
    end_time = time.time()

    # Calculate and print the elapsed time
    elapsed_time = end_time - start_time
    print(f"Time taken to retrieve courses: {elapsed_time:.2f} seconds")

    # Print the retrieved courses
    for idx, course in enumerate(results):
        print(f"Course {idx + 1}: {course}")
        print("\n")
