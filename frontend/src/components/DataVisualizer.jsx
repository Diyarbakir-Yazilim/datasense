import React from 'react';
import { FiPieChart, FiBarChart2, FiTrendingUp } from 'react-icons/fi';

export default function DataVisualizer({ data }) {
  // Mock Data for Premium UI Showcase since backend chart data is not fully integrated yet
  return (
    <div className="glass-panel fade-in" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <FiBarChart2 size={24} className="gradient-text" />
        <h3 style={{ margin: 0 }}>Görselleştirme & Analiz (Önizleme)</h3>
      </div>
      
      <div className="dashboard-grid">
        <div style={{ 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.05)', 
          borderRadius: '12px', 
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '250px'
        }}>
          <FiPieChart size={64} color="var(--accent-purple)" style={{ opacity: 0.5, marginBottom: '16px' }} />
          <h4 style={{ color: 'var(--text-secondary)' }}>Sınıflandırma Dağılımı</h4>
          <p style={{ textAlign: 'center', fontSize: '0.9rem', color: 'rgba(255,255,255,0.4)', marginTop: '8px' }}>
            Plotly/Echarts Entegrasyonu Bekleniyor...
          </p>
        </div>
        
        <div style={{ 
          background: 'rgba(255,255,255,0.02)', 
          border: '1px solid rgba(255,255,255,0.05)', 
          borderRadius: '12px', 
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '250px'
        }}>
          <FiTrendingUp size={64} color="var(--accent-cyan)" style={{ opacity: 0.5, marginBottom: '16px' }} />
          <h4 style={{ color: 'var(--text-secondary)' }}>Korelasyon Matrisi</h4>
          <p style={{ textAlign: 'center', fontSize: '0.9rem', color: 'rgba(255,255,255,0.4)', marginTop: '8px' }}>
            Hedef değişken ilişkileri analiz ediliyor...
          </p>
        </div>
      </div>
    </div>
  );
}
