import apiClient from '@/lib/api-client';
import type { ApiPattern, ApiAgent, ApiROIDashboard } from '@/types/api';

export const automationService = {
  async getPatterns(status?: string): Promise<ApiPattern[]> {
    const { data } = await apiClient.get<ApiPattern[]>('/automation/patterns', {
      params: status ? { status } : undefined,
    });
    return data;
  },

  async acceptPattern(patternId: string): Promise<ApiPattern> {
    const { data } = await apiClient.post<ApiPattern>(`/automation/patterns/${patternId}/accept`);
    return data;
  },

  async getAgents(status?: string): Promise<ApiAgent[]> {
    const { data } = await apiClient.get<ApiAgent[]>('/automation/agents', {
      params: status ? { status } : undefined,
    });
    return data;
  },

  async createAgent(payload: { name: string; description?: string; pattern_id?: string; config?: Record<string, unknown> }): Promise<ApiAgent> {
    const { data } = await apiClient.post<ApiAgent>('/automation/agents', payload);
    return data;
  },

  async updateAgentStatus(agentId: string, status: string): Promise<ApiAgent> {
    const { data } = await apiClient.patch<ApiAgent>(`/automation/agents/${agentId}/status`, { status });
    return data;
  },

  async getROI(): Promise<ApiROIDashboard> {
    const { data } = await apiClient.get<ApiROIDashboard>('/automation/roi');
    return data;
  },
};
