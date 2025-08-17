import { apiHelpers } from "@/lib/api";
import { 
  CounselorResponse, 
  CounselorCreate, 
  CounselorUpdate, 
  PaginatedResponse, 
  PaginationParams 
} from "@/lib/types";

// Type for the actual API response format
interface ApiCounselorResponse {
  uid: string;
  name: string;
  employee_id: string;
  dept: string;
  email: string;
  mobile_number: string;
}

// Type for the API's expected create format
interface ApiCounselorCreate {
  name: string;
  employee_id: string;
  dept: string;
  email: string;
  mobile_number: string;
}

// List counselors with pagination
export const listCounselors = async (params: PaginationParams = { skip: 0, limit: 10 }) => {
  try {
    // The API returns an array directly, not a paginated response
    const response = await apiHelpers.get<ApiCounselorResponse[]>("/counselors", params as Record<string, unknown>);
    const counselors = response.data;
    
    // Transform the API response to match our expected format
    const transformedCounselors: CounselorResponse[] = counselors.map((counselor: ApiCounselorResponse, index: number) => ({
      // Map API fields to our expected interface
      id: index + 1, // Generate ID since API doesn't provide it
      uid: counselor.uid,
      name: counselor.name,
      specialty: counselor.dept, // Map dept to specialty
      email: counselor.email,
      phone: counselor.mobile_number, // Map mobile_number to phone
      bio: undefined,
      years_of_experience: undefined,
      hourly_rate: undefined,
      availability_status: "available" as const, // Default status since API doesn't provide it
      rating: undefined,
      total_sessions: undefined,
      created_at: new Date().toISOString(), // Default timestamp
      updated_at: new Date().toISOString(), // Default timestamp
    }));

    // Apply client-side pagination since API doesn't handle it
    const skip = params.skip || 0;
    const limit = params.limit || 10;
    const paginatedItems = transformedCounselors.slice(skip, skip + limit);

    // Return in the expected paginated format
    return {
      items: paginatedItems,
      total: transformedCounselors.length,
      skip: skip,
      limit: limit,
    } as PaginatedResponse<CounselorResponse>;
  } catch (error: unknown) {
    const err = error as { response?: { status?: number }; code?: string } | undefined;
    const status = err?.response?.status as number | undefined;
    const code = err?.code as string | undefined;
    if (code === "ECONNABORTED" || status === 408) {
      console.warn("Counselors request timed out");
  } else if (!err?.response) {
      console.warn("Network error while fetching counselors");
    } else if (status === 405) {
      console.warn("GET /counselors method not allowed on backend");
    }
    console.error("Failed to fetch counselors:", error);
    // Return empty result structure for graceful UI handling
    return {
      items: [],
      total: 0,
      skip: params.skip || 0,
      limit: params.limit || 10,
    } as PaginatedResponse<CounselorResponse>;
  }
};

// Create a new counselor
export const createCounselor = async (body: CounselorCreate) => {
  try {
    // Transform our format to API's expected format
    const apiPayload: ApiCounselorCreate = {
      name: body.name,
      employee_id: body.employee_id,
      dept: body.specialty, // Map specialty to dept
      email: body.email,
      mobile_number: body.phone || "", // Map phone to mobile_number
    };

    const response = await apiHelpers.post<ApiCounselorResponse>("/counselors", apiPayload);
    
    // Transform the API response back to our expected format
    const transformedResponse: CounselorResponse = {
      id: Math.floor(Math.random() * 10000), // Generate ID since API doesn't provide it
      uid: response.data.uid,
      name: response.data.name,
      specialty: response.data.dept,
      email: response.data.email,
      phone: response.data.mobile_number,
      bio: undefined,
      years_of_experience: undefined,
      hourly_rate: undefined,
      availability_status: "available" as const,
      rating: undefined,
      total_sessions: undefined,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return transformedResponse;
  } catch (error) {
    console.error("Failed to create counselor:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Get a specific counselor by UID (accepts string)
export const getCounselor = async (uid: string) => {
  try {
    const response = await apiHelpers.get<CounselorResponse>(`/counselors/${uid}`);
    return response.data;
  } catch (error) {
    console.error("Failed to fetch counselor:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Update a counselor by UID
export const updateCounselor = async (uid: string, body: CounselorUpdate) => {
  try {
    const response = await apiHelpers.put<CounselorResponse>(`/counselors/${uid}`, body);
    return response.data;
  } catch (error) {
    console.error("Failed to update counselor:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Delete a counselor by UID
export const deleteCounselor = async (uid: string) => {
  try {
    const response = await apiHelpers.del<{ message: string }>(`/counselors/${uid}`, { counselor_uid: uid });
    return response.data;
  } catch (error) {
    console.error("Failed to delete counselor:", error);
    throw error; // Re-throw to let the UI handle the error
  }
};

// Export all counselor services as default
export const counselorService = {
  listCounselors,
  createCounselor,
  getCounselor,
  updateCounselor,
  deleteCounselor,
};
