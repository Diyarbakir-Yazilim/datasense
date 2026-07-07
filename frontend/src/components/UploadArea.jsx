import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { FiUploadCloud, FiCheckCircle, FiFileText } from 'react-icons/fi';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function UploadArea({ onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxFiles: 1
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus('Uploading file...');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload the file
      const uploadRes = await axios.post(`${API_URL}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const jobId = uploadRes.data.job_id;
      setStatus('File uploaded! Analyzing data...');
      
      // 2. Poll the status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API_URL}/status/${jobId}`);
          const state = statusRes.data.state;
          
          if (state === 'SUCCESS') {
            clearInterval(pollInterval);
            setStatus('Analysis complete!');
            setProgress(100);
            setTimeout(() => {
              onUploadComplete(jobId);
            }, 1000);
          } else if (state === 'FAILURE') {
            clearInterval(pollInterval);
            setStatus('Error during analysis: ' + statusRes.data.status);
            setUploading(false);
          } else {
            // Processing
            const curr = statusRes.data.current || 0;
            const total = statusRes.data.total || 100;
            const msg = statusRes.data.status || 'Processing...';
            setProgress(Math.round((curr / total) * 100));
            setStatus(msg);
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000); // Poll every 2 seconds

    } catch (err) {
      console.error(err);
      setStatus('Failed to upload file.');
      setUploading(false);
    }
  };

  return (
    <div className="glass-panel fade-in" style={{ padding: '30px' }}>
      {!uploading ? (
        <div {...getRootProps()} className={`upload-area ${isDragActive ? 'dragging' : ''}`}>
          <input {...getInputProps()} />
          <FiUploadCloud className="upload-icon" />
          <h2 style={{ marginBottom: '10px' }}>
            {isDragActive ? "Drop the file here..." : "Drag & Drop your dataset"}
          </h2>
          <p style={{ color: 'var(--text-secondary)' }}>Supports CSV and Excel files</p>
          
          {file && (
            <div style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FiFileText color="var(--accent-blue)" />
              <span style={{ fontWeight: '500' }}>{file.name}</span>
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
          {progress === 100 ? (
            <FiCheckCircle size={50} color="#10b981" />
          ) : (
            <div className="spinner"></div>
          )}
          <h3 style={{ fontWeight: '500' }}>{status}</h3>
          
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ 
              height: '100%', 
              width: `${progress}%`, 
              background: 'linear-gradient(to right, var(--accent-blue), var(--accent-purple))',
              transition: 'width 0.3s ease'
            }}></div>
          </div>
        </div>
      )}

      {file && !uploading && (
        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <button className="btn-primary" onClick={handleUpload}>
            Start Analysis
          </button>
        </div>
      )}
    </div>
  );
}
