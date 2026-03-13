-- ============================================================================
-- TaskPulse AI - Complete PostgreSQL DDL Schema
-- Generated from SQLAlchemy models
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE plan_tier AS ENUM (
    'starter', 'professional', 'enterprise', 'enterprise_plus'
);

CREATE TYPE user_role AS ENUM (
    'super_admin', 'org_admin', 'manager', 'team_lead', 'employee', 'viewer'
);

CREATE TYPE skill_level AS ENUM (
    'junior', 'mid', 'senior', 'lead'
);

CREATE TYPE task_status AS ENUM (
    'todo', 'in_progress', 'blocked', 'review', 'done', 'archived'
);

CREATE TYPE task_priority AS ENUM (
    'critical', 'high', 'medium', 'low'
);

CREATE TYPE blocker_type AS ENUM (
    'logic', 'tool', 'dependency', 'bug', 'resource', 'unknown'
);

CREATE TYPE checkin_trigger AS ENUM (
    'scheduled', 'progress_stall', 'deadline_approaching',
    'manual', 'blocker_detected', 'status_change'
);

CREATE TYPE checkin_status AS ENUM (
    'pending', 'responded', 'skipped', 'expired', 'escalated'
);

CREATE TYPE progress_indicator AS ENUM (
    'on_track', 'slightly_behind', 'significantly_behind',
    'blocked', 'ahead', 'completed'
);

CREATE TYPE document_source AS ENUM (
    'manual_upload', 'confluence', 'notion', 'github',
    'gitlab', 'jira', 'slack', 'internal_wiki', 'external_url'
);

CREATE TYPE document_status AS ENUM (
    'pending', 'processing', 'indexed', 'failed', 'archived'
);

CREATE TYPE document_type AS ENUM (
    'documentation', 'code_snippet', 'tutorial', 'faq', 'runbook',
    'policy', 'meeting_notes', 'architecture', 'guide', 'troubleshooting', 'other'
);

CREATE TYPE skill_category AS ENUM (
    'technical', 'process', 'soft', 'domain', 'tool', 'language'
);

CREATE TYPE skill_trend AS ENUM (
    'improving', 'stable', 'declining'
);

CREATE TYPE gap_type AS ENUM (
    'critical', 'growth', 'stretch'
);

CREATE TYPE prediction_type AS ENUM (
    'task_completion', 'project_delivery', 'team_velocity',
    'attrition_risk', 'hiring_needs'
);

CREATE TYPE pattern_status AS ENUM (
    'detected', 'suggested', 'accepted', 'rejected', 'implemented'
);

CREATE TYPE agent_status AS ENUM (
    'created', 'shadow', 'supervised', 'live', 'paused', 'retired'
);

CREATE TYPE notification_type AS ENUM (
    'checkin_reminder', 'task_assigned', 'task_completed', 'task_blocked',
    'escalation', 'deadline_approaching', 'ai_suggestion', 'mention', 'system'
);

CREATE TYPE notification_channel AS ENUM (
    'in_app', 'email', 'slack', 'teams', 'webhook'
);

CREATE TYPE notification_priority AS ENUM (
    'low', 'medium', 'high', 'urgent'
);

CREATE TYPE integration_type AS ENUM (
    'jira', 'github', 'gitlab', 'slack', 'teams',
    'confluence', 'notion', 'custom_webhook'
);

CREATE TYPE integration_status AS ENUM (
    'pending', 'active', 'error', 'disconnected'
);

CREATE TYPE actor_type AS ENUM (
    'user', 'admin', 'system', 'ai', 'api', 'integration'
);

CREATE TYPE audit_action AS ENUM (
    'login', 'logout', 'password_change', 'mfa_enabled',
    'create', 'read', 'update', 'delete',
    'role_change', 'permission_change', 'config_change',
    'export', 'import',
    'data_request', 'data_deletion'
);

CREATE TYPE agent_type_enum AS ENUM (
    'ai', 'integration', 'conversation'
);

CREATE TYPE agent_status_db AS ENUM (
    'active', 'paused', 'error', 'disabled'
);

CREATE TYPE execution_status AS ENUM (
    'pending', 'running', 'completed', 'failed', 'cancelled'
);

-- ============================================================================
-- TABLE: organizations (no foreign key dependencies)
-- ============================================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) NOT NULL,
    description     TEXT,
    plan            plan_tier NOT NULL DEFAULT 'starter',
    settings_data   JSONB DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX ix_organizations_slug ON organizations (slug);
CREATE INDEX ix_organizations_id ON organizations (id);
CREATE INDEX ix_organizations_created_at ON organizations (created_at);

-- ============================================================================
-- TABLE: users (depends on: organizations)
-- ============================================================================

CREATE TABLE users (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    -- Organization
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Authentication
    email                   VARCHAR(255) NOT NULL,
    password_hash           VARCHAR(255),
    is_sso_user             BOOLEAN DEFAULT FALSE,
    supabase_auth_id        UUID,

    -- Profile
    first_name              VARCHAR(100) NOT NULL,
    last_name               VARCHAR(100) NOT NULL,
    avatar_url              VARCHAR(500),
    phone                   VARCHAR(50),
    timezone                VARCHAR(50) NOT NULL DEFAULT 'UTC',

    -- Role and permissions
    role                    user_role NOT NULL DEFAULT 'employee',
    skill_level             skill_level NOT NULL DEFAULT 'mid',

    -- Team / reporting structure
    team_id                 UUID,
    manager_id              UUID REFERENCES users(id) ON DELETE SET NULL,

    -- GDPR consent tracking
    consent_data            JSONB DEFAULT '{}',

    -- Status
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified       BOOLEAN DEFAULT FALSE,
    last_login              TIMESTAMP,
    failed_login_attempts   INTEGER DEFAULT 0,
    lockout_until           TIMESTAMP,

    -- Constraints
    CONSTRAINT uq_user_org_email UNIQUE (org_id, email)
);

CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_created_at ON users (created_at);
CREATE INDEX ix_users_org_id ON users (org_id);
CREATE INDEX ix_users_email ON users (email);
CREATE UNIQUE INDEX ix_users_supabase_auth_id ON users (supabase_auth_id);
CREATE INDEX ix_users_team_id ON users (team_id);

-- ============================================================================
-- TABLE: tasks (depends on: organizations, users)
-- ============================================================================

CREATE TABLE tasks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    -- Organization
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Basic info
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    goal                TEXT,

    -- Status and priority
    status              task_status NOT NULL DEFAULT 'todo',
    priority            task_priority NOT NULL DEFAULT 'medium',

    -- Assignment
    assigned_to         UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by          UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,

    -- Team/project grouping
    team_id             UUID,
    project_id          UUID,

    -- Time tracking
    deadline            TIMESTAMP WITH TIME ZONE,
    estimated_hours     DOUBLE PRECISION,
    actual_hours        DOUBLE PRECISION DEFAULT 0.0,
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,

    -- AI-generated scores
    risk_score          DOUBLE PRECISION,
    confidence_score    DOUBLE PRECISION,
    complexity_score    DOUBLE PRECISION,

    -- Blocker info
    blocker_type        blocker_type,
    blocker_description TEXT,

    -- Metadata (JSONB)
    tools               JSONB DEFAULT '[]',
    tags                JSONB DEFAULT '[]',
    skills_required     JSONB DEFAULT '[]',

    -- Parent task (for subtasks, self-reference)
    parent_task_id      UUID REFERENCES tasks(id) ON DELETE CASCADE,

    -- Ordering
    sort_order          INTEGER DEFAULT 0,

    -- Draft flag
    is_draft            BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX ix_tasks_id ON tasks (id);
CREATE INDEX ix_tasks_created_at ON tasks (created_at);
CREATE INDEX ix_tasks_org_id ON tasks (org_id);
CREATE INDEX ix_tasks_status ON tasks (status);
CREATE INDEX ix_tasks_assigned_to ON tasks (assigned_to);
CREATE INDEX ix_tasks_team_id ON tasks (team_id);
CREATE INDEX ix_tasks_project_id ON tasks (project_id);
CREATE INDEX ix_tasks_parent_task_id ON tasks (parent_task_id);
CREATE INDEX ix_tasks_is_draft ON tasks (is_draft);

-- ============================================================================
-- TABLE: task_dependencies (depends on: tasks)
-- ============================================================================

CREATE TABLE task_dependencies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_id   UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    is_blocking     BOOLEAN DEFAULT TRUE,
    description     VARCHAR(500)
);

CREATE INDEX ix_task_dependencies_id ON task_dependencies (id);
CREATE INDEX ix_task_dependencies_created_at ON task_dependencies (created_at);
CREATE INDEX ix_task_dependencies_task_id ON task_dependencies (task_id);
CREATE INDEX ix_task_dependencies_depends_on_id ON task_dependencies (depends_on_id);

-- ============================================================================
-- TABLE: task_history (depends on: tasks, users)
-- ============================================================================

CREATE TABLE task_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,

    action          VARCHAR(50) NOT NULL,
    field_name      VARCHAR(100),
    old_value       TEXT,
    new_value       TEXT,
    details         JSONB DEFAULT '{}'
);

CREATE INDEX ix_task_history_id ON task_history (id);
CREATE INDEX ix_task_history_created_at ON task_history (created_at);
CREATE INDEX ix_task_history_task_id ON task_history (task_id);

-- ============================================================================
-- TABLE: task_comments (depends on: tasks, users)
-- ============================================================================

CREATE TABLE task_comments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,

    content         TEXT NOT NULL,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    is_edited       BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_task_comments_id ON task_comments (id);
CREATE INDEX ix_task_comments_created_at ON task_comments (created_at);
CREATE INDEX ix_task_comments_task_id ON task_comments (task_id);

-- ============================================================================
-- TABLE: checkins (depends on: tasks, users, organizations)
-- ============================================================================

CREATE TABLE checkins (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    task_id                     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id                     UUID REFERENCES users(id) ON DELETE SET NULL,
    org_id                      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Check-in metadata
    cycle_number                INTEGER DEFAULT 1,
    trigger                     checkin_trigger DEFAULT 'scheduled',
    status                      checkin_status DEFAULT 'pending',

    -- Timing
    scheduled_at                TIMESTAMP WITH TIME ZONE NOT NULL,
    responded_at                TIMESTAMP WITH TIME ZONE,
    expires_at                  TIMESTAMP WITH TIME ZONE,

    -- User response
    progress_indicator          progress_indicator,
    progress_notes              TEXT,
    completed_since_last        TEXT,
    blockers_reported           TEXT,
    help_needed                 BOOLEAN DEFAULT FALSE,
    estimated_completion_change DOUBLE PRECISION,

    -- AI analysis
    ai_suggestion               TEXT,
    ai_confidence               DOUBLE PRECISION,
    sentiment_score             DOUBLE PRECISION,
    friction_detected           BOOLEAN DEFAULT FALSE,

    -- Escalation
    escalated                   BOOLEAN DEFAULT FALSE,
    escalated_to                UUID REFERENCES users(id),
    escalated_at                TIMESTAMP WITH TIME ZONE,
    escalation_reason           TEXT
);

CREATE INDEX ix_checkins_id ON checkins (id);
CREATE INDEX ix_checkins_created_at ON checkins (created_at);
CREATE INDEX ix_checkins_task_id ON checkins (task_id);
CREATE INDEX ix_checkins_user_id ON checkins (user_id);
CREATE INDEX ix_checkins_org_id ON checkins (org_id);
CREATE INDEX ix_checkins_status ON checkins (status);

-- ============================================================================
-- TABLE: checkin_configs (depends on: organizations, users, tasks)
-- ============================================================================

