import { apiHelpers } from "@/lib/api";
import { 
  SessionResponse, 
  SessionCreate, 
  SessionUpdate, 
  PaginatedResponse, 
  PaginationParams 
} from "@/lib/types";

// Types for session analysis responses
export interface AnalysisTaskResponse {
  task_id: string;
  status: string;
}

// List sessions with pagination
export const listSessions = async (params: PaginationParams = { skip: 0, limit: 10 }) => {
  try {
    const response = await apiHelpers.get<PaginatedResponse<SessionResponse>>("/sessions/all", params as Record<string, unknown>);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch sessions:", error);
    // Return empty result structure for graceful UI handling
    return {
      items: [],
      total: 0,
      skip: params.skip || 0,
      limit: params.limit || 10,
    } as PaginatedResponse<SessionResponse>;
  }
};

// Create a new session
export const createSession = async (body: SessionCreate) => {
  try {
  // Use default Axios (no timeout) so the request can run until the server completes.
  const response = await apiHelpers.post<SessionResponse>("/sessions", body);
    return response.data;
  } catch (error) {
    // Map timeout vs cancel distinctly for easier debugging
    const err = error as { code?: string; message?: string };
    if (err?.code === "ECONNABORTED") {
      console.warn("createSession aborted due to timeout");
    }
    console.error("Failed to create session:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Get a specific session by ID or UID (accepts string)
export const getSession = async (idOrUid: string) => {
  try {
    const response = await apiHelpers.get<SessionResponse>(`/sessions/${idOrUid}`);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch session:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Update a session by ID or UID
export const updateSession = async (idOrUid: string, body: SessionUpdate) => {
  try {
    const response = await apiHelpers.put<SessionResponse>(`/sessions/${idOrUid}`, body);
    return response.data;
  } catch (error) {
    console.error("Failed to update session:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Delete a session by ID or UID
export const deleteSession = async (idOrUid: string) => {
  try {
    const response = await apiHelpers.del<{ message: string }>(`/sessions/${idOrUid}`);
    return response.data;
  } catch (error) {
    console.error("Failed to delete session:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// List sessions by counselor UID with pagination
export const listSessionsByCounselor = async (
  counselorUid: string, 
  params: PaginationParams = { skip: 0, limit: 10 }
) => {
  try {
    const response = await apiHelpers.get<PaginatedResponse<SessionResponse>>(
      `/sessions/by-counselor/${counselorUid}`, 
      params as Record<string, unknown>
    );
    return response.data;
  } catch (error) {
    console.error("Failed to fetch sessions by counselor:", error);
    // Return empty result structure for graceful UI handling
    return {
      items: [],
      total: 0,
      skip: params.skip || 0,
      limit: params.limit || 10,
    } as PaginatedResponse<SessionResponse>;
  }
};

// Trigger session analysis with Celery backend
export const analyzeSession = async (sessionUid: string): Promise<AnalysisTaskResponse> => {
  try {
    const response = await apiHelpers.get<AnalysisTaskResponse>(`/sessions/${sessionUid}/analysis_by_celery`);
    await new Promise(resolve => setTimeout(resolve, 3000)); // Temporary delay for demo purposes
    return response.data;
  } catch (error) {
    console.error("Failed to start session analysis:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Types for raw transcript response
interface RawTranscriptResponse {
  uid: string;
  total_segments: number;
  status?: "PENDING" | "STARTED" | "COMPLETED" | "FAILED";
  raw_transcript: {
    metadata: {
      chunk_name: string;
      processing_time_seconds: number;
      timestamp: string;
      role_mapping: {
        counselor: number;
        student: number;
      };
      total_speakers: number;
    };
    utterances: Array<{
      speaker: number;
      text: string;
      start_time: string;
      end_time: string;
      confidence: number;
      role: string;
    }>;
  };
  created_at: string;
  updated_at: string;
  session: {
    uid: string;
    description: string;
    session_date: string;
    counselor: {
      uid: string;
      name: string;
    };
  };
}

// Get raw transcript by session UID
export const getRawTranscript = async (sessionUid: string): Promise<RawTranscriptResponse | null> => {
  try {
    const response = await apiHelpers.get<RawTranscriptResponse>(`/raw-transcripts/by-session/${sessionUid}`);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch raw transcript:", error);
    // Return null instead of throwing error to handle gracefully
    return null;
  }
};

// Export all session services as default
export const sessionService = {
  listSessions,
  createSession,
  getSession,
  updateSession,
  deleteSession,
  listSessionsByCounselor,
  analyzeSession,
  getRawTranscript,
};
