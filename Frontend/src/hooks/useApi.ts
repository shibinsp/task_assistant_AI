import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// ─── Query Key Factory ───────────────────────────────────────────────

export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
    sessions: ['auth', 'sessions'] as const,
    consent: ['auth', 'consent'] as const,
  },
  tasks: {
    all: ['tasks'] as const,
    list: (filters?: Record<string, unknown>) => ['tasks', 'list', filters] as const,
    detail: (id: string) => ['tasks', 'detail', id] as const,
    statistics: (filters?: Record<string, unknown>) => ['tasks', 'statistics', filters] as const,
    subtasks: (taskId: string) => ['tasks', 'subtasks', taskId] as const,
    dependencies: (taskId: string) => ['tasks', 'dependencies', taskId] as const,
    comments: (taskId: string) => ['tasks', 'comments', taskId] as const,
    history: (taskId: string) => ['tasks', 'history', taskId] as const,
    drafts: (filters?: Record<string, unknown>) => ['tasks', 'drafts', filters] as const,
  },
  dashboard: {
    metrics: (filters?: Record<string, unknown>) => ['dashboard', 'metrics', filters] as const,
    velocity: (params?: Record<string, unknown>) => ['dashboard', 'velocity', params] as const,
    bottlenecks: (params?: Record<string, unknown>) => ['dashboard', 'bottlenecks', params] as const,
    executiveSummary: (days?: number) => ['dashboard', 'executive-summary', days] as const,
    teamWorkload: ['dashboard', 'team-workload'] as const,
    checkinSummary: (params?: Record<string, unknown>) => ['dashboard', 'checkin-summary', params] as const,
    teamProductivity: (params?: Record<string, unknown>) => ['dashboard', 'team-productivity', params] as const,
  },
  notifications: {
    all: ['notifications'] as const,
    list: (filters?: Record<string, unknown>) => ['notifications', 'list', filters] as const,
    unreadCount: ['notifications', 'unread-count'] as const,
    preferences: ['notifications', 'preferences'] as const,
  },
  automation: {
    patterns: (status?: string) => ['automation', 'patterns', status] as const,
    agents: (status?: string) => ['automation', 'agents', status] as const,
    agent: (id: string) => ['automation', 'agent', id] as const,
    shadowReport: (id: string) => ['automation', 'shadow-report', id] as const,
    roi: ['automation', 'roi'] as const,
  },
  ai: {
    history: ['ai', 'history'] as const,
    knowledgeBase: {
      status: ['ai', 'kb', 'status'] as const,
      documents: (filters?: Record<string, unknown>) => ['ai', 'kb', 'documents', filters] as const,
      document: (id: string) => ['ai', 'kb', 'document', id] as const,
    },
  },
  team: {
    users: (filters?: Record<string, unknown>) => ['team', 'users', filters] as const,
    user: (id: string) => ['team', 'user', id] as const,
    permissions: (id: string) => ['team', 'permissions', id] as const,
  },
  settings: {
    profile: ['settings', 'profile'] as const,
  },
  checkins: {
    all: ['checkins'] as const,
    list: (filters?: Record<string, unknown>) => ['checkins', 'list', filters] as const,
    pending: ['checkins', 'pending'] as const,
    detail: (id: string) => ['checkins', 'detail', id] as const,
    statistics: (params?: Record<string, unknown>) => ['checkins', 'statistics', params] as const,
    feed: (params?: Record<string, unknown>) => ['checkins', 'feed', params] as const,
    configs: ['checkins', 'configs'] as const,
    config: (id: string) => ['checkins', 'config', id] as const,
  },
  organizations: {
    all: ['organizations'] as const,
    current: ['organizations', 'current'] as const,
    detail: (id: string) => ['organizations', id] as const,
    settings: (id: string) => ['organizations', 'settings', id] as const,
    features: (id: string) => ['organizations', 'features', id] as const,
    stats: (id: string) => ['organizations', 'stats', id] as const,
  },
  admin: {
    auditLogs: (filters?: Record<string, unknown>) => ['admin', 'audit-logs', filters] as const,
    systemHealth: ['admin', 'system-health'] as const,
    apiKeys: ['admin', 'api-keys'] as const,
    aiGovernance: ['admin', 'ai-governance'] as const,
  },
  skills: {
    catalog: (filters?: Record<string, unknown>) => ['skills', 'catalog', filters] as const,
    graph: (userId: string) => ['skills', 'graph', userId] as const,
    velocity: (userId: string, days?: number) => ['skills', 'velocity', userId, days] as const,
    userSkills: (userId: string) => ['skills', 'user', userId] as const,
    gaps: (userId: string) => ['skills', 'gaps', userId] as const,
    learningPaths: (userId: string) => ['skills', 'learning-paths', userId] as const,
    selfSufficiency: (userId: string) => ['skills', 'self-sufficiency', userId] as const,
    teamComposition: (teamId: string) => ['skills', 'team', teamId] as const,
  },
  predictions: {
    task: (taskId: string) => ['predictions', 'task', taskId] as const,
    teamVelocity: (teamId: string) => ['predictions', 'velocity', teamId] as const,
    hiring: ['predictions', 'hiring'] as const,
    accuracy: (days?: number) => ['predictions', 'accuracy', days] as const,
  },
  workforce: {
    scores: (filters?: Record<string, unknown>) => ['workforce', 'scores', filters] as const,
    userScore: (userId: string) => ['workforce', 'score', userId] as const,
    managerRankings: ['workforce', 'managers'] as const,
    orgHealth: ['workforce', 'org-health'] as const,
    attritionRisk: (level?: string) => ['workforce', 'attrition', level] as const,
    simulation: (id: string) => ['workforce', 'simulation', id] as const,
    hiringPlan: ['workforce', 'hiring-plan'] as const,
  },
  integrations: {
    all: ['integrations'] as const,
    detail: (id: string) => ['integrations', id] as const,
    webhooks: ['integrations', 'webhooks'] as const,
    webhook: (id: string) => ['integrations', 'webhook', id] as const,
    deliveries: (webhookId: string) => ['integrations', 'deliveries', webhookId] as const,
  },
  agents: {
    all: ['agents'] as const,
    detail: (name: string) => ['agents', name] as const,
    executions: (name: string) => ['agents', 'executions', name] as const,
    stats: ['agents', 'stats'] as const,
    recommendations: (taskId?: string) => ['agents', 'recommendations', taskId] as const,
  },
  chat: {
    conversations: ['chat', 'conversations'] as const,
    conversation: (id: string) => ['chat', 'conversation', id] as const,
  },
};
