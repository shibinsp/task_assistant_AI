import apiClient from '@/lib/api-client';
import type {
  ApiOrganization,
  ApiOrganizationDetail,
  ApiOrganizationUpdate,
  ApiOrganizationSettings,
  ApiOrganizationFeatures,
  ApiOrganizationStats,
  ApiOrganizationListResponse,
} from '@/types/api';

export const organizationsService = {
  async list(params?: {
    skip?: number;
    limit?: number;
    plan?: string;
    is_active?: boolean;
    search?: string;
  }): Promise<ApiOrganizationListResponse> {
    const { data } = await apiClient.get<ApiOrganizationListResponse>('/organizations', { params });
    return data;
  },

  async getCurrent(): Promise<ApiOrganizationDetail> {
    const { data } = await apiClient.get<ApiOrganizationDetail>('/organizations/current');
    return data;
  },

  async get(orgId: string): Promise<ApiOrganizationDetail> {
    const { data } = await apiClient.get<ApiOrganizationDetail>(`/organizations/${orgId}`);
    return data;
  },

  async update(orgId: string, payload: ApiOrganizationUpdate): Promise<ApiOrganization> {
    const { data } = await apiClient.patch<ApiOrganization>(`/organizations/${orgId}`, payload);
    return data;
  },

  async getSettings(orgId: string): Promise<ApiOrganizationSettings> {
    const { data } = await apiClient.get<ApiOrganizationSettings>(`/organizations/${orgId}/settings`);
    return data;
  },

  async updateSettings(orgId: string, payload: Partial<ApiOrganizationSettings>): Promise<ApiOrganizationSettings> {
    const { data } = await apiClient.patch<ApiOrganizationSettings>(`/organizations/${orgId}/settings`, payload);
    return data;
  },

  async getFeatures(orgId: string): Promise<ApiOrganizationFeatures> {
    const { data } = await apiClient.get<ApiOrganizationFeatures>(`/organizations/${orgId}/features`);
    return data;
  },

  async getStats(orgId: string): Promise<ApiOrganizationStats> {
    const { data } = await apiClient.get<ApiOrganizationStats>(`/organizations/${orgId}/stats`);
    return data;
  },
};
