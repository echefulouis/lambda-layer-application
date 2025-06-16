import axios from 'axios';

// Try to get API URL from environment or use placeholder
const API_BASE_URL = process.env.REACT_APP_API_URL || 
                     window.APP_CONFIG?.API_URL || 
                     'https://your-api-id.execute-api.your-region.amazonaws.com/prod';

console.log('API Base URL:', API_BASE_URL);

// Check if we're still using placeholder URL
const isPlaceholderURL = API_BASE_URL.includes('your-api-id');
if (isPlaceholderURL) {
  console.warn('⚠️  Using placeholder API URL. Make sure deployment completed successfully.');
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    });
    return Promise.reject(error);
  }
);

const handleApiError = (error, operation) => {
  if (isPlaceholderURL) {
    return new Error('❌ API not configured. Please run deployment script to set up the backend.');
  }
  
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.error || error.response.statusText;
    return new Error(`API Error (${status}): ${message}`);
  } else if (error.request) {
    // Request was made but no response received
    if (error.code === 'ECONNABORTED') {
      if (operation === 'package creation') {
        return new Error('❌ Package creation timed out. This usually happens with complex packages or when installing many dependencies. Try reducing the number of dependencies or use simpler packages.');
      }
      return new Error('❌ Request timeout. The API is taking too long to respond.');
    }
    return new Error(`❌ Cannot reach API at ${API_BASE_URL}. Check if the backend is deployed and accessible.`);
  } else {
    // Something else happened
    return new Error(`❌ Unexpected error during ${operation}: ${error.message}`);
  }
};

export const createPackage = async (packageData) => {
  try {
    console.log('🚀 Creating package with data:', packageData);
    
    // Calculate timeout based on number of dependencies
    const dependencyCount = packageData.dependencies ? packageData.dependencies.length : 0;
    const baseTimeout = 60000; // 1 minute base
    const perDependencyTimeout = 120000; // 2 minutes per dependency
    const maxTimeout = 900000; // 15 minutes maximum
    
    const calculatedTimeout = Math.min(
      baseTimeout + (dependencyCount * perDependencyTimeout),
      maxTimeout
    );
    
    console.log(`⏱️ Using timeout: ${calculatedTimeout / 1000}s for ${dependencyCount} dependencies`);
    
    const response = await api.post('/packages', packageData, {
      timeout: calculatedTimeout
    });
    return response.data;
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      throw new Error(`⏱️ Package creation timed out. Try with fewer dependencies or simpler packages. Large packages with many dependencies can take several minutes to install.`);
    }
    throw handleApiError(error, 'package creation');
  }
};

export const getPackages = async (searchQuery = '') => {
  try {
    console.log(`📦 Fetching packages list${searchQuery ? ` (search: "${searchQuery}")` : ''}...`);
    const params = searchQuery ? { search: searchQuery } : {};
    const response = await api.get('/packages', { params });
    if (response.data.success) {
      console.log(`✅ Found ${response.data.packages.length} packages`);
      return response.data.packages;
    } else {
      throw new Error(response.data.error || 'Failed to load packages');
    }
  } catch (error) {
    throw handleApiError(error, 'loading packages');
  }
};

export const getDownloadUrl = async (s3Key) => {
  try {
    console.log('🔗 Generating download URL for:', s3Key);
    const response = await api.get(`/packages/${encodeURIComponent(s3Key)}/download`);
    if (response.data.success && response.data.downloadUrl) {
      return response.data.downloadUrl;
    } else {
      throw new Error('Failed to generate download URL');
    }
  } catch (error) {
    throw handleApiError(error, 'generating download URL');
  }
};

// Add a health check function
export const checkHealth = async () => {
  try {
    console.log('🏥 Checking API health...');
    const response = await api.get('/packages');
    return { healthy: true, url: API_BASE_URL };
  } catch (error) {
    return { 
      healthy: false, 
      url: API_BASE_URL, 
      error: error.message,
      isPlaceholder: isPlaceholderURL 
    };
  }
}; 