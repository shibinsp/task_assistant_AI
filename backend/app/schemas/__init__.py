"""
TaskPulse - AI Assistant - Pydantic Schemas
Request/Response schemas for API validation
"""

# Common response schemas
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List
from datetime import datetime

T = TypeVar("T")


class ResponseBase(BaseModel):
    """Base response schema with common fields."""
    success: bool = True
    message: Optional[str] = None


class PaginatedResponse(ResponseBase, Generic[T]):
    """Paginated response schema."""
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: str
    message: str
    details: dict = {}
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: ErrorDetail


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: datetime


# Schemas imported by module
# User schemas
from app.schemas.user import (
    UserRegister, UserLogin, UserCreate, UserUpdate, UserAdminUpdate,
    TokenResponse, TokenRefresh, PasswordReset, PasswordResetConfirm,
    UserResponse, UserDetailResponse, UserListResponse, CurrentUserResponse,
    ConsentUpdate, ConsentResponse, SessionResponse, SessionListResponse,
)

# Notification schemas
from app.schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationResponse, NotificationListResponse,
    NotificationPreferenceUpdate, NotificationPreferenceResponse,
    WebhookCreate, WebhookUpdate, WebhookResponse, WebhookListResponse,
    WebhookDeliveryResponse,
)

# Prediction schemas
from app.schemas.prediction import (
    TaskPredictionRequest, TaskPredictionResponse,
    PredictionResponse, PredictionListResponse,
    VelocitySnapshotResponse, VelocityTrendResponse,
    HiringPredictionRequest, HiringPredictionResponse,
)

# Automation schemas
from app.schemas.automation import (
    AutomationPatternResponse, PatternListResponse,
    AIAgentCreate, AIAgentUpdate, AIAgentResponse, AIAgentListResponse,
    AgentRunResponse, AgentRunListResponse,
    ShadowReportResponse, ROIDashboardResponse,
)

# Workforce schemas
from app.schemas.workforce import (
    WorkforceScoreResponse, WorkforceScoreListResponse,
    AttritionRiskResponse, BurnoutRiskResponse,
    ManagerEffectivenessResponse,
    OrgHealthSnapshotResponse,
    RestructuringScenarioRequest, RestructuringScenarioResponse,
    HiringPlanResponse,
)

# Audit schemas
from app.schemas.audit import (
    AuditLogResponse, AuditLogListResponse,
    GDPRRequestCreate, GDPRRequestResponse, GDPRRequestListResponse,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, APIKeyListResponse,
    SystemHealthResponse, AIGovernanceDashboardResponse,
)

# Agent schemas
from app.schemas.agent import (
    AgentResponse, AgentDetailResponse, AgentListResponse, AgentStatsResponse,
    AgentConfigUpdate, ExecuteAgentRequest,
    AgentExecutionResponse, ExecutionListResponse,
    AgentConversationResponse, ConversationListResponse,
    SendMessageRequest, ChatMessageResponse,
    OrchestrationRequest, OrchestrationResponse,
    AgentScheduleCreate, AgentScheduleUpdate, AgentScheduleResponse,
    RecommendationsResponse,
)
