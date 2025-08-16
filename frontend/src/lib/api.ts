import axios, { AxiosResponse } from "axios";
import { toast } from "sonner";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for auth tokens, etc.
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = localStorage.getItem('authToken');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors here
    if (error.response?.status === 401) {
      // Handle unauthorized error
      console.log("Unauthorized access");
      toast.error("Unauthorized access. Please log in again.");
    } else if (error.response?.status === 422) {
      // Handle validation errors
      const detail = error.response?.data?.detail || "Validation error";
      console.log("Validation error:", detail);
      toast.error(`Validation error: ${detail}`);
      
      // Special handling for session ID format issues
      if (detail.includes("session_id") || detail.includes("invalid format")) {
        toast.error("Backend API expects different ID format. Please check with backend team for alignment.");
      }
    } else if (error.response?.status >= 500) {
      toast.error("Server error. Please try again later.");
    }
    return Promise.reject(error);
  }
);

// Helper functions
export const apiHelpers = {
  get: <T>(url: string, params?: Record<string, unknown>): Promise<AxiosResponse<T>> => {
    return api.get(url, { params });
  },

  post: <T>(url: string, data?: unknown): Promise<AxiosResponse<T>> => {
    return api.post(url, data);
  },

  put: <T>(url: string, data?: unknown): Promise<AxiosResponse<T>> => {
    return api.put(url, data);
  },

  del: <T>(url: string, params?: Record<string, unknown>): Promise<AxiosResponse<T>> => {
    return api.delete(url, { params });
  },
};