CREATE TABLE checkin_configs (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Scope
    team_id                         UUID,
    user_id                         UUID REFERENCES users(id),
    task_id                         UUID REFERENCES tasks(id),

    -- Check-in settings
    interval_hours                  DOUBLE PRECISION DEFAULT 3.0,
    enabled                         BOOLEAN DEFAULT TRUE,
    silent_mode_threshold           DOUBLE PRECISION DEFAULT 0.8,
    max_daily_checkins              INTEGER DEFAULT 4,

    -- Working hours
    work_start_hour                 INTEGER DEFAULT 9,
    work_end_hour                   INTEGER DEFAULT 18,
    respect_timezone                BOOLEAN DEFAULT TRUE,
    excluded_days                   VARCHAR(50) DEFAULT '0,6',

    -- Escalation settings
    auto_escalate_after_missed      INTEGER DEFAULT 2,
    escalate_to_manager             BOOLEAN DEFAULT TRUE,

    -- AI settings
    ai_suggestions_enabled          BOOLEAN DEFAULT TRUE,
    ai_sentiment_analysis           BOOLEAN DEFAULT TRUE
);

CREATE INDEX ix_checkin_configs_id ON checkin_configs (id);
CREATE INDEX ix_checkin_configs_created_at ON checkin_configs (created_at);
CREATE INDEX ix_checkin_configs_org_id ON checkin_configs (org_id);
CREATE INDEX ix_checkin_configs_team_id ON checkin_configs (team_id);
CREATE INDEX ix_checkin_configs_user_id ON checkin_configs (user_id);
CREATE INDEX ix_checkin_configs_task_id ON checkin_configs (task_id);

-- ============================================================================
-- TABLE: checkin_reminders (depends on: checkins, users)
-- ============================================================================

CREATE TABLE checkin_reminders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    checkin_id          UUID NOT NULL REFERENCES checkins(id) ON DELETE CASCADE,
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,

    reminder_number     INTEGER DEFAULT 1,
    channel             VARCHAR(50) DEFAULT 'in_app',
    sent_at             TIMESTAMP WITH TIME ZONE DEFAULT now(),
    acknowledged        BOOLEAN DEFAULT FALSE,
    acknowledged_at     TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_checkin_reminders_id ON checkin_reminders (id);
CREATE INDEX ix_checkin_reminders_created_at ON checkin_reminders (created_at);
CREATE INDEX ix_checkin_reminders_checkin_id ON checkin_reminders (checkin_id);

-- ============================================================================
-- TABLE: documents (depends on: organizations)
-- ============================================================================

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Document metadata
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    source          document_source DEFAULT 'manual_upload',
    source_url      VARCHAR(2000),
    source_id       VARCHAR(255),

    -- Content
    content         TEXT NOT NULL,
    content_hash    VARCHAR(64),
    doc_type        document_type DEFAULT 'documentation',

    -- Processing status
    status          document_status DEFAULT 'pending',
    error_message   TEXT,
    processed_at    TIMESTAMP,

    -- File metadata
    file_name       VARCHAR(500),
    file_type       VARCHAR(50),
    file_size       INTEGER,
    storage_path    VARCHAR(500),
    storage_url     VARCHAR(2000),
    language        VARCHAR(50) DEFAULT 'en',

    -- Access control
    is_public       BOOLEAN DEFAULT FALSE,
    team_ids        JSONB DEFAULT '[]',

    -- Categorization
    tags            JSONB DEFAULT '[]',
    categories      JSONB DEFAULT '[]',

    -- Stats
    view_count      INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,

    -- Sync
    last_synced_at  TIMESTAMP,
    sync_enabled    BOOLEAN DEFAULT TRUE
);

CREATE INDEX ix_documents_id ON documents (id);
CREATE INDEX ix_documents_created_at ON documents (created_at);
CREATE INDEX ix_documents_org_id ON documents (org_id);
CREATE INDEX ix_documents_status ON documents (status);

-- ============================================================================
-- TABLE: document_chunks (depends on: documents) — uses pgvector
-- ============================================================================

CREATE TABLE document_chunks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    document_id         UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Chunk content
    content             TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL,
    start_char          INTEGER,
    end_char            INTEGER,

    -- Embedding (pgvector)
    embedding           vector(1536),
    embedding_model     VARCHAR(100),

    -- Metadata
    token_count         INTEGER,
    chunk_metadata      JSONB DEFAULT '{}'
);

CREATE INDEX ix_document_chunks_id ON document_chunks (id);
CREATE INDEX ix_document_chunks_created_at ON document_chunks (created_at);
CREATE INDEX ix_document_chunks_document_id ON document_chunks (document_id);

-- ============================================================================
-- TABLE: unblock_sessions (depends on: organizations, users, tasks, checkins)
-- ============================================================================

CREATE TABLE unblock_sessions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id                 UUID REFERENCES users(id) ON DELETE SET NULL,
    task_id                 UUID REFERENCES tasks(id) ON DELETE SET NULL,
    checkin_id              UUID REFERENCES checkins(id) ON DELETE SET NULL,

    -- Query
    query                   TEXT NOT NULL,
    blocker_type            VARCHAR(50),
    user_skill_level        VARCHAR(50) DEFAULT 'intermediate',

    -- Response
    response                TEXT,
    confidence              DOUBLE PRECISION,
    sources                 JSONB DEFAULT '[]',

    -- Escalation
    escalation_recommended  BOOLEAN DEFAULT FALSE,
    escalated               BOOLEAN DEFAULT FALSE,
    escalated_to            UUID REFERENCES users(id),

    -- Feedback
    was_helpful             BOOLEAN,
    feedback_text           TEXT,
    feedback_at             TIMESTAMP
);

CREATE INDEX ix_unblock_sessions_id ON unblock_sessions (id);
CREATE INDEX ix_unblock_sessions_created_at ON unblock_sessions (created_at);
CREATE INDEX ix_unblock_sessions_org_id ON unblock_sessions (org_id);
CREATE INDEX ix_unblock_sessions_user_id ON unblock_sessions (user_id);
CREATE INDEX ix_unblock_sessions_task_id ON unblock_sessions (task_id);

-- ============================================================================
-- TABLE: skills (depends on: organizations)
-- ============================================================================

