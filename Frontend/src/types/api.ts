// ─── Backend API Types ───────────────────────────────────────────────
// These mirror the backend Pydantic schemas exactly (snake_case).

// Enums
export type ApiTaskStatus = 'OPEN' | 'IN_PROGRESS' | 'BLOCKED' | 'IN_REVIEW' | 'COMPLETED';
export type ApiTaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ApiUserRole = 'super_admin' | 'org_admin' | 'manager' | 'team_lead' | 'employee' | 'viewer';
export type ApiPatternStatus = 'DETECTED' | 'ACCEPTED' | 'REJECTED' | 'IMPLEMENTED';
export type ApiAgentStatus = 'CREATED' | 'SHADOW' | 'LIVE' | 'PAUSED' | 'RETIRED';

// ─── Auth ────────────────────────────────────────────────────────────

export interface ApiUserRegister {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  org_name?: string;
  org_id?: string;
}

export interface ApiUserLogin {
  email: string;
  password: string;
}

export interface ApiTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiTokenRefresh {
  refresh_token: string;
}

export interface ApiCurrentUser {
  id: string;
  org_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: ApiUserRole;
  skill_level: string;
  timezone: string;
  is_active: boolean;
  is_email_verified: boolean;
  avatar_url?: string;
  phone?: string;
  team_id?: string;
  manager_id?: string;
  last_login?: string;
  created_at: string;
  updated_at: string;
  organization_name: string;
  organization_plan: string;
  permissions: string[];
}

export interface ApiPasswordChange {
  current_password: string;
  new_password: string;
}

export interface ApiRegisterResponse {
  message: string;
  user: ApiCurrentUser;
  organization: { id: string; name: string; slug: string };
  tokens: ApiTokenResponse;
}

export interface ApiLoginResponse {
  message: string;
  user: ApiCurrentUser;
  tokens: ApiTokenResponse;
}

// ─── Tasks ───────────────────────────────────────────────────────────

export interface ApiTask {
  id: string;
  org_id: string;
  title: string;
  description?: string;
  goal?: string;
  status: ApiTaskStatus;
  priority: ApiTaskPriority;
  assigned_to?: string;
  created_by: string;
  team_id?: string;
  project_id?: string;
  deadline?: string;
  estimated_hours?: number;
  actual_hours: number;
  started_at?: string;
  completed_at?: string;
  risk_score?: number;
  confidence_score?: number;
  complexity_score?: number;
  blocker_type?: string;
  blocker_description?: string;
  tools: string[];
  tags: string[];
  skills_required: string[];
  parent_task_id?: string;
  sort_order: number;
  is_subtask: boolean;
  is_blocked: boolean;
  is_completed: boolean;
  is_overdue: boolean;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface ApiTaskDetail extends ApiTask {
  subtask_count: number;
  completed_subtask_count: number;
  dependency_count: number;
  comment_count: number;
  assignee_name?: string;
  creator_name?: string;
}

export interface ApiTaskCreate {
  title: string;
  description?: string;
  goal?: string;
  priority?: ApiTaskPriority;
  deadline?: string;
  estimated_hours?: number;
  team_id?: string;
  project_id?: string;
  assigned_to?: string;
  parent_task_id?: string;
  tools?: string[];
  tags?: string[];
  skills_required?: string[];
}

export interface ApiTaskUpdate {
  title?: string;
  description?: string;
  goal?: string;
  priority?: ApiTaskPriority;
  deadline?: string;
  estimated_hours?: number;
  actual_hours?: number;
  team_id?: string;
  project_id?: string;
  assigned_to?: string;
  tools?: string[];
  tags?: string[];
  skills_required?: string[];
  sort_order?: number;
}

export interface ApiTaskStatusUpdate {
  status: ApiTaskStatus;
  blocker_type?: string;
  blocker_description?: string;
}

export interface ApiTaskListResponse {
  tasks: ApiTask[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Users ───────────────────────────────────────────────────────────

export interface ApiUser {
  id: string;
  org_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: ApiUserRole;
  is_active: boolean;
  avatar_url?: string;
  team_id?: string;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiUserListResponse {
  users: ApiUser[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiUserCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: ApiUserRole;
}

// ─── Notifications ───────────────────────────────────────────────────

export interface ApiNotification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  read_at?: string;
  action_url?: string;
  action_label?: string;
  created_at: string;
}

export interface ApiNotificationListResponse {
  notifications: ApiNotification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

export interface ApiNotificationPreferences {
  id: string;
  channels: string[];
  email_enabled: boolean;
  push_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  notification_types: Record<string, unknown>;
}

export interface ApiNotificationPreferencesUpdate {
  channels?: string[];
  email_enabled?: boolean;
  push_enabled?: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  notification_types?: Record<string, unknown>;
}

// ─── Reports / Dashboard ─────────────────────────────────────────────

export interface ApiDashboardMetrics {
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  blocked_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  avg_completion_hours: number;
  tasks_created_this_week: number;
  tasks_completed_this_week: number;
  [key: string]: unknown;
}

export interface ApiVelocityData {
  weeks: Array<{
    week: string;
    planned: number;
    completed: number;
    velocity: number;
  }>;
  avg_velocity: number;
  trend: string;
}

// ─── Automation ──────────────────────────────────────────────────────

export interface ApiPattern {
  id: string;
  name: string;
  description?: string;
  pattern_type?: string;
  status: ApiPatternStatus;
  frequency_per_week?: number;
  consistency_score?: number;
  users_affected: number;
  estimated_hours_saved_weekly?: number;
  implementation_complexity: number;
  created_at: string;
}

export interface ApiAgent {
  id: string;
  name: string;
  description?: string;
  status: ApiAgentStatus;
  pattern_id?: string;
  shadow_match_rate?: number;
  shadow_runs: number;
  total_runs: number;
  successful_runs: number;
  hours_saved_total: number;
  last_run_at?: string;
  created_at: string;
}

export interface ApiROIDashboard {
  total_agents: number;
  active_agents: number;
  total_hours_saved: number;
  total_cost_savings: number;
  patterns_detected: number;
  patterns_implemented: number;
}

// ─── AI Unblock ──────────────────────────────────────────────────────

export interface ApiUnblockRequest {
  query: string;
  task_id?: string;
  context?: string;
  skill_level?: string;
}

export interface ApiUnblockSource {
  document_id: string;
  title: string;
  relevance_score: number;
  snippet: string;
}

export interface ApiUnblockResponse {
  session_id: string;
  suggestion: string;
  confidence: number;
  sources: ApiUnblockSource[];
  code_snippets: string[];
  related_docs: string[];
  escalation_recommended: boolean;
  recommended_contacts: string[];
  detail_level: string;
}

export interface ApiUnblockFeedback {
  was_helpful: boolean;
  feedback_text?: string;
}

// ─── Settings / Profile ──────────────────────────────────────────────

export interface ApiUserUpdate {
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  phone?: string;
  timezone?: string;
}

// ─── Generic ─────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | { msg: string; type: string }[];
}
