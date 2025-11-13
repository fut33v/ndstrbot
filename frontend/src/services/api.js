import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Enable cookies
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API methods
export const fetchData = async (endpoint) => {
  try {
    const response = await api.get(`/${endpoint}`);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch ${endpoint}: ${error.message}`);
  }
};

// Specific API methods for each entity
export const getUsers = () => fetchData('users');
export const getAdmins = () => fetchData('admins');
export const getRequests = () => fetchData('requests');
export const getRequestById = (id) => fetchData(`requests/${id}`);
export const getFiles = () => fetchData('files');
export const getFilesByRequestId = (requestId) => fetchData(`requests/${requestId}/files`);
export const getAuditLogs = () => fetchData('audit');
export const getTemplates = () => fetchData('templates');
export const getTemplateById = (id) => fetchData(`templates/${id}`);

export const deleteTemplate = async (templateId) => {
  try {
    const response = await api.delete(`/templates/${templateId}`);
    return response.data;
  } catch (error) {
    throw new Error(`Failed to delete template: ${error.message}`);
  }
};

// Template upload
export const uploadTemplate = async (name, description, file) => {
  try {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file', file);
    
    const response = await api.post('/templates/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to upload template: ${error.message}`);
  }
};

// Auth methods
export const getCurrentUser = async () => {
  try {
    const response = await api.get('/auth/me');
    return response.data;
  } catch (error) {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      return null;
    }
    throw error;
  }
};

export const addAdmin = async (userId) => {
  try {
    const response = await api.post('/admins', { user_id: userId });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to add admin: ${error.message}`);
  }
};

export const logout = async () => {
  try {
    const response = await api.post('/auth/logout');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to logout: ${error.message}`);
  }
};

export default api;