CREATE TABLE skills (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    name                    VARCHAR(200) NOT NULL,
    description             TEXT,
    category                skill_category DEFAULT 'technical',

    -- Metadata (JSONB)
    aliases                 JSONB DEFAULT '[]',
    related_skills          JSONB DEFAULT '[]',
    prerequisites           JSONB DEFAULT '[]',

    -- Benchmarks
    org_average_level       DOUBLE PRECISION,
    industry_average_level  DOUBLE PRECISION,

    -- Status
    is_active               BOOLEAN DEFAULT TRUE
);

CREATE INDEX ix_skills_id ON skills (id);
CREATE INDEX ix_skills_created_at ON skills (created_at);
CREATE INDEX ix_skills_org_id ON skills (org_id);

-- ============================================================================
-- TABLE: user_skills (depends on: users, skills, organizations)
-- ============================================================================

CREATE TABLE user_skills (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id                UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Current assessment
    level                   DOUBLE PRECISION DEFAULT 1.0,
    confidence              DOUBLE PRECISION DEFAULT 0.5,
    trend                   skill_trend DEFAULT 'stable',

    -- Evidence
    last_demonstrated       TIMESTAMP WITH TIME ZONE,
    demonstration_count     INTEGER DEFAULT 0,
    source                  VARCHAR(50) DEFAULT 'inferred',

    -- History (JSONB)
    level_history           JSONB DEFAULT '[]',
    notes                   TEXT,

    -- Certification
    is_certified            BOOLEAN DEFAULT FALSE,
    certification_date      TIMESTAMP WITH TIME ZONE,
    certification_expiry    TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_user_skills_id ON user_skills (id);
CREATE INDEX ix_user_skills_created_at ON user_skills (created_at);
CREATE INDEX ix_user_skills_user_id ON user_skills (user_id);
CREATE INDEX ix_user_skills_skill_id ON user_skills (skill_id);
CREATE INDEX ix_user_skills_org_id ON user_skills (org_id);

-- ============================================================================
-- TABLE: skill_gaps (depends on: users, skills, organizations)
-- ============================================================================

CREATE TABLE skill_gaps (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id            UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Gap details
    gap_type            gap_type DEFAULT 'growth',
    current_level       DOUBLE PRECISION,
    required_level      DOUBLE PRECISION NOT NULL,
    gap_size            DOUBLE PRECISION NOT NULL,

    -- Context
    for_role            VARCHAR(200),
    priority            INTEGER DEFAULT 5,
    identified_at       TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Resolution
    is_resolved         BOOLEAN DEFAULT FALSE,
    resolved_at         TIMESTAMP WITH TIME ZONE,

    -- Recommendations (JSONB)
    learning_resources  JSONB DEFAULT '[]'
);

CREATE INDEX ix_skill_gaps_id ON skill_gaps (id);
CREATE INDEX ix_skill_gaps_created_at ON skill_gaps (created_at);
CREATE INDEX ix_skill_gaps_user_id ON skill_gaps (user_id);
CREATE INDEX ix_skill_gaps_skill_id ON skill_gaps (skill_id);
CREATE INDEX ix_skill_gaps_org_id ON skill_gaps (org_id);

-- ============================================================================
-- TABLE: skill_metrics (depends on: users, organizations)
-- ============================================================================

CREATE TABLE skill_metrics (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id                         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id                          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Period
    period_start                    TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end                      TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Velocity metrics
    task_completion_velocity        DOUBLE PRECISION,
    quality_score                   DOUBLE PRECISION,
    self_sufficiency_index          DOUBLE PRECISION,
    learning_velocity               DOUBLE PRECISION,

    -- Collaboration
    collaboration_score             DOUBLE PRECISION,
    help_given_count                INTEGER DEFAULT 0,
    help_received_count             INTEGER DEFAULT 0,

    -- Blocker analysis
    blockers_encountered            INTEGER DEFAULT 0,
    blockers_self_resolved          INTEGER DEFAULT 0,
    avg_blocker_resolution_hours    DOUBLE PRECISION,

    -- Peer comparison (percentile)
    velocity_percentile             DOUBLE PRECISION,
    quality_percentile              DOUBLE PRECISION,
    learning_percentile             DOUBLE PRECISION
);

CREATE INDEX ix_skill_metrics_id ON skill_metrics (id);
CREATE INDEX ix_skill_metrics_created_at ON skill_metrics (created_at);
CREATE INDEX ix_skill_metrics_user_id ON skill_metrics (user_id);
CREATE INDEX ix_skill_metrics_org_id ON skill_metrics (org_id);

-- ============================================================================
-- TABLE: learning_paths (depends on: users, organizations)
-- ============================================================================

CREATE TABLE learning_paths (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Path details
    title                   VARCHAR(500) NOT NULL,
    description             TEXT,
    target_role             VARCHAR(200),

    -- Skills to develop (JSONB)
    skills_data             JSONB DEFAULT '[]',
    milestones              JSONB DEFAULT '[]',

    -- Progress
    progress_percentage     DOUBLE PRECISION DEFAULT 0.0,
    started_at              TIMESTAMP WITH TIME ZONE,
    target_completion       TIMESTAMP WITH TIME ZONE,
    completed_at            TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active               BOOLEAN DEFAULT TRUE,
    is_ai_generated         BOOLEAN DEFAULT TRUE
);

CREATE INDEX ix_learning_paths_id ON learning_paths (id);
CREATE INDEX ix_learning_paths_created_at ON learning_paths (created_at);
CREATE INDEX ix_learning_paths_user_id ON learning_paths (user_id);
CREATE INDEX ix_learning_paths_org_id ON learning_paths (org_id);

-- ============================================================================
-- TABLE: predictions (depends on: organizations, tasks, users)
-- ============================================================================

CREATE TABLE predictions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    prediction_type     prediction_type NOT NULL,

    -- Target
    task_id             UUID REFERENCES tasks(id),
    project_id          UUID,
    user_id             UUID REFERENCES users(id),
    team_id             UUID,

    -- Prediction values
    predicted_date_p25  TIMESTAMP WITH TIME ZONE,
    predicted_date_p50  TIMESTAMP WITH TIME ZONE,
    predicted_date_p90  TIMESTAMP WITH TIME ZONE,
    confidence          DOUBLE PRECISION,
    risk_score          DOUBLE PRECISION,

    -- Factors
    risk_factors        JSONB DEFAULT '[]',
    model_version       VARCHAR(50) DEFAULT 'v1',
    features            JSONB DEFAULT '{}',

    -- Accuracy tracking
    actual_date         TIMESTAMP WITH TIME ZONE,
    accuracy_score      DOUBLE PRECISION
);

