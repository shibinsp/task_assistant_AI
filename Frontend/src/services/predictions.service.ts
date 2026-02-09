import apiClient from '@/lib/api-client';
import type {
  ApiPrediction,
  ApiVelocityForecast,
  ApiHiringPrediction,
  ApiPredictionAccuracy,
} from '@/types/api';

export const predictionsService = {
  async getTaskPrediction(taskId: string): Promise<ApiPrediction> {
    const { data } = await apiClient.get<ApiPrediction>(`/predictions/tasks/${taskId}`);
    return data;
  },

  async getTeamVelocity(teamId: string): Promise<ApiVelocityForecast> {
    const { data } = await apiClient.get<ApiVelocityForecast>(`/predictions/team/${teamId}/velocity`);
    return data;
  },

  async getHiringPredictions(): Promise<ApiHiringPrediction[]> {
    const { data } = await apiClient.get<ApiHiringPrediction[]>('/predictions/hiring');
    return data;
  },

  async getPredictionAccuracy(days?: number): Promise<ApiPredictionAccuracy> {
    const { data } = await apiClient.get<ApiPredictionAccuracy>('/predictions/accuracy', {
      params: days ? { days } : undefined,
    });
    return data;
  },
};
