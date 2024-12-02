import React, { useState, useRef } from 'react';
import ChatBox from './components/ChatBox';
import CourseList from './components/CourseList';
import Header from './components/Header';
import Footer from './components/Footer';

const App = () => {
  const [courses, setCourses] = useState([]);
  const chatBoxRef = useRef(null);

  const handleCoursesReceived = (coursesData) => setCourses(coursesData);

  return (
    <div>
      <Header chatBoxRef={chatBoxRef} />
      <ChatBox ref={chatBoxRef} onCoursesReceived={handleCoursesReceived} />
      {courses.length > 0 && (
        <div className="course-list-container">
          <h2>Your Course Recommendations:</h2>
          <CourseList courses={courses} />
        </div>
      )}
      <Footer />
    </div>
  );
};

export default App;
