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
  },
  tasks: {
    all: ['tasks'] as const,
    list: (filters?: Record<string, unknown>) => ['tasks', 'list', filters] as const,
    detail: (id: string) => ['tasks', 'detail', id] as const,
    statistics: (filters?: Record<string, unknown>) => ['tasks', 'statistics', filters] as const,
  },
  dashboard: {
    metrics: (filters?: Record<string, unknown>) => ['dashboard', 'metrics', filters] as const,
    velocity: (params?: Record<string, unknown>) => ['dashboard', 'velocity', params] as const,
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
    roi: ['automation', 'roi'] as const,
  },
  ai: {
    history: ['ai', 'history'] as const,
  },
  team: {
    users: (filters?: Record<string, unknown>) => ['team', 'users', filters] as const,
  },
  settings: {
    profile: ['settings', 'profile'] as const,
  },
};