CREATE INDEX ix_predictions_id ON predictions (id);
CREATE INDEX ix_predictions_created_at ON predictions (created_at);
CREATE INDEX ix_predictions_org_id ON predictions (org_id);

-- ============================================================================
-- TABLE: velocity_snapshots (depends on: organizations)
-- ============================================================================

CREATE TABLE velocity_snapshots (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    team_id                     UUID NOT NULL,

    period_start                TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end                  TIMESTAMP WITH TIME ZONE NOT NULL,

    tasks_completed             INTEGER DEFAULT 0,
    story_points_completed      DOUBLE PRECISION DEFAULT 0,
    velocity                    DOUBLE PRECISION,
    capacity_utilization        DOUBLE PRECISION
);

CREATE INDEX ix_velocity_snapshots_id ON velocity_snapshots (id);
CREATE INDEX ix_velocity_snapshots_created_at ON velocity_snapshots (created_at);
CREATE INDEX ix_velocity_snapshots_team_id ON velocity_snapshots (team_id);

-- ============================================================================
-- TABLE: automation_patterns (depends on: organizations, users)
-- ============================================================================

CREATE TABLE automation_patterns (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Pattern details
    name                            VARCHAR(500) NOT NULL,
    description                     TEXT,
    pattern_type                    VARCHAR(100),
    status                          pattern_status DEFAULT 'detected',

    -- Detection info
    frequency_per_week              DOUBLE PRECISION,
    consistency_score               DOUBLE PRECISION,
    users_affected                  INTEGER DEFAULT 0,

    -- Savings estimate
    estimated_hours_saved_weekly    DOUBLE PRECISION,
    estimated_cost_savings_monthly  DOUBLE PRECISION,
    implementation_complexity       INTEGER DEFAULT 5,

    -- Automation details
    automation_recipe               JSONB DEFAULT '{}',
    triggers                        JSONB DEFAULT '[]',
    actions                         JSONB DEFAULT '[]',

    -- User feedback
    accepted_by                     UUID REFERENCES users(id),
    accepted_at                     TIMESTAMP WITH TIME ZONE,
    rejection_reason                TEXT
);

CREATE INDEX ix_automation_patterns_id ON automation_patterns (id);
CREATE INDEX ix_automation_patterns_created_at ON automation_patterns (created_at);
CREATE INDEX ix_automation_patterns_org_id ON automation_patterns (org_id);

-- ============================================================================
-- TABLE: ai_agents (depends on: organizations, automation_patterns, users)
-- ============================================================================

CREATE TABLE ai_agents (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pattern_id          UUID REFERENCES automation_patterns(id),

    -- Agent info
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    status              agent_status DEFAULT 'created',

    -- Configuration
    config              JSONB DEFAULT '{}',
    permissions         JSONB DEFAULT '[]',

    -- Shadow mode tracking
    shadow_started_at   TIMESTAMP WITH TIME ZONE,
    shadow_match_rate   DOUBLE PRECISION,
    shadow_runs         INTEGER DEFAULT 0,

    -- Performance
    total_runs          INTEGER DEFAULT 0,
    successful_runs     INTEGER DEFAULT 0,
    hours_saved_total   DOUBLE PRECISION DEFAULT 0,
    last_run_at         TIMESTAMP WITH TIME ZONE,
    live_started_at     TIMESTAMP WITH TIME ZONE,

    -- Ownership
    created_by          UUID NOT NULL REFERENCES users(id),
    approved_by         UUID REFERENCES users(id),
    approved_at         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_ai_agents_id ON ai_agents (id);
CREATE INDEX ix_ai_agents_created_at ON ai_agents (created_at);
CREATE INDEX ix_ai_agents_org_id ON ai_agents (org_id);

-- ============================================================================
-- TABLE: agent_runs (depends on: ai_agents, organizations)
-- ============================================================================

CREATE TABLE agent_runs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    agent_id            UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Execution
    started_at          TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at        TIMESTAMP WITH TIME ZONE,
    status              VARCHAR(50) DEFAULT 'running',
    execution_time_ms   INTEGER,

    -- Results
    input_data          JSONB DEFAULT '{}',
    output_data         JSONB DEFAULT '{}',
    error_message       TEXT,

    -- Shadow mode comparison
    is_shadow           BOOLEAN DEFAULT FALSE,
    human_action        JSONB,
    matched_human       BOOLEAN
);

CREATE INDEX ix_agent_runs_id ON agent_runs (id);
CREATE INDEX ix_agent_runs_created_at ON agent_runs (created_at);
CREATE INDEX ix_agent_runs_agent_id ON agent_runs (agent_id);

-- ============================================================================
-- TABLE: workforce_scores (depends on: users, organizations)
-- ============================================================================

CREATE TABLE workforce_scores (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    snapshot_date           TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Component scores (0-100)
    velocity_score          DOUBLE PRECISION,
    quality_score           DOUBLE PRECISION,
    self_sufficiency_score  DOUBLE PRECISION,
    learning_score          DOUBLE PRECISION,
    collaboration_score     DOUBLE PRECISION,

    -- Composite
    overall_score           DOUBLE PRECISION,
    percentile_rank         DOUBLE PRECISION,

    -- Risk indicators
    attrition_risk_score    DOUBLE PRECISION,
    burnout_risk_score      DOUBLE PRECISION,

    -- Trend
    score_trend             VARCHAR(20) DEFAULT 'stable'
);

CREATE INDEX ix_workforce_scores_id ON workforce_scores (id);
CREATE INDEX ix_workforce_scores_created_at ON workforce_scores (created_at);
CREATE INDEX ix_workforce_scores_user_id ON workforce_scores (user_id);
CREATE INDEX ix_workforce_scores_org_id ON workforce_scores (org_id);

