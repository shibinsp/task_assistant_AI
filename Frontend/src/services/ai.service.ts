import apiClient from '@/lib/api-client';
import type { ApiUnblockRequest, ApiUnblockResponse, ApiUnblockFeedback } from '@/types/api';

export const aiService = {
  async unblock(payload: ApiUnblockRequest): Promise<ApiUnblockResponse> {
    const { data } = await apiClient.post<ApiUnblockResponse>('/ai/unblock', payload);
    return data;
  },

  async submitFeedback(sessionId: string, payload: ApiUnblockFeedback): Promise<void> {
    await apiClient.post(`/ai/unblock/${sessionId}/feedback`, payload);
  },

  async getHistory(params?: { skip?: number; limit?: number; task_id?: string }) {
    const { data } = await apiClient.get('/ai/unblock/history', { params });
    return data;
  },
};
