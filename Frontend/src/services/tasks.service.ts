import apiClient from '@/lib/api-client';
import type {
  ApiTask,
  ApiTaskListResponse,
  ApiTaskCreate,
  ApiTaskUpdate,
  ApiTaskStatusUpdate,
  ApiTaskStatus,
  ApiTaskPriority,
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
  async list(params?: TaskListParams): Promise<ApiTaskListResponse> {
    const { data } = await apiClient.get<ApiTaskListResponse>('/tasks', { params });
    return data;
  },

  async get(taskId: string): Promise<ApiTask> {
    const { data } = await apiClient.get<ApiTask>(`/tasks/${taskId}`);
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
};
