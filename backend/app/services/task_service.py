"""
TaskPulse - AI Assistant - Task Service
Business logic for task management
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import (
    Task, TaskDependency, TaskHistory, TaskComment,
    TaskStatus, TaskPriority, BlockerType, VALID_STATUS_TRANSITIONS
)
from app.models.user import User
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskStatusUpdate,
    SubtaskCreate, SubtaskUpdate, DependencyCreate,
    CommentCreate, CommentUpdate, BulkTaskUpdate
)
from app.utils.helpers import generate_uuid
from app.core.exceptions import (
    NotFoundException, ValidationException, ForbiddenException
)


class TaskService:
    """Service class for task operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Task CRUD ====================

    async def create_task(
        self,
        task_data: TaskCreate,
        org_id: str,
        created_by: str
    ) -> Task:
        """Create a new task."""
        # Validate parent task if provided
        if task_data.parent_task_id:
            parent = await self.get_task_by_id(task_data.parent_task_id, org_id)
            if not parent:
                raise NotFoundException("Parent task", task_data.parent_task_id)

        # Create task
        task = Task(
            id=generate_uuid(),
            org_id=org_id,
            title=task_data.title,
            description=task_data.description,
            goal=task_data.goal,
            priority=task_data.priority,
            deadline=task_data.deadline,
            estimated_hours=task_data.estimated_hours,
            team_id=task_data.team_id,
            project_id=task_data.project_id,
            assigned_to=task_data.assigned_to,
            created_by=created_by,
            parent_task_id=task_data.parent_task_id,
            is_draft=task_data.is_draft,
        )

        # Set JSON fields
        task.tools = task_data.tools
        task.tags = task_data.tags
        task.skills_required = task_data.skills_required

        self.db.add(task)
        await self.db.flush()

        # Create history entry
        await self._create_history(task.id, created_by, "created")

        await self.db.refresh(task)
        return task

    async def get_task_by_id(
        self,
        task_id: str,
        org_id: str,
        include_subtasks: bool = False
    ) -> Optional[Task]:
        """Get a task by ID."""
        query = select(Task).where(
            and_(Task.id == task_id, Task.org_id == org_id)
        )

        if include_subtasks:
            query = query.options(selectinload(Task.subtasks))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        org_id: str,
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        is_root_only: bool = False,
        search: Optional[str] = None,
        is_draft: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Task], int]:
        """Get tasks with filters."""
        query = select(Task).where(Task.org_id == org_id)

        # Apply filters — exclude drafts by default
        if is_draft is not None:
            query = query.where(Task.is_draft == is_draft)
        else:
            query = query.where(Task.is_draft == False)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)
        if team_id:
            query = query.where(Task.team_id == team_id)
        if project_id:
            query = query.where(Task.project_id == project_id)
        if parent_task_id:
            query = query.where(Task.parent_task_id == parent_task_id)
        if is_root_only:
            query = query.where(Task.parent_task_id == None)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        query = query.order_by(Task.sort_order, Task.created_at.desc())

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def update_task(
        self,
        task_id: str,
        org_id: str,
        task_data: TaskUpdate,
        updated_by: str
    ) -> Task:
        """Update a task."""
        task = await self.get_task_by_id(task_id, org_id)
        if not task:
            raise NotFoundException("Task", task_id)

        update_dict = task_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if field in ('tools', 'tags', 'skills_required'):
                # Use property setters for JSON fields
                setattr(task, field, value)
            else:
                old_value = getattr(task, field, None)
                if old_value != value:
                    setattr(task, field, value)
                    # Record change in history
                    await self._create_history(
                        task_id, updated_by, "updated",
                        field, str(old_value) if old_value else None,
                        str(value) if value else None
                    )

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update_task_status(
        self,
        task_id: str,
        org_id: str,
        status_data: TaskStatusUpdate,
        updated_by: str
    ) -> Task:
        """Update task status with validation."""
        task = await self.get_task_by_id(task_id, org_id)
        if not task:
            raise NotFoundException("Task", task_id)

        old_status = task.status
        new_status = status_data.status

        # Validate transition
        if not task.can_transition_to(new_status):
            valid_transitions = VALID_STATUS_TRANSITIONS.get(old_status, [])
            raise ValidationException(
                f"Cannot transition from {old_status.value} to {new_status.value}. "
                f"Valid transitions: {[s.value for s in valid_transitions]}"
            )

        # Handle blocked status
        if new_status == TaskStatus.BLOCKED:
            if not status_data.blocker_type:
                raise ValidationException("Blocker type required when setting status to blocked")
            task.blocker_type = status_data.blocker_type
            task.blocker_description = status_data.blocker_description
        elif old_status == TaskStatus.BLOCKED:
            # Clear blocker fields when unblocking
            task.blocker_type = None
            task.blocker_description = None

        # Perform transition
        task.transition_to(new_status)

        # Record history
        await self._create_history(
            task_id, updated_by, "status_changed",
            "status", old_status.value, new_status.value
        )

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def publish_draft(
        self,
        task_id: str,
        org_id: str,
        published_by: str
    ) -> Task:
        """Publish a draft task."""
        task = await self.get_task_by_id(task_id, org_id)
        if not task:
            raise NotFoundException("Task", task_id)
        if not task.is_draft:
            raise ValidationException("Task is not a draft")

        task.is_draft = False
        await self._create_history(
            task_id, published_by, "published",
            "is_draft", "true", "false"
        )
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete_task(
        self,
        task_id: str,
        org_id: str,
        deleted_by: str,
        hard_delete: bool = False
    ) -> bool:
        """Delete or archive a task."""
        task = await self.get_task_by_id(task_id, org_id, include_subtasks=True)
        if not task:
            raise NotFoundException("Task", task_id)

        if hard_delete:
            await self.db.delete(task)
        else:
            # Soft delete - archive
            task.status = TaskStatus.ARCHIVED
            await self._create_history(task_id, deleted_by, "archived")

        await self.db.flush()
        return True

    # ==================== Subtask Operations ====================

    async def create_subtask(
        self,
        parent_task_id: str,
        org_id: str,
        subtask_data: SubtaskCreate,
        created_by: str
    ) -> Task:
        """Create a subtask for a parent task."""
        parent = await self.get_task_by_id(parent_task_id, org_id)
        if not parent:
            raise NotFoundException("Parent task", parent_task_id)

        # Create subtask using TaskCreate
        task_create = TaskCreate(
            title=subtask_data.title,
            description=subtask_data.description,
            priority=subtask_data.priority,
            estimated_hours=subtask_data.estimated_hours,
            assigned_to=subtask_data.assigned_to,
            parent_task_id=parent_task_id,
            team_id=parent.team_id,
            project_id=parent.project_id
        )

        subtask = await self.create_task(task_create, org_id, created_by)

        # Set sort order
        subtask.sort_order = subtask_data.sort_order or 0
        await self.db.flush()
        await self.db.refresh(subtask)

        return subtask

    async def get_subtasks(
        self,
        parent_task_id: str,
        org_id: str
    ) -> List[Task]:
        """Get all subtasks for a parent task."""
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.parent_task_id == parent_task_id,
                    Task.org_id == org_id
                )
            ).order_by(Task.sort_order, Task.created_at)
        )
        return list(result.scalars().all())

    async def reorder_subtasks(
        self,
        parent_task_id: str,
        org_id: str,
        subtask_order: List[str],
        updated_by: str
    ) -> List[Task]:
        """Reorder subtasks."""
        subtasks = await self.get_subtasks(parent_task_id, org_id)
        subtask_map = {s.id: s for s in subtasks}

        for index, subtask_id in enumerate(subtask_order):
            if subtask_id in subtask_map:
                subtask_map[subtask_id].sort_order = index

        await self.db.flush()
        return await self.get_subtasks(parent_task_id, org_id)

    # ==================== Dependency Operations ====================

    async def add_dependency(
        self,
        task_id: str,
        org_id: str,
        dependency_data: DependencyCreate,
        created_by: str
    ) -> TaskDependency:
        """Add a dependency to a task."""
        # Validate both tasks exist
        task = await self.get_task_by_id(task_id, org_id)
        if not task:
            raise NotFoundException("Task", task_id)

        depends_on = await self.get_task_by_id(dependency_data.depends_on_id, org_id)
        if not depends_on:
            raise NotFoundException("Dependency task", dependency_data.depends_on_id)

        # Prevent self-dependency
        if task_id == dependency_data.depends_on_id:
            raise ValidationException("Task cannot depend on itself")

        # Check for circular dependency
        if await self._has_circular_dependency(task_id, dependency_data.depends_on_id, org_id):
            raise ValidationException("Adding this dependency would create a circular reference")

        # Check if dependency already exists
        existing = await self.db.execute(
            select(TaskDependency).where(
                and_(
                    TaskDependency.task_id == task_id,
                    TaskDependency.depends_on_id == dependency_data.depends_on_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationException("This dependency already exists")

        dependency = TaskDependency(
            id=generate_uuid(),
            task_id=task_id,
            depends_on_id=dependency_data.depends_on_id,
            is_blocking=dependency_data.is_blocking,
            description=dependency_data.description
        )

        self.db.add(dependency)
        await self.db.flush()

        await self._create_history(
            task_id, created_by, "dependency_added",
            details={"depends_on_id": dependency_data.depends_on_id}
        )

        await self.db.refresh(dependency)
        return dependency

    async def remove_dependency(
        self,
        task_id: str,
        dependency_id: str,
        org_id: str,
        removed_by: str
    ) -> bool:
        """Remove a dependency."""
        result = await self.db.execute(
            select(TaskDependency).where(
                and_(
                    TaskDependency.id == dependency_id,
                    TaskDependency.task_id == task_id
                )
            )
        )
        dependency = result.scalar_one_or_none()

        if not dependency:
            raise NotFoundException("Dependency", dependency_id)

        await self.db.delete(dependency)
        await self.db.flush()

        await self._create_history(
            task_id, removed_by, "dependency_removed",
            details={"dependency_id": dependency_id}
        )

        return True

    async def get_task_dependencies(
        self,
        task_id: str,
        org_id: str
    ) -> List[TaskDependency]:
        """Get all dependencies for a task."""
        result = await self.db.execute(
            select(TaskDependency).where(
                TaskDependency.task_id == task_id
            ).options(selectinload(TaskDependency.depends_on))
        )
        return list(result.scalars().all())

    async def _has_circular_dependency(
        self,
        task_id: str,
        depends_on_id: str,
        org_id: str,
        visited: Optional[set] = None
    ) -> bool:
        """Check for circular dependencies."""
        if visited is None:
            visited = set()

        if depends_on_id in visited:
            return True

        visited.add(depends_on_id)

        # Get dependencies of the depends_on task
        deps = await self.get_task_dependencies(depends_on_id, org_id)
        for dep in deps:
            if dep.depends_on_id == task_id:
                return True
            if await self._has_circular_dependency(task_id, dep.depends_on_id, org_id, visited):
                return True

        return False

    # ==================== Comment Operations ====================

    async def add_comment(
        self,
        task_id: str,
        org_id: str,
        comment_data: CommentCreate,
        user_id: str,
        is_ai_generated: bool = False
    ) -> TaskComment:
        """Add a comment to a task."""
        task = await self.get_task_by_id(task_id, org_id)
        if not task:
            raise NotFoundException("Task", task_id)

        comment = TaskComment(
            id=generate_uuid(),
            task_id=task_id,
            user_id=user_id,
            content=comment_data.content,
            is_ai_generated=is_ai_generated
        )

        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)

        return comment

    async def update_comment(
        self,
        comment_id: str,
        task_id: str,
        comment_data: CommentUpdate,
        user_id: str
    ) -> TaskComment:
        """Update a comment."""
        result = await self.db.execute(
            select(TaskComment).where(
                and_(
                    TaskComment.id == comment_id,
                    TaskComment.task_id == task_id
                )
            )
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("Comment", comment_id)

        # Only allow owner to edit
        if comment.user_id != user_id:
            raise ForbiddenException("You can only edit your own comments")

        comment.content = comment_data.content
        comment.is_edited = True

        await self.db.flush()
        await self.db.refresh(comment)

        return comment

    async def delete_comment(
        self,
        comment_id: str,
        task_id: str,
        user_id: str,
        is_admin: bool = False
    ) -> bool:
        """Delete a comment."""
        result = await self.db.execute(
            select(TaskComment).where(
                and_(
                    TaskComment.id == comment_id,
                    TaskComment.task_id == task_id
                )
            )
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise NotFoundException("Comment", comment_id)

        # Only allow owner or admin to delete
        if comment.user_id != user_id and not is_admin:
            raise ForbiddenException("You can only delete your own comments")

        await self.db.delete(comment)
        await self.db.flush()

        return True

    async def get_task_comments(
        self,
        task_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskComment]:
        """Get comments for a task."""
        result = await self.db.execute(
            select(TaskComment).where(
                TaskComment.task_id == task_id
            ).order_by(TaskComment.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    # ==================== History Operations ====================

    async def _create_history(
        self,
        task_id: str,
        user_id: str,
        action: str,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: Optional[dict] = None
    ) -> TaskHistory:
        """Create a task history entry."""
        history = TaskHistory(
            id=generate_uuid(),
            task_id=task_id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )

        if details:
            history.details = details

        self.db.add(history)
        await self.db.flush()

        return history

    async def get_task_history(
        self,
        task_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskHistory]:
        """Get history for a task."""
        result = await self.db.execute(
            select(TaskHistory).where(
                TaskHistory.task_id == task_id
            ).order_by(TaskHistory.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    # ==================== Bulk Operations ====================

    async def bulk_update_tasks(
        self,
        org_id: str,
        bulk_data: BulkTaskUpdate,
        updated_by: str
    ) -> Tuple[int, int, List[dict]]:
        """Bulk update tasks."""
        successful = 0
        failed = 0
        errors = []

        update_fields = bulk_data.model_dump(exclude={'task_ids'}, exclude_unset=True)

        for task_id in bulk_data.task_ids:
            try:
                task = await self.get_task_by_id(task_id, org_id)
                if not task:
                    raise NotFoundException("Task", task_id)

                for field, value in update_fields.items():
                    if value is not None:
                        if field == 'status':
                            if task.can_transition_to(value):
                                task.transition_to(value)
                        else:
                            setattr(task, field, value)

                successful += 1

            except Exception as e:
                failed += 1
                errors.append({"task_id": task_id, "error": str(e)})

        await self.db.flush()
        return successful, failed, errors

    # ==================== Assignment Operations ====================

    async def assign_task(
        self,
        task_id: str,
        org_id: str,
        assignee_id: Optional[str],
        assigned_by: str
    ) -> Task:
        """Assign or unassign a task."""
        task = await self.get_task_by_id(task_id, org_id)
        if not task:
            raise NotFoundException("Task", task_id)

        # Validate assignee belongs to the same organization
        if assignee_id:
            assignee_query = select(User).where(
                and_(User.id == assignee_id, User.org_id == org_id, User.is_active == True)
            )
            assignee = (await self.db.execute(assignee_query)).scalar_one_or_none()
            if not assignee:
                raise ValidationException(f"User {assignee_id} not found in this organization")

        old_assignee = task.assigned_to
        task.assigned_to = assignee_id

        await self._create_history(
            task_id, assigned_by,
            "assigned" if assignee_id else "unassigned",
            "assigned_to", old_assignee, assignee_id
        )

        await self.db.flush()
        await self.db.refresh(task)

        return task

    # ==================== Statistics ====================

    async def get_task_statistics(
        self,
        org_id: str,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> dict:
        """Get task statistics."""
        base_query = select(Task).where(Task.org_id == org_id)

        if team_id:
            base_query = base_query.where(Task.team_id == team_id)
        if project_id:
            base_query = base_query.where(Task.project_id == project_id)
        if user_id:
            base_query = base_query.where(Task.assigned_to == user_id)

        # Get counts by status
        status_counts = {}
        for status in TaskStatus:
            count_query = select(func.count()).select_from(
                base_query.where(Task.status == status).subquery()
            )
            status_counts[status.value] = (await self.db.execute(count_query)).scalar() or 0

        # Get total
        total_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(total_query)).scalar() or 0

        # Get overdue count
        overdue_query = select(func.count()).select_from(
            base_query.where(
                and_(
                    Task.deadline < datetime.utcnow(),
                    Task.status.notin_([TaskStatus.DONE, TaskStatus.ARCHIVED])
                )
            ).subquery()
        )
        overdue = (await self.db.execute(overdue_query)).scalar() or 0

        # Get priority breakdown
        priority_counts = {}
        for priority in TaskPriority:
            count_query = select(func.count()).select_from(
                base_query.where(Task.priority == priority).subquery()
            )
            priority_counts[priority.value] = (await self.db.execute(count_query)).scalar() or 0

        return {
            "total": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "overdue": overdue,
            "completion_rate": round(
                (status_counts.get("done", 0) + status_counts.get("archived", 0)) / total * 100, 1
            ) if total > 0 else 0
        }
