import React, { useState } from 'react';
import AgentChat from './components/AgentChat';

export default function App() {
  const [jobId, setJobId] = useState('');

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>🧠 DataSense + Synapse-AI</h1>
      <p>Autonomous Data Analysis Pipeline & Conversational AI Agent</p>
      
      <div style={{ padding: '20px', border: '1px dashed #ccc', marginBottom: '20px' }}>
        <h3>1. Upload & Clean Data</h3>
        <p><i>DataSense Celery Workers will clean your dataset here.</i></p>
        <input 
          type="text" 
          placeholder="Simulate: Enter a Job ID to chat with" 
          value={jobId} 
          onChange={(e) => setJobId(e.target.value)} 
          style={{ padding: '8px', width: '100%' }}
        />
      </div>

      {jobId && (
        <div>
          <h3>2. Synapse-AI Agent</h3>
          <AgentChat jobId={jobId} />
        </div>
      )}
    </div>
  );
}
