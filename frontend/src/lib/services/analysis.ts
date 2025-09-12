import { useQuery } from "@tanstack/react-query";
import { apiHelpers } from "@/lib/api";
import { 
  SessionAnalysisResponse, 
  UseSessionAnalysisOptions,
  BulkAnalysisResponse
} from "@/lib/types.analysis";

/**
 * Get session analysis by session UID
 * Endpoint: GET /session-analysis/by-session/{sessionUid}
 */
export const getSessionAnalysisBySession = async (sessionUid: string): Promise<SessionAnalysisResponse | null> => {
  try {
    const response = await apiHelpers.get<SessionAnalysisResponse>(`/session-analysis/by-session/${sessionUid}`);
    
    // The response data comes directly in response.data, not wrapped
    return response.data;
  } catch (error) {
    console.error("Failed to fetch session analysis:", error);
    // Return null instead of throwing error to handle gracefully in UI
    return null;
  }
};

/**
 * Trigger session analysis
 * Endpoint: GET /sessions/{uid}/analysis?session_id={uid}
 */
export const triggerSessionAnalysis = async (sessionUid: string): Promise<void> => {
  try {
    await apiHelpers.get(`/sessions/${sessionUid}/analysis`, { session_id: sessionUid });
  } catch (error) {
    console.error("Failed to trigger session analysis:", error);
    throw error;
  }
};

/**
 * Get bulk session analyses for dashboard
 * Endpoint: GET /session-analysis/bulk?session_ids=uid1,uid2,uid3
 */
export const getBulkSessionAnalyses = async (sessionIds: string[]): Promise<BulkAnalysisResponse> => {
  try {
    const sessionIdsParam = sessionIds.join(',');
    const response = await apiHelpers.get<BulkAnalysisResponse>(`/session-analysis/bulk?session_ids=${sessionIdsParam}`);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch bulk session analyses:", error);
    // Return empty analyses array on error to handle gracefully
    return { analyses: [] };
  }
};

/**
 * React Query hook for session analysis
 * @param sessionUid - The session UID to fetch analysis for
 * @param options - Optional configuration for the query
 */
export const useSessionAnalysis = (
  sessionUid: string, 
  options: UseSessionAnalysisOptions = {}
) => {
  const {
    enabled = true,
    refetchOnWindowFocus = false,
    refetchInterval,
  } = options;

  return useQuery({
    queryKey: ["session-analysis", sessionUid],
    queryFn: () => getSessionAnalysisBySession(sessionUid),
    enabled: !!sessionUid && enabled,
    refetchOnWindowFocus,
    refetchInterval,
    // Add meta information for debugging
    meta: {
      description: `Session analysis for session ${sessionUid}`,
    },
  });
};

/**
 * React Query hook with automatic refetching for pending analysis
 * Useful when analysis is still processing
 */
export const useSessionAnalysisWithPolling = (
  sessionUid: string,
  options: UseSessionAnalysisOptions & { pollingInterval?: number } = {}
) => {
  const { pollingInterval = 5000, ...queryOptions } = options;
  
  // First get the basic query
  const baseQuery = useSessionAnalysis(sessionUid, queryOptions);
  
  // Determine if we should continue polling based on status
  const shouldPoll = baseQuery.data?.status;
  
  // Create a polling query that inherits from the base query
  const pollingQuery = useSessionAnalysis(sessionUid, {
    ...queryOptions,
    refetchInterval: shouldPoll ? pollingInterval : undefined,
  });

  return pollingQuery;
};

// Export all analysis services
export const analysisService = {
  getSessionAnalysisBySession,
  triggerSessionAnalysis,
  getBulkSessionAnalyses,
  useSessionAnalysis,
  useSessionAnalysisWithPolling,
};
