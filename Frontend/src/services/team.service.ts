import apiClient from '@/lib/api-client';
import type { ApiUserListResponse, ApiUserCreate, ApiUser, ApiUserPermissions } from '@/types/api';

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

  async getUser(userId: string): Promise<ApiUser> {
    const { data } = await apiClient.get<ApiUser>(`/users/${userId}`);
    return data;
  },

  async createUser(payload: ApiUserCreate): Promise<ApiUser> {
    const { data } = await apiClient.post<ApiUser>('/users', payload);
    return data;
  },

  async deleteUser(userId: string): Promise<void> {
    await apiClient.delete(`/users/${userId}`);
  },

  async activateUser(userId: string): Promise<ApiUser> {
    const { data } = await apiClient.post<ApiUser>(`/users/${userId}/activate`);
    return data;
  },

  async getUserPermissions(userId: string): Promise<ApiUserPermissions> {
    const { data } = await apiClient.get<ApiUserPermissions>(`/users/${userId}/permissions`);
    return data;
  },
};
