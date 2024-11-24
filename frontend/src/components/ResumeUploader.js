import React, { useState } from 'react';
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUpload } from '@fortawesome/free-solid-svg-icons';

const ResumeUploader = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

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
      <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'inline-block', marginTop: '20px' }}>
        <FontAwesomeIcon icon={faUpload} size="2x" />
        <p>Click to Upload</p>
        <input
          id="file-upload"
          type="file"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </label>
      <button
        onClick={handleUpload}
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          backgroundColor: '#007BFF',
          color: '#fff',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
        }}
      >
        Upload Resume
      </button>
      <p style={{ marginTop: '10px', color: uploadStatus.includes("failed") ? "red" : "green" }}>
        {uploadStatus}
      </p>
    </div>
  );
};

export default ResumeUploader;
