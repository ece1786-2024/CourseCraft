import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid'; // Install with `npm install uuid`

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import { faUpload } from '@fortawesome/free-solid-svg-icons';

const ResumeUploader = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [userId, setUserId] = useState(""); // State for userId

  useEffect(() => {
    // Generate a unique userId when the component mounts
    setUserId(uuidv4());
  }, []);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setUploadStatus(""); // Reset status when a new file is selected
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append('resume', selectedFile);
    formData.append('userId', userId); // Pass the userId here

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadStatus("File uploaded successfully!");
      console.log('Response:', response.data);
    } catch (error) {
      setUploadStatus("File upload failed. Please try again.");
      console.error('Error uploading file:', error);
    }
  };

  return (
    <div style={{ textAlign: 'center', marginTop: '20px' }}>
      <h2>Upload Your Resume</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <p>{uploadStatus}</p>
    </div>
  );
};

export default ResumeUploader;
