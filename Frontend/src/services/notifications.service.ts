import apiClient from '@/lib/api-client';
import type {
  ApiNotificationListResponse,
  ApiNotification,
  ApiNotificationPreferences,
  ApiNotificationPreferencesUpdate,
} from '@/types/api';

export const notificationsService = {
  async list(params?: { skip?: number; limit?: number; unread_only?: boolean }): Promise<ApiNotificationListResponse> {
    const { data } = await apiClient.get<ApiNotificationListResponse>('/notifications', { params });
    return data;
  },

  async getUnreadCount(): Promise<{ unread_count: number }> {
    const { data } = await apiClient.get<{ unread_count: number }>('/notifications/unread-count');
    return data;
  },

  async markRead(notificationId: string): Promise<ApiNotification> {
    const { data } = await apiClient.patch<ApiNotification>(`/notifications/${notificationId}/read`);
    return data;
  },

  async markAllRead(): Promise<{ marked_read: number }> {
    const { data } = await apiClient.post<{ marked_read: number }>('/notifications/read-all');
    return data;
  },

  async delete(notificationId: string): Promise<void> {
    await apiClient.delete(`/notifications/${notificationId}`);
  },

  async getPreferences(): Promise<ApiNotificationPreferences> {
    const { data } = await apiClient.get<ApiNotificationPreferences>('/notifications/preferences');
    return data;
  },

  async updatePreferences(payload: ApiNotificationPreferencesUpdate): Promise<ApiNotificationPreferences> {
    const { data } = await apiClient.patch<ApiNotificationPreferences>('/notifications/preferences', payload);
    return data;
  },
};