-- ============================================================================
-- TABLE: manager_effectiveness (depends on: users, organizations)
-- ============================================================================

CREATE TABLE manager_effectiveness (
    id                                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    manager_id                          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id                              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    snapshot_date                       TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Team metrics
    team_size                           INTEGER DEFAULT 0,
    team_velocity_avg                   DOUBLE PRECISION,
    team_quality_avg                    DOUBLE PRECISION,

    -- Manager-specific
    escalation_response_time_hours      DOUBLE PRECISION,
    escalation_resolution_rate          DOUBLE PRECISION,
    team_attrition_rate                 DOUBLE PRECISION,
    team_satisfaction_score             DOUBLE PRECISION,

    -- AI comparison
    redundancy_score                    DOUBLE PRECISION,
    assignment_quality_score            DOUBLE PRECISION,
    workload_distribution_score         DOUBLE PRECISION,

    -- Ranking
    effectiveness_score                 DOUBLE PRECISION,
    org_percentile                      DOUBLE PRECISION
);

CREATE INDEX ix_manager_effectiveness_id ON manager_effectiveness (id);
CREATE INDEX ix_manager_effectiveness_created_at ON manager_effectiveness (created_at);
CREATE INDEX ix_manager_effectiveness_manager_id ON manager_effectiveness (manager_id);
CREATE INDEX ix_manager_effectiveness_org_id ON manager_effectiveness (org_id);

-- ============================================================================
-- TABLE: org_health_snapshots (depends on: organizations)
-- ============================================================================

CREATE TABLE org_health_snapshots (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    snapshot_date                   TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Health components (0-100)
    productivity_index              DOUBLE PRECISION,
    skill_coverage_index            DOUBLE PRECISION,
    management_quality_index        DOUBLE PRECISION,
    automation_maturity_index       DOUBLE PRECISION,
    delivery_predictability_index   DOUBLE PRECISION,

    -- Composite
    overall_health_score            DOUBLE PRECISION,

    -- Key metrics
    total_employees                 INTEGER DEFAULT 0,
    active_tasks                    INTEGER DEFAULT 0,
    blocked_tasks                   INTEGER DEFAULT 0,
    overdue_tasks                   INTEGER DEFAULT 0,

    -- Risk counts
    high_attrition_risk_count       INTEGER DEFAULT 0,
    high_burnout_risk_count         INTEGER DEFAULT 0
);

CREATE INDEX ix_org_health_snapshots_id ON org_health_snapshots (id);
CREATE INDEX ix_org_health_snapshots_created_at ON org_health_snapshots (created_at);
CREATE INDEX ix_org_health_snapshots_org_id ON org_health_snapshots (org_id);

-- ============================================================================
-- TABLE: restructuring_scenarios (depends on: organizations, users)
-- ============================================================================

CREATE TABLE restructuring_scenarios (
    id                                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by                          UUID NOT NULL REFERENCES users(id),

    name                                VARCHAR(500) NOT NULL,
    description                         TEXT,

    -- Scenario config
    scenario_type                       VARCHAR(100) NOT NULL,
    config                              JSONB DEFAULT '{}',

    -- Impact projections
    projected_cost_change               DOUBLE PRECISION,
    projected_productivity_change       DOUBLE PRECISION,
    projected_skill_coverage_change     DOUBLE PRECISION,
    affected_employees                  INTEGER DEFAULT 0,

    -- Risk assessment
    risk_factors                        JSONB DEFAULT '[]',
    overall_risk_score                  DOUBLE PRECISION,

    -- Status
    is_draft                            BOOLEAN DEFAULT TRUE,
    executed                            BOOLEAN DEFAULT FALSE,
    executed_at                         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_restructuring_scenarios_id ON restructuring_scenarios (id);
CREATE INDEX ix_restructuring_scenarios_created_at ON restructuring_scenarios (created_at);
CREATE INDEX ix_restructuring_scenarios_org_id ON restructuring_scenarios (org_id);

-- ============================================================================
-- TABLE: notifications (depends on: users, organizations, tasks, checkins)
-- ============================================================================

CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    notification_type   notification_type NOT NULL,
    title               VARCHAR(500) NOT NULL,
    message             TEXT,

    -- Related entities
    task_id             UUID REFERENCES tasks(id),
    checkin_id          UUID REFERENCES checkins(id),

    -- Status
    is_read             BOOLEAN DEFAULT FALSE,
    read_at             TIMESTAMP WITH TIME ZONE,

    -- Delivery
    channel             notification_channel DEFAULT 'in_app',
    delivered           BOOLEAN DEFAULT FALSE,
    delivered_at        TIMESTAMP WITH TIME ZONE,

    -- Action
    action_url          VARCHAR(1000),
    action_data         JSONB DEFAULT '{}'
);

CREATE INDEX ix_notifications_id ON notifications (id);
CREATE INDEX ix_notifications_created_at ON notifications (created_at);
CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE INDEX ix_notifications_org_id ON notifications (org_id);

-- ============================================================================
-- TABLE: notification_preferences (depends on: users, organizations)
-- ============================================================================

CREATE TABLE notification_preferences (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    user_id                     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    org_id                      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    notification_type           notification_type NOT NULL,
    channel                     notification_channel NOT NULL,

    enabled                     BOOLEAN DEFAULT TRUE,
    quiet_hours_start           INTEGER,
    quiet_hours_end             INTEGER,
    batch_frequency_minutes     INTEGER DEFAULT 0
);

CREATE INDEX ix_notification_preferences_id ON notification_preferences (id);
CREATE INDEX ix_notification_preferences_created_at ON notification_preferences (created_at);
CREATE INDEX ix_notification_preferences_user_id ON notification_preferences (user_id);

-- ============================================================================
-- TABLE: integrations (depends on: organizations, users)
-- ============================================================================

