"""
TaskPulse - AI Assistant - Skill Schemas
Pydantic schemas for skill management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.skill import SkillCategory, SkillTrend, GapType


# ==================== Skill Catalog ====================

class SkillBase(BaseModel):
    """Base skill schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: SkillCategory = SkillCategory.TECHNICAL
    aliases: List[str] = Field(default_factory=list)
    related_skills: List[str] = Field(default_factory=list)


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[SkillCategory] = None
    aliases: Optional[List[str]] = None
    related_skills: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SkillResponse(BaseModel):
    """Skill response schema."""
    id: str
    org_id: str
    name: str
    description: Optional[str]
    category: SkillCategory
    aliases: List[str]
    related_skills: List[str]
    org_average_level: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """Paginated skill list."""
    skills: List[SkillResponse]
    total: int
    page: int
    page_size: int


# ==================== User Skills ====================

class UserSkillBase(BaseModel):
    """Base user skill schema."""
    skill_id: str
    level: float = Field(default=1.0, ge=1.0, le=10.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = "self_reported"
    notes: Optional[str] = None


class UserSkillCreate(UserSkillBase):
    """Schema for adding a skill to user."""
    pass


class UserSkillUpdate(BaseModel):
    """Schema for updating user skill."""
    level: Optional[float] = Field(None, ge=1.0, le=10.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    is_certified: Optional[bool] = None
    certification_date: Optional[datetime] = None
    certification_expiry: Optional[datetime] = None


class UserSkillResponse(BaseModel):
    """User skill response."""
    id: str
    user_id: str
    skill_id: str
    skill_name: Optional[str] = None
    skill_category: Optional[SkillCategory] = None
    level: float
    confidence: float
    trend: SkillTrend
    last_demonstrated: Optional[datetime]
    demonstration_count: int
    source: str
    is_certified: bool
    level_history: List[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Skill Graph ====================

class SkillGraphNode(BaseModel):
    """Node in the skill graph."""
    skill_id: str
    skill_name: str
    category: SkillCategory
    level: float
    trend: SkillTrend
    confidence: float


class SkillGraphEdge(BaseModel):
    """Edge connecting related skills."""
    from_skill: str
    to_skill: str
    relationship: str  # prerequisite, related, etc.


class SkillGraphResponse(BaseModel):
    """User's skill graph."""
    user_id: str
    nodes: List[SkillGraphNode]
    edges: List[SkillGraphEdge]
    total_skills: int
    average_level: float
    strongest_category: Optional[SkillCategory]


# ==================== Skill Velocity ====================

class SkillVelocityResponse(BaseModel):
    """User's skill velocity metrics."""
    user_id: str
    period_days: int
    task_completion_velocity: Optional[float]
    quality_score: Optional[float]
    self_sufficiency_index: Optional[float]
    learning_velocity: Optional[float]
    skills_improved: int
    skills_demonstrated: int
    velocity_percentile: Optional[float]
    quality_percentile: Optional[float]


# ==================== Team Composition ====================

class TeamSkillSummary(BaseModel):
    """Skill summary for a team."""
    skill_id: str
    skill_name: str
    category: SkillCategory
    team_average_level: float
    coverage: float  # % of team with this skill
    experts: int  # Members with level >= 7
    novices: int  # Members with level <= 3


class TeamSkillComposition(BaseModel):
    """Team's skill composition."""
    team_id: str
    total_members: int
    skills: List[TeamSkillSummary]
    strongest_skills: List[str]
    weakest_skills: List[str]
    skill_coverage: float  # Overall coverage %


# ==================== Skill Gaps ====================

class SkillGapResponse(BaseModel):
    """Identified skill gap."""
    id: str
    user_id: str
    skill_id: str
    skill_name: Optional[str] = None
    gap_type: GapType
    current_level: Optional[float]
    required_level: float
    gap_size: float
    for_role: Optional[str]
    priority: int
    learning_resources: List[dict]
    is_resolved: bool
    identified_at: datetime

    class Config:
        from_attributes = True


class SkillGapSummary(BaseModel):
    """Summary of skill gaps."""
    user_id: str
    total_gaps: int
    critical_gaps: int
    growth_gaps: int
    stretch_gaps: int
    gaps: List[SkillGapResponse]


# ==================== Learning Path ====================

class LearningMilestone(BaseModel):
    """Milestone in learning path."""
    title: str
    description: Optional[str]
    skill_id: Optional[str]
    target_level: Optional[float]
    completed: bool = False
    completed_at: Optional[datetime] = None


class LearningPathCreate(BaseModel):
    """Schema for creating learning path."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    target_role: Optional[str] = None
    skills: List[dict] = Field(default_factory=list)
    target_completion: Optional[datetime] = None


class LearningPathResponse(BaseModel):
    """Learning path response."""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    target_role: Optional[str]
    skills: List[dict]
    milestones: List[dict]
    progress_percentage: float
    started_at: Optional[datetime]
    target_completion: Optional[datetime]
    completed_at: Optional[datetime]
    is_active: bool
    is_ai_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Self-Sufficiency ====================

class SelfSufficiencyMetrics(BaseModel):
    """Self-sufficiency metrics for a user."""
    user_id: str
    overall_score: float  # 0-1
    by_skill_category: dict  # category -> score
    blockers_self_resolved: int
    blockers_total: int
    help_requests_trend: str  # increasing, stable, decreasing
    improvement_areas: List[str]


# ==================== Peer Benchmarking ====================

class PeerBenchmark(BaseModel):
    """Anonymized peer benchmarking."""
    skill_id: str
    skill_name: str
    user_level: float
    peer_average: float
    peer_percentile: float  # User's percentile among peers
    top_10_percent_level: float
    peers_count: int
