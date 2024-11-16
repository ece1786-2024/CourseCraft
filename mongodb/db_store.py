import json
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np

# Load the transformed data
input_file_path = "transformed_data.json"
with open(input_file_path, 'r', encoding='utf-8') as infile:
    transformed_data = json.load(infile)

courses_data_list = transformed_data['courses']
meeting_sections_data_list = transformed_data['meeting_sections']

# Initialize the SentenceTransformer model
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')  # You can choose a different model if you prefer

# Function to encode text data
def encode_text(text_list):
    return model.encode(text_list)

# Prepare text data for encoding
course_descriptions = [course['description'] for course in courses_data_list]
prerequisites = [course['prerequisites'] if course['prerequisites'] else "No prerequisites" for course in courses_data_list]
divisions_departments = [f"{course['division']} {course['department']}" for course in courses_data_list]
course_names = [course['name'] for course in courses_data_list]

# Encode the textual data
description_embeddings = encode_text(course_descriptions)
prerequisites_embeddings = encode_text(prerequisites)
division_department_embeddings = encode_text(divisions_departments)
name_embeddings = encode_text(course_names)

# Add embeddings to courses data
for idx, course in enumerate(courses_data_list):
    # Convert embeddings to lists for JSON serialization
    course['description_embedding'] = description_embeddings[idx].tolist()
    course['prerequisites_embedding'] = prerequisites_embeddings[idx].tolist()
    course['division_department_embedding'] = division_department_embeddings[idx].tolist()
    course['name_embedding'] = name_embeddings[idx].tolist()

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
