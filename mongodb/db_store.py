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