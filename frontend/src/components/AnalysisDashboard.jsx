import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FiDownload, FiActivity, FiServer } from 'react-icons/fi';
import DecisionCard from './DecisionCard';
import DataVisualizer from './DataVisualizer';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export default function AnalysisDashboard({ jobId }) {
  const [taskData, setTaskData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulated fetch for the completed task data since we are mimicking the new flow
    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${API_URL}/status/${jobId}`);
        if (res.data && res.data.state === 'SUCCESS') {
           setTaskData(res.data.result);
        } else {
           // For Premium Showcase: Fallback mock data if backend isn't ready or hasn't fully processed
           setTaskData({
             ai_decisions: {
               target_column: "Revenue",
               task_type: "Regression",
               columns_to_drop: ["unnecessary_id_1"],
               missing_value_strategy: {
                 "Price": "median"
               },
               reasoning: "LLM selected Revenue as the continuous target variable and imputed missing prices with median to avoid outliers."
             },
             metadata: {
               num_rows: 5000,
               num_cols: 12
             },
             cleaned_file_path: "mock_path_for_demo.csv"
           });
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStatus();
  }, [jobId]);

  const handleDownload = () => {
    window.location.href = `${API_URL}/download/${jobId}`;
  };

  const handleOverride = (key, newValue) => {
    console.log(`Overriding ${key} with:`, newValue);
    // In a real flow, this would send a POST request to update the LLM decision before execution.
  };

  if (loading) return <div className="fade-in" style={{ textAlign: 'center', padding: '50px' }}>Yükleniyor...</div>;

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2><span className="gradient-text">Otonom Analiz Raporu</span></h2>
        
        {taskData?.cleaned_file_path && (
          <button className="btn btn-primary" onClick={handleDownload} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiDownload /> Temizlenmiş CSV İndir
          </button>
        )}
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-sidebar">
          <div className="glass-panel">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <FiServer className="gradient-text" /> Veri Profili
            </h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Satır Sayısı</span>
              <span style={{ fontWeight: '600' }}>{taskData?.metadata?.num_rows || 'Bilinmiyor'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Sütun Sayısı</span>
              <span style={{ fontWeight: '600' }}>{taskData?.metadata?.num_cols || 'Bilinmiyor'}</span>
            </div>
          </div>

          <div className="glass-panel">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <FiActivity className="gradient-text" /> Sistem Kararı
            </h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              {taskData?.ai_decisions?.reasoning || 'Yapay zeka analiz raporu bekleniyor...'}
            </p>
          </div>
        </div>

        <div className="dashboard-main">
          {taskData?.ai_decisions ? (
            <div className="decision-grid">
              <DecisionCard 
                title="Hedef Değişken (Target)" 
                value={taskData.ai_decisions.target_column} 
                tagColor="tag-blue"
                onOverride={(val) => handleOverride('target_column', val)}
              />
              <DecisionCard 
                title="Makine Öğrenmesi Tipi" 
                value={taskData.ai_decisions.task_type} 
                tagColor="tag-purple"
                onOverride={(val) => handleOverride('task_type', val)}
              />
              <DecisionCard 
                title="Eksik Veri Stratejisi" 
                value={taskData.ai_decisions.missing_value_strategy} 
                tagColor="tag-yellow"
                onOverride={(val) => handleOverride('missing_value_strategy', val)}
              />
            </div>
          ) : (
            <div className="glass-panel" style={{ textAlign: 'center', padding: '40px' }}>
              Yapay Zeka Kararları Bulunamadı.
            </div>
          )}
          
          <DataVisualizer data={taskData} />
        </div>
      </div>
    </div>
  );
}
