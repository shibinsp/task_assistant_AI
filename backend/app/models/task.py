"""
TaskPulse - AI Assistant - Task Model
Task management with subtasks, dependencies, and AI scoring
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional, List

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Task status workflow states."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    ARCHIVED = "archived"


class TaskPriority(str, enum.Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BlockerType(str, enum.Enum):
    """Types of blockers for tasks."""
    LOGIC = "logic"
    TOOL = "tool"
    DEPENDENCY = "dependency"
    BUG = "bug"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.ARCHIVED],
    TaskStatus.IN_PROGRESS: [TaskStatus.BLOCKED, TaskStatus.REVIEW, TaskStatus.DONE, TaskStatus.TODO],
    TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.TODO],
    TaskStatus.REVIEW: [TaskStatus.DONE, TaskStatus.IN_PROGRESS],
    TaskStatus.DONE: [TaskStatus.ARCHIVED, TaskStatus.IN_PROGRESS],
    TaskStatus.ARCHIVED: [TaskStatus.TODO],
}


class Task(Base):
    """
    Main task model with AI-enhanced features.
    Tasks can have subtasks and dependencies.
    """

    __tablename__ = "tasks"

    # Organization
    org_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)

    # Status and priority
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.TODO,
        nullable=False,
        index=True
    )
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False
    )

    # Assignment
    assigned_to = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )

    # Team/project grouping
    team_id = Column(String(36), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)

    # Time tracking
    deadline = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # AI-generated scores
    risk_score = Column(Float, nullable=True)  # 0.00 - 1.00
    confidence_score = Column(Float, nullable=True)  # 0.00 - 1.00
    complexity_score = Column(Float, nullable=True)  # 0.00 - 1.00

    # Blocker info
    blocker_type = Column(Enum(BlockerType), nullable=True)
    blocker_description = Column(Text, nullable=True)

    # Metadata stored as JSON string
    tools_json = Column(Text, default="[]")  # Tools involved
    tags_json = Column(Text, default="[]")  # Custom tags
    skills_required_json = Column(Text, default="[]")  # Required skills

    # Parent task (for subtasks)
    parent_task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Ordering
    sort_order = Column(Integer, default=0)

    # Relationships
    organization = relationship("Organization", backref="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to], backref="assigned_tasks")
    creator = relationship("User", foreign_keys=[created_by], backref="created_tasks")
    parent_task = relationship(
        "Task",
        remote_side="Task.id",
        foreign_keys=[parent_task_id],
        backref="subtasks"
    )
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        backref="task",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title[:30]}..., status={self.status})>"

    # JSON property helpers
    @property
    def tools(self) -> List[str]:
        import json
        try:
            return json.loads(self.tools_json or "[]")
        except json.JSONDecodeError:
            return []

    @tools.setter
    def tools(self, value: List[str]) -> None:
        import json
        self.tools_json = json.dumps(value)

    @property
    def tags(self) -> List[str]:
        import json
        try:
            return json.loads(self.tags_json or "[]")
        except json.JSONDecodeError:
            return []

    @tags.setter
    def tags(self, value: List[str]) -> None:
        import json
        self.tags_json = json.dumps(value)

    @property
    def skills_required(self) -> List[str]:
        import json
        try:
            return json.loads(self.skills_required_json or "[]")
        except json.JSONDecodeError:
            return []

    @skills_required.setter
    def skills_required(self, value: List[str]) -> None:
        import json
        self.skills_required_json = json.dumps(value)

    @property
    def is_subtask(self) -> bool:
        return self.parent_task_id is not None

    @property
    def is_blocked(self) -> bool:
        return self.status == TaskStatus.BLOCKED

    @property
    def is_completed(self) -> bool:
        return self.status in (TaskStatus.DONE, TaskStatus.ARCHIVED)

    @property
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline and not self.is_completed

    @property
    def progress_percentage(self) -> float:
        """Calculate progress based on subtasks or time."""
        from sqlalchemy.orm import attributes
        state = attributes.instance_state(self)
        # Only access subtasks if already loaded (avoid lazy-load in async)
        if 'subtasks' in state.dict:
            subtasks = self.subtasks
            if subtasks:
                total = len(subtasks)
                completed = sum(1 for st in subtasks if st.is_completed)
                return round((completed / total) * 100, 1)
        if self.estimated_hours and self.actual_hours:
            return min(100.0, round((self.actual_hours / self.estimated_hours) * 100, 1))
        return 0.0

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = VALID_STATUS_TRANSITIONS.get(self.status, [])
        return new_status in valid_transitions

    def transition_to(self, new_status: TaskStatus) -> bool:
        """Transition to a new status if valid."""
        if not self.can_transition_to(new_status):
            return False

        old_status = self.status
        self.status = new_status

        # Update timestamps
        if new_status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.utcnow()
        elif new_status == TaskStatus.DONE:
            self.completed_at = datetime.utcnow()

        # Clear blocker info when unblocked
        if old_status == TaskStatus.BLOCKED and new_status != TaskStatus.BLOCKED:
            self.blocker_type = None
            self.blocker_description = None

        return True


class TaskDependency(Base):
    """
    Task dependency tracking.
    Defines blocking relationships between tasks.
    """

    __tablename__ = "task_dependencies"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    depends_on_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Dependency type
    is_blocking = Column(Boolean, default=True)  # If true, blocks task until dependency is done
    description = Column(String(500), nullable=True)

    # Relationship to dependent task
    depends_on = relationship("Task", foreign_keys=[depends_on_id])

    def __repr__(self) -> str:
        return f"<TaskDependency(task={self.task_id}, depends_on={self.depends_on_id})>"


class TaskHistory(Base):
    """
    Task change history for audit trail.
    """

    __tablename__ = "task_history"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Change details
    action = Column(String(50), nullable=False)  # created, updated, status_changed, assigned, etc.
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    details_json = Column(Text, default="{}")

    # Relationships
    task = relationship("Task", backref="history")
    user = relationship("User", backref="task_changes")

    @property
    def details(self) -> dict:
        import json
        try:
            return json.loads(self.details_json or "{}")
        except json.JSONDecodeError:
            return {}

    @details.setter
    def details(self, value: dict) -> None:
        import json
        self.details_json = json.dumps(value)


class TaskComment(Base):
    """
    Comments on tasks for collaboration.
    """

    __tablename__ = "task_comments"

    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    content = Column(Text, nullable=False)
    is_ai_generated = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)

    # Relationships
    task = relationship("Task", backref="comments")
    user = relationship("User", backref="task_comments")
