import axios, { AxiosResponse, AxiosRequestConfig } from "axios";
import { toast } from "sonner";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  // timeout: 30000,
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
    // Standardize common error handling with clearer mapping
    const status = error?.response?.status as number | undefined;
    const code = error?.code as string | undefined; // e.g. ECONNABORTED on timeout
    const method = (error?.config?.method || "").toUpperCase();
    const url = error?.config?.url || "";

    // 1) Client timeout (ECONNABORTED) or HTTP 408
    // We do not set a client timeout; if seen, surface a minimal notice.
    if (code === "ECONNABORTED" || status === 408) {
      console.warn(`Request timed out/canceled by client: ${method} ${url}`);
      toast.error("Request canceled by client", {
        description: "The request did not complete. Please retry.",
      });
      return Promise.reject(error);
    }

    // 2) Network error (no response) — offline/CORS/server unreachable
    if (!error?.response) {
      const isOffline = typeof navigator !== "undefined" && navigator && navigator.onLine === false;
      if (isOffline) {
        toast.error("You appear to be offline", {
          description: "Check your internet connection and try again.",
        });
      } else {
        console.warn(`Network error contacting API: ${method} ${url}`);
        toast.error("Network error", {
          description: "Couldn’t reach the API server. Please try again shortly.",
        });
      }
      return Promise.reject(error);
    }

    // 3) Auth error
    if (status === 401) {
      console.log("Unauthorized access");
      toast.error("Unauthorized access. Please log in again.");
      return Promise.reject(error);
    }

    // 4) Validation errors
    if (status === 422) {
      const detail = error.response?.data?.detail || "Validation error";
      console.log("Validation error:", detail);
      toast.error("Validation error", { description: String(detail) });
      // Special handling for session ID format issues
      if (String(detail).includes("session_id") || String(detail).includes("invalid format")) {
        toast.error("ID format mismatch", {
          description: "Backend expects a different ID format. Please verify the identifier.",
        });
      }
      return Promise.reject(error);
    }

    // 5) Method not allowed — likely endpoint not implemented
    if (status === 405) {
      console.warn(`Method not allowed (405): ${method} ${url}`);
      // Don’t toast by default to avoid noise in UI; console warning is enough
      return Promise.reject(error);
    }

    // 6) Rate limited
    if (status === 429) {
      toast.error("Too many requests", {
        description: "You’re being rate limited. Please slow down and try again in a moment.",
      });
      return Promise.reject(error);
    }

    // 7) Server errors
    if (status && status >= 500) {
      toast.error("Server error", { description: "Please try again later." });
      return Promise.reject(error);
    }

    // Fallback
    return Promise.reject(error);
  }
);

// Helper functions
export const apiHelpers = {
  get: <T>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.get(url, { params, ...(config || {}) });
  },

  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.post(url, data, config);
  },

  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.put(url, data, config);
  },

  del: <T>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.delete(url, { params, ...(config || {}) });
  },
};
