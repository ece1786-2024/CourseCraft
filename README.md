# **Course Data Processing and Recommendation System**

## **Project Overview**
This project is a course recommendation system powered by a Retrieval-Augmented Generation (RAG) model. It uses a database of university courses to provide intelligent course suggestions based on user queries. The data pipeline includes scraping course data, preprocessing it, and storing it in a database for efficient retrieval and embedding-based similarity searches.

---

## **Data Collection and Preprocessing**

1. **Environment Setup**:
   Install Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```

2. **Run Data Collection**:
     ```bash
   python scraper.py
   python data_transform.py
   ```

3. **Encode the data and store it into MongoDB**
    ```bash
    python db_store.py
    ```
    
### **2. Preprocessing Data**
- **Objective**: Convert the raw scraped data into a structured format and encode necessary fields.
- **Steps**:
  1. Load the raw JSON files.
  2. Transform the data to extract the following fields:
     - `course_id`: Unique identifier for the course.
     - `course_code`: Course code (e.g., "CSC101").
     - `section_code`: Course section (e.g., "Y").
     - `name`: Course title.
     - `description`: Detailed course information.
     - `division`: Faculty or department offering the course.
     - `prerequisites`: Required courses or conditions.
     - `exclusions`: Courses that cannot be taken with this course.
     - `sessions`: Academic terms when the course is offered.
  3. Encode the `description` field into vector embeddings using Sentence-Transformer:
     - **Purpose**: Capture the semantic content of course descriptions for similarity searches.
  4. Save the transformed data in a database-friendly JSON format.

### **3. Storing Data**
- Use MongoDB to store preprocessed data.
- Key details:
  - **Encoded Fields**:
    - `description`: Stored as STransformer vector embeddings.
  - **Raw Fields**: All other fields are stored in plain text for reference and display.

---

## **Work Distribution**

Here’s a list of tasks to help distribute work among team members:

### **Data Collection**
1. Set up the course data scraper and verify data completeness.
2. Handle any website/API changes that require adjustments to the scraper.

### **Data Preprocessing**
1. Write a script to clean and normalize raw JSON data.
2. Develop a function to encode the `description` field using STransformer.
3. Test encoding results and validate the embeddings.

### **Database Setup**
1. Design MongoDB schemas for `courses` and `meeting_sections` collections.
2. Write and test scripts for inserting data into MongoDB.
3. Optimize database queries for similarity searches.

### **Model Integration**
1. Integrate SBERT-encoded embeddings with the RAG pipeline.
2. Test retrieval accuracy and adjust embeddings or preprocessing logic if necessary.


---
