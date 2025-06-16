import React, { useState, useEffect } from 'react';
import { checkHealth } from '../services/api';

const ApiStatus = () => {
  const [status, setStatus] = useState({ checking: true });
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    setStatus({ checking: true });
    try {
      const result = await checkHealth();
      setStatus(result);
    } catch (error) {
      setStatus({ 
        healthy: false, 
        error: error.message,
        url: 'Unknown'
      });
    }
  };

  if (status.checking) {
    return (
      <div style={{ 
        padding: '10px 15px', 
        backgroundColor: '#fff3cd', 
        border: '1px solid #ffeeba',
        borderRadius: '8px',
        marginBottom: '20px',
        fontSize: '0.9rem'
      }}>
        <i className="fas fa-spinner fa-spin"></i> Checking API connection...
      </div>
    );
  }

  if (status.healthy) {
    return (
      <div style={{ 
        padding: '10px 15px', 
        backgroundColor: '#d4edda', 
        border: '1px solid #c3e6cb',
        borderRadius: '8px',
        marginBottom: '20px',
        fontSize: '0.9rem'
      }}>
        <i className="fas fa-check-circle" style={{ color: '#155724' }}></i> API Connected
        {showDetails && (
          <div style={{ marginTop: '8px', fontSize: '0.8rem', color: '#155724' }}>
            <strong>URL:</strong> {status.url}
          </div>
        )}
        <button 
          onClick={() => setShowDetails(!showDetails)}
          style={{ 
            background: 'none', 
            border: 'none', 
            color: '#155724', 
            textDecoration: 'underline',
            cursor: 'pointer',
            fontSize: '0.8rem',
            marginLeft: '10px'
          }}
        >
          {showDetails ? 'Hide' : 'Show'} Details
        </button>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '15px', 
      backgroundColor: '#f8d7da', 
      border: '1px solid #f5c6cb',
      borderRadius: '8px',
      marginBottom: '20px'
    }}>
      <div style={{ color: '#721c24', fontWeight: '500', marginBottom: '10px' }}>
        <i className="fas fa-exclamation-triangle"></i> API Connection Error
      </div>
      
      <div style={{ fontSize: '0.9rem', color: '#721c24', marginBottom: '15px' }}>
        {status.isPlaceholder ? (
          <>
            <strong>🔧 Setup Required:</strong> The API backend hasn't been configured yet.
            <br />
            <strong>📋 Next Steps:</strong>
            <ol style={{ marginTop: '8px', paddingLeft: '20px' }}>
              <li>Run <code style={{ background: '#fff', padding: '2px 4px', borderRadius: '3px' }}>python deploy.py</code></li>
              <li>Wait for deployment to complete</li>
              <li>Refresh this page</li>
            </ol>
          </>
        ) : (
          <>
            <strong>Error:</strong> {status.error}
            <br />
            <strong>API URL:</strong> {status.url}
          </>
        )}
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button 
          onClick={checkApiHealth}
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '6px 12px' }}
        >
          <i className="fas fa-redo"></i> Retry
        </button>
        
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="btn btn-secondary"
          style={{ fontSize: '0.8rem', padding: '6px 12px' }}
        >
          <i className="fas fa-info-circle"></i> {showDetails ? 'Hide' : 'Show'} Debug Info
        </button>
      </div>

      {showDetails && (
        <div style={{ 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: '#fff',
          borderRadius: '4px',
          fontSize: '0.8rem',
          fontFamily: 'monospace'
        }}>
          <strong>Debug Information:</strong>
          <pre style={{ margin: '5px 0', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify({
              url: status.url,
              isPlaceholder: status.isPlaceholder,
              error: status.error,
              timestamp: new Date().toISOString(),
              userAgent: navigator.userAgent
            }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ApiStatus; 