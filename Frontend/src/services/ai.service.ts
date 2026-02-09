import apiClient from '@/lib/api-client';
import type {
  ApiUnblockRequest,
  ApiUnblockResponse,
  ApiUnblockFeedback,
  ApiKnowledgeBaseStatus,
  ApiDocument,
  ApiDocumentCreate,
  ApiDocumentUpdate,
  ApiDocumentListResponse,
} from '@/types/api';

export const aiService = {
  // ─── Unblock ────────────────────────────────────────────────────

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

  // ─── Knowledge Base ─────────────────────────────────────────────

  async getKnowledgeBaseStatus(): Promise<ApiKnowledgeBaseStatus> {
    const { data } = await apiClient.get<ApiKnowledgeBaseStatus>('/ai/knowledge-base/status');
    return data;
  },

  async listDocuments(params?: {
    skip?: number;
    limit?: number;
    source?: string;
    doc_type?: string;
    status?: string;
    search?: string;
  }): Promise<ApiDocumentListResponse> {
    const { data } = await apiClient.get<ApiDocumentListResponse>('/ai/knowledge-base/documents', { params });
    return data;
  },

  async createDocument(payload: ApiDocumentCreate): Promise<ApiDocument> {
    const { data } = await apiClient.post<ApiDocument>('/ai/knowledge-base/documents', payload);
    return data;
  },

  async getDocument(docId: string): Promise<ApiDocument> {
    const { data } = await apiClient.get<ApiDocument>(`/ai/knowledge-base/documents/${docId}`);
    return data;
  },

  async updateDocument(docId: string, payload: ApiDocumentUpdate): Promise<ApiDocument> {
    const { data } = await apiClient.patch<ApiDocument>(`/ai/knowledge-base/documents/${docId}`, payload);
    return data;
  },

  async deleteDocument(docId: string): Promise<void> {
    await apiClient.delete(`/ai/knowledge-base/documents/${docId}`);
  },

  async uploadDocument(file: File, docType?: string, isPublic?: boolean): Promise<ApiDocument> {
    const formData = new FormData();
    formData.append('file', file);
    if (docType) formData.append('doc_type', docType);
    if (isPublic !== undefined) formData.append('is_public', String(isPublic));
    const { data } = await apiClient.post<ApiDocument>('/ai/knowledge-base/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
};
