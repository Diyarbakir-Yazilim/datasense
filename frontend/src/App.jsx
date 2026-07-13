import { useState } from 'react';
import AnalysisDashboard from './components/AnalysisDashboard';
import UploadArea from './components/UploadArea';

export default function App() {
  const [jobId, setJobId] = useState('');

  return (
    <div className="app-container">
      <div className="header fade-in">
        <h1>DataSense <span className="gradient-text">Premium</span></h1>
        <p>Autonomous Data Analyst & Decision Support System</p>
      </div>
      
      {!jobId ? (
        <UploadArea onUploadComplete={(id) => setJobId(id)} />
      ) : (
        <div className="fade-in">
          <AnalysisDashboard jobId={jobId} />
        </div>
      )}
    </div>
  );
}
