import apiClient from '@/lib/api-client';
import type {
  ApiCheckIn,
  ApiCheckInListResponse,
  ApiCheckInSubmit,
  ApiCheckInSkip,
  ApiCheckInCreate,
  ApiCheckInConfig,
  ApiCheckInConfigCreate,
  ApiCheckInConfigUpdate,
  ApiCheckInStatistics,
  ApiCheckInFeedResponse,
  ApiEscalationRequest,
  ApiEscalationResponse,
} from '@/types/api';

export interface CheckInListParams {
  skip?: number;
  limit?: number;
  status?: string;
  task_id?: string;
  user_id?: string;
  team_id?: string;
}

export const checkinsService = {
  // ─── Check-In CRUD ──────────────────────────────────────────────

  async list(params?: CheckInListParams): Promise<ApiCheckInListResponse> {
    const { data } = await apiClient.get<ApiCheckInListResponse>('/checkins', { params });
    return data;
  },

  async getPending(): Promise<ApiCheckIn[]> {
    const { data } = await apiClient.get<ApiCheckIn[]>('/checkins/pending');
    return data;
  },

  async get(checkinId: string): Promise<ApiCheckIn> {
    const { data } = await apiClient.get<ApiCheckIn>(`/checkins/${checkinId}`);
    return data;
  },

  async create(payload: ApiCheckInCreate): Promise<ApiCheckIn> {
    const { data } = await apiClient.post<ApiCheckIn>('/checkins', payload);
    return data;
  },

  // ─── Check-In Actions ──────────────────────────────────────────

  async respond(checkinId: string, payload: ApiCheckInSubmit): Promise<ApiCheckIn> {
    const { data } = await apiClient.post<ApiCheckIn>(`/checkins/${checkinId}/respond`, payload);
    return data;
  },

  async skip(checkinId: string, payload?: ApiCheckInSkip): Promise<ApiCheckIn> {
    const { data } = await apiClient.post<ApiCheckIn>(`/checkins/${checkinId}/skip`, payload || {});
    return data;
  },

  async escalate(checkinId: string, payload: ApiEscalationRequest): Promise<ApiEscalationResponse> {
    const { data } = await apiClient.post<ApiEscalationResponse>(`/checkins/${checkinId}/escalate`, payload);
    return data;
  },

  // ─── Statistics & Feed ─────────────────────────────────────────

  async getStatistics(params?: { team_id?: string; user_id?: string; days?: number }): Promise<ApiCheckInStatistics> {
    const { data } = await apiClient.get<ApiCheckInStatistics>('/checkins/statistics', { params });
    return data;
  },

  async getManagerFeed(params?: { skip?: number; limit?: number; needs_attention?: boolean }): Promise<ApiCheckInFeedResponse> {
    const { data } = await apiClient.get<ApiCheckInFeedResponse>('/checkins/feed', { params });
    return data;
  },

  // ─── Configuration ─────────────────────────────────────────────

  async getConfigs(): Promise<ApiCheckInConfig[]> {
    const { data } = await apiClient.get<ApiCheckInConfig[]>('/checkins/config');
    return data;
  },

  async createConfig(payload: ApiCheckInConfigCreate): Promise<ApiCheckInConfig> {
    const { data } = await apiClient.post<ApiCheckInConfig>('/checkins/config', payload);
    return data;
  },

  async getConfig(configId: string): Promise<ApiCheckInConfig> {
    const { data } = await apiClient.get<ApiCheckInConfig>(`/checkins/config/${configId}`);
    return data;
  },

  async updateConfig(configId: string, payload: ApiCheckInConfigUpdate): Promise<ApiCheckInConfig> {
    const { data } = await apiClient.patch<ApiCheckInConfig>(`/checkins/config/${configId}`, payload);
    return data;
  },

  async deleteConfig(configId: string): Promise<void> {
    await apiClient.delete(`/checkins/config/${configId}`);
  },
};
