import apiClient from '@/lib/api-client';
import type { ApiUserListResponse, ApiUserCreate } from '@/types/api';

export interface UserListParams {
  role?: string;
  team_id?: string;
  is_active?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

export const teamService = {
  async listUsers(params?: UserListParams): Promise<ApiUserListResponse> {
    const { data } = await apiClient.get<ApiUserListResponse>('/users', { params });
    return data;
  },

  async getUser(userId: string) {
    const { data } = await apiClient.get(`/users/${userId}`);
    return data;
  },

  async createUser(payload: ApiUserCreate) {
    const { data } = await apiClient.post('/users', payload);
    return data;
  },

  async deleteUser(userId: string) {
    await apiClient.delete(`/users/${userId}`);
  },
};
