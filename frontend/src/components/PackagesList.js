import React, { useState } from 'react';

const PackagesList = ({ packages, onDownload, onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    onSearch(value);
  };

  const clearSearch = () => {
    setSearchTerm('');
    onSearch('');
  };

  const renderDependencies = (dependencies) => {
    if (!dependencies || dependencies.length === 0) {
      return <span className="no-dependencies">No dependencies</span>;
    }

    return (
      <div className="dependencies-list">
        {dependencies.map((dep, index) => (
          <span key={index} className="dependency-tag">
            {dep}
          </span>
        ))}
      </div>
    );
  };

  const renderPlatformInfo = (pkg) => {
    const platform = pkg.platform ? pkg.platform.replace('manylinux2014_', '') : '';
    const pythonVersion = pkg.pythonVersion || '';
    
    if (platform || pythonVersion) {
      return (
        <div className="platform-info">
          {pythonVersion && <span className="python-version">Python {pythonVersion}</span>}
          {platform && <span className="platform-arch">{platform}</span>}
        </div>
      );
    }
    return null;
  };

  if (packages.length === 0) {
    return (
      <div className="packages-section">
        <div className="search-box">
          <div className="search-input-container">
            <i className="fas fa-search search-icon"></i>
            <input
              type="text"
              placeholder="Search layers by name or dependencies..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="search-input"
            />
            {searchTerm && (
              <button className="clear-search" onClick={clearSearch}>
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
        </div>
        
        <div className="empty-state">
          <i className="fas fa-layer-group"></i>
          <p>
            {searchTerm 
              ? `No layers found matching "${searchTerm}"`
              : "No layers created yet. Create your first Lambda layer!"
            }
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="packages-section">
      <div className="search-box">
        <div className="search-input-container">
          <i className="fas fa-search search-icon"></i>
          <input
            type="text"
            placeholder="Search layers by name or dependencies..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="search-input"
          />
          {searchTerm && (
            <button className="clear-search" onClick={clearSearch}>
              <i className="fas fa-times"></i>
            </button>
          )}
        </div>
      </div>
      
      <div className="packages-list">
        {packages.map((pkg, index) => (
          <div key={index} className="package-item">
            <div className="package-header">
              <div className="package-name">{pkg.fileName}</div>
              <div className="package-meta">
                <i className="fas fa-calendar"></i> {formatDate(pkg.lastModified)} | 
                <i className="fas fa-file"></i> {formatFileSize(pkg.size)}
                {pkg.dependencyCount > 0 && (
                  <>
                    | <i className="fas fa-cube"></i> {pkg.dependencyCount} dependencies
                  </>
                )}
              </div>
            </div>
            
            {renderPlatformInfo(pkg)}
            
            <div className="dependencies-section">
              <div className="dependencies-label">Dependencies:</div>
              {renderDependencies(pkg.dependencies)}
            </div>
            
            <button 
              className="btn btn-success" 
              onClick={() => onDownload(pkg.key, pkg.fileName)}
            >
              <i className="fas fa-download"></i> Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PackagesList; 