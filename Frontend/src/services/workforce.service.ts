import apiClient from '@/lib/api-client';
import type {
  ApiWorkforceScore,
  ApiManagerRanking,
  ApiOrgHealth,
  ApiAttritionRisk,
  ApiSimulationCreate,
  ApiSimulation,
  ApiHiringPlan,
} from '@/types/api';

export const workforceService = {
  async getScores(params?: {
    skip?: number;
    limit?: number;
    team_id?: string;
    min_score?: number;
  }): Promise<ApiWorkforceScore[]> {
    const { data } = await apiClient.get<ApiWorkforceScore[]>('/workforce/scores', { params });
    return data;
  },

  async getUserScore(userId: string): Promise<ApiWorkforceScore> {
    const { data } = await apiClient.get<ApiWorkforceScore>(`/workforce/scores/${userId}`);
    return data;
  },

  async getManagerRankings(): Promise<ApiManagerRanking[]> {
    const { data } = await apiClient.get<ApiManagerRanking[]>('/workforce/managers/ranking');
    return data;
  },

  async getOrgHealth(): Promise<ApiOrgHealth> {
    const { data } = await apiClient.get<ApiOrgHealth>('/workforce/org-health');
    return data;
  },

  async getAttritionRisk(riskLevel?: string): Promise<ApiAttritionRisk[]> {
    const { data } = await apiClient.get<ApiAttritionRisk[]>('/workforce/attrition-risk', {
      params: riskLevel ? { risk_level: riskLevel } : undefined,
    });
    return data;
  },

  async createSimulation(payload: ApiSimulationCreate): Promise<ApiSimulation> {
    const { data } = await apiClient.post<ApiSimulation>('/workforce/simulate', payload);
    return data;
  },

  async getSimulations(): Promise<ApiSimulation[]> {
    const { data } = await apiClient.get<ApiSimulation[]>('/workforce/scenarios');
    return data;
  },

  async getSimulation(scenarioId: string): Promise<ApiSimulation> {
    const { data } = await apiClient.get<ApiSimulation>(`/workforce/scenarios/${scenarioId}`);
    return data;
  },

  async getHiringPlan(): Promise<ApiHiringPlan> {
    const { data } = await apiClient.get<ApiHiringPlan>('/workforce/hiring-gaps');
    return data;
  },
};
