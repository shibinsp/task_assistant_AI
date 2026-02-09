import apiClient from '@/lib/api-client';
import type {
  ApiOrchestratorAgent,
  ApiAgentExecuteRequest,
  ApiAgentExecuteResponse,
  ApiAgentExecution,
} from '@/types/api';

export const agentsService = {
  async list(params?: { agent_type?: string; is_enabled?: boolean }): Promise<ApiOrchestratorAgent[]> {
    const { data } = await apiClient.get<ApiOrchestratorAgent[]>('/agents', { params });
    return data;
  },

  async get(agentName: string): Promise<ApiOrchestratorAgent> {
    const { data } = await apiClient.get<ApiOrchestratorAgent>(`/agents/${agentName}`);
    return data;
  },

  async execute(agentName: string, payload: ApiAgentExecuteRequest): Promise<ApiAgentExecuteResponse> {
    const { data } = await apiClient.post<ApiAgentExecuteResponse>(`/agents/${agentName}/execute`, payload);
    return data;
  },

  async getExecutions(agentName: string, limit?: number): Promise<ApiAgentExecution[]> {
    const { data } = await apiClient.get<ApiAgentExecution[]>(`/agents/${agentName}/executions`, {
      params: limit ? { limit } : undefined,
    });
    return data;
  },

  async updateConfig(agentName: string, config: Record<string, unknown>): Promise<{ status: string }> {
    const { data } = await apiClient.patch<{ status: string }>(`/agents/${agentName}/config`, { config });
    return data;
  },

  async orchestrate(payload: {
    event_type: string;
    event_data: Record<string, unknown>;
    task_id?: string;
  }): Promise<Record<string, unknown>> {
    const { data } = await apiClient.post<Record<string, unknown>>('/agents/orchestrate', payload);
    return data;
  },

  async getRecommendations(taskId?: string): Promise<{
    recommendations: Array<{ agent_name: string; reason: string; confidence: number }>;
  }> {
    const { data } = await apiClient.get('/agents/recommendations', {
      params: taskId ? { task_id: taskId } : undefined,
    });
    return data;
  },

  async getStats(): Promise<Record<string, unknown>> {
    const { data } = await apiClient.get('/agents/stats');
    return data;
  },
};
