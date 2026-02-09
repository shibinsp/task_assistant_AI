"""
TaskPulse - AI Assistant - Tasks API
Endpoints for task management
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.task import TaskStatus, TaskPriority
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse, TaskDetailResponse,
    TaskListResponse, SubtaskCreate, SubtaskUpdate,
    DependencyCreate, DependencyResponse,
    CommentCreate, CommentUpdate, CommentResponse,
    TaskHistoryResponse, BulkTaskUpdate, BulkOperationResult
)
from app.services.task_service import TaskService
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    """Dependency to get task service."""
    return TaskService(db)


# ==================== Task CRUD ====================

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create a new task"
)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Create a new task."""
    if not has_permission(current_user.role, Permission.TASKS_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create tasks"
        )

    task = await service.create_task(
        task_data, current_user.org_id, current_user.id
    )

    return TaskResponse(
        **task.__dict__,
        tools=task.tools,
        tags=task.tags,
        skills_required=task.skills_required,
        is_subtask=task.is_subtask,
        is_blocked=task.is_blocked,
        is_completed=task.is_completed,
        is_overdue=task.is_overdue,
        progress_percentage=task.progress_percentage
    )


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks",
    description="List tasks with filters"
)
async def list_tasks(
    pagination: PaginationParams = Depends(get_pagination),
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[TaskPriority] = Query(None),
    assigned_to: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    parent_task_id: Optional[str] = Query(None),
    root_only: bool = Query(False, description="Only return root tasks (no subtasks)"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """List tasks with optional filters."""
    # Check permissions
    can_read_all = has_permission(current_user.role, Permission.TASKS_READ)
    can_read_team = has_permission(current_user.role, Permission.TASKS_READ_TEAM)
    can_read_own = has_permission(current_user.role, Permission.TASKS_READ_OWN)

    # Apply permission-based filtering
    if not can_read_all:
        if can_read_team:
            team_id = current_user.team_id
        elif can_read_own:
            assigned_to = current_user.id

    tasks, total = await service.get_tasks(
        org_id=current_user.org_id,
        status=status_filter,
        priority=priority,
        assigned_to=assigned_to,
        team_id=team_id,
        project_id=project_id,
        parent_task_id=parent_task_id,
        is_root_only=root_only,
        search=search,
        skip=pagination.skip,
        limit=pagination.limit
    )

    task_responses = [
        TaskResponse(
            **t.__dict__,
            tools=t.tools,
            tags=t.tags,
            skills_required=t.skills_required,
            is_subtask=t.is_subtask,
            is_blocked=t.is_blocked,
            is_completed=t.is_completed,
            is_overdue=t.is_overdue,
            progress_percentage=t.progress_percentage
        ) for t in tasks
    ]

    return TaskListResponse(
        tasks=task_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get(
    "/statistics",
    summary="Get task statistics",
    description="Get task statistics for the organization"
)
async def get_task_statistics(
    team_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Get task statistics."""
    return await service.get_task_statistics(
        org_id=current_user.org_id,
        team_id=team_id,
        project_id=project_id,
        user_id=user_id
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="Get task",
    description="Get task details by ID"
)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Get task details."""
    task = await service.get_task_by_id(task_id, current_user.org_id, include_subtasks=True)

    if not task:
        raise NotFoundException("Task", task_id)

    # Check permissions
    can_read = (
        has_permission(current_user.role, Permission.TASKS_READ) or
        (has_permission(current_user.role, Permission.TASKS_READ_TEAM) and
         task.team_id == current_user.team_id) or
        (has_permission(current_user.role, Permission.TASKS_READ_OWN) and
         task.assigned_to == current_user.id)
    )

    if not can_read:
        raise ForbiddenException("Not authorized to view this task")

    # Get additional counts
    subtasks = await service.get_subtasks(task_id, current_user.org_id)
    dependencies = await service.get_task_dependencies(task_id, current_user.org_id)
    comments = await service.get_task_comments(task_id)

    return TaskDetailResponse(
        **task.__dict__,
        tools=task.tools,
        tags=task.tags,
        skills_required=task.skills_required,
        is_subtask=task.is_subtask,
        is_blocked=task.is_blocked,
        is_completed=task.is_completed,
        is_overdue=task.is_overdue,
        progress_percentage=task.progress_percentage,
        subtask_count=len(subtasks),
        completed_subtask_count=sum(1 for s in subtasks if s.is_completed),
        dependency_count=len(dependencies),
        comment_count=len(comments)
    )


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update task details"
)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Update task details."""
    task = await service.get_task_by_id(task_id, current_user.org_id)
    if not task:
        raise NotFoundException("Task", task_id)

    # Check permissions
    can_update = (
        has_permission(current_user.role, Permission.TASKS_UPDATE) or
        (has_permission(current_user.role, Permission.TASKS_UPDATE_OWN) and
         task.assigned_to == current_user.id)
    )

    if not can_update:
        raise ForbiddenException("Not authorized to update this task")

    task = await service.update_task(task_id, current_user.org_id, task_data, current_user.id)

    return TaskResponse(
        **task.__dict__,
        tools=task.tools,
        tags=task.tags,
        skills_required=task.skills_required,
        is_subtask=task.is_subtask,
        is_blocked=task.is_blocked,
        is_completed=task.is_completed,
        is_overdue=task.is_overdue,
        progress_percentage=task.progress_percentage
    )


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update task status",
    description="Update task status with workflow validation"
)
async def update_task_status(
    task_id: str,
    status_data: TaskStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Update task status with validation."""
    task = await service.get_task_by_id(task_id, current_user.org_id)
    if not task:
        raise NotFoundException("Task", task_id)

    # Check permissions
    can_update = (
        has_permission(current_user.role, Permission.TASKS_UPDATE) or
        (has_permission(current_user.role, Permission.TASKS_UPDATE_OWN) and
         task.assigned_to == current_user.id)
    )

    if not can_update:
        raise ForbiddenException("Not authorized to update this task")

    task = await service.update_task_status(
        task_id, current_user.org_id, status_data, current_user.id
    )

    return TaskResponse(
        **task.__dict__,
        tools=task.tools,
        tags=task.tags,
        skills_required=task.skills_required,
        is_subtask=task.is_subtask,
        is_blocked=task.is_blocked,
        is_completed=task.is_completed,
        is_overdue=task.is_overdue,
        progress_percentage=task.progress_percentage
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete or archive a task"
)
async def delete_task(
    task_id: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of archive"),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Delete or archive a task."""
    if not has_permission(current_user.role, Permission.TASKS_DELETE):
        raise ForbiddenException("Not authorized to delete tasks")

    await service.delete_task(task_id, current_user.org_id, current_user.id, hard_delete)


@router.post(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="Assign task",
    description="Assign task to a user"
)
async def assign_task(
    task_id: str,
    assignee_id: Optional[str] = Query(None, description="User ID to assign to, or null to unassign"),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Assign a task to a user."""
    if not has_permission(current_user.role, Permission.TASKS_ASSIGN):
        raise ForbiddenException("Not authorized to assign tasks")

    task = await service.assign_task(
        task_id, current_user.org_id, assignee_id, current_user.id
    )

    return TaskResponse(
        **task.__dict__,
        tools=task.tools,
        tags=task.tags,
        skills_required=task.skills_required,
        is_subtask=task.is_subtask,
        is_blocked=task.is_blocked,
        is_completed=task.is_completed,
        is_overdue=task.is_overdue,
        progress_percentage=task.progress_percentage
    )


# ==================== Bulk Operations ====================

@router.post(
    "/bulk/update",
    response_model=BulkOperationResult,
    summary="Bulk update tasks",
    description="Update multiple tasks at once"
)
async def bulk_update_tasks(
    bulk_data: BulkTaskUpdate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: TaskService = Depends(get_task_service)
):
    """Bulk update tasks."""
    successful, failed, errors = await service.bulk_update_tasks(
        current_user.org_id, bulk_data, current_user.id
    )

    return BulkOperationResult(
        total=len(bulk_data.task_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


# ==================== Subtask Endpoints ====================

@router.post(
    "/{task_id}/subtasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create subtask",
    description="Create a subtask for a task"
)
async def create_subtask(
    task_id: str,
    subtask_data: SubtaskCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Create a subtask."""
    if not has_permission(current_user.role, Permission.TASKS_CREATE):
        raise ForbiddenException("Not authorized to create tasks")

    subtask = await service.create_subtask(
        task_id, current_user.org_id, subtask_data, current_user.id
    )

    return TaskResponse(
        **subtask.__dict__,
        tools=subtask.tools,
        tags=subtask.tags,
        skills_required=subtask.skills_required,
        is_subtask=subtask.is_subtask,
        is_blocked=subtask.is_blocked,
        is_completed=subtask.is_completed,
        is_overdue=subtask.is_overdue,
        progress_percentage=subtask.progress_percentage
    )


@router.get(
    "/{task_id}/subtasks",
    response_model=List[TaskResponse],
    summary="Get subtasks",
    description="Get all subtasks for a task"
)
async def get_subtasks(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Get subtasks for a task."""
    subtasks = await service.get_subtasks(task_id, current_user.org_id)

    return [
        TaskResponse(
            **s.__dict__,
            tools=s.tools,
            tags=s.tags,
            skills_required=s.skills_required,
            is_subtask=s.is_subtask,
            is_blocked=s.is_blocked,
            is_completed=s.is_completed,
            is_overdue=s.is_overdue,
            progress_percentage=s.progress_percentage
        ) for s in subtasks
    ]


@router.post(
    "/{task_id}/subtasks/reorder",
    response_model=List[TaskResponse],
    summary="Reorder subtasks",
    description="Reorder subtasks"
)
async def reorder_subtasks(
    task_id: str,
    subtask_ids: List[str],
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Reorder subtasks."""
    subtasks = await service.reorder_subtasks(
        task_id, current_user.org_id, subtask_ids, current_user.id
    )

    return [
        TaskResponse(
            **s.__dict__,
            tools=s.tools,
            tags=s.tags,
            skills_required=s.skills_required,
            is_subtask=s.is_subtask,
            is_blocked=s.is_blocked,
            is_completed=s.is_completed,
            is_overdue=s.is_overdue,
            progress_percentage=s.progress_percentage
        ) for s in subtasks
    ]


# ==================== Dependency Endpoints ====================

@router.post(
    "/{task_id}/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add dependency",
    description="Add a dependency to a task"
)
async def add_dependency(
    task_id: str,
    dependency_data: DependencyCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Add a dependency to a task."""
    if not has_permission(current_user.role, Permission.TASKS_UPDATE):
        raise ForbiddenException("Not authorized to modify dependencies")

    dependency = await service.add_dependency(
        task_id, current_user.org_id, dependency_data, current_user.id
    )

    return DependencyResponse(
        id=dependency.id,
        task_id=dependency.task_id,
        depends_on_id=dependency.depends_on_id,
        is_blocking=dependency.is_blocking,
        description=dependency.description,
        created_at=dependency.created_at
    )


@router.get(
    "/{task_id}/dependencies",
    response_model=List[DependencyResponse],
    summary="Get dependencies",
    description="Get all dependencies for a task"
)
async def get_dependencies(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Get task dependencies."""
    dependencies = await service.get_task_dependencies(task_id, current_user.org_id)

    return [
        DependencyResponse(
            id=d.id,
            task_id=d.task_id,
            depends_on_id=d.depends_on_id,
            is_blocking=d.is_blocking,
            description=d.description,
            depends_on_title=d.depends_on.title if d.depends_on else None,
            depends_on_status=d.depends_on.status if d.depends_on else None,
            created_at=d.created_at
        ) for d in dependencies
    ]


@router.delete(
    "/{task_id}/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove dependency",
    description="Remove a dependency from a task"
)
async def remove_dependency(
    task_id: str,
    dependency_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Remove a dependency."""
    if not has_permission(current_user.role, Permission.TASKS_UPDATE):
        raise ForbiddenException("Not authorized to modify dependencies")

    await service.remove_dependency(
        task_id, dependency_id, current_user.org_id, current_user.id
    )


# ==================== Comment Endpoints ====================

@router.post(
    "/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a comment to a task"
)
async def add_comment(
    task_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Add a comment to a task."""
    comment = await service.add_comment(
        task_id, current_user.org_id, comment_data, current_user.id
    )

    return CommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        user_id=comment.user_id,
        content=comment.content,
        is_ai_generated=comment.is_ai_generated,
        is_edited=comment.is_edited,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.get(
    "/{task_id}/comments",
    response_model=List[CommentResponse],
    summary="Get comments",
    description="Get all comments for a task"
)
async def get_comments(
    task_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Get task comments."""
    comments = await service.get_task_comments(
        task_id, skip=pagination.skip, limit=pagination.limit
    )

    return [
        CommentResponse(
            id=c.id,
            task_id=c.task_id,
            user_id=c.user_id,
            content=c.content,
            is_ai_generated=c.is_ai_generated,
            is_edited=c.is_edited,
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in comments
    ]


@router.patch(
    "/{task_id}/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Update comment",
    description="Update a comment"
)
async def update_comment(
    task_id: str,
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Update a comment."""
    comment = await service.update_comment(
        comment_id, task_id, comment_data, current_user.id
    )

    return CommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        user_id=comment.user_id,
        content=comment.content,
        is_ai_generated=comment.is_ai_generated,
        is_edited=comment.is_edited,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )


@router.delete(
    "/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
    description="Delete a comment"
)
async def delete_comment(
    task_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Delete a comment."""
    is_admin = has_permission(current_user.role, Permission.TASKS_DELETE)
    await service.delete_comment(comment_id, task_id, current_user.id, is_admin)


# ==================== History Endpoints ====================

@router.get(
    "/{task_id}/history",
    response_model=List[TaskHistoryResponse],
    summary="Get task history",
    description="Get change history for a task"
)
async def get_task_history(
    task_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Get task history."""
    history = await service.get_task_history(
        task_id, skip=pagination.skip, limit=pagination.limit
    )

    return [
        TaskHistoryResponse(
            id=h.id,
            task_id=h.task_id,
            user_id=h.user_id,
            action=h.action,
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            details=h.details,
            created_at=h.created_at
        ) for h in history
    ]


# ==================== AI Decomposition Endpoints ====================

from app.schemas.task import TaskDecompositionRequest, TaskDecompositionResponse, SubtaskSuggestion
from app.services.ai_service import get_ai_service


@router.post(
    "/{task_id}/decompose",
    response_model=TaskDecompositionResponse,
    summary="AI task decomposition",
    description="Use AI to decompose a task into subtasks"
)
async def decompose_task(
    task_id: str,
    request: TaskDecompositionRequest,
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Decompose a task into subtasks using AI."""
    if not has_permission(current_user.role, Permission.TASKS_APPROVE_AI):
        raise ForbiddenException("Not authorized to use AI decomposition")

    task = await service.get_task_by_id(task_id, current_user.org_id)
    if not task:
        raise NotFoundException("Task", task_id)

    ai_service = get_ai_service()
    result = await ai_service.decompose_task(
        title=task.title,
        description=task.description or "",
        goal=task.goal,
        max_subtasks=request.max_subtasks
    )

    return TaskDecompositionResponse(
        task_id=task_id,
        suggested_subtasks=[
            SubtaskSuggestion(
                title=s["title"],
                description=s["description"],
                estimated_hours=s["estimated_hours"] if request.include_time_estimates else None,
                skills_required=s["skills_required"] if request.include_skill_requirements else [],
                order=s["order"]
            ) for s in result["subtasks"]
        ],
        total_estimated_hours=result["total_estimated_hours"],
        complexity_score=result["complexity_score"],
        risk_factors=result["risk_factors"],
        recommendations=result["recommendations"]
    )


@router.post(
    "/{task_id}/decompose/apply",
    response_model=List[TaskResponse],
    summary="Apply AI decomposition",
    description="Apply AI-suggested subtasks to a task"
)
async def apply_decomposition(
    task_id: str,
    subtasks: List[SubtaskSuggestion],
    current_user: User = Depends(get_current_active_user),
    service: TaskService = Depends(get_task_service)
):
    """Apply AI-suggested subtasks to create actual subtasks."""
    if not has_permission(current_user.role, Permission.TASKS_APPROVE_AI):
        raise ForbiddenException("Not authorized to approve AI subtasks")

    task = await service.get_task_by_id(task_id, current_user.org_id)
    if not task:
        raise NotFoundException("Task", task_id)

    created_subtasks = []
    for suggestion in subtasks:
        subtask_data = SubtaskCreate(
            title=suggestion.title,
            description=suggestion.description,
            estimated_hours=suggestion.estimated_hours,
            sort_order=suggestion.order
        )

        subtask = await service.create_subtask(
            task_id, current_user.org_id, subtask_data, current_user.id
        )

        # Set skills if provided
        if suggestion.skills_required:
            subtask.skills_required = suggestion.skills_required
            await service.db.flush()

        created_subtasks.append(subtask)

    return [
        TaskResponse(
            **s.__dict__,
            tools=s.tools,
            tags=s.tags,
            skills_required=s.skills_required,
            is_subtask=s.is_subtask,
            is_blocked=s.is_blocked,
            is_completed=s.is_completed,
            is_overdue=s.is_overdue,
            progress_percentage=s.progress_percentage
        ) for s in created_subtasks
    ]
