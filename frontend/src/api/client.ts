import axios, { AxiosInstance, AxiosError } from 'axios';
import { tokenStorage } from '@/auth/tokenStorage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = tokenStorage.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - clear it
          tokenStorage.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });
    return response.data;
  }

  // Users endpoints
  async getUsers() {
    const response = await this.client.get('/users');
    return response.data;
  }

  async createUser(data: { email: string; username: string; password: string; role: 'admin' | 'clerk' }) {
    const response = await this.client.post('/users', data);
    return response.data;
  }

  // Camera endpoints
  async getCameras() {
    const response = await this.client.get('/cameras');
    return response.data;
  }

  async getCamera(cameraId: string) {
    const response = await this.client.get(`/cameras/${cameraId}`);
    return response.data;
  }

  async createCamera(data: {
    name: string;
    description?: string;
    lat: number;
    lon: number;
    heading?: number;
    rtsp_url?: string;
    active?: boolean;
  }) {
    const response = await this.client.post('/cameras', data);
    return response.data;
  }

  async updateCamera(cameraId: string, data: Partial<{
    name: string;
    description: string;
    lat: number;
    lon: number;
    heading: number;
    rtsp_url: string;
    active: boolean;
  }>) {
    const response = await this.client.patch(`/cameras/${cameraId}`, data);
    return response.data;
  }

  // Upload endpoints
  async uploadVideo(cameraId: string, file: File) {
    const formData = new FormData();
    formData.append('camera_id', cameraId);
    formData.append('file', file);

    const response = await this.client.post('/uploads', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getJobStatus(jobId: string) {
    const response = await this.client.get(`/jobs/${jobId}`);
    return response.data;
  }

  // Events endpoints
  async getEvents(params?: {
    plate?: string;
    normalized?: boolean;
    camera_id?: string;
    from_ts?: string;
    to_ts?: string;
    limit?: number;
  }) {
    const response = await this.client.get('/events', { params });
    return response.data;
  }

  async getEvent(eventId: string) {
    const response = await this.client.get(`/events/${eventId}`);
    return response.data;
  }

  async confirmEvent(eventId: string, data: { confirmed_by?: string; notes?: string }) {
    const response = await this.client.post(`/events/${eventId}/confirm`, data);
    return response.data;
  }

  async correctEvent(eventId: string, data: { corrected_plate: string; comments?: string }) {
    const response = await this.client.post(`/events/${eventId}/correction`, data);
    return response.data;
  }

  // Feedback endpoints
  async getPendingEvents() {
    const response = await this.client.get('/feedback/pending');
    return response.data;
  }

  async exportFeedback(params?: { from_ts?: string; to_ts?: string }) {
    const response = await this.client.get('/feedback/export', { params });
    return response.data;
  }

  // BOLO endpoints
  async getBOLOs() {
    const response = await this.client.get('/bolos');
    return response.data;
  }

  async createBOLO(data: {
    plate_pattern: string;
    description?: string;
    active?: boolean;
  }) {
    const response = await this.client.post('/bolos', data);
    return response.data;
  }

  // License endpoints
  async activateLicense(data: { license_key: string; node_id?: string }) {
    const response = await this.client.post('/licenses/activate', data);
    return response.data;
  }

  async getLicenseUsage() {
    const response = await this.client.get('/licenses/usage');
    return response.data;
  }

  // Admin endpoints
  async getHealth() {
    const response = await this.client.get('/admin/health');
    return response.data;
  }
}

export const apiClient = new APIClient();
