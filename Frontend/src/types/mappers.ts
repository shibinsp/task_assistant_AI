import type {
  ApiTask,
  ApiTaskStatus,
  ApiTaskPriority,
  ApiCurrentUser,
  ApiUserRole,
  ApiUser,
} from './api';

// ─── Frontend Types ──────────────────────────────────────────────────

export type FrontendTaskStatus = 'todo' | 'in-progress' | 'review' | 'done';
export type FrontendTaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type FrontendUserRole = 'admin' | 'manager' | 'member' | 'viewer';

export interface FrontendTask {
  id: string;
  title: string;
  description: string;
  status: FrontendTaskStatus;
  priority: FrontendTaskPriority;
  assignee: string;
  assigneeName: string;
  dueDate: string;
  tags: string[];
  estimatedHours: number;
  createdAt: string;
}

export interface FrontendUser {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: FrontendUserRole;
  organizationId?: string;
}

export interface FrontendTeamMember {
  id: string;
  name: string;
  email: string;
  role: FrontendUserRole;
  status: 'active' | 'invited' | 'inactive';
  avatar?: string;
  lastActive: string;
}

// ─── Status Mappers ──────────────────────────────────────────────────

const statusToFrontend: Record<ApiTaskStatus, FrontendTaskStatus> = {
  todo: 'todo',
  in_progress: 'in-progress',
  blocked: 'in-progress',
  review: 'review',
  done: 'done',
  archived: 'done',
};

const statusToApi: Record<FrontendTaskStatus, ApiTaskStatus> = {
  'todo': 'todo',
  'in-progress': 'in_progress',
  'review': 'review',
  'done': 'done',
};

export function mapStatusToFrontend(status: ApiTaskStatus): FrontendTaskStatus {
  return statusToFrontend[status] ?? 'todo';
}

export function mapStatusToApi(status: FrontendTaskStatus): ApiTaskStatus {
  return statusToApi[status] ?? 'todo';
}

// ─── Priority Mappers ────────────────────────────────────────────────

const priorityToFrontend: Record<ApiTaskPriority, FrontendTaskPriority> = {
  low: 'low',
  medium: 'medium',
  high: 'high',
  critical: 'urgent',
};

const priorityToApi: Record<FrontendTaskPriority, ApiTaskPriority> = {
  low: 'low',
  medium: 'medium',
  high: 'high',
  urgent: 'critical',
};

export function mapPriorityToFrontend(priority: ApiTaskPriority): FrontendTaskPriority {
  return priorityToFrontend[priority] ?? 'medium';
}

export function mapPriorityToApi(priority: FrontendTaskPriority): ApiTaskPriority {
  return priorityToApi[priority] ?? 'medium';
}

// ─── Role Mappers ────────────────────────────────────────────────────

const roleToFrontend: Record<ApiUserRole, FrontendUserRole> = {
  super_admin: 'admin',
  org_admin: 'admin',
  manager: 'manager',
  team_lead: 'manager',
  employee: 'member',
  viewer: 'viewer',
};

export function mapRoleToFrontend(role: ApiUserRole): FrontendUserRole {
  return roleToFrontend[role] ?? 'member';
}

// ─── Task Mapper ─────────────────────────────────────────────────────

export function mapTaskToFrontend(task: ApiTask): FrontendTask {
  // Use assignee_name from ApiTaskDetail if available, otherwise fallback
  const detail = task as ApiTask & { assignee_name?: string; creator_name?: string };
  return {
    id: task.id,
    title: task.title,
    description: task.description ?? '',
    status: mapStatusToFrontend(task.status),
    priority: mapPriorityToFrontend(task.priority),
    assignee: task.assigned_to ?? '',
    assigneeName: detail.assignee_name ?? '',
    dueDate: task.deadline ?? '',
    tags: task.tags ?? [],
    estimatedHours: task.estimated_hours ?? 0,
    createdAt: task.created_at,
  };
}

// ─── User Mappers ────────────────────────────────────────────────────

export function mapCurrentUserToFrontend(user: ApiCurrentUser): FrontendUser {
  return {
    id: user.id,
    email: user.email,
    name: `${user.first_name} ${user.last_name}`.trim(),
    avatar: user.avatar_url,
    role: mapRoleToFrontend(user.role),
    organizationId: user.org_id,
  };
}

export function mapApiUserToTeamMember(user: ApiUser): FrontendTeamMember {
  return {
    id: user.id,
    name: `${user.first_name} ${user.last_name}`.trim(),
    email: user.email,
    role: mapRoleToFrontend(user.role),
    status: user.is_active ? 'active' : 'inactive',
    avatar: user.avatar_url,
    lastActive: user.last_login
      ? formatRelativeTime(user.last_login)
      : 'Never',
  };
}

// ─── Helpers ─────────────────────────────────────────────────────────

function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
}

export function splitFullName(fullName: string): { firstName: string; lastName: string } {
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 1) {
    return { firstName: parts[0], lastName: parts[0] };
  }
  return {
    firstName: parts[0],
    lastName: parts.slice(1).join(' '),
  };
}
