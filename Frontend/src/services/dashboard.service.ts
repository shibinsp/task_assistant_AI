import apiClient from '@/lib/api-client';
import type { ApiDashboardMetrics, ApiVelocityData } from '@/types/api';

export const dashboardService = {
  async getMetrics(params?: { team_id?: string; user_id?: string }): Promise<ApiDashboardMetrics> {
    const { data } = await apiClient.get<ApiDashboardMetrics>('/reports/dashboard', { params });
    return data;
  },

  async getVelocity(params?: { team_id?: string; weeks?: number }): Promise<ApiVelocityData> {
    const { data } = await apiClient.get<ApiVelocityData>('/reports/velocity', { params });
    return data;
  },

  async getBottlenecks(params?: { team_id?: string }) {
    const { data } = await apiClient.get('/reports/bottlenecks', { params });
    return data;
  },

  async getExecutiveSummary(periodDays?: number) {
    const { data } = await apiClient.get('/reports/executive-summary', {
      params: { period_days: periodDays },
    });
    return data;
  },
};
