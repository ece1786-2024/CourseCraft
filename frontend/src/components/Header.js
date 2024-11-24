// components/Header.js
import React, { useRef } from 'react';
import ChatBox from './ChatBox'; // Adjust the path as needed
import './../App.css';
import './Header.css';

const Header = () => {
  const chatBoxRef = useRef(null);

  const handleStartClick = () => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <>
      <header className="header-banner">
        <div className="container-width">
          <div className="logo-container">
            <div className="logo">Fall 2024</div>
          </div>
          <div className="lead-title">CourseCraft - Making Course Selection Easier</div>
          <div className="sub-lead-title">
            Feeling overwhelmed by course selection? <br />
            Don't worry—we're here to help you navigate your choices with personalized AI recommendations!
          </div>
          <button className="lead-btn" onClick={handleStartClick}>
            Start!
          </button>
        </div>
      </header>

      {/* Embed the ChatBox component */}
      <div ref={chatBoxRef}>
        <ChatBox />
      </div>
    </>
  );
};

export default Header;
