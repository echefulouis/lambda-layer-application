import React from 'react';

const DownloadStatus = ({ isDownloading, fileName, onCancel }) => {
  if (!isDownloading) return null;

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      backgroundColor: '#fff',
      border: '2px solid #667eea',
      borderRadius: '10px',
      padding: '15px 20px',
      boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
      zIndex: 1000,
      minWidth: '300px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '20px',
          height: '20px',
          border: '2px solid #667eea',
          borderTop: '2px solid transparent',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: '600', color: '#2c3e50' }}>
            <i className="fas fa-download" style={{ color: '#667eea', marginRight: '8px' }}></i>
            Downloading Layer
          </div>
          <div style={{ fontSize: '0.9rem', color: '#6c757d', marginTop: '2px' }}>
            {fileName}
          </div>
        </div>
        
        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.2rem',
              color: '#6c757d',
              cursor: 'pointer',
              padding: '0',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Dismiss"
          >
            ×
          </button>
        )}
      </div>
      
      <div style={{
        fontSize: '0.8rem',
        color: '#6c757d',
        marginTop: '8px',
        fontStyle: 'italic'
      }}>
        Your download should start automatically...
      </div>
      
      <div style={{
        fontSize: '0.75rem',
        color: '#6c757d',
        marginTop: '5px'
      }}>
        Download not starting? Check your browser's download settings or popup blocker.
      </div>
      
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default DownloadStatus; 