import apiClient from '@/lib/api-client';
import type {
  ApiTask,
  ApiTaskDetail,
  ApiTaskListResponse,
  ApiTaskCreate,
  ApiTaskUpdate,
  ApiTaskStatusUpdate,
  ApiTaskStatus,
  ApiTaskPriority,
  ApiSubtaskCreate,
  ApiDependency,
  ApiDependencyCreate,
  ApiComment,
  ApiCommentCreate,
  ApiCommentUpdate,
  ApiTaskHistory,
  ApiTaskDecompositionRequest,
  ApiTaskDecompositionResponse,
  ApiSubtaskSuggestion,
  ApiBulkTaskUpdate,
  ApiBulkOperationResult,
} from '@/types/api';

export interface TaskListParams {
  skip?: number;
  limit?: number;
  status?: ApiTaskStatus;
  priority?: ApiTaskPriority;
  assigned_to?: string;
  team_id?: string;
  project_id?: string;
  root_only?: boolean;
  search?: string;
}

export const tasksService = {
  // ─── Core CRUD ──────────────────────────────────────────────────

  async list(params?: TaskListParams): Promise<ApiTaskListResponse> {
    const { data } = await apiClient.get<ApiTaskListResponse>('/tasks', { params });
    return data;
  },

  async get(taskId: string): Promise<ApiTaskDetail> {
    const { data } = await apiClient.get<ApiTaskDetail>(`/tasks/${taskId}`);
    return data;
  },

  async create(payload: ApiTaskCreate): Promise<ApiTask> {
    const { data } = await apiClient.post<ApiTask>('/tasks', payload);
    return data;
  },

  async update(taskId: string, payload: ApiTaskUpdate): Promise<ApiTask> {
    const { data } = await apiClient.patch<ApiTask>(`/tasks/${taskId}`, payload);
    return data;
  },

  async updateStatus(taskId: string, payload: ApiTaskStatusUpdate): Promise<ApiTask> {
    const { data } = await apiClient.patch<ApiTask>(`/tasks/${taskId}/status`, payload);
    return data;
  },

  async delete(taskId: string): Promise<void> {
    await apiClient.delete(`/tasks/${taskId}`);
  },

  async getStatistics(params?: { team_id?: string; project_id?: string; user_id?: string }) {
    const { data } = await apiClient.get('/tasks/statistics', { params });
    return data;
  },

  // ─── Assignment ─────────────────────────────────────────────────

  async assign(taskId: string, assigneeId?: string): Promise<ApiTask> {
    const { data } = await apiClient.post<ApiTask>(`/tasks/${taskId}/assign`, null, {
      params: { assignee_id: assigneeId },
    });
    return data;
  },

  // ─── Bulk Operations ───────────────────────────────────────────

  async bulkUpdate(payload: ApiBulkTaskUpdate): Promise<ApiBulkOperationResult> {
    const { data } = await apiClient.post<ApiBulkOperationResult>('/tasks/bulk/update', payload);
    return data;
  },

  // ─── Subtasks ───────────────────────────────────────────────────

  async getSubtasks(taskId: string): Promise<ApiTask[]> {
    const { data } = await apiClient.get<ApiTask[]>(`/tasks/${taskId}/subtasks`);
    return data;
  },

  async createSubtask(taskId: string, payload: ApiSubtaskCreate): Promise<ApiTask> {
    const { data } = await apiClient.post<ApiTask>(`/tasks/${taskId}/subtasks`, payload);
    return data;
  },

  async reorderSubtasks(taskId: string, subtaskIds: string[]): Promise<ApiTask[]> {
    const { data } = await apiClient.post<ApiTask[]>(`/tasks/${taskId}/subtasks/reorder`, subtaskIds);
    return data;
  },

  // ─── Dependencies ──────────────────────────────────────────────

  async getDependencies(taskId: string): Promise<ApiDependency[]> {
    const { data } = await apiClient.get<ApiDependency[]>(`/tasks/${taskId}/dependencies`);
    return data;
  },

  async addDependency(taskId: string, payload: ApiDependencyCreate): Promise<ApiDependency> {
    const { data } = await apiClient.post<ApiDependency>(`/tasks/${taskId}/dependencies`, payload);
    return data;
  },

  async removeDependency(taskId: string, dependencyId: string): Promise<void> {
    await apiClient.delete(`/tasks/${taskId}/dependencies/${dependencyId}`);
  },

  // ─── Comments ──────────────────────────────────────────────────

  async getComments(taskId: string, params?: { skip?: number; limit?: number }): Promise<ApiComment[]> {
    const { data } = await apiClient.get<ApiComment[]>(`/tasks/${taskId}/comments`, { params });
    return data;
  },

  async addComment(taskId: string, payload: ApiCommentCreate): Promise<ApiComment> {
    const { data } = await apiClient.post<ApiComment>(`/tasks/${taskId}/comments`, payload);
    return data;
  },

  async updateComment(taskId: string, commentId: string, payload: ApiCommentUpdate): Promise<ApiComment> {
    const { data } = await apiClient.patch<ApiComment>(`/tasks/${taskId}/comments/${commentId}`, payload);
    return data;
  },

  async deleteComment(taskId: string, commentId: string): Promise<void> {
    await apiClient.delete(`/tasks/${taskId}/comments/${commentId}`);
  },

  // ─── History ───────────────────────────────────────────────────

  async getHistory(taskId: string, params?: { skip?: number; limit?: number }): Promise<ApiTaskHistory[]> {
    const { data } = await apiClient.get<ApiTaskHistory[]>(`/tasks/${taskId}/history`, { params });
    return data;
  },

  // ─── AI Decomposition ─────────────────────────────────────────

  async decompose(taskId: string, payload?: ApiTaskDecompositionRequest): Promise<ApiTaskDecompositionResponse> {
    const { data } = await apiClient.post<ApiTaskDecompositionResponse>(
      `/tasks/${taskId}/decompose`,
      payload || {}
    );
    return data;
  },

  async applyDecomposition(taskId: string, subtasks: ApiSubtaskSuggestion[]): Promise<ApiTask[]> {
    const { data } = await apiClient.post<ApiTask[]>(`/tasks/${taskId}/decompose/apply`, subtasks);
    return data;
  },
};
