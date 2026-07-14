import { useState } from 'react';
import { FiEdit2, FiCheck, FiX, FiInfo } from 'react-icons/fi';

export default function DecisionCard({ title, value, tagColor, onOverride }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  const handleSave = () => {
    onOverride(editValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  return (
    <div className="decision-card glass-panel fade-in">
      <div className="decision-card-header">
        <h4 style={{ margin: 0, fontSize: '1rem' }}>{title}</h4>
        <span className={`tag ${tagColor}`}>AI Decision</span>
      </div>
      
      {!isEditing ? (
        <div style={{ marginTop: '16px' }}>
          <div style={{ 
            fontSize: '1.1rem', 
            fontWeight: '500', 
            color: 'var(--text-primary)',
            background: 'rgba(255,255,255,0.03)',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '16px',
            wordBreak: 'break-all'
          }}>
            {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
          </div>
          
          <button 
            className="btn" 
            style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%', justifyContent: 'center' }}
            onClick={() => setIsEditing(true)}
          >
            <FiEdit2 /> Override (Manual Edit)
          </button>
        </div>
      ) : (
        <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--warning-yellow)', fontSize: '0.85rem' }}>
            <FiInfo /> <span>Overriding the LLM decision manually.</span>
          </div>
          <textarea 
            value={typeof editValue === 'object' ? JSON.stringify(editValue, null, 2) : editValue}
            onChange={(e) => {
              try {
                // If it was an object, try to parse it back, otherwise keep string
                if (typeof value === 'object') {
                   setEditValue(JSON.parse(e.target.value));
                } else {
                   setEditValue(e.target.value);
                }
              } catch {
                setEditValue(e.target.value);
              }
            }}
            style={{
              width: '100%',
              minHeight: '80px',
              background: 'rgba(0,0,0,0.2)',
              border: '1px solid var(--glass-border)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              padding: '12px',
              fontFamily: 'monospace'
            }}
          />
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-success" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }} onClick={handleSave}>
              <FiCheck /> Confirm
            </button>
            <button className="btn btn-danger" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }} onClick={handleCancel}>
              <FiX /> Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
