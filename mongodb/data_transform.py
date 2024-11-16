import json
import os
from datetime import datetime, timedelta

# Data structure to hold transformed data
courses_data_list = []
meeting_sections_data_list = []

# Function to convert milliseconds of the day to HH:MM:SS format
def millis_to_time(millisofday):
    # Start from midnight
    base_time = datetime(1970, 1, 1)
    # Add the milliseconds as timedelta
    time_of_day = base_time + timedelta(milliseconds=millisofday)
    # Return formatted time string
    return time_of_day.strftime('%H:%M:%S')

# Process each JSON file and transform data
number_of_files = len(os.listdir("./result"))
for i in range(1, number_of_files + 1):
    file_path = f'result/{i}.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract courses data from JSON
    courses_data = data['payload']["pageableCourse"]["courses"]
    
    for course_data in courses_data:
        # Prepare course data dictionary
        course = {
            'course_id': course_data["id"],
            'course_code': course_data["code"],
            'section_code': course_data["sectionCode"],
            'name': course_data["name"],
            'description': '',
            'division': '',
            'prerequisites': '',
            'exclusions': '',
            'department': course_data["department"]["name"] if course_data.get("department") else None,
            'campus': course_data["campus"],
            'sessions': course_data["sessions"]
        }
        
        # If additional information exists, populate it
        if course_data.get("cmCourseInfo"):
            course['description'] = course_data["cmCourseInfo"].get('description', '')
            course['division'] = course_data["cmCourseInfo"].get('division', '')
            course['prerequisites'] = course_data["cmCourseInfo"].get('prerequisitesText', '')
            course['exclusions'] = course_data["cmCourseInfo"].get('exclusionsText', '')
        
        # Append transformed course data to the list
        courses_data_list.append(course)

        # Extract meeting sections for each course
        meeting_times_data = course_data["sections"]
        
        for meeting_time_data in meeting_times_data:
            # Prepare meeting section data dictionary
            meeting_section = {
                'course_id': course_data["id"],
                'course_code': course_data["code"],
                'section_code': meeting_time_data['name'],
                'type': meeting_time_data.get('type', ''),
                'instructors': [instructor["firstName"] + ' ' + instructor["lastName"] for instructor in meeting_time_data.get('instructors', [])],
                'times': [
                    {
                        'day': time["start"]['day'],
                        'start': millis_to_time(time["start"]['millisofday']),
                        'end': millis_to_time(time["end"]["millisofday"]),
                        'location': time["building"]["buildingCode"]
                    }
                    for time in meeting_time_data.get('meetingTimes', [])
                ],
                'size': meeting_time_data.get('maxEnrolment', 0),
                'enrolment': meeting_time_data.get('currentEnrolment', 0),
                'notes': meeting_time_data.get('deliveryModes', [{}])[0].get('mode', '')
            }
            
            # Append transformed meeting section data to the list
            meeting_sections_data_list.append(meeting_section)

    print(f'File {i} successfully transformed')

# Combine all data into a single dictionary for JSON export
transformed_data = {
    "courses": courses_data_list,
    "meeting_sections": meeting_sections_data_list
}

# Save the transformed data to a JSON file
output_file_path = "transformed_data.json"
with open(output_file_path, 'w', encoding='utf-8') as outfile:
    json.dump(transformed_data, outfile, ensure_ascii=False, indent=4)

print(f"Transformed data successfully written to {output_file_path}")
