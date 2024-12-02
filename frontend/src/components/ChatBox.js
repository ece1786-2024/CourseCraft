// ChatBox.js
import React, { useState, useRef, useEffect, forwardRef } from 'react';
import './ChatBox.css';
import chat_bot_icon from "./../images/chat_bot_icon.jpg";
import { v4 as uuidv4 } from 'uuid';

// Import Font Awesome components
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faUpload } from '@fortawesome/free-solid-svg-icons';
import ReactMarkdown from 'react-markdown';


const ChatBox = forwardRef(({ onCoursesReceived }, ref) => {
  const fake_response = "The server is not connected ~~";
  const [input, setInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { text: "Hello! 😊 Welcome to the University of Toronto's course selection assistant. Let's start!", isBot: true },
  ]);
  const [isThinking, setIsThinking] = useState(false);
  const historyRef = useRef(null);
  const userId = useRef(uuidv4()); // Generate a unique ID for the session
  const fileInputRef = useRef(null); // Reference for the hidden file input

  useEffect(() => {
    const scrollToBottom = () => {
      if (historyRef.current) {
        historyRef.current.scrollTop = historyRef.current.scrollHeight;
      }
    };
    scrollToBottom();
  }, [chatHistory]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (input.trim()) {
      addUserMessage(input);
      setInput('');
      setIsThinking(true);
      await getBotResponse(input);
    }
  };

  const addUserMessage = (message) => {
    setChatHistory(prev => [...prev, { text: message, isBot: false }]);
  };

  const getBotResponse = async (userMessage) => {
    try {
      // Add "I am thinking ..." indicator to chat history
      setChatHistory(prev => [...prev, { text: 'I am thinking ...', isBot: true }]);

      const response = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: userId.current,
          message: userMessage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Network response was not ok');
      }

      // Remove "I am thinking ..." message
      setIsThinking(false);
      setChatHistory(prev => prev.slice(0, -1));

      // Add the assistant's response to the chat history
      let botMessage = data.response;

      setChatHistory(prev => [
        ...prev,
        { text: botMessage, isBot: true },
      ]);

      if (data.conversationEnded) {
        // Parse and handle the courses data
        let courses = [];
        try {
          courses = JSON.parse(data.finalOutput);
          console.log("Parsed JSON:", courses);

          // Pass the courses data to the parent component (if needed)
          onCoursesReceived(courses);
        } catch (error) {
          console.error("Failed to parse JSON:", error);
          onCoursesReceived([]);
        }
      }
    } catch (error) {
      console.error("Error fetching bot response:", error);
      let botMessage = fake_response;

      setIsThinking(false);
      setChatHistory(prev => prev.slice(0, -1)); // Remove "I am thinking ..." message
      setChatHistory(prev => [
        ...prev,
        { text: botMessage, isBot: true },
      ]);
    }
  };

  const updateBotMessage = (botMessage) => {
    setChatHistory(prev => {
      const updatedHistory = [...prev];
      updatedHistory[updatedHistory.length - 1] = { text: botMessage, isBot: true };
      return updatedHistory;
    });
  };

  const resetChat = async () => {
    setChatHistory([{ text: "Hello! 😊 Welcome to the University of Toronto's course selection assistant. Let's start!", isBot: true }]);
    setIsThinking(false);

    // Send reset request to backend
    await fetch('http://127.0.0.1:5000/reset', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId: userId.current }),
    });
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type and size if necessary
      const formData = new FormData();
      formData.append('resume', file);
      formData.append('userId', userId.current);

      // Log FormData entries
      for (var pair of formData.entries()) {
        console.log(pair[0]+ ', ' + pair[1]);
      }

      try {
        const response = await fetch('http://127.0.0.1:5000/upload_resume', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          alert('Resume uploaded successfully!');
          // Optionally, add a message to chat history or trigger further actions
          setChatHistory(prev => [...prev, { text: '📄 Your resume has been uploaded successfully!', isBot: true }]);
        } else {
          alert(`Upload failed: ${data.error}`);
        }
      } catch (error) {
        console.error('Error uploading resume:', error);
        alert('An error occurred while uploading your resume.');
      }
    }
  };

  return (
    <div ref={ref} className="chatbox-container">
      <div className="chat-header">
        <img src={chat_bot_icon} className="img-avatar" alt="Chat Bot Avatar" />
        <div className="text-chat">Course Recommender</div>

        {/* Upload Resume Button */}
        <button onClick={handleUploadClick} type="button" className="upload-button" aria-label="Upload Resume">
          <FontAwesomeIcon icon={faUpload} />
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
          accept=".pdf,.doc,.docx"
        />

        {/* Reset Chat Button */}
        <button onClick={resetChat} type="button" className="trash-button" aria-label="Reset Chat">
          <FontAwesomeIcon icon={faTrash} />
        </button>
      </div>

      <div className="chatbox" ref={historyRef}>
        <div className="historyChat">
        {chatHistory.map((message, index) => (
          <div key={index} className={`text ${message.isBot ? 'botText' : 'userText'}`}>
            {message.isBot ? (
              <ReactMarkdown>{message.text}</ReactMarkdown>
            ) : (
              <p>{message.text}</p>
            )}
          </div>
        ))}
        </div>
      </div>

      <div className="user-input">
        <textarea
          type="text"
          name="msg"
          className="course-input"
          value={input}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Type your message here"
        />
        <button className="send-button" onClick={handleSubmit} aria-label="Send Message">
          <div className="svg-wrapper-1">
            <div className="svg-wrapper">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                <path fill="none" d="M0 0h24v24H0z"></path>
                <path fill="currentColor" d="M1.946 9.315c-.522-.174-.527-.455.01-.634l19.087-6.362c.529-.176.832.12.684.638l-5.454 
                19.086c-.15.529-.455.547-.679.045L12 14l6-8-8 6-8.054-2.685z"></path>
              </svg>
            </div>
          </div>
        </button>
      </div>
    </div>
  );
});

export default ChatBox;
