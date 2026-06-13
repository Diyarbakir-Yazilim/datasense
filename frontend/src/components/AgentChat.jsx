import React, { useState } from 'react';
import axios from 'axios';

const AgentChat = ({ jobId }) => {
  const [messages, setMessages] = useState([{ sender: 'bot', text: 'Hello! I am Synapse-AI. Ask me anything about your data.' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useCleanedData, setUseCleanedData] = useState(true);

  const sendMessage = async () => {
    if (!input.trim() || !jobId) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/chat', {
        job_id: jobId,
        message: userMessage.text,
        use_cleaned_data: useCleanedData
      });

      setMessages((prev) => [...prev, { sender: 'bot', text: response.data.response }]);
    } catch (error) {
      setMessages((prev) => [...prev, { sender: 'bot', text: `Error: ${error.response?.data?.detail || error.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-chat-container" style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '16px', marginTop: '20px' }}>
      <h3>💬 Synapse-AI Data Assistant</h3>
      <div style={{ marginBottom: '10px' }}>
        <label>
          <input 
            type="checkbox" 
            checked={useCleanedData} 
            onChange={(e) => setUseCleanedData(e.target.checked)} 
          />
          Use Cleaned Data (Uncheck for Raw Data)
        </label>
      </div>

      <div className="chat-window" style={{ height: '300px', overflowY: 'scroll', backgroundColor: '#f9f9f9', padding: '10px', borderRadius: '4px' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', marginBottom: '10px' }}>
            <span style={{ 
              display: 'inline-block', 
              padding: '8px 12px', 
              borderRadius: '16px', 
              backgroundColor: msg.sender === 'user' ? '#007bff' : '#e0e0e0',
              color: msg.sender === 'user' ? 'white' : 'black'
            }}>
              {msg.text}
            </span>
          </div>
        ))}
        {loading && <div style={{ textAlign: 'left', color: '#888' }}>Thinking...</div>}
      </div>

      <div style={{ display: 'flex', marginTop: '10px' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask a question..."
          style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading} style={{ marginLeft: '10px', padding: '8px 16px', borderRadius: '4px', backgroundColor: '#28a745', color: 'white', border: 'none' }}>
          Send
        </button>
      </div>
    </div>
  );
};

export default AgentChat;
