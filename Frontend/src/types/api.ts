// ─── Backend API Types ───────────────────────────────────────────────
// These mirror the backend Pydantic schemas exactly (snake_case).

// Enums
export type ApiTaskStatus = 'todo' | 'in_progress' | 'blocked' | 'review' | 'done' | 'archived';
export type ApiTaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type ApiUserRole = 'super_admin' | 'org_admin' | 'manager' | 'team_lead' | 'employee' | 'viewer';
export type ApiPatternStatus = 'detected' | 'suggested' | 'accepted' | 'rejected' | 'implemented';
export type ApiAgentStatus = 'created' | 'shadow' | 'supervised' | 'live' | 'paused' | 'retired';

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
  is_draft: boolean;
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
  is_draft?: boolean;
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
  is_draft?: boolean;
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

// ─── Task Subtasks ───────────────────────────────────────────────────

export interface ApiSubtaskCreate {
  title: string;
  description?: string;
  priority?: ApiTaskPriority;
  estimated_hours?: number;
  assigned_to?: string;
  sort_order?: number;
}

// ─── Task Dependencies ──────────────────────────────────────────────

export interface ApiDependencyCreate {
  depends_on_id: string;
  is_blocking?: boolean;
  description?: string;
}

export interface ApiDependency {
  id: string;
  task_id: string;
  depends_on_id: string;
  is_blocking: boolean;
  description?: string;
  depends_on_title?: string;
  depends_on_status?: ApiTaskStatus;
  created_at: string;
}

// ─── Task Comments ──────────────────────────────────────────────────

export interface ApiCommentCreate {
  content: string;
}

export interface ApiCommentUpdate {
  content: string;
}

export interface ApiComment {
  id: string;
  task_id: string;
  user_id?: string;
  content: string;
  is_ai_generated: boolean;
  is_edited: boolean;
  user_name?: string;
  created_at: string;
  updated_at: string;
}

// ─── Task History ───────────────────────────────────────────────────

export interface ApiTaskHistory {
  id: string;
  task_id: string;
  user_id?: string;
  action: string;
  field_name?: string;
  old_value?: string;
  new_value?: string;
  details: Record<string, unknown>;
  user_name?: string;
  created_at: string;
}

// ─── Task AI Decomposition ──────────────────────────────────────────

export interface ApiTaskDecompositionRequest {
  max_subtasks?: number;
  include_time_estimates?: boolean;
  include_skill_requirements?: boolean;
}

export interface ApiSubtaskSuggestion {
  title: string;
  description: string;
  estimated_hours?: number;
  skills_required: string[];
  order: number;
}

export interface ApiTaskDecompositionResponse {
  task_id: string;
  suggested_subtasks: ApiSubtaskSuggestion[];
  total_estimated_hours: number;
  complexity_score: number;
  risk_factors: string[];
  recommendations: string[];
}

// ─── Task Bulk Operations ───────────────────────────────────────────

export interface ApiBulkTaskUpdate {
  task_ids: string[];
  status?: ApiTaskStatus;
  priority?: ApiTaskPriority;
  assigned_to?: string;
  team_id?: string;
  project_id?: string;
}

export interface ApiBulkOperationResult {
  total: number;
  successful: number;
  failed: number;
  errors: Record<string, unknown>[];
}

// ─── Auth Extended ──────────────────────────────────────────────────

export interface ApiConsentResponse {
  ai_monitoring: boolean;
  skill_tracking: boolean;
  analytics: boolean;
  marketing: boolean;
  updated_at?: string;
}

export interface ApiConsentUpdate {
  ai_monitoring?: boolean;
  skill_tracking?: boolean;
  analytics?: boolean;
  marketing?: boolean;
}

export interface ApiSession {
  id: string;
  device_info?: string;
  ip_address?: string;
  user_agent?: string;
  last_activity?: string;
  created_at: string;
  is_current: boolean;
}

export interface ApiForgotPassword {
  email: string;
}

export interface ApiResetPassword {
  token: string;
  new_password: string;
}

// ─── Knowledge Base ─────────────────────────────────────────────────

