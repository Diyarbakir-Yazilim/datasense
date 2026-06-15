import React, { useState } from 'react';
import AgentChat from './components/AgentChat';
import UploadArea from './components/UploadArea';

export default function App() {
  const [jobId, setJobId] = useState('');

  return (
    <div className="app-container">
      <div className="header fade-in">
        <h1>DataSense 🧠</h1>
        <p>Autonomous Data Analysis Pipeline & Conversational AI Agent</p>
      </div>
      
      {!jobId ? (
        <UploadArea onUploadComplete={(id) => setJobId(id)} />
      ) : (
        <div className="fade-in">
          <AgentChat jobId={jobId} />
        </div>
      )}
    </div>
  );
}
