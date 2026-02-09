import apiClient from '@/lib/api-client';
import type {
  ApiAuditLogListResponse,
  ApiSystemHealthResponse,
  ApiGDPRExportResponse,
  ApiAIGovernanceResponse,
  ApiAPIKey,
  ApiAPIKeyCreate,
  ApiAPIKeyCreatedResponse,
} from '@/types/api';

export const adminService = {
  // ─── Audit Logs ─────────────────────────────────────────────────

  async getAuditLogs(params?: {
    skip?: number;
    limit?: number;
    actor_type?: string;
    action?: string;
    resource_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<ApiAuditLogListResponse> {
    const { data } = await apiClient.get<ApiAuditLogListResponse>('/admin/audit-logs', { params });
    return data;
  },

  // ─── System Health ──────────────────────────────────────────────

  async getSystemHealth(): Promise<ApiSystemHealthResponse> {
    const { data } = await apiClient.get<ApiSystemHealthResponse>('/admin/system/health');
    return data;
  },

  // ─── GDPR ───────────────────────────────────────────────────────

  async requestGDPRExport(userId: string): Promise<ApiGDPRExportResponse> {
    const { data } = await apiClient.post<ApiGDPRExportResponse>(`/admin/gdpr/export/${userId}`);
    return data;
  },

  async requestGDPRErasure(userId: string): Promise<{ request_id: string; status: string; message: string }> {
    const { data } = await apiClient.delete<{ request_id: string; status: string; message: string }>(
      `/admin/gdpr/erase/${userId}`
    );
    return data;
  },

  // ─── AI Governance ──────────────────────────────────────────────

  async getAIGovernance(): Promise<ApiAIGovernanceResponse> {
    const { data } = await apiClient.get<ApiAIGovernanceResponse>('/admin/ai/governance');
    return data;
  },

  // ─── API Keys ───────────────────────────────────────────────────

  async listAPIKeys(): Promise<ApiAPIKey[]> {
    const { data } = await apiClient.get<ApiAPIKey[]>('/admin/api-keys');
    return data;
  },

  async createAPIKey(payload: ApiAPIKeyCreate): Promise<ApiAPIKeyCreatedResponse> {
    const { data } = await apiClient.post<ApiAPIKeyCreatedResponse>('/admin/api-keys', payload);
    return data;
  },

  async revokeAPIKey(keyId: string): Promise<void> {
    await apiClient.delete(`/admin/api-keys/${keyId}`);
  },
};
