"""
TaskPulse - AI Assistant - Task Schemas
Pydantic schemas for task management
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.task import TaskStatus, TaskPriority, BlockerType


# ==================== Base Schemas ====================

class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    goal: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    team_id: Optional[str] = None
    project_id: Optional[str] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    assigned_to: Optional[str] = None
    parent_task_id: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    skills_required: List[str] = Field(default_factory=list)
    is_draft: bool = False

    @field_validator('tools', 'tags', 'skills_required', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        return v


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    goal: Optional[str] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    assigned_to: Optional[str] = None
    tools: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_draft: Optional[bool] = None


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""
    status: TaskStatus
    blocker_type: Optional[BlockerType] = None
    blocker_description: Optional[str] = None

    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        """Accept common aliases for task statuses."""
        if isinstance(v, str):
            aliases = {
                "completed": "done",
                "complete": "done",
                "in-progress": "in_progress",
                "inprogress": "in_progress",
            }
            v = aliases.get(v.lower(), v)
        return v

    @field_validator('blocker_type', mode='before')
    @classmethod
    def normalize_blocker_type(cls, v):
        """Accept common aliases for blocker types."""
        if isinstance(v, str):
            aliases = {
                "external_dependency": "dependency",
                "external": "dependency",
            }
            v = aliases.get(v.lower(), v)
        return v

    @field_validator('blocker_description')
    @classmethod
    def validate_blocker_description(cls, v, info):
        return v


# ==================== Response Schemas ====================

class TaskResponse(BaseModel):
    """Task response schema."""
    id: str
    org_id: str
    title: str
    description: Optional[str]
    goal: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assigned_to: Optional[str]
    created_by: str
    team_id: Optional[str]
    project_id: Optional[str]
    deadline: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    risk_score: Optional[float]
    confidence_score: Optional[float]
    complexity_score: Optional[float]
    blocker_type: Optional[BlockerType]
    blocker_description: Optional[str]
    tools: List[str]
    tags: List[str]
    skills_required: List[str]
    parent_task_id: Optional[str]
    sort_order: int
    is_draft: bool
    is_subtask: bool
    is_blocked: bool
    is_completed: bool
    is_overdue: bool
    progress_percentage: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    """Detailed task response with relationships."""
    subtask_count: int = 0
    completed_subtask_count: int = 0
    dependency_count: int = 0
    comment_count: int = 0
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None


class TaskListResponse(BaseModel):
    """Paginated task list response."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


# ==================== Subtask Schemas ====================

class SubtaskCreate(BaseModel):
    """Schema for creating a subtask."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: Optional[float] = Field(None, ge=0)
    assigned_to: Optional[str] = None
    sort_order: Optional[int] = 0


class SubtaskUpdate(BaseModel):
    """Schema for updating a subtask."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    assigned_to: Optional[str] = None
    sort_order: Optional[int] = None


# ==================== Dependency Schemas ====================

class DependencyCreate(BaseModel):
    """Schema for creating a task dependency."""
    depends_on_id: str
    is_blocking: bool = True
    description: Optional[str] = Field(None, max_length=500)


class DependencyResponse(BaseModel):
    """Task dependency response."""
    id: str
    task_id: str
    depends_on_id: str
    is_blocking: bool
    description: Optional[str]
    depends_on_title: Optional[str] = None
    depends_on_status: Optional[TaskStatus] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== History Schemas ====================

class TaskHistoryResponse(BaseModel):
    """Task history entry response."""
    id: str
    task_id: str
    user_id: Optional[str]
    action: str
    field_name: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    details: dict
    user_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Comment Schemas ====================

class CommentCreate(BaseModel):
    """Schema for creating a task comment."""
    content: str = Field(..., min_length=1)


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1)


class CommentResponse(BaseModel):
    """Task comment response."""
    id: str
    task_id: str
    user_id: Optional[str]
    content: str
    is_ai_generated: bool
    is_edited: bool
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Bulk Operation Schemas ====================

class BulkTaskUpdate(BaseModel):
    """Schema for bulk task updates."""
    task_ids: List[str] = Field(..., min_length=1)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    team_id: Optional[str] = None
    project_id: Optional[str] = None


class BulkOperationResult(BaseModel):
    """Result of bulk operation."""
    total: int
    successful: int
    failed: int
    errors: List[dict] = Field(default_factory=list)


# ==================== AI Decomposition Schemas ====================

class TaskDecompositionRequest(BaseModel):
    """Request to decompose a task using AI."""
    max_subtasks: int = Field(default=10, ge=1, le=20)
    include_time_estimates: bool = True
    include_skill_requirements: bool = True


class SubtaskSuggestion(BaseModel):
    """AI-suggested subtask."""
    title: str
    description: str
    estimated_hours: Optional[float]
    skills_required: List[str]
    order: int


class TaskDecompositionResponse(BaseModel):
    """Response from AI task decomposition."""
    task_id: str
    suggested_subtasks: List[SubtaskSuggestion]
    total_estimated_hours: float
    complexity_score: float
    risk_factors: List[str]
    recommendations: List[str]
