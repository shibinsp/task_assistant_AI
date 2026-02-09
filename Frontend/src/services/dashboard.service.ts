import apiClient from '@/lib/api-client';
import type {
  ApiDashboardMetrics,
  ApiVelocityData,
  ApiTeamWorkload,
  ApiCheckinSummary,
  ApiReportRequest,
  ApiTeamProductivity,
  ApiScheduleReportRequest,
} from '@/types/api';

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

  async getTeamWorkload(teamId?: string): Promise<ApiTeamWorkload> {
    const url = teamId ? `/reports/team/${teamId}/workload` : '/reports/workload';
    const { data } = await apiClient.get<ApiTeamWorkload>(url);
    return data;
  },

  async getCheckinSummary(params?: { team_id?: string; days?: number }): Promise<ApiCheckinSummary> {
    const { data } = await apiClient.get<ApiCheckinSummary>('/reports/checkin-summary', { params });
    return data;
  },

  async generateReport(payload: ApiReportRequest) {
    const { data } = await apiClient.post('/reports/generate', payload);
    return data;
  },

  async getTeamProductivity(params?: { period?: string; start_date?: string; end_date?: string; team_id?: string }): Promise<ApiTeamProductivity> {
    if (params?.team_id) {
      const { team_id, ...rest } = params;
      const { data } = await apiClient.get<ApiTeamProductivity>(`/reports/team/${team_id}/productivity`, { params: rest });
      return data;
    }
    const { data } = await apiClient.get<ApiTeamProductivity>('/reports/productivity', { params });
    return data;
  },

  async scheduleReport(payload: ApiScheduleReportRequest) {
    const { data } = await apiClient.post('/reports/schedule', payload);
    return data;
  },
};
