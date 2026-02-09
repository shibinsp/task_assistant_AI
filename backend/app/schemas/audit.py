"""
TaskPulse - AI Assistant - Audit Schemas
Pydantic schemas for audit logs, GDPR, API keys, and system health
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.audit import ActorType, AuditAction


# ==================== Audit Log Schemas ====================

class AuditLogResponse(BaseModel):
    """Schema for audit log in API responses."""
    id: str
    org_id: str

    # Actor
    actor_type: ActorType
    actor_id: str
    actor_email: Optional[str] = None
    actor_ip: Optional[str] = None

    # Action
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None

    # Details
    details: Dict[str, Any] = Field(default_factory=dict)
    changes: Dict[str, Any] = Field(default_factory=dict)

    # Context
    request_id: Optional[str] = None
    user_agent: Optional[str] = None

    # Status
    success: bool = True
    error_message: Optional[str] = None

    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Response for list of audit logs."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogFilterRequest(BaseModel):
    """Request for filtering audit logs."""
    actor_type: Optional[ActorType] = None
    actor_id: Optional[str] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None


class AuditLogSummaryResponse(BaseModel):
    """Summary of audit logs."""
    total_events: int
    by_action: Dict[str, int] = Field(default_factory=dict)
    by_actor_type: Dict[str, int] = Field(default_factory=dict)
    by_resource_type: Dict[str, int] = Field(default_factory=dict)
    failed_events: int = 0
    period_start: datetime
    period_end: datetime


# ==================== GDPR Request Schemas ====================

class GDPRRequestCreate(BaseModel):
    """Schema for creating a GDPR request."""
    request_type: str = Field(..., description="Type: data_export, data_deletion, data_rectification")
    user_id: Optional[str] = Field(None, description="User ID (admin can specify)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for request")


class GDPRRequestResponse(BaseModel):
    """Schema for GDPR request in API responses."""
    id: str
    org_id: str
    user_id: str

    # Request details
    request_type: str
    reason: Optional[str] = None

    # Status
    status: str = Field(..., description="Status: pending, processing, completed, rejected")

    # Processing
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Results
    data_url: Optional[str] = None  # For data export
    expires_at: Optional[datetime] = None  # For data export URL

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GDPRRequestListResponse(BaseModel):
    """Response for list of GDPR requests."""
    requests: List[GDPRRequestResponse]
    total: int
    pending_count: int = 0
    page: int
    page_size: int


class GDPRRequestProcessRequest(BaseModel):
    """Request to process a GDPR request."""
    action: str = Field(..., description="Action: approve, reject")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")


# ==================== API Key Schemas ====================

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    scopes: List[str] = Field(default_factory=list, description="Permission scopes")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days")


class APIKeyResponse(BaseModel):
    """Schema for API key in API responses."""
    id: str
    org_id: str
    user_id: str

    # Key info (key itself only shown on creation)
    name: str
    description: Optional[str] = None
    key_prefix: str = Field(..., description="First 8 characters of the key")

    # Permissions
    scopes: List[str] = Field(default_factory=list)

    # Status
    is_active: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0

    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreateResponse(APIKeyResponse):
    """Response for API key creation (includes full key)."""
    key: str = Field(..., description="Full API key (only shown once)")


class APIKeyListResponse(BaseModel):
    """Response for list of API keys."""
    keys: List[APIKeyResponse]
    total: int


class APIKeyRevokeRequest(BaseModel):
    """Request to revoke an API key."""
    key_id: str = Field(..., description="API key ID to revoke")
    reason: Optional[str] = Field(None, description="Reason for revocation")


# ==================== System Health Schemas ====================

class ServiceHealth(BaseModel):
    """Health status of a service."""
    name: str
    status: str = Field(..., description="Status: healthy, degraded, unhealthy")
    response_time_ms: Optional[int] = None
    last_check: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    """Schema for system health in API responses."""
    id: str
    org_id: Optional[str] = None

    # Overall status
    status: str = Field(..., description="Status: healthy, degraded, unhealthy")
    uptime_seconds: int = 0
    uptime_percentage: float = Field(ge=0, le=100)

    # Services
    services: List[ServiceHealth] = Field(default_factory=list)

    # Metrics
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_usage: Optional[float] = Field(None, ge=0, le=100)
    disk_usage: Optional[float] = Field(None, ge=0, le=100)

    # Database
    db_connections_active: Optional[int] = None
    db_connections_idle: Optional[int] = None

    # Queue
    queue_size: Optional[int] = None
    queue_processing_rate: Optional[float] = None

    # Timestamps
    checked_at: datetime

    model_config = {"from_attributes": True}


class SystemHealthHistoryResponse(BaseModel):
    """Response for system health history."""
    snapshots: List[SystemHealthResponse]
    average_uptime: float
    incidents: int = 0
    period_start: datetime
    period_end: datetime


# ==================== AI Governance Schemas ====================

class AIGovernanceMetrics(BaseModel):
    """AI governance metrics."""
    total_ai_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_response_time_ms: float = 0.0

    # Usage by feature
    usage_by_feature: Dict[str, int] = Field(default_factory=dict)

    # Consent tracking
    users_with_ai_consent: int = 0
    total_users: int = 0
    consent_rate: float = Field(ge=0, le=1)

    # Cost
    estimated_cost: float = 0.0


class AIGovernanceDashboardResponse(BaseModel):
    """Response for AI governance dashboard."""
    # Metrics
    metrics: AIGovernanceMetrics

    # This period
    this_week: AIGovernanceMetrics
    this_month: AIGovernanceMetrics

    # Trends
    call_trend: List[Dict[str, Any]] = Field(default_factory=list)
    cost_trend: List[Dict[str, Any]] = Field(default_factory=list)

    # Compliance
    compliance_status: str = Field(..., description="Status: compliant, review_needed, non_compliant")
    compliance_issues: List[str] = Field(default_factory=list)

    generated_at: datetime


# ==================== Compliance Report Schemas ====================

class ComplianceReportRequest(BaseModel):
    """Request for compliance report generation."""
    report_type: str = Field(..., description="Type: gdpr, soc2, hipaa, general")
    period_start: datetime
    period_end: datetime
    include_details: bool = Field(default=True)


class ComplianceReportResponse(BaseModel):
    """Response for compliance report."""
    id: str
    org_id: str

    # Report info
    report_type: str
    period_start: datetime
    period_end: datetime

    # Summary
    compliance_score: float = Field(ge=0, le=100)
    status: str = Field(..., description="Status: compliant, partially_compliant, non_compliant")

    # Findings
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0

    # Details
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    generated_at: datetime