CREATE TABLE integrations (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    integration_type        integration_type NOT NULL,
    name                    VARCHAR(200) NOT NULL,
    description             TEXT,

    -- Connection
    is_active               BOOLEAN DEFAULT FALSE,
    config                  JSONB DEFAULT '{}',
    credentials             JSONB DEFAULT '{}',

    -- Sync
    sync_enabled            BOOLEAN DEFAULT TRUE,
    last_sync_at            TIMESTAMP WITH TIME ZONE,
    last_sync_status        VARCHAR(50),
    sync_error              TEXT,

    -- OAuth
    oauth_access_token      TEXT,
    oauth_refresh_token     TEXT,
    oauth_expires_at        TIMESTAMP WITH TIME ZONE,

    connected_by            UUID REFERENCES users(id),
    connected_at            TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_integrations_id ON integrations (id);
CREATE INDEX ix_integrations_created_at ON integrations (created_at);
CREATE INDEX ix_integrations_org_id ON integrations (org_id);

-- ============================================================================
-- TABLE: webhooks (depends on: organizations, users)
-- ============================================================================

CREATE TABLE webhooks (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    name                    VARCHAR(200) NOT NULL,
    url                     VARCHAR(2000) NOT NULL,
    secret                  VARCHAR(255),

    -- Events
    events                  JSONB DEFAULT '[]',

    -- Status
    is_active               BOOLEAN DEFAULT TRUE,

    -- Headers
    headers                 JSONB DEFAULT '{}',

    -- Stats
    total_deliveries        INTEGER DEFAULT 0,
    successful_deliveries   INTEGER DEFAULT 0,
    last_delivery_at        TIMESTAMP WITH TIME ZONE,
    last_delivery_status    INTEGER,

    created_by              UUID NOT NULL REFERENCES users(id)
);

CREATE INDEX ix_webhooks_id ON webhooks (id);
CREATE INDEX ix_webhooks_created_at ON webhooks (created_at);
CREATE INDEX ix_webhooks_org_id ON webhooks (org_id);

-- ============================================================================
-- TABLE: webhook_deliveries (depends on: webhooks, organizations)
-- ============================================================================

CREATE TABLE webhook_deliveries (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    webhook_id          UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    event_type          VARCHAR(100) NOT NULL,
    payload             JSONB DEFAULT '{}',

    -- Delivery
    attempted_at        TIMESTAMP WITH TIME ZONE DEFAULT now(),
    response_status     INTEGER,
    response_body       TEXT,
    response_time_ms    INTEGER,

    -- Retry
    retry_count         INTEGER DEFAULT 0,
    next_retry_at       TIMESTAMP WITH TIME ZONE,
    is_successful       BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_webhook_deliveries_id ON webhook_deliveries (id);
CREATE INDEX ix_webhook_deliveries_created_at ON webhook_deliveries (created_at);
CREATE INDEX ix_webhook_deliveries_webhook_id ON webhook_deliveries (webhook_id);

-- ============================================================================
-- TABLE: audit_logs (depends on: organizations)
-- ============================================================================

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Actor
    actor_type      actor_type NOT NULL,
    actor_id        UUID,
    actor_name      VARCHAR(200),

    -- Action
    action          audit_action NOT NULL,
    resource_type   VARCHAR(100) NOT NULL,
    resource_id     UUID,

    -- Details
    description     TEXT,
    old_value       JSONB,
    new_value       JSONB,
    audit_metadata  JSONB DEFAULT '{}',

    -- Context
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    request_id      VARCHAR(36),

    -- Timestamp (immutable record)
    timestamp       TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX ix_audit_logs_id ON audit_logs (id);
CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX ix_audit_logs_org_id ON audit_logs (org_id);
CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);

-- ============================================================================
-- TABLE: gdpr_requests (depends on: organizations, users)
-- ============================================================================

CREATE TABLE gdpr_requests (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id),

    request_type        VARCHAR(50) NOT NULL,
    status              VARCHAR(50) DEFAULT 'pending',

    -- Processing
    requested_at        TIMESTAMP WITH TIME ZONE DEFAULT now(),
    processed_at        TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    processed_by        UUID REFERENCES users(id),

    -- Result
    result_url          VARCHAR(2000),
    result_expiry       TIMESTAMP WITH TIME ZONE,
    error_message       TEXT,

    -- Verification
    verification_token  VARCHAR(255),
    verified_at         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_gdpr_requests_id ON gdpr_requests (id);
CREATE INDEX ix_gdpr_requests_created_at ON gdpr_requests (created_at);
CREATE INDEX ix_gdpr_requests_org_id ON gdpr_requests (org_id);
CREATE INDEX ix_gdpr_requests_user_id ON gdpr_requests (user_id);

-- ============================================================================
-- TABLE: api_keys (depends on: organizations, users)
-- ============================================================================

CREATE TABLE api_keys (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id),

    name                VARCHAR(200) NOT NULL,
    key_hash            VARCHAR(255) NOT NULL,
    key_prefix          VARCHAR(10) NOT NULL,

    -- Permissions
    scopes              JSONB DEFAULT '[]',
    is_full_access      BOOLEAN DEFAULT FALSE,

    -- Status
    is_active           BOOLEAN DEFAULT TRUE,
    expires_at          TIMESTAMP WITH TIME ZONE,

    -- Usage
    last_used_at        TIMESTAMP WITH TIME ZONE,
    last_used_ip        VARCHAR(45),
    usage_count         INTEGER DEFAULT 0,

    -- Limits
    rate_limit          INTEGER DEFAULT 1000,
    current_usage       INTEGER DEFAULT 0,
    usage_reset_at      TIMESTAMP WITH TIME ZONE,

    created_by          UUID NOT NULL REFERENCES users(id)
);

CREATE INDEX ix_api_keys_id ON api_keys (id);
CREATE INDEX ix_api_keys_created_at ON api_keys (created_at);
CREATE INDEX ix_api_keys_org_id ON api_keys (org_id);

-- ============================================================================
-- TABLE: system_health (no foreign key dependencies)
-- ============================================================================

