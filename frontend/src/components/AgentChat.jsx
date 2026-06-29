import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FiSend } from 'react-icons/fi';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const AgentChat = ({ jobId }) => {
  const [messages, setMessages] = useState([{ sender: 'bot', text: 'Hello! I am Datasense. Your data is ready. What would you like to know?' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useCleanedData, setUseCleanedData] = useState(true);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || !jobId) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
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
    <div className="glass-panel chat-container fade-in">
      <div style={{ padding: '20px', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, background: 'linear-gradient(to right, var(--accent-blue), var(--accent-purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          💬 Datasense
        </h3>
        <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <input 
            type="checkbox" 
            checked={useCleanedData} 
            onChange={(e) => setUseCleanedData(e.target.checked)} 
            style={{ accentColor: 'var(--accent-purple)' }}
          />
          Use Cleaned Data
        </label>
      </div>

      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-bot'}`}>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="message-bubble message-bot" style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
            <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
            Thinking...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-area">
        <input 
          type="text" 
          className="chat-input"
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about correlations, missing values, or insights..."
          disabled={loading}
        />
        <button 
          className="btn-primary" 
          onClick={sendMessage} 
          disabled={loading}
          style={{ padding: '0 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          <FiSend size={20} />
        </button>
      </div>
    </div>
  );
};

export default AgentChat;