export type ApiDocumentSource = 'manual' | 'confluence' | 'notion' | 'github' | 'slack' | 'web';
export type ApiDocumentType = 'guide' | 'faq' | 'tutorial' | 'reference' | 'troubleshooting' | 'other';
export type ApiDocumentStatus = 'pending' | 'processing' | 'indexed' | 'failed' | 'archived';

export interface ApiDocument {
  id: string;
  org_id: string;
  title: string;
  description?: string;
  source: ApiDocumentSource;
  source_url?: string;
  doc_type: ApiDocumentType;
  status: ApiDocumentStatus;
  content?: string;
  file_name?: string;
  file_type?: string;
  file_size?: number;
  language?: string;
  is_public: boolean;
  tags: string[];
  categories: string[];
  view_count: number;
  helpful_count: number;
  not_helpful_count: number;
  error_message?: string;
  processed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiDocumentCreate {
  title: string;
  description?: string;
  source?: ApiDocumentSource;
  source_url?: string;
  doc_type?: ApiDocumentType;
  content?: string;
  is_public?: boolean;
  tags?: string[];
  categories?: string[];
}

export interface ApiDocumentUpdate {
  title?: string;
  description?: string;
  doc_type?: ApiDocumentType;
  content?: string;
  is_public?: boolean;
  tags?: string[];
  categories?: string[];
}

export interface ApiDocumentListResponse {
  documents: ApiDocument[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiKnowledgeBaseStatus {
  total_documents: number;
  indexed_documents: number;
  pending_documents: number;
  failed_documents: number;
  total_chunks: number;
  last_updated: string;
}

// ─── Automation Extended ────────────────────────────────────────────

export interface ApiShadowReport {
  agent_id: string;
  shadow_period_days: number;
  total_runs: number;
  match_rate: number;
  mismatches: Array<{ run_id: string; reason: string; severity: string }>;
  recommendation: string;
}

// ─── Reports Extended ───────────────────────────────────────────────

export interface ApiTeamWorkload {
  team_id: string;
  team_name: string;
  members: Array<{
    user_id: string;
    name: string;
    active_tasks: number;
    completed_tasks: number;
    total_estimated_hours: number;
    utilization_percentage: number;
  }>;
  total_tasks: number;
  avg_utilization: number;
}

export interface ApiCheckinSummary {
  total_checkins: number;
  responded: number;
  skipped: number;
  expired: number;
  escalated: number;
  response_rate: number;
  avg_response_time_minutes: number;
}

export interface ApiReportRequest {
  report_type: string;
  format?: 'json' | 'xlsx' | 'pdf';
  team_id?: string;
  start_date?: string;
  end_date?: string;
  filters?: Record<string, unknown>;
}

export interface ApiScheduleReportRequest {
  report_type: string;
  schedule: string;
  recipients: string[];
  format?: string;
  filters?: Record<string, unknown>;
}

export interface ApiTeamProductivity {
  team_id: string;
  period_start: string;
  period_end: string;
  tasks_completed: number;
  avg_completion_hours: number;
  velocity: number;
  efficiency_score: number;
  daily_breakdown: Array<{
    date: string;
    tasks_completed: number;
    hours_logged: number;
  }>;
}

// ─── Check-Ins ──────────────────────────────────────────────────────

export type ApiCheckInStatus = 'pending' | 'responded' | 'skipped' | 'expired' | 'escalated';
export type ApiCheckInTrigger = 'scheduled' | 'manual' | 'escalation' | 'system';

export interface ApiCheckIn {
  id: string;
  task_id: string;
  user_id: string;
  org_id: string;
  cycle_number: number;
  trigger: ApiCheckInTrigger;
  status: ApiCheckInStatus;
  scheduled_at: string;
  responded_at?: string;
  expires_at?: string;
  progress_indicator?: string;
  progress_notes?: string;
  completed_since_last?: string;
  blockers_reported?: string;
  help_needed?: string;
  estimated_completion_change?: string;
  ai_suggestion?: string;
  ai_confidence?: number;
  sentiment_score?: number;
  friction_detected: boolean;
  escalated: boolean;
  escalated_to?: string;
  escalated_at?: string;
  escalation_reason?: string;
  task_title?: string;
  user_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiCheckInListResponse {
  checkins: ApiCheckIn[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiCheckInSubmit {
  progress_indicator: string;
  progress_notes?: string;
  completed_since_last?: string;
  blockers_reported?: string;
  help_needed?: string;
  estimated_completion_change?: string;
}

export interface ApiCheckInSkip {
  reason?: string;
}

export interface ApiCheckInCreate {
  task_id: string;
  user_id?: string;
  trigger?: ApiCheckInTrigger;
}

export interface ApiCheckInConfig {
  id: string;
  org_id: string;
  team_id?: string;
  user_id?: string;
  task_id?: string;
  interval_hours: number;
  enabled: boolean;
  silent_mode_threshold: number;
  max_daily_checkins: number;
  work_start_hour: number;
  work_end_hour: number;
  respect_timezone: boolean;
  excluded_days: number[];
  auto_escalate_after_missed: number;
  escalate_to_manager: boolean;
  ai_suggestions_enabled: boolean;
  ai_sentiment_analysis: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiCheckInConfigCreate {
  team_id?: string;
  user_id?: string;
  task_id?: string;
  interval_hours?: number;
  enabled?: boolean;
  silent_mode_threshold?: number;
  max_daily_checkins?: number;
  work_start_hour?: number;
  work_end_hour?: number;
  excluded_days?: number[];
  auto_escalate_after_missed?: number;
  escalate_to_manager?: boolean;
  ai_suggestions_enabled?: boolean;
  ai_sentiment_analysis?: boolean;
}

export interface ApiCheckInConfigUpdate extends Partial<ApiCheckInConfigCreate> {}

export interface ApiCheckInStatistics {
  total_checkins: number;
  responded: number;
  skipped: number;
  expired: number;
  escalated: number;
  response_rate: number;
  avg_response_time_minutes: number;
  friction_detected_count: number;
}

export interface ApiCheckInFeedItem {
  checkin: ApiCheckIn;
  needs_attention: boolean;
  attention_reason?: string;
}

export interface ApiCheckInFeedResponse {
  items: ApiCheckInFeedItem[];
  total: number;
  needs_attention_count: number;
}

export interface ApiEscalationRequest {
  reason: string;
  escalate_to?: string;
}

export interface ApiEscalationResponse {
  checkin_id: string;
  escalated_to: string;
  escalation_reason: string;
  notification_sent: boolean;
}

// ─── Organizations ──────────────────────────────────────────────────

export type ApiOrgPlan = 'starter' | 'professional' | 'enterprise' | 'enterprise_plus';

export interface ApiOrganization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  plan: ApiOrgPlan;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiOrganizationDetail extends ApiOrganization {
  member_count: number;
  max_users: number;
  features: Record<string, boolean>;
}

export interface ApiOrganizationUpdate {
  name?: string;
  description?: string;
}

export interface ApiOrganizationSettings {
  ai_monitoring_enabled: boolean;
  skill_tracking_enabled: boolean;
  checkin_enabled: boolean;
  default_checkin_interval_hours: number;
  automation_enabled: boolean;
  require_consent: boolean;
  [key: string]: unknown;
}

export interface ApiOrganizationFeatures {
  plan: ApiOrgPlan;
  features: Record<string, boolean>;
  max_users: number;
  max_agents: number;
  max_integrations: number;
}

export interface ApiOrganizationStats {
  total_members: number;
  active_members: number;
  total_tasks: number;
  completed_tasks: number;
  active_agents: number;
  integrations_connected: number;
  roles_distribution: Record<string, number>;
}

export interface ApiOrganizationListResponse {
  organizations: ApiOrganization[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Admin ──────────────────────────────────────────────────────────

export type ApiAuditAction = 'CREATE' | 'UPDATE' | 'DELETE' | 'LOGIN' | 'LOGOUT' | 'ACCESS' | 'EXPORT' | 'IMPORT';
export type ApiActorType = 'user' | 'system' | 'agent' | 'api_key';

export interface ApiAuditLog {
  id: string;
  org_id: string;
  timestamp: string;
  actor_type: ApiActorType;
  actor_id: string;
  actor_name: string;
  action: ApiAuditAction;
  resource_type: string;
  resource_id?: string;
  description: string;
  ip_address?: string;
  user_agent?: string;
  request_id?: string;
}

export interface ApiAuditLogListResponse {
  logs: ApiAuditLog[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiSystemHealthResponse {
  status: string;
  uptime_seconds: number;
  db_connections_active: number;
  db_query_avg_ms: number;
  api_requests_per_minute: number;
  api_error_rate: number;
  api_latency_p50_ms: number;
  api_latency_p99_ms: number;
  ai_requests_per_hour: number;
  ai_avg_latency_ms: number;
  ai_cache_hit_rate: number;
  jobs_pending: number;
  jobs_failed: number;
  storage_used_mb: number;
  active_alerts: string[];
}

export interface ApiGDPRExportResponse {
  request_id: string;
  status: string;
  message: string;
  download_url?: string;
  expires_at?: string;
}

export interface ApiAIGovernanceResponse {
  total_ai_requests: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
  provider: string;
  model: string;
  total_tokens_used: number;
  estimated_cost: number;
  quality_metrics: {
    avg_confidence: number;
    helpful_rate: number;
    escalation_rate: number;
  };
}

export interface ApiAPIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_full_access: boolean;
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  usage_count: number;
  rate_limit: number;
  created_at: string;
}

export interface ApiAPIKeyCreate {
  name: string;
  scopes?: string[];
  is_full_access?: boolean;
  expires_at?: string;
  rate_limit?: number;
}

export interface ApiAPIKeyCreatedResponse extends ApiAPIKey {
  key: string; // Only returned on creation
}

// ─── Skills ─────────────────────────────────────────────────────────

export type ApiSkillCategory = 'technical' | 'process' | 'soft' | 'domain' | 'tool' | 'language';
export type ApiSkillSource = 'inferred' | 'self_reported' | 'manager_assessed' | 'certification';
export type ApiSkillTrend = 'improving' | 'stable' | 'declining';
export type ApiGapType = 'critical' | 'growth' | 'stretch';

export interface ApiSkill {
  id: string;
  org_id: string;
  name: string;
  description?: string;
  category: ApiSkillCategory;
  aliases: string[];
  related_skills: string[];
  prerequisites: string[];
  org_average_level: number;
  industry_average_level: number;
  is_active: boolean;
  created_at: string;
}

export interface ApiSkillCreate {
  name: string;
  description?: string;
  category: ApiSkillCategory;
  aliases?: string[];
  related_skills?: string[];
  prerequisites?: string[];
}

export interface ApiSkillListResponse {
  skills: ApiSkill[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiUserSkill {
  id: string;
  user_id: string;
  skill_id: string;
  skill_name: string;
  skill_category: ApiSkillCategory;
  level: number;
  confidence: number;
  trend: ApiSkillTrend;
  source: ApiSkillSource;
  last_demonstrated?: string;
  demonstration_count: number;
  is_certified: boolean;
  certification_date?: string;
  certification_expiry?: string;
}

export interface ApiUserSkillCreate {
  skill_id: string;
  level: number;
  source?: ApiSkillSource;
}

export interface ApiSkillGraph {
  user_id: string;
  skills: ApiUserSkill[];
  top_skills: Array<{ name: string; level: number; category: ApiSkillCategory }>;
  skill_count: number;
  avg_level: number;
  strongest_category: ApiSkillCategory;
}

export interface ApiSkillVelocity {
  user_id: string;
  period_days: number;
  skills_improved: number;
  skills_declined: number;
  avg_improvement_rate: number;
  learning_velocity: number;
  history: Array<{
    date: string;
    skill_name: string;
    old_level: number;
    new_level: number;
  }>;
}

export interface ApiTeamSkillComposition {
  team_id: string;
  total_members: number;
  skill_coverage: Record<string, { avg_level: number; member_count: number; gap: boolean }>;
  strengths: string[];
  gaps: string[];
}

export interface ApiSkillGap {
  id: string;
  user_id: string;
  skill_id: string;
  skill_name: string;
  gap_type: ApiGapType;
  current_level: number;
  required_level: number;
  gap_size: number;
  for_role?: string;
  priority: number;
  is_resolved: boolean;
  learning_resources: string[];
}

export interface ApiSkillGapSummary {
  user_id: string;
  total_gaps: number;
  critical_gaps: number;
  gaps: ApiSkillGap[];
  recommended_focus: string[];
}

export interface ApiLearningPath {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  target_role?: string;
  skills: Array<{ skill_id: string; skill_name: string; target_level: number; current_level: number }>;
  milestones: Array<{ title: string; description: string; completed: boolean; target_date?: string }>;
  progress_percentage: number;
  is_active: boolean;
  is_ai_generated: boolean;
  started_at?: string;
  target_completion?: string;
  completed_at?: string;
  created_at: string;
}

export interface ApiLearningPathCreate {
  title: string;
  description?: string;
  target_role?: string;
  skills: Array<{ skill_id: string; target_level: number }>;
}

export interface ApiSelfSufficiencyMetrics {
  user_id: string;
  self_sufficiency_index: number;
  blockers_encountered: number;
  blockers_self_resolved: number;
  avg_blocker_resolution_hours: number;
  help_given_count: number;
  help_received_count: number;
  collaboration_score: number;
  trend: ApiSkillTrend;
}

// ─── Predictions ────────────────────────────────────────────────────

export interface ApiPrediction {
  id: string;
  task_id: string;
  predicted_date_p25?: string;
  predicted_date_p50?: string;
  predicted_date_p90?: string;
  confidence: number;
  risk_score: number;
  risk_factors: string[];
  recommendations: string[];
  model_version: string;
  created_at: string;
}

export interface ApiVelocityForecast {
  team_id: string;
  snapshots: Array<{
    period_start: string;
    period_end: string;
    tasks_completed: number;
    velocity: number;
    capacity_utilization: number;
  }>;
  forecasted_velocity: number;
  trend: string;
}

export interface ApiHiringPrediction {
  skill_name: string;
  skill_category: ApiSkillCategory;
  current_coverage: number;
  required_coverage: number;
  gap: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  recommended_hires: number;
  estimated_impact: string;
}

export interface ApiPredictionAccuracy {
  period_days: number;
  total_predictions: number;
  p50_accuracy: number;
  p90_accuracy: number;
  mean_absolute_error_days: number;
  model_version: string;
  last_retrained?: string;
}

// ─── Workforce Intelligence ─────────────────────────────────────────

export interface ApiWorkforceScore {
  id: string;
  user_id: string;
  user_name: string;
  snapshot_date: string;
  velocity_score: number;
  quality_score: number;
  self_sufficiency_score: number;
  learning_score: number;
  collaboration_score: number;
  overall_score: number;
  percentile_rank: number;
  attrition_risk_score: number;
  burnout_risk_score: number;
  score_trend: ApiSkillTrend;
}

export interface ApiManagerRanking {
  manager_id: string;
  manager_name: string;
  team_size: number;
  team_velocity_avg: number;
  team_quality_avg: number;
  escalation_response_time_hours: number;
  escalation_resolution_rate: number;
  team_attrition_rate: number;
  team_satisfaction_score: number;
  effectiveness_score: number;
  org_percentile: number;
}

export interface ApiOrgHealth {
  org_id: string;
  snapshot_date: string;
  productivity_index: number;
  skill_coverage_index: number;
  management_quality_index: number;
  automation_maturity_index: number;
  delivery_predictability_index: number;
  overall_health_score: number;
  total_employees: number;
  active_tasks: number;
  blocked_tasks: number;
  overdue_tasks: number;
  high_attrition_risk_count: number;
  high_burnout_risk_count: number;
}

export interface ApiAttritionRisk {
  user_id: string;
  user_name: string;
  role: ApiUserRole;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  recommended_actions: string[];
}

export interface ApiSimulationCreate {
  name: string;
  description?: string;
  scenario_type: 'team_merge' | 'role_change' | 'automation_replace' | 'reduction';
  config: Record<string, unknown>;
}

export interface ApiSimulation {
  id: string;
  name: string;
  description?: string;
  scenario_type: string;
  config: Record<string, unknown>;
  projected_cost_change: number;
  projected_productivity_change: number;
  projected_skill_coverage_change: number;
  affected_employees: number;
  risk_factors: string[];
  overall_risk_score: number;
  is_draft: boolean;
  created_at: string;
}

export interface ApiHiringPlan {
  recommendations: ApiHiringPrediction[];
  total_recommended_hires: number;
  estimated_timeline_months: number;
  estimated_cost: number;
  priority_order: string[];
}

// ─── Integrations ───────────────────────────────────────────────────

export type ApiIntegrationType = 'jira' | 'github' | 'gitlab' | 'slack' | 'teams' | 'confluence' | 'notion' | 'custom_webhook';

export interface ApiIntegration {
  id: string;
  org_id: string;
  integration_type: ApiIntegrationType;
  name: string;
  description?: string;
  is_active: boolean;
  sync_enabled: boolean;
  last_sync_at?: string;
  last_sync_status?: string;
  sync_error?: string;
  connected_by?: string;
  connected_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiIntegrationCreate {
  integration_type: ApiIntegrationType;
  name: string;
  description?: string;
  config?: Record<string, unknown>;
}

export interface ApiWebhook {
  id: string;
  org_id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  total_deliveries: number;
  successful_deliveries: number;
  last_delivery_at?: string;
  last_delivery_status?: string;
  created_at: string;
  updated_at: string;
}

export interface ApiWebhookCreate {
  name: string;
  url: string;
  events: string[];
  secret?: string;
  headers?: Record<string, string>;
}

export interface ApiWebhookUpdate {
  name?: string;
  url?: string;
  events?: string[];
  is_active?: boolean;
  headers?: Record<string, string>;
}

export interface ApiWebhookDelivery {
  id: string;
  webhook_id: string;
  event_type: string;
  attempted_at: string;
  response_status?: number;
  response_time_ms?: number;
  is_successful: boolean;
  retry_count: number;
  error_message?: string;
}

// ─── Agents (Orchestration) ─────────────────────────────────────────

export type ApiOrchestratorAgentType = 'AI' | 'integration' | 'conversation';

export interface ApiOrchestratorAgent {
  name: string;
  display_name: string;
  description: string;
  agent_type: ApiOrchestratorAgentType;
  capabilities: string[];
  status: string;
  is_enabled: boolean;
  execution_count: number;
  success_count: number;
  error_count: number;
  avg_duration_ms: number;
}

export interface ApiAgentExecuteRequest {
  event_type: string;
  event_data: Record<string, unknown>;
  task_id?: string;
  context?: Record<string, unknown>;
}

export interface ApiAgentExecuteResponse {
  execution_id: string;
  agent_name: string;
  status: string;
  output: Record<string, unknown>;
  duration_ms: number;
  tokens_used?: number;
}

export interface ApiAgentExecution {
  id: string;
  agent_name: string;
  event_type: string;
  status: string;
  success: boolean;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  output_data?: Record<string, unknown>;
  error_message?: string;
  tokens_used?: number;
}

// ─── Chat ───────────────────────────────────────────────────────────

export interface ApiChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ApiChatMessageRequest {
  message: string;
  conversation_id?: string;
  agent_name?: string;
  context?: Record<string, unknown>;
}

export interface ApiChatMessageResponse {
  conversation_id: string;
  message: ApiChatMessage;
  suggestions?: string[];
  actions?: Array<{ label: string; action: string; data?: Record<string, unknown> }>;
}

export interface ApiConversation {
  id: string;
  title: string;
  agent_name: string;
  is_active: boolean;
  message_count: number;
  started_at: string;
  last_message_at?: string;
}

export interface ApiConversationDetail extends ApiConversation {
  messages: ApiChatMessage[];
}

// ─── User Permissions ───────────────────────────────────────────────

export interface ApiUserPermissions {
  user_id: string;
  role: ApiUserRole;
  permissions: string[];
}

// ─── Generic ─────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | { msg: string; type: string }[];
}
