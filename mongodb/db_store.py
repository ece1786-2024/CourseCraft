import json
from pymongo import MongoClient
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

# Load the transformed data
current_dir = os.path.dirname(__file__)
input_file_path = os.path.join(current_dir, 'transformed_data.json')

with open(input_file_path, 'r', encoding='utf-8') as infile:
    transformed_data = json.load(infile)

courses_data_list = transformed_data['courses']
meeting_sections_data_list = transformed_data['meeting_sections']

# Function to encode text data using OpenAI's text-embedding-ada-002
def encode_text_with_openai(text_list):
    embeddings = []
    for text in text_list:
        course_info = text.replace("\n", " ")
        response = client.embeddings.create(
            input=course_info,
            model="text-embedding-3-small"
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def extract_lecture_meeting_sections(course_id, meeting_sections_data_list):
    """
    Extract lecture meeting sections for a specific course_id.
    
    Args:
        course_id (str): The unique identifier for the course.
        meeting_sections (list): List of meeting section dictionaries.

    Returns:
        list: A list of formatted strings representing lecture meeting sections.
    """
    lecture_sections = [
        """Section: {section_code}, Type: {type}, Instructors: {instructors}, Times: {times}, Class Size: {size}""".format(
            section_code=meeting.get('section_code', 'N/A'),
            type=meeting.get('type', 'N/A'),
            instructors=', '.join(meeting.get('instructors', [])),
            times=", ".join([
                f"Day {time.get('day', 'N/A')}, {time.get('start', 'N/A')}-{time.get('end', 'N/A')} at {time.get('location', 'N/A')}"
                for time in meeting.get('times', [])
            ]),
            size=meeting.get('size', 'N/A')
        )
        for meeting in meeting_sections_data_list
        if meeting['course_id'] == course_id and meeting['type'] == "Lecture"
    ]
    return lecture_sections


def main():
    # Load the transformed data
    input_file_path = "transformed_data.json"
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        transformed_data = json.load(infile)

    courses_data_list = transformed_data.get('courses', [])
    meeting_sections_data_list = transformed_data.get('meeting_sections', [])

    # Prepare text data for encoding
    combined_texts = []
    for course in courses_data_list:
        meeting_info = '\n'.join(extract_lecture_meeting_sections(course.get('course_id', '')))
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
            prerequisites=course.get('prerequisites', 'No prerequisites') or 'No prerequisites',
            exclusions=course.get('exclusions', 'No exclusions') or 'No exclusions',
            campus=course.get('campus', 'N/A'),
            sessions=', '.join(course.get('sessions', [])) or 'N/A',
            meeting_info=meeting_info or 'N/A'
        )
        combined_texts.append(combined_text)

    print("Encoding combined course information...")
    combined_embeddings = encode_text_with_openai(combined_texts)

    # Add embeddings to courses data
    for idx, course in enumerate(courses_data_list):
        # Convert embeddings to lists for JSON serialization
        if combined_embeddings[idx] is not None:
            course['embedding'] = combined_embeddings[idx]
        else:
            course['embedding'] = []

    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)

    # Access the database (will create it if it doesn't exist)
    db = client['uoft_courses']

    # Define the collections
    courses_collection = db['courses']
    meeting_sections_collection = db['meeting_sections']

    # Insert courses data
    if courses_data_list:
        # Remove any existing documents to avoid duplicates (optional)
        courses_collection.delete_many({})
        courses_collection.insert_many(courses_data_list)
        print(f"Inserted {len(courses_data_list)} documents into 'courses' collection.")
    else:
        print("No courses data to insert.")

    # Insert meeting sections data
    if meeting_sections_data_list:
        # Remove any existing documents to avoid duplicates (optional)
        meeting_sections_collection.delete_many({})
        meeting_sections_collection.insert_many(meeting_sections_data_list)
        print(f"Inserted {len(meeting_sections_data_list)} documents into 'meeting_sections' collection.")
    else:
        print("No meeting sections data to insert.")

if __name__ == '__main__':
    main()