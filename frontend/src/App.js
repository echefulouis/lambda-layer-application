import React, { useState, useEffect } from 'react';
import './App.css';
import PackageForm from './components/PackageForm';
import PackagesList from './components/PackagesList';
import Alert from './components/Alert';
import ApiStatus from './components/ApiStatus';
import DownloadStatus from './components/DownloadStatus';
import * as api from './services/api';

function App() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: '', message: '' });
  const [downloadStatus, setDownloadStatus] = useState({ isDownloading: false, fileName: '' });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async (search = '') => {
    try {
      const packagesList = await api.getPackages(search);
      setPackages(packagesList);
    } catch (error) {
      console.error('Error loading packages:', error);
      showAlert('error', 'Failed to load packages. Please check your API configuration.');
    }
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    await loadPackages(query);
  };

  const showAlert = (type, message) => {
    setAlert({ show: true, type, message });
    setTimeout(() => {
      setAlert({ show: false, type: '', message: '' });
    }, 5000);
  };

  const triggerDownload = async (downloadUrl, fileName) => {
    try {
      console.log('🔽 Starting download:', fileName);
      setDownloadStatus({ isDownloading: true, fileName });
      
      // Validate the download URL
      if (!downloadUrl || !downloadUrl.startsWith('http')) {
        throw new Error('Invalid download URL received from server');
      }
      
      // Method 1: Try direct download
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = fileName;
      a.style.display = 'none';
      a.rel = 'noopener noreferrer';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      console.log('✅ Download triggered successfully');
      
      // Hide download status after a short delay
      setTimeout(() => {
        setDownloadStatus({ isDownloading: false, fileName: '' });
      }, 3000);
      
      return true;
    } catch (error) {
      console.error('❌ Download failed:', error);
      setDownloadStatus({ isDownloading: false, fileName: '' });
      
      // Method 2: Fallback to window.open
      try {
        console.log('🔄 Trying fallback download method...');
        window.open(downloadUrl, '_blank');
        
        setTimeout(() => {
          setDownloadStatus({ isDownloading: false, fileName: '' });
        }, 2000);
        
        return true;
      } catch (fallbackError) {
        console.error('❌ Fallback download also failed:', fallbackError);
        setDownloadStatus({ isDownloading: false, fileName: '' });
        throw new Error('Download failed - please try downloading manually from the Recent Layers list');
      }
    }
  };

  const handlePackageCreated = async (packageData) => {
    setLoading(true);
    try {
      console.log('🚀 Creating layer...', packageData.packageName);
      
      // Show different messages based on dependency count
      const dependencyCount = packageData.dependencies ? packageData.dependencies.length : 0;
      if (dependencyCount > 2) {
        showAlert('info', `Creating layer with ${dependencyCount} dependencies. This may take several minutes...`);
      } else if (dependencyCount > 0) {
        showAlert('info', `Creating layer with ${dependencyCount} dependencies...`);
      }
      
      const result = await api.createPackage(packageData);
      
      if (result.success) {
        console.log('✅ Layer created successfully:', result);
        
        const fileName = `${result.packageName}.zip`;
        showAlert('success', `Layer "${result.packageName}" created successfully! Download starting...`);
        
        // Small delay to ensure the success message is visible
        setTimeout(async () => {
          try {
            const downloadSuccess = await triggerDownload(result.downloadUrl, fileName);
            if (downloadSuccess) {
              showAlert('success', `Layer "${result.packageName}" created and downloaded successfully!`);
            }
          } catch (downloadError) {
            console.error('Download error:', downloadError);
            showAlert('error', `Layer created but download failed: ${downloadError.message}`);
          }
        }, 500);
        
        // Refresh packages list
        setTimeout(() => loadPackages(searchQuery), 1000);
        
        return true; // Success
      } else {
        throw new Error(result.error || 'Failed to create layer');
      }
    } catch (error) {
      console.error('❌ Error creating layer:', error);
      
      // Enhanced error messages for multiple dependencies
      let errorMessage = error.message;
      const dependencyCount = packageData.dependencies ? packageData.dependencies.length : 0;
      
      if (error.message.includes('timeout') && dependencyCount > 2) {
        errorMessage = `Creation timed out with ${dependencyCount} dependencies. Try creating separate layers with fewer dependencies, or use only the most essential packages.`;
      }
      
      showAlert('error', errorMessage);
      return false; // Failure
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPackage = async (s3Key, fileName) => {
    try {
      console.log('🔽 Requesting download URL for:', fileName);
      const downloadUrl = await api.getDownloadUrl(s3Key);
      
      console.log('🔗 Got download URL, triggering download...');
      const downloadSuccess = await triggerDownload(downloadUrl, fileName);
      
      if (downloadSuccess) {
        showAlert('success', `Layer "${fileName}" downloaded successfully!`);
      }
    } catch (error) {
      console.error('❌ Download error:', error);
      showAlert('error', `Failed to download layer: ${error.message}`);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1><i className="fas fa-layer-group"></i> Lambda Layer Builder</h1>
        <p>Create and download AWS Lambda Layers with platform-specific dependencies</p>
      </div>

      <div className="main-content">
        <div className="form-section">
          <h2 className="section-title">
            <i className="fas fa-layer-group"></i>
            Create Layer
          </h2>

          <ApiStatus />

          {alert.show && (
            <Alert type={alert.type} message={alert.message} />
          )}

          <PackageForm 
            onSubmit={handlePackageCreated}
            loading={loading}
          />
        </div>

        <div className="packages-section">
          <h2 className="section-title">
            <i className="fas fa-archive"></i>
            Recent Layers
            <button 
              className="btn btn-secondary" 
              onClick={() => loadPackages(searchQuery)}
              style={{ marginLeft: 'auto' }}
            >
              <i className="fas fa-refresh"></i> Refresh
            </button>
          </h2>

          <PackagesList 
            packages={packages}
            onDownload={handleDownloadPackage}
            onSearch={handleSearch}
          />
        </div>
      </div>

      <DownloadStatus 
        isDownloading={downloadStatus.isDownloading}
        fileName={downloadStatus.fileName}
        onCancel={() => setDownloadStatus({ isDownloading: false, fileName: '' })}
      />
    </div>
  );
}

export default App; 