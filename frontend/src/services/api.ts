import axios from 'axios';

const API_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export const apiClient = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT token in Authorization header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('fitvision_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Auth API Calls
export const authApi = {
  signup: async (payload: any) => {
    const res = await apiClient.post('/auth/signup', payload);
    return res.data;
  },
  login: async (payload: any) => {
    const res = await apiClient.post('/auth/login', payload);
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

// Workouts API Calls
export const workoutsApi = {
  create: async (workoutData: any) => {
    const res = await apiClient.post('/workouts/', workoutData);
    return res.data;
  },
  getHistory: async () => {
    const res = await apiClient.get('/workouts/history');
    return res.data;
  },
  getStats: async () => {
    const res = await apiClient.get('/workouts/stats');
    return res.data;
  },
  getLeaderboard: async () => {
    const res = await apiClient.get('/workouts/leaderboard');
    return res.data;
  },
  getAchievements: async () => {
    const res = await apiClient.get('/workouts/achievements');
    return res.data;
  },
  exportReport: async (format: 'csv' | 'excel' | 'pdf') => {
    const response = await apiClient.get(`/workouts/export?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Users API Calls
export const usersApi = {
  updateMe: async (payload: any) => {
    const res = await apiClient.put('/users/me', payload);
    return res.data;
  },
  uploadAvatar: async (formData: FormData) => {
    const res = await apiClient.post('/users/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
};

// Helper for WebSocket url resolution
export const getWebSocketUrl = (exerciseName: string, variation: string): string => {
  const wsBase = (import.meta as any).env.VITE_WS_URL || 'ws://localhost:8000';
  return `${wsBase}${API_PREFIX}/websocket/ws/${exerciseName.toLowerCase()}?variation=${encodeURIComponent(variation)}`;
};
