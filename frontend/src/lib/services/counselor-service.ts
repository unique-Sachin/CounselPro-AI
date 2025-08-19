import { 
  CounselorResponse, 
  CounselorUpdate,
  PaginatedResponse 
} from "@/lib/types";
import { apiHelpers } from "@/lib/api";

export const listCounselors = async (
  skip: number = 0,
  limit: number = 10
): Promise<PaginatedResponse<CounselorResponse>> => {
  const response = await apiHelpers.get<PaginatedResponse<CounselorResponse>>("/counselors", { skip, limit });
  return response.data;
};

export const createCounselor = async (data: CounselorUpdate): Promise<CounselorResponse> => {
  const response = await apiHelpers.post<CounselorResponse>("/counselors", data);
  return response.data;
};

export const updateCounselor = async (
  id: string,
  data: CounselorUpdate
): Promise<CounselorResponse> => {
  const response = await apiHelpers.put<CounselorResponse>(`/counselors/${id}`, data);
  return response.data;
};

export const deleteCounselor = async (id: string): Promise<void> => {
  await apiHelpers.del(`/counselors/${id}`);
};