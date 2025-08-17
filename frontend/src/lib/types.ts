// Base types
export interface BaseModel {
  id: number;
  uid: string;
  created_at: string;
  updated_at: string;
}

// Counselor types
export interface CounselorResponse extends BaseModel {
  name: string;
  specialty: string;
  email: string;
  phone?: string;
  bio?: string;
  years_of_experience?: number;
  hourly_rate?: number;
  availability_status: "available" | "busy" | "offline";
  rating?: number;
  total_sessions?: number;
}

export interface CounselorCreate {
  name: string;
  employee_id: string;
  specialty: string;
  email: string;
  phone?: string;
  bio?: string;
  years_of_experience?: number;
  hourly_rate?: number;
  availability_status?: "available" | "busy" | "offline";
}

export interface CounselorUpdate {
  name?: string;
  specialty?: string;
  email?: string;
  phone?: string;
  bio?: string;
  years_of_experience?: number;
  hourly_rate?: number;
  availability_status?: "available" | "busy" | "offline";
}

// Session types
export interface SessionResponse {
  uid: string;
  description: string;
  session_date: string;
  recording_link: string;
  counselor: {
    uid: string;
    name: string;
  };
}

export interface SessionCreate {
  counselor_uid: string;
  description: string;
  session_date: string;
  recording_link: string;
}

export interface SessionUpdate {
  counselor_uid?: string;
  description?: string;
  session_date?: string;
  recording_link?: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Query parameters
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// Common response wrapper
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}
