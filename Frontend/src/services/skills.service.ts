import apiClient from '@/lib/api-client';
import type {
  ApiSkill,
  ApiSkillCreate,
  ApiSkillListResponse,
  ApiUserSkill,
  ApiUserSkillCreate,
  ApiSkillGraph,
  ApiSkillVelocity,
  ApiTeamSkillComposition,
  ApiSkillGapSummary,
  ApiLearningPath,
  ApiLearningPathCreate,
  ApiSelfSufficiencyMetrics,
} from '@/types/api';

export const skillsService = {
  // ─── Skill Catalog ──────────────────────────────────────────────

  async listSkills(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    search?: string;
  }): Promise<ApiSkillListResponse> {
    const { data } = await apiClient.get<ApiSkillListResponse>('/skills', { params });
    return data;
  },

  async createSkill(payload: ApiSkillCreate): Promise<ApiSkill> {
    const { data } = await apiClient.post<ApiSkill>('/skills', payload);
    return data;
  },

  // ─── User Skills ───────────────────────────────────────────────

  async getSkillGraph(userId: string): Promise<ApiSkillGraph> {
    const { data } = await apiClient.get<ApiSkillGraph>(`/skills/${userId}/graph`);
    return data;
  },

  async getSkillVelocity(userId: string, days?: number): Promise<ApiSkillVelocity> {
    const { data } = await apiClient.get<ApiSkillVelocity>(`/skills/${userId}/velocity`, {
      params: days ? { days } : undefined,
    });
    return data;
  },

  async getUserSkills(userId: string): Promise<ApiUserSkill[]> {
    const { data } = await apiClient.get<ApiUserSkill[]>(`/skills/${userId}/skills`);
    return data;
  },

  async addUserSkill(userId: string, payload: ApiUserSkillCreate): Promise<ApiUserSkill> {
    const { data } = await apiClient.post<ApiUserSkill>(`/skills/${userId}/skills`, payload);
    return data;
  },

  // ─── Team Skills ───────────────────────────────────────────────

  async getTeamComposition(teamId: string): Promise<ApiTeamSkillComposition> {
    const { data } = await apiClient.get<ApiTeamSkillComposition>(`/skills/team/${teamId}/composition`);
    return data;
  },

  // ─── Skill Gaps ────────────────────────────────────────────────

  async getSkillGaps(userId: string): Promise<ApiSkillGapSummary> {
    const { data } = await apiClient.get<ApiSkillGapSummary>(`/skills/${userId}/gaps`);
    return data;
  },

  async analyzeSkillGaps(userId: string, targetRole?: string): Promise<ApiSkillGapSummary> {
    const { data } = await apiClient.post<ApiSkillGapSummary>(`/skills/${userId}/gaps/analyze`, {
      target_role: targetRole,
    });
    return data;
  },

  // ─── Learning Paths ────────────────────────────────────────────

  async getLearningPaths(userId: string, activeOnly?: boolean): Promise<ApiLearningPath[]> {
    const { data } = await apiClient.get<ApiLearningPath[]>(`/skills/${userId}/learning-path`, {
      params: activeOnly !== undefined ? { active_only: activeOnly } : undefined,
    });
    return data;
  },

  async createLearningPath(userId: string, payload: ApiLearningPathCreate): Promise<ApiLearningPath> {
    const { data } = await apiClient.post<ApiLearningPath>(`/skills/${userId}/learning-path`, payload);
    return data;
  },

  // ─── Self-Sufficiency ──────────────────────────────────────────

  async getSelfSufficiency(userId: string): Promise<ApiSelfSufficiencyMetrics> {
    const { data } = await apiClient.get<ApiSelfSufficiencyMetrics>(`/skills/${userId}/self-sufficiency`);
    return data;
  },
};
