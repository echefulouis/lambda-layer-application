import React, { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import CodeTemplates from './CodeTemplates';

const PackageForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    packageName: '',
    runtime: 'python3.12',
    platform: 'manylinux2014_x86_64',
    installDependencies: true,
    upgradePackages: false, // Don't upgrade by default to preserve specific versions
    packageType: 'layer', // Fixed to layer only
  });
  const [dependencies, setDependencies] = useState([]);
  const [dependencyInput, setDependencyInput] = useState('');

  const platformOptions = [
    { value: 'manylinux2014_x86_64', label: 'x86_64 (Intel/AMD)' },
    { value: 'manylinux2014_aarch64', label: 'arm64 (ARM/Graviton)' },
  ];

  const runtimeOptions = [
    { value: 'python3.12', label: 'Python 3.12', version: '3.12' },
    { value: 'python3.11', label: 'Python 3.11', version: '3.11' },
    { value: 'python3.10', label: 'Python 3.10', version: '3.10' },
    { value: 'python3.9', label: 'Python 3.9', version: '3.9' },
    { value: 'python3.8', label: 'Python 3.8', version: '3.8' },
  ];

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const addDependency = () => {
    const dependency = dependencyInput.trim();
    
    if (dependency && !dependencies.includes(dependency)) {
      setDependencies(prev => [...prev, dependency]);
      setDependencyInput('');
    }
  };

  const removeDependency = (dependency) => {
    setDependencies(prev => prev.filter(dep => dep !== dependency));
  };

  const handleDependencyKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addDependency();
    }
  };

  const addCommonDependency = (dep) => {
    if (!dependencies.includes(dep)) {
      setDependencies(prev => [...prev, dep]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const selectedRuntime = runtimeOptions.find(r => r.value === formData.runtime);
    
    const packageData = {
      ...formData,
      dependencies,
      pythonVersion: selectedRuntime?.version || '3.12'
    };

    const success = await onSubmit(packageData);
    
    if (success) {
      // Reset form
      setFormData({
        packageName: '',
        runtime: 'python3.12',
        platform: 'manylinux2014_x86_64',
        installDependencies: true,
        upgradePackages: false,
        packageType: 'layer',
      });
      setDependencies([]);
      setDependencyInput('');
    }
  };

  const commonDependencies = [
    'requests', 'boto3', 'pandas', 'numpy', 'fastapi', 'mangum', 
    'pydantic', 'sqlalchemy', 'psycopg2-binary', 'pymongo',
    'redis', 'celery', 'pillow', 'beautifulsoup4', 'lxml',
    'scipy', 'matplotlib', 'seaborn', 'plotly', 'streamlit'
  ];

  return (
    <>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="packageName">Layer Name</label>
          <input 
            type="text" 
            id="packageName"
            name="packageName"
            className="form-control" 
            placeholder="my-lambda-layer" 
            value={formData.packageName}
            onChange={handleInputChange}
            required 
          />
          <small className="form-text">
            This will be the name of your Lambda Layer package
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="runtime">Python Runtime</label>
          <select 
            id="runtime"
            name="runtime"
            className="form-control"
            value={formData.runtime}
            onChange={handleInputChange}
          >
            {runtimeOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <small className="form-text">
            Choose the Python version your Lambda functions will use
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="platform">Target Platform</label>
          <select 
            id="platform"
            name="platform"
            className="form-control"
            value={formData.platform}
            onChange={handleInputChange}
          >
            {platformOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <small className="form-text">
            Choose <strong>x86_64</strong> for standard Lambda functions or <strong>arm64</strong> for Graviton-based functions
          </small>
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="installDependencies"
              checked={formData.installDependencies}
              onChange={handleInputChange}
            />
            <span style={{marginLeft: '8px'}}>Install dependencies with pip (recommended)</span>
          </label>
          <small className="form-text">
            Installs dependencies with platform-specific binaries compatible with Lambda runtime
          </small>
        </div>

        {formData.installDependencies && (
          <div className="form-group" style={{ marginTop: '-15px' }}>
            <label>
              <input
                type="checkbox"
                name="upgradePackages"
                checked={formData.upgradePackages}
                onChange={handleInputChange}
              />
              <span style={{marginLeft: '8px'}}>Upgrade packages to latest versions (--upgrade)</span>
            </label>
            <small className="form-text">
              When unchecked, respects exact versions specified (e.g., requests==2.28.1). 
              When checked, upgrades to latest compatible versions.
            </small>
          </div>
        )}

        <div className="form-group">
          <label>Layer Dependencies</label>
          
          {/* Common Dependencies */}
          <div style={{ marginBottom: '15px' }}>
            <label style={{ fontSize: '0.9rem', color: '#6c757d' }}>Popular Packages:</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '5px' }}>
              {commonDependencies.map(dep => (
                <button
                  key={dep}
                  type="button"
                  className="btn"
                  style={{
                    fontSize: '0.75rem',
                    padding: '4px 8px',
                    backgroundColor: dependencies.includes(dep) ? '#28a745' : '#e9ecef',
                    color: dependencies.includes(dep) ? 'white' : '#495057',
                    border: '1px solid #dee2e6'
                  }}
                  onClick={() => addCommonDependency(dep)}
                  disabled={dependencies.includes(dep)}
                >
                  {dep}
                </button>
              ))}
            </div>
          </div>

          <div className="dependencies-input">
            <input 
              type="text" 
              className="form-control" 
              placeholder="e.g., requests==2.31.0 or fastapi[all]"
              value={dependencyInput}
              onChange={(e) => setDependencyInput(e.target.value)}
              onKeyPress={handleDependencyKeyPress}
            />
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={addDependency}
            >
              <i className="fas fa-plus"></i> Add
            </button>
          </div>
          <div className="dependencies-list">
            {dependencies.map((dep, index) => (
              <div key={index} className="dependency-tag">
                {dep}
                <span 
                  className="remove" 
                  onClick={() => removeDependency(dep)}
                >
                  &times;
                </span>
              </div>
            ))}
          </div>

          {formData.installDependencies && dependencies.length > 0 && (
            <div style={{ marginTop: '15px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.9rem', color: '#495057', marginBottom: '8px' }}>
                <i className="fas fa-info-circle" style={{ color: '#17a2b8' }}></i> 
                <strong> Installation Command Preview:</strong>
              </div>
              <code style={{ 
                display: 'block', 
                padding: '10px', 
                backgroundColor: '#e9ecef', 
                borderRadius: '4px',
                fontSize: '0.8rem',
                wordBreak: 'break-all'
              }}>
                pip install --platform {formData.platform} --target=python/lib/python{runtimeOptions.find(r => r.value === formData.runtime)?.version}/site-packages --implementation cp --python-version {runtimeOptions.find(r => r.value === formData.runtime)?.version} --only-binary=:all:{formData.upgradePackages ? ' --upgrade' : ''} {dependencies.join(' ')}
              </code>
            </div>
          )}

          {dependencies.length === 0 && (
            <div style={{ marginTop: '10px', fontSize: '0.9rem', color: '#6c757d', fontStyle: 'italic' }}>
              <i className="fas fa-exclamation-triangle"></i> Add at least one dependency to create a useful layer
            </div>
          )}
        </div>

        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading || !formData.packageName || dependencies.length === 0}
        >
          <i className="fas fa-layer-group"></i>
          {loading ? 'Creating Layer...' : 'Create Lambda Layer'}
        </button>
      </form>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Creating your Lambda Layer...</p>
          {formData.installDependencies && dependencies.length > 0 && (
            <p style={{ fontSize: '0.9rem', color: '#6c757d' }}>
              Installing {dependencies.length} dependencies with platform-specific binaries...
            </p>
          )}
        </div>
      )}
    </>
  );
};

export default PackageForm; 