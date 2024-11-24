// Header.js
import React from 'react';
import './../App.css';
import './Header.css';

const Header = ({ chatBoxRef }) => {
  const handleStartClick = () => {
    if (chatBoxRef && chatBoxRef.current) {
      chatBoxRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
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
  );
};

export default Header;
