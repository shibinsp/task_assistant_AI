import apiClient from '@/lib/api-client';
import type {
  ApiChatMessageRequest,
  ApiChatMessageResponse,
  ApiConversation,
  ApiConversationDetail,
} from '@/types/api';

export const chatService = {
  async sendMessage(payload: ApiChatMessageRequest): Promise<ApiChatMessageResponse> {
    const { data } = await apiClient.post<ApiChatMessageResponse>('/chat', payload);
    return data;
  },

  async listConversations(params?: {
    is_active?: boolean;
    limit?: number;
  }): Promise<ApiConversation[]> {
    const { data } = await apiClient.get<ApiConversation[]>('/chat/conversations', { params });
    return data;
  },

  async getConversation(conversationId: string): Promise<ApiConversationDetail> {
    const { data } = await apiClient.get<ApiConversationDetail>(`/chat/conversations/${conversationId}`);
    return data;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/chat/conversations/${conversationId}`);
  },

  async endConversation(conversationId: string): Promise<void> {
    await apiClient.post(`/chat/conversations/${conversationId}/end`);
  },
};
