import json
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

# Load the transformed data
input_file_path = "transformed_data.json"
with open(input_file_path, 'r', encoding='utf-8') as infile:
    transformed_data = json.load(infile)

courses_data_list = transformed_data['courses']
meeting_sections_data_list = transformed_data['meeting_sections']

# Function to encode text data using OpenAI's text-embedding-ada-002
def encode_text_with_openai(text_list):
    embeddings = []
    for text in text_list:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embeddings.append(response.data[0].embedding)
    return embeddings


# Prepare text data for encoding
course_descriptions = [course['description'] for course in courses_data_list]
prerequisites = [course['prerequisites'] if course['prerequisites'] else "No prerequisites" for course in courses_data_list]
divisions_departments = [f"{course['division']} {course['department']}" for course in courses_data_list]
course_names = [course['name'] for course in courses_data_list]

# Encode the textual data using OpenAI
print("Encoding course descriptions...")
description_embeddings = encode_text_with_openai(course_descriptions)

print("Encoding course prerequisites...")
prerequisites_embeddings = encode_text_with_openai(prerequisites)

print("Encoding divisions and departments...")
division_department_embeddings = encode_text_with_openai(divisions_departments)

print("Encoding course names...")
name_embeddings = encode_text_with_openai(course_names)

# Add embeddings to courses data
for idx, course in enumerate(courses_data_list):
    # Convert embeddings to lists for JSON serialization
    course['description_embedding'] = description_embeddings[idx]
    course['prerequisites_embedding'] = prerequisites_embeddings[idx]
    course['division_department_embedding'] = division_department_embeddings[idx]
    course['name_embedding'] = name_embeddings[idx]

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Access the database (will create it if it doesn't exist)
db = client['university_courses']

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
