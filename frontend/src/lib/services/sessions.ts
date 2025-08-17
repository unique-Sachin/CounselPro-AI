import { apiHelpers } from "@/lib/api";
import { 
  SessionResponse, 
  SessionCreate, 
  SessionUpdate, 
  PaginatedResponse, 
  PaginationParams 
} from "@/lib/types";

// List sessions with pagination
export const listSessions = async (params: PaginationParams = { skip: 0, limit: 10 }) => {
  try {
    const response = await apiHelpers.get<SessionResponse[]>("/sessions/all", params as Record<string, unknown>);
    const sessions = response.data;
    
    // Transform the array response into paginated format
    return {
      items: sessions,
      total: sessions.length,
      skip: params.skip || 0,
      limit: params.limit || 10,
    } as PaginatedResponse<SessionResponse>;
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

// List sessions by counselor ID with pagination
export const listSessionsByCounselor = async (
  counselorIdNumber: number, 
  params: PaginationParams = { skip: 0, limit: 10 }
) => {
  try {
    const response = await apiHelpers.get<PaginatedResponse<SessionResponse>>(
      `/sessions/by-counselor/${counselorIdNumber}`, 
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

// Export all session services as default
export const sessionService = {
  listSessions,
  createSession,
  getSession,
  updateSession,
  deleteSession,
  listSessionsByCounselor,
};
