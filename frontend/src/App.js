import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import Footer from './components/Footer';
import Section from './components/Section';
import ResumeUploader from './components/ResumeUploader';


const App = () => {
  return (
    <div>
      <Header />
      <Section />
      {/* <Footer /> */}
      <div>
      <ResumeUploader />
      </div>
    </div>
  );
};

export default App;
