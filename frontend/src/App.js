import React, { useRef, useState } from 'react';
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import ChatBox from './components/ChatBox';

const App = () => {
  const [courses, setCourses] = useState([]);
  const chatBoxRef = useRef(null);

  const handleCoursesReceived = (coursesData) => setCourses(coursesData);

  return (
    <div>
      <Header chatBoxRef={chatBoxRef} />
      <ChatBox ref={chatBoxRef} onCoursesReceived={handleCoursesReceived} />
      {/* <CourseList courses={courses} /> */}
      <Footer />
    </div>
  );
};

export default App;
