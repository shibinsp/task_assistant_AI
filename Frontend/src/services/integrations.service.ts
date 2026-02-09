import apiClient from '@/lib/api-client';
import type {
  ApiIntegration,
  ApiIntegrationCreate,
  ApiWebhook,
  ApiWebhookCreate,
  ApiWebhookUpdate,
  ApiWebhookDelivery,
} from '@/types/api';

export const integrationsService = {
  // ─── Integrations ──────────────────────────────────────────────

  async list(params?: { integration_type?: string; is_active?: boolean }): Promise<ApiIntegration[]> {
    const { data } = await apiClient.get<ApiIntegration[]>('/integrations', { params });
    return data;
  },

  async create(payload: ApiIntegrationCreate): Promise<ApiIntegration> {
    const { data } = await apiClient.post<ApiIntegration>('/integrations', payload);
    return data;
  },

  async get(integrationId: string): Promise<ApiIntegration> {
    const { data } = await apiClient.get<ApiIntegration>(`/integrations/${integrationId}`);
    return data;
  },

  async update(integrationId: string, payload: Partial<ApiIntegrationCreate>): Promise<ApiIntegration> {
    const { data } = await apiClient.patch<ApiIntegration>(`/integrations/${integrationId}`, payload);
    return data;
  },

  async delete(integrationId: string): Promise<void> {
    await apiClient.delete(`/integrations/${integrationId}`);
  },

  async sync(integrationId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.post<{ status: string; message: string }>(`/integrations/${integrationId}/sync`);
    return data;
  },

  async testConnection(integrationId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.post<{ status: string; message: string }>(`/integrations/${integrationId}/test`);
    return data;
  },

  async initiateOAuth(integrationType: string, redirectUri: string): Promise<{ auth_url: string; state: string }> {
    const { data } = await apiClient.post<{ auth_url: string; state: string }>('/integrations/oauth/initiate', {
      integration_type: integrationType,
      redirect_uri: redirectUri,
    });
    return data;
  },

  async completeOAuth(integrationType: string, code: string, state: string): Promise<ApiIntegration> {
    const { data } = await apiClient.post<ApiIntegration>('/integrations/oauth/complete', {
      integration_type: integrationType,
      code,
      state,
    });
    return data;
  },

  // ─── Webhooks ──────────────────────────────────────────────────

  async listWebhooks(activeOnly?: boolean): Promise<ApiWebhook[]> {
    const { data } = await apiClient.get<ApiWebhook[]>('/webhooks', {
      params: activeOnly !== undefined ? { active_only: activeOnly } : undefined,
    });
    return data;
  },

  async createWebhook(payload: ApiWebhookCreate): Promise<ApiWebhook> {
    const { data } = await apiClient.post<ApiWebhook>('/webhooks', payload);
    return data;
  },

  async getWebhook(webhookId: string): Promise<ApiWebhook> {
    const { data } = await apiClient.get<ApiWebhook>(`/webhooks/${webhookId}`);
    return data;
  },

  async updateWebhook(webhookId: string, payload: ApiWebhookUpdate): Promise<ApiWebhook> {
    const { data } = await apiClient.patch<ApiWebhook>(`/webhooks/${webhookId}`, payload);
    return data;
  },

  async deleteWebhook(webhookId: string): Promise<void> {
    await apiClient.delete(`/webhooks/${webhookId}`);
  },

  async testWebhook(webhookId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.post<{ status: string; message: string }>(`/webhooks/${webhookId}/test`);
    return data;
  },

  async getWebhookDeliveries(webhookId: string, limit?: number): Promise<ApiWebhookDelivery[]> {
    const { data } = await apiClient.get<ApiWebhookDelivery[]>(`/webhooks/${webhookId}/deliveries`, {
      params: limit ? { limit } : undefined,
    });
    return data;
  },

  async retryDelivery(deliveryId: string): Promise<{ status: string; message: string }> {
    const { data } = await apiClient.post<{ status: string; message: string }>(`/webhooks/deliveries/${deliveryId}/retry`);
    return data;
  },
};
