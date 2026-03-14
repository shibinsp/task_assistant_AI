-- =============================================================
-- TaskPulse AI Assistant - PostgreSQL Schema
-- Auto-generated from SQLAlchemy models
-- =============================================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================
-- ENUM TYPES
-- =============================================================

DO $$ BEGIN
    CREATE TYPE plantier AS ENUM ('starter', 'professional', 'enterprise', 'enterprise_plus');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE agenttype AS ENUM ('ai', 'integration', 'conversation');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE agentstatusdb AS ENUM ('active', 'paused', 'error', 'disabled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE actortype AS ENUM ('user', 'admin', 'system', 'ai', 'api', 'integration');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE auditaction AS ENUM ('login', 'logout', 'password_change', 'mfa_enabled', 'create', 'read', 'update', 'delete', 'role_change', 'permission_change', 'config_change', 'export', 'import', 'data_request', 'data_deletion');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE documentsource AS ENUM ('manual_upload', 'confluence', 'notion', 'github', 'gitlab', 'jira', 'slack', 'internal_wiki', 'external_url');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE documenttype AS ENUM ('documentation', 'code_snippet', 'tutorial', 'faq', 'runbook', 'policy', 'meeting_notes', 'architecture', 'guide', 'troubleshooting', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE documentstatus AS ENUM ('pending', 'processing', 'indexed', 'failed', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE skillcategory AS ENUM ('technical', 'process', 'soft', 'domain', 'tool', 'language');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('super_admin', 'org_admin', 'manager', 'team_lead', 'employee', 'viewer');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE skilllevel AS ENUM ('junior', 'mid', 'senior', 'lead');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE patternstatus AS ENUM ('detected', 'suggested', 'accepted', 'rejected', 'implemented');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE integrationtype AS ENUM ('jira', 'github', 'gitlab', 'slack', 'teams', 'confluence', 'notion', 'custom_webhook');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE notificationtype AS ENUM ('checkin_reminder', 'task_assigned', 'task_completed', 'task_blocked', 'escalation', 'deadline_approaching', 'ai_suggestion', 'mention', 'system');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE notificationchannel AS ENUM ('in_app', 'email', 'slack', 'teams', 'webhook');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE gaptype AS ENUM ('critical', 'growth', 'stretch');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE taskstatus AS ENUM ('todo', 'in_progress', 'blocked', 'review', 'done', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE taskpriority AS ENUM ('critical', 'high', 'medium', 'low');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE blockertype AS ENUM ('logic', 'tool', 'dependency', 'bug', 'resource', 'unknown');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE skilltrend AS ENUM ('improving', 'stable', 'declining');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE executionstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE agentstatus AS ENUM ('created', 'shadow', 'supervised', 'live', 'paused', 'retired');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE checkintrigger AS ENUM ('scheduled', 'progress_stall', 'deadline_approaching', 'manual', 'blocker_detected', 'status_change');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE checkinstatus AS ENUM ('pending', 'responded', 'skipped', 'expired', 'escalated');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE progressindicator AS ENUM ('on_track', 'slightly_behind', 'significantly_behind', 'blocked', 'ahead', 'completed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE predictiontype AS ENUM ('task_completion', 'project_delivery', 'team_velocity', 'attrition_risk', 'hiring_needs');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================
-- TABLES
-- =============================================================

-- Table: organizations
CREATE TABLE organizations (
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	description TEXT, 
	plan plantier NOT NULL, 
	settings_json TEXT, 
	is_active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

-- Table: system_health
CREATE TABLE system_health (
	snapshot_time TIMESTAMP WITHOUT TIME ZONE, 
	db_connections_active INTEGER, 
	db_query_avg_ms FLOAT, 
	api_requests_per_minute INTEGER, 
	api_error_rate FLOAT, 
	api_latency_p50_ms FLOAT, 
	api_latency_p99_ms FLOAT, 
	ai_requests_per_hour INTEGER, 
	ai_avg_latency_ms FLOAT, 
	ai_cache_hit_rate FLOAT, 
	jobs_pending INTEGER, 
	jobs_failed INTEGER, 
	storage_used_mb FLOAT, 
	active_alerts_json TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

-- Table: agents
CREATE TABLE agents (
	id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	version VARCHAR(20), 
	agent_type agenttype NOT NULL, 
	capabilities JSON, 
	status agentstatusdb, 
	is_enabled BOOLEAN, 
	config JSON, 
	permissions JSON, 
	execution_count INTEGER, 
	success_count INTEGER, 
	error_count INTEGER, 
	avg_duration_ms FLOAT, 
	last_execution_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id), 
	UNIQUE (name)
);

-- Table: audit_logs
CREATE TABLE audit_logs (
	org_id VARCHAR(36) NOT NULL, 
	actor_type actortype NOT NULL, 
	actor_id VARCHAR(36), 
	actor_name VARCHAR(200), 
	action auditaction NOT NULL, 
	resource_type VARCHAR(100) NOT NULL, 
	resource_id VARCHAR(36), 
	description TEXT, 
	old_value_json TEXT, 
	new_value_json TEXT, 
	metadata_json TEXT, 
	ip_address VARCHAR(45), 
	user_agent VARCHAR(500), 
	request_id VARCHAR(36), 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: documents
CREATE TABLE documents (
	org_id VARCHAR(36) NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	description TEXT, 
	source documentsource, 
	source_url VARCHAR(2000), 
	source_id VARCHAR(255), 
	content TEXT NOT NULL, 
	content_hash VARCHAR(64), 
	doc_type documenttype, 
	status documentstatus, 
	error_message TEXT, 
	processed_at TIMESTAMP WITHOUT TIME ZONE, 
	file_name VARCHAR(500), 
	file_type VARCHAR(50), 
	file_size INTEGER, 
	language VARCHAR(50), 
	is_public BOOLEAN, 
	team_ids_json TEXT, 
	tags_json TEXT, 
	categories_json TEXT, 
	view_count INTEGER, 
	helpful_count INTEGER, 
	not_helpful_count INTEGER, 
	last_synced_at TIMESTAMP WITHOUT TIME ZONE, 
	sync_enabled BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: org_health_snapshots
CREATE TABLE org_health_snapshots (
	org_id VARCHAR(36) NOT NULL, 
	snapshot_date TIMESTAMP WITHOUT TIME ZONE, 
	productivity_index FLOAT, 
	skill_coverage_index FLOAT, 
	management_quality_index FLOAT, 
	automation_maturity_index FLOAT, 
	delivery_predictability_index FLOAT, 
	overall_health_score FLOAT, 
	total_employees INTEGER, 
	active_tasks INTEGER, 
	blocked_tasks INTEGER, 
	overdue_tasks INTEGER, 
	high_attrition_risk_count INTEGER, 
	high_burnout_risk_count INTEGER, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: skills
CREATE TABLE skills (
	org_id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	category skillcategory, 
	aliases_json TEXT, 
	related_skills_json TEXT, 
	prerequisites_json TEXT, 
	org_average_level FLOAT, 
	industry_average_level FLOAT, 
	is_active BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: users
CREATE TABLE users (
	org_id VARCHAR(36) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255), 
	is_sso_user BOOLEAN, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL, 
	avatar_url VARCHAR(500), 
	phone VARCHAR(50), 
	timezone VARCHAR(50) NOT NULL, 
	role userrole NOT NULL, 
	skill_level skilllevel NOT NULL, 
	team_id VARCHAR(36), 
	manager_id VARCHAR(36), 
	consent_json TEXT, 
	is_active BOOLEAN NOT NULL, 
	is_email_verified BOOLEAN, 
	last_login TIMESTAMP WITHOUT TIME ZONE, 
	failed_login_attempts VARCHAR(10), 
	lockout_until TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(manager_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Table: velocity_snapshots
CREATE TABLE velocity_snapshots (
	org_id VARCHAR(36) NOT NULL, 
	team_id VARCHAR(36) NOT NULL, 
	period_start TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	period_end TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	tasks_completed INTEGER, 
	story_points_completed FLOAT, 
	velocity FLOAT, 
	capacity_utilization FLOAT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: agent_conversations
CREATE TABLE agent_conversations (
	id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	title VARCHAR(200), 
	agent_name VARCHAR(100) NOT NULL, 
	is_active BOOLEAN, 
	message_count INTEGER, 
	messages JSON, 
	context_data JSON, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	last_message_at TIMESTAMP WITHOUT TIME ZONE, 
	ended_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Table: agent_schedules
CREATE TABLE agent_schedules (
	id VARCHAR(36) NOT NULL, 
	agent_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	cron_expression VARCHAR(100) NOT NULL, 
	timezone VARCHAR(50), 
	is_enabled BOOLEAN, 
	config JSON, 
	last_run_at TIMESTAMP WITHOUT TIME ZONE, 
	next_run_at TIMESTAMP WITHOUT TIME ZONE, 
	run_count INTEGER, 
	failure_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(agent_id) REFERENCES agents (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id)
);

-- Table: api_keys
CREATE TABLE api_keys (
	org_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	key_hash VARCHAR(255) NOT NULL, 
	key_prefix VARCHAR(10) NOT NULL, 
	scopes_json TEXT, 
	is_full_access BOOLEAN, 
	is_active BOOLEAN, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	last_used_at TIMESTAMP WITHOUT TIME ZONE, 
	last_used_ip VARCHAR(45), 
	usage_count INTEGER, 
	rate_limit INTEGER, 
	current_usage INTEGER, 
	usage_reset_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

-- Table: automation_patterns
CREATE TABLE automation_patterns (
	org_id VARCHAR(36) NOT NULL, 
	name VARCHAR(500) NOT NULL, 
	description TEXT, 
	pattern_type VARCHAR(100), 
	status patternstatus, 
	frequency_per_week FLOAT, 
	consistency_score FLOAT, 
	users_affected INTEGER, 
	estimated_hours_saved_weekly FLOAT, 
	estimated_cost_savings_monthly FLOAT, 
	implementation_complexity INTEGER, 
	automation_recipe_json TEXT, 
	triggers_json TEXT, 
	actions_json TEXT, 
	accepted_by VARCHAR(36), 
	accepted_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(accepted_by) REFERENCES users (id)
);

-- Table: document_chunks
CREATE TABLE document_chunks (
	document_id VARCHAR(36) NOT NULL, 
	content TEXT NOT NULL, 
	chunk_index INTEGER NOT NULL, 
	start_char INTEGER, 
	end_char INTEGER, 
	embedding_json TEXT, 
	embedding_model VARCHAR(100), 
	token_count INTEGER, 
	metadata_json TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

-- Table: gdpr_requests
CREATE TABLE gdpr_requests (
	org_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	request_type VARCHAR(50) NOT NULL, 
	status VARCHAR(50), 
	requested_at TIMESTAMP WITHOUT TIME ZONE, 
	processed_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	processed_by VARCHAR(36), 
	result_url VARCHAR(2000), 
	result_expiry TIMESTAMP WITHOUT TIME ZONE, 
	error_message TEXT, 
	verification_token VARCHAR(255), 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(processed_by) REFERENCES users (id)
);

-- Table: integrations
CREATE TABLE integrations (
	org_id VARCHAR(36) NOT NULL, 
	integration_type integrationtype NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	is_active BOOLEAN, 
	config_json TEXT, 
	credentials_json TEXT, 
	sync_enabled BOOLEAN, 
	last_sync_at TIMESTAMP WITHOUT TIME ZONE, 
	last_sync_status VARCHAR(50), 
	sync_error TEXT, 
	oauth_access_token TEXT, 
	oauth_refresh_token TEXT, 
	oauth_expires_at TIMESTAMP WITHOUT TIME ZONE, 
	connected_by VARCHAR(36), 
	connected_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(connected_by) REFERENCES users (id)
);

-- Table: learning_paths
CREATE TABLE learning_paths (
	user_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	description TEXT, 
	target_role VARCHAR(200), 
	skills_json TEXT, 
	milestones_json TEXT, 
	progress_percentage FLOAT, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	target_completion TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	is_active BOOLEAN, 
	is_ai_generated BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: manager_effectiveness
CREATE TABLE manager_effectiveness (
	manager_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	snapshot_date TIMESTAMP WITHOUT TIME ZONE, 
	team_size INTEGER, 
	team_velocity_avg FLOAT, 
	team_quality_avg FLOAT, 
	escalation_response_time_hours FLOAT, 
	escalation_resolution_rate FLOAT, 
	team_attrition_rate FLOAT, 
	team_satisfaction_score FLOAT, 
	redundancy_score FLOAT, 
	assignment_quality_score FLOAT, 
	workload_distribution_score FLOAT, 
	effectiveness_score FLOAT, 
	org_percentile FLOAT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(manager_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: notification_preferences
CREATE TABLE notification_preferences (
	user_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	notification_type notificationtype NOT NULL, 
	channel notificationchannel NOT NULL, 
	enabled BOOLEAN, 
	quiet_hours_start INTEGER, 
	quiet_hours_end INTEGER, 
	batch_frequency_minutes INTEGER, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: restructuring_scenarios
CREATE TABLE restructuring_scenarios (
	org_id VARCHAR(36) NOT NULL, 
	created_by VARCHAR(36) NOT NULL, 
	name VARCHAR(500) NOT NULL, 
	description TEXT, 
	scenario_type VARCHAR(100) NOT NULL, 
	config_json TEXT, 
	projected_cost_change FLOAT, 
	projected_productivity_change FLOAT, 
	projected_skill_coverage_change FLOAT, 
	affected_employees INTEGER, 
	risk_factors_json TEXT, 
	overall_risk_score FLOAT, 
	is_draft BOOLEAN, 
	executed BOOLEAN, 
	executed_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

-- Table: sessions
CREATE TABLE sessions (
	user_id VARCHAR(36) NOT NULL, 
	token_hash VARCHAR(255) NOT NULL, 
	refresh_token_hash VARCHAR(255), 
	device_info VARCHAR(255), 
	ip_address VARCHAR(45), 
	user_agent VARCHAR(500), 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	refresh_expires_at TIMESTAMP WITHOUT TIME ZONE, 
	is_active BOOLEAN NOT NULL, 
	last_activity TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (refresh_token_hash)
);

-- Table: skill_gaps
CREATE TABLE skill_gaps (
	user_id VARCHAR(36) NOT NULL, 
	skill_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	gap_type gaptype, 
	current_level FLOAT, 
	required_level FLOAT NOT NULL, 
	gap_size FLOAT NOT NULL, 
	for_role VARCHAR(200), 
	priority INTEGER, 
	identified_at TIMESTAMP WITHOUT TIME ZONE, 
	is_resolved BOOLEAN, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	learning_resources_json TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: skill_metrics
CREATE TABLE skill_metrics (
	user_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	period_start TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	period_end TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	task_completion_velocity FLOAT, 
	quality_score FLOAT, 
	self_sufficiency_index FLOAT, 
	learning_velocity FLOAT, 
	collaboration_score FLOAT, 
	help_given_count INTEGER, 
	help_received_count INTEGER, 
	blockers_encountered INTEGER, 
	blockers_self_resolved INTEGER, 
	avg_blocker_resolution_hours FLOAT, 
	velocity_percentile FLOAT, 
	quality_percentile FLOAT, 
	learning_percentile FLOAT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: tasks
CREATE TABLE tasks (
	org_id VARCHAR(36) NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	description TEXT, 
	goal TEXT, 
	status taskstatus NOT NULL, 
	priority taskpriority NOT NULL, 
	assigned_to VARCHAR(36), 
	created_by VARCHAR(36) NOT NULL, 
	team_id VARCHAR(36), 
	project_id VARCHAR(36), 
	deadline TIMESTAMP WITHOUT TIME ZONE, 
	estimated_hours FLOAT, 
	actual_hours FLOAT, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	risk_score FLOAT, 
	confidence_score FLOAT, 
	complexity_score FLOAT, 
	blocker_type blockertype, 
	blocker_description TEXT, 
	tools_json TEXT, 
	tags_json TEXT, 
	skills_required_json TEXT, 
	parent_task_id VARCHAR(36), 
	sort_order INTEGER, 
	is_draft BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(assigned_to) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(parent_task_id) REFERENCES tasks (id) ON DELETE CASCADE
);

-- Table: user_skills
CREATE TABLE user_skills (
	user_id VARCHAR(36) NOT NULL, 
	skill_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	level FLOAT, 
	confidence FLOAT, 
	trend skilltrend, 
	last_demonstrated TIMESTAMP WITHOUT TIME ZONE, 
	demonstration_count INTEGER, 
	source VARCHAR(50), 
	level_history_json TEXT, 
	notes TEXT, 
	is_certified BOOLEAN, 
	certification_date TIMESTAMP WITHOUT TIME ZONE, 
	certification_expiry TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: webhooks
CREATE TABLE webhooks (
	org_id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	url VARCHAR(2000) NOT NULL, 
	secret VARCHAR(255), 
	events_json TEXT, 
	is_active BOOLEAN, 
	headers_json TEXT, 
	total_deliveries INTEGER, 
	successful_deliveries INTEGER, 
	last_delivery_at TIMESTAMP WITHOUT TIME ZONE, 
	last_delivery_status INTEGER, 
	created_by VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

-- Table: workforce_scores
CREATE TABLE workforce_scores (
	user_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	snapshot_date TIMESTAMP WITHOUT TIME ZONE, 
	velocity_score FLOAT, 
	quality_score FLOAT, 
	self_sufficiency_score FLOAT, 
	learning_score FLOAT, 
	collaboration_score FLOAT, 
	overall_score FLOAT, 
	percentile_rank FLOAT, 
	attrition_risk_score FLOAT, 
	burnout_risk_score FLOAT, 
	score_trend VARCHAR(20), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: agent_executions
CREATE TABLE agent_executions (
	id VARCHAR(36) NOT NULL, 
	agent_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	event_type VARCHAR(100) NOT NULL, 
	event_id VARCHAR(36), 
	trigger_source VARCHAR(100), 
	user_id VARCHAR(36), 
	task_id VARCHAR(36), 
	context_data JSON, 
	status executionstatus, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	duration_ms INTEGER, 
	success BOOLEAN, 
	output_data JSON, 
	error_message TEXT, 
	error_code VARCHAR(50), 
	tokens_used INTEGER, 
	api_calls INTEGER, 
	parent_execution_id VARCHAR(36), 
	chain_depth INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(agent_id) REFERENCES agents (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id), 
	FOREIGN KEY(parent_execution_id) REFERENCES agent_executions (id)
);

-- Table: ai_agents
CREATE TABLE ai_agents (
	org_id VARCHAR(36) NOT NULL, 
	pattern_id VARCHAR(36), 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	status agentstatus, 
	config_json TEXT, 
	permissions_json TEXT, 
	shadow_started_at TIMESTAMP WITHOUT TIME ZONE, 
	shadow_match_rate FLOAT, 
	shadow_runs INTEGER, 
	total_runs INTEGER, 
	successful_runs INTEGER, 
	hours_saved_total FLOAT, 
	last_run_at TIMESTAMP WITHOUT TIME ZONE, 
	live_started_at TIMESTAMP WITHOUT TIME ZONE, 
	created_by VARCHAR(36) NOT NULL, 
	approved_by VARCHAR(36), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(pattern_id) REFERENCES automation_patterns (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
);

-- Table: checkin_configs
CREATE TABLE checkin_configs (
	org_id VARCHAR(36) NOT NULL, 
	team_id VARCHAR(36), 
	user_id VARCHAR(36), 
	task_id VARCHAR(36), 
	interval_hours FLOAT, 
	enabled BOOLEAN, 
	silent_mode_threshold FLOAT, 
	max_daily_checkins INTEGER, 
	work_start_hour INTEGER, 
	work_end_hour INTEGER, 
	respect_timezone BOOLEAN, 
	excluded_days VARCHAR(50), 
	auto_escalate_after_missed INTEGER, 
	escalate_to_manager BOOLEAN, 
	ai_suggestions_enabled BOOLEAN, 
	ai_sentiment_analysis BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);

-- Table: checkins
CREATE TABLE checkins (
	task_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	org_id VARCHAR(36) NOT NULL, 
	cycle_number INTEGER, 
	trigger checkintrigger, 
	status checkinstatus, 
	scheduled_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	responded_at TIMESTAMP WITHOUT TIME ZONE, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	progress_indicator progressindicator, 
	progress_notes TEXT, 
	completed_since_last TEXT, 
	blockers_reported TEXT, 
	help_needed BOOLEAN, 
	estimated_completion_change FLOAT, 
	ai_suggestion TEXT, 
	ai_confidence FLOAT, 
	sentiment_score FLOAT, 
	friction_detected BOOLEAN, 
	escalated BOOLEAN, 
	escalated_to VARCHAR(36), 
	escalated_at TIMESTAMP WITHOUT TIME ZONE, 
	escalation_reason TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(escalated_to) REFERENCES users (id)
);

-- Table: predictions
CREATE TABLE predictions (
	org_id VARCHAR(36) NOT NULL, 
	prediction_type predictiontype NOT NULL, 
	task_id VARCHAR(36), 
	project_id VARCHAR(36), 
	user_id VARCHAR(36), 
	team_id VARCHAR(36), 
	predicted_date_p25 TIMESTAMP WITHOUT TIME ZONE, 
	predicted_date_p50 TIMESTAMP WITHOUT TIME ZONE, 
	predicted_date_p90 TIMESTAMP WITHOUT TIME ZONE, 
	confidence FLOAT, 
	risk_score FLOAT, 
	risk_factors_json TEXT, 
	model_version VARCHAR(50), 
	features_json TEXT, 
	actual_date TIMESTAMP WITHOUT TIME ZONE, 
	accuracy_score FLOAT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(task_id) REFERENCES tasks (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Table: task_comments
CREATE TABLE task_comments (
	task_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	content TEXT NOT NULL, 
	is_ai_generated BOOLEAN, 
	is_edited BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Table: task_dependencies
CREATE TABLE task_dependencies (
	task_id VARCHAR(36) NOT NULL, 
	depends_on_id VARCHAR(36) NOT NULL, 
	is_blocking BOOLEAN, 
	description VARCHAR(500), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE, 
	FOREIGN KEY(depends_on_id) REFERENCES tasks (id) ON DELETE CASCADE
);

-- Table: task_history
CREATE TABLE task_history (
	task_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	action VARCHAR(50) NOT NULL, 
	field_name VARCHAR(100), 
	old_value TEXT, 
	new_value TEXT, 
	details_json TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Table: webhook_deliveries
CREATE TABLE webhook_deliveries (
	webhook_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	event_type VARCHAR(100) NOT NULL, 
	payload_json TEXT, 
	attempted_at TIMESTAMP WITHOUT TIME ZONE, 
	response_status INTEGER, 
	response_body TEXT, 
	response_time_ms INTEGER, 
	retry_count INTEGER, 
	next_retry_at TIMESTAMP WITHOUT TIME ZONE, 
	is_successful BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(webhook_id) REFERENCES webhooks (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: agent_runs
CREATE TABLE agent_runs (
	agent_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(50), 
	execution_time_ms INTEGER, 
	input_data_json TEXT, 
	output_data_json TEXT, 
	error_message TEXT, 
	is_shadow BOOLEAN, 
	human_action_json TEXT, 
	matched_human BOOLEAN, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(agent_id) REFERENCES ai_agents (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

-- Table: checkin_reminders
CREATE TABLE checkin_reminders (
	checkin_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	reminder_number INTEGER, 
	channel VARCHAR(50), 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	acknowledged BOOLEAN, 
	acknowledged_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(checkin_id) REFERENCES checkins (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Table: notifications
CREATE TABLE notifications (
	user_id VARCHAR(36) NOT NULL, 
	org_id VARCHAR(36) NOT NULL, 
	notification_type notificationtype NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	message TEXT, 
	task_id VARCHAR(36), 
	checkin_id VARCHAR(36), 
	is_read BOOLEAN, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	channel notificationchannel, 
	delivered BOOLEAN, 
	delivered_at TIMESTAMP WITHOUT TIME ZONE, 
	action_url VARCHAR(1000), 
	action_data_json TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(task_id) REFERENCES tasks (id), 
	FOREIGN KEY(checkin_id) REFERENCES checkins (id)
);

-- Table: unblock_sessions
CREATE TABLE unblock_sessions (
	org_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36), 
	task_id VARCHAR(36), 
	checkin_id VARCHAR(36), 
	query TEXT NOT NULL, 
	blocker_type VARCHAR(50), 
	user_skill_level VARCHAR(50), 
	response TEXT, 
	confidence FLOAT, 
	sources_json TEXT, 
	escalation_recommended BOOLEAN, 
	escalated BOOLEAN, 
	escalated_to VARCHAR(36), 
	was_helpful BOOLEAN, 
	feedback_text TEXT, 
	feedback_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(task_id) REFERENCES tasks (id) ON DELETE SET NULL, 
	FOREIGN KEY(checkin_id) REFERENCES checkins (id) ON DELETE SET NULL, 
	FOREIGN KEY(escalated_to) REFERENCES users (id)
);

-- =============================================================
-- INDEXES
-- =============================================================

CREATE UNIQUE INDEX ix_organizations_slug ON organizations (slug);
CREATE INDEX ix_organizations_id ON organizations (id);
CREATE INDEX ix_organizations_created_at ON organizations (created_at);
CREATE INDEX ix_system_health_id ON system_health (id);
CREATE INDEX ix_system_health_created_at ON system_health (created_at);
CREATE INDEX ix_system_health_snapshot_time ON system_health (snapshot_time);
CREATE INDEX ix_agents_org_id ON agents (org_id);
CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_org_id ON audit_logs (org_id);
CREATE INDEX ix_audit_logs_id ON audit_logs (id);
CREATE INDEX ix_documents_created_at ON documents (created_at);
CREATE INDEX ix_documents_org_id ON documents (org_id);
CREATE INDEX ix_documents_id ON documents (id);
CREATE INDEX ix_documents_status ON documents (status);
CREATE INDEX ix_org_health_snapshots_created_at ON org_health_snapshots (created_at);
CREATE INDEX ix_org_health_snapshots_id ON org_health_snapshots (id);
CREATE INDEX ix_org_health_snapshots_org_id ON org_health_snapshots (org_id);
CREATE INDEX ix_skills_id ON skills (id);
CREATE INDEX ix_skills_org_id ON skills (org_id);
CREATE INDEX ix_skills_created_at ON skills (created_at);
CREATE INDEX ix_users_created_at ON users (created_at);
CREATE INDEX ix_users_team_id ON users (team_id);
CREATE INDEX ix_users_org_id ON users (org_id);
CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_velocity_snapshots_created_at ON velocity_snapshots (created_at);
CREATE INDEX ix_velocity_snapshots_id ON velocity_snapshots (id);
CREATE INDEX ix_velocity_snapshots_team_id ON velocity_snapshots (team_id);
CREATE INDEX ix_agent_conversations_user_id ON agent_conversations (user_id);
CREATE INDEX ix_agent_conversations_created_at ON agent_conversations (created_at);
CREATE INDEX ix_agent_conversations_org_id ON agent_conversations (org_id);
CREATE INDEX ix_agent_schedules_org_id ON agent_schedules (org_id);
CREATE INDEX ix_agent_schedules_agent_id ON agent_schedules (agent_id);
CREATE INDEX ix_api_keys_org_id ON api_keys (org_id);
CREATE INDEX ix_api_keys_created_at ON api_keys (created_at);
CREATE INDEX ix_api_keys_id ON api_keys (id);
CREATE INDEX ix_automation_patterns_org_id ON automation_patterns (org_id);
CREATE INDEX ix_automation_patterns_id ON automation_patterns (id);
CREATE INDEX ix_automation_patterns_created_at ON automation_patterns (created_at);
CREATE INDEX ix_document_chunks_id ON document_chunks (id);
CREATE INDEX ix_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX ix_document_chunks_created_at ON document_chunks (created_at);
CREATE INDEX ix_gdpr_requests_user_id ON gdpr_requests (user_id);
CREATE INDEX ix_gdpr_requests_created_at ON gdpr_requests (created_at);
CREATE INDEX ix_gdpr_requests_id ON gdpr_requests (id);
CREATE INDEX ix_gdpr_requests_org_id ON gdpr_requests (org_id);
CREATE INDEX ix_integrations_id ON integrations (id);
CREATE INDEX ix_integrations_created_at ON integrations (created_at);
CREATE INDEX ix_integrations_org_id ON integrations (org_id);
CREATE INDEX ix_learning_paths_id ON learning_paths (id);
CREATE INDEX ix_learning_paths_user_id ON learning_paths (user_id);
CREATE INDEX ix_learning_paths_created_at ON learning_paths (created_at);
CREATE INDEX ix_learning_paths_org_id ON learning_paths (org_id);
CREATE INDEX ix_manager_effectiveness_org_id ON manager_effectiveness (org_id);
CREATE INDEX ix_manager_effectiveness_id ON manager_effectiveness (id);
CREATE INDEX ix_manager_effectiveness_manager_id ON manager_effectiveness (manager_id);
CREATE INDEX ix_manager_effectiveness_created_at ON manager_effectiveness (created_at);
CREATE INDEX ix_notification_preferences_created_at ON notification_preferences (created_at);
CREATE INDEX ix_notification_preferences_user_id ON notification_preferences (user_id);
CREATE INDEX ix_notification_preferences_id ON notification_preferences (id);
CREATE INDEX ix_restructuring_scenarios_id ON restructuring_scenarios (id);
CREATE INDEX ix_restructuring_scenarios_created_at ON restructuring_scenarios (created_at);
CREATE INDEX ix_restructuring_scenarios_org_id ON restructuring_scenarios (org_id);
CREATE INDEX ix_sessions_id ON sessions (id);
CREATE UNIQUE INDEX ix_sessions_token_hash ON sessions (token_hash);
CREATE INDEX ix_sessions_user_id ON sessions (user_id);
CREATE INDEX ix_sessions_created_at ON sessions (created_at);
CREATE INDEX ix_skill_gaps_id ON skill_gaps (id);
CREATE INDEX ix_skill_gaps_skill_id ON skill_gaps (skill_id);
CREATE INDEX ix_skill_gaps_org_id ON skill_gaps (org_id);
CREATE INDEX ix_skill_gaps_user_id ON skill_gaps (user_id);
CREATE INDEX ix_skill_gaps_created_at ON skill_gaps (created_at);
CREATE INDEX ix_skill_metrics_id ON skill_metrics (id);
CREATE INDEX ix_skill_metrics_user_id ON skill_metrics (user_id);
CREATE INDEX ix_skill_metrics_created_at ON skill_metrics (created_at);
CREATE INDEX ix_skill_metrics_org_id ON skill_metrics (org_id);
CREATE INDEX ix_tasks_parent_task_id ON tasks (parent_task_id);
CREATE INDEX ix_tasks_assigned_to ON tasks (assigned_to);
CREATE INDEX ix_tasks_org_id ON tasks (org_id);
CREATE INDEX ix_tasks_is_draft ON tasks (is_draft);
CREATE INDEX ix_tasks_project_id ON tasks (project_id);
CREATE INDEX ix_tasks_id ON tasks (id);
CREATE INDEX ix_tasks_created_at ON tasks (created_at);
CREATE INDEX ix_tasks_team_id ON tasks (team_id);
CREATE INDEX ix_tasks_status ON tasks (status);
CREATE INDEX ix_user_skills_id ON user_skills (id);
CREATE INDEX ix_user_skills_created_at ON user_skills (created_at);
CREATE INDEX ix_user_skills_skill_id ON user_skills (skill_id);
CREATE INDEX ix_user_skills_user_id ON user_skills (user_id);
CREATE INDEX ix_user_skills_org_id ON user_skills (org_id);
CREATE INDEX ix_webhooks_created_at ON webhooks (created_at);
CREATE INDEX ix_webhooks_org_id ON webhooks (org_id);
CREATE INDEX ix_webhooks_id ON webhooks (id);
CREATE INDEX ix_workforce_scores_org_id ON workforce_scores (org_id);
CREATE INDEX ix_workforce_scores_user_id ON workforce_scores (user_id);
CREATE INDEX ix_workforce_scores_id ON workforce_scores (id);
CREATE INDEX ix_workforce_scores_created_at ON workforce_scores (created_at);
CREATE INDEX ix_agent_executions_org_id ON agent_executions (org_id);
CREATE INDEX ix_agent_executions_agent_id ON agent_executions (agent_id);
CREATE INDEX ix_ai_agents_org_id ON ai_agents (org_id);
CREATE INDEX ix_ai_agents_id ON ai_agents (id);
CREATE INDEX ix_ai_agents_created_at ON ai_agents (created_at);
CREATE INDEX ix_checkin_configs_org_id ON checkin_configs (org_id);
CREATE INDEX ix_checkin_configs_id ON checkin_configs (id);
CREATE INDEX ix_checkin_configs_created_at ON checkin_configs (created_at);
CREATE INDEX ix_checkin_configs_task_id ON checkin_configs (task_id);
CREATE INDEX ix_checkin_configs_user_id ON checkin_configs (user_id);
CREATE INDEX ix_checkin_configs_team_id ON checkin_configs (team_id);
CREATE INDEX ix_checkins_user_id ON checkins (user_id);
CREATE INDEX ix_checkins_org_id ON checkins (org_id);
CREATE INDEX ix_checkins_task_id ON checkins (task_id);
CREATE INDEX ix_checkins_created_at ON checkins (created_at);
CREATE INDEX ix_checkins_status ON checkins (status);
CREATE INDEX ix_checkins_id ON checkins (id);
CREATE INDEX ix_predictions_created_at ON predictions (created_at);
CREATE INDEX ix_predictions_id ON predictions (id);
CREATE INDEX ix_predictions_org_id ON predictions (org_id);
CREATE INDEX ix_task_comments_id ON task_comments (id);
CREATE INDEX ix_task_comments_created_at ON task_comments (created_at);
CREATE INDEX ix_task_comments_task_id ON task_comments (task_id);
CREATE INDEX ix_task_dependencies_depends_on_id ON task_dependencies (depends_on_id);
CREATE INDEX ix_task_dependencies_id ON task_dependencies (id);
CREATE INDEX ix_task_dependencies_task_id ON task_dependencies (task_id);
CREATE INDEX ix_task_dependencies_created_at ON task_dependencies (created_at);
CREATE INDEX ix_task_history_created_at ON task_history (created_at);
CREATE INDEX ix_task_history_task_id ON task_history (task_id);
CREATE INDEX ix_task_history_id ON task_history (id);
CREATE INDEX ix_webhook_deliveries_created_at ON webhook_deliveries (created_at);
CREATE INDEX ix_webhook_deliveries_webhook_id ON webhook_deliveries (webhook_id);
CREATE INDEX ix_webhook_deliveries_id ON webhook_deliveries (id);
CREATE INDEX ix_agent_runs_agent_id ON agent_runs (agent_id);
CREATE INDEX ix_agent_runs_id ON agent_runs (id);
CREATE INDEX ix_agent_runs_created_at ON agent_runs (created_at);
CREATE INDEX ix_checkin_reminders_checkin_id ON checkin_reminders (checkin_id);
CREATE INDEX ix_checkin_reminders_id ON checkin_reminders (id);
CREATE INDEX ix_checkin_reminders_created_at ON checkin_reminders (created_at);
CREATE INDEX ix_notifications_org_id ON notifications (org_id);
CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE INDEX ix_notifications_id ON notifications (id);
CREATE INDEX ix_notifications_created_at ON notifications (created_at);
CREATE INDEX ix_unblock_sessions_task_id ON unblock_sessions (task_id);
CREATE INDEX ix_unblock_sessions_id ON unblock_sessions (id);
CREATE INDEX ix_unblock_sessions_created_at ON unblock_sessions (created_at);
CREATE INDEX ix_unblock_sessions_user_id ON unblock_sessions (user_id);
CREATE INDEX ix_unblock_sessions_org_id ON unblock_sessions (org_id);

-- =============================================================
-- END OF SCHEMA
-- =============================================================