CREATE TABLE system_health (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    snapshot_time           TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Database
    db_connections_active   INTEGER,
    db_query_avg_ms         DOUBLE PRECISION,

    -- API
    api_requests_per_minute INTEGER,
    api_error_rate          DOUBLE PRECISION,
    api_latency_p50_ms      DOUBLE PRECISION,
    api_latency_p99_ms      DOUBLE PRECISION,

    -- AI
    ai_requests_per_hour    INTEGER,
    ai_avg_latency_ms       DOUBLE PRECISION,
    ai_cache_hit_rate       DOUBLE PRECISION,

    -- Background jobs
    jobs_pending            INTEGER,
    jobs_failed             INTEGER,

    -- Storage
    storage_used_mb         DOUBLE PRECISION,

    -- Alerts
    active_alerts           JSONB DEFAULT '[]'
);

CREATE INDEX ix_system_health_id ON system_health (id);
CREATE INDEX ix_system_health_created_at ON system_health (created_at);
CREATE INDEX ix_system_health_snapshot_time ON system_health (snapshot_time);

-- ============================================================================
-- TABLE: agents (Phase 15 - Agent Orchestration) (depends on: organizations)
-- ============================================================================

CREATE TABLE agents (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id              UUID NOT NULL REFERENCES organizations(id),

    -- Identity
    name                VARCHAR(100) NOT NULL UNIQUE,
    display_name        VARCHAR(200) NOT NULL,
    description         TEXT,
    version             VARCHAR(20) DEFAULT '1.0.0',

    -- Classification
    agent_type          agent_type_enum NOT NULL DEFAULT 'ai',
    capabilities        JSONB DEFAULT '[]',

    -- Status
    status              agent_status_db DEFAULT 'active',
    is_enabled          BOOLEAN DEFAULT TRUE,

    -- Configuration
    config              JSONB DEFAULT '{}',
    permissions         JSONB DEFAULT '[]',

    -- Metrics
    execution_count     INTEGER DEFAULT 0,
    success_count       INTEGER DEFAULT 0,
    error_count         INTEGER DEFAULT 0,
    avg_duration_ms     DOUBLE PRECISION,
    last_execution_at   TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_agents_id ON agents (id);
CREATE INDEX ix_agents_created_at ON agents (created_at);
CREATE INDEX ix_agents_org_id ON agents (org_id);

-- ============================================================================
-- TABLE: agent_executions (depends on: agents, organizations, users, tasks)
-- ============================================================================

CREATE TABLE agent_executions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    agent_id                UUID NOT NULL REFERENCES agents(id),
    org_id                  UUID NOT NULL REFERENCES organizations(id),

    -- Trigger information
    event_type              VARCHAR(100) NOT NULL,
    event_id                UUID,
    trigger_source          VARCHAR(100),

    -- Context
    user_id                 UUID REFERENCES users(id),
    task_id                 UUID REFERENCES tasks(id),
    context_data            JSONB DEFAULT '{}',

    -- Execution details
    status                  execution_status DEFAULT 'pending',
    started_at              TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at            TIMESTAMP WITH TIME ZONE,
    duration_ms             INTEGER,

    -- Results
    success                 BOOLEAN DEFAULT FALSE,
    output_data             JSONB DEFAULT '{}',
    error_message           TEXT,
    error_code              VARCHAR(50),

    -- Metrics
    tokens_used             INTEGER DEFAULT 0,
    api_calls               INTEGER DEFAULT 0,

    -- Chain information
    parent_execution_id     UUID REFERENCES agent_executions(id),
    chain_depth             INTEGER DEFAULT 0
);

CREATE INDEX ix_agent_executions_id ON agent_executions (id);
CREATE INDEX ix_agent_executions_created_at ON agent_executions (created_at);
CREATE INDEX ix_agent_executions_agent_id ON agent_executions (agent_id);
CREATE INDEX ix_agent_executions_org_id ON agent_executions (org_id);

-- ============================================================================
-- TABLE: agent_conversations (depends on: organizations, users)
-- ============================================================================

CREATE TABLE agent_conversations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    org_id              UUID NOT NULL REFERENCES organizations(id),
    user_id             UUID NOT NULL REFERENCES users(id),

    -- Conversation metadata
    title               VARCHAR(200),
    agent_name          VARCHAR(100) NOT NULL DEFAULT 'chat_agent',

    -- State
    is_active           BOOLEAN DEFAULT TRUE,
    message_count       INTEGER DEFAULT 0,

    -- Conversation data
    messages            JSONB DEFAULT '[]',
    context_data        JSONB DEFAULT '{}',

    -- Timestamps
    started_at          TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_message_at     TIMESTAMP WITH TIME ZONE DEFAULT now(),
    ended_at            TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_agent_conversations_id ON agent_conversations (id);
CREATE INDEX ix_agent_conversations_created_at ON agent_conversations (created_at);
CREATE INDEX ix_agent_conversations_org_id ON agent_conversations (org_id);
CREATE INDEX ix_agent_conversations_user_id ON agent_conversations (user_id);

-- ============================================================================
-- TABLE: agent_schedules (depends on: agents, organizations)
-- ============================================================================

CREATE TABLE agent_schedules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    agent_id            UUID NOT NULL REFERENCES agents(id),
    org_id              UUID NOT NULL REFERENCES organizations(id),

    -- Schedule definition
    name                VARCHAR(100) NOT NULL,
    cron_expression     VARCHAR(100) NOT NULL,
    timezone            VARCHAR(50) DEFAULT 'UTC',

    -- Configuration
    is_enabled          BOOLEAN DEFAULT TRUE,
    config              JSONB DEFAULT '{}',

    -- Tracking
    last_run_at         TIMESTAMP WITH TIME ZONE,
    next_run_at         TIMESTAMP WITH TIME ZONE,
    run_count           INTEGER DEFAULT 0,
    failure_count       INTEGER DEFAULT 0
);

CREATE INDEX ix_agent_schedules_id ON agent_schedules (id);
CREATE INDEX ix_agent_schedules_created_at ON agent_schedules (created_at);
CREATE INDEX ix_agent_schedules_agent_id ON agent_schedules (agent_id);
CREATE INDEX ix_agent_schedules_org_id ON agent_schedules (org_id);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
