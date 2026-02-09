"""
TaskPulse - AI Assistant - Reports API
Report generation and analytics endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User, UserRole
from app.services.report_service import ReportService
from app.services.analytics_service import AnalyticsService
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.exceptions import ForbiddenException
from pydantic import BaseModel, Field

router = APIRouter()


# Schemas
class ReportRequest(BaseModel):
    report_type: str = Field(..., description="Type: team_productivity, task_completion, blocker_analysis, executive_summary")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_id: Optional[str] = None
    format: str = Field(default="json", description="Output format: json, csv, xlsx")


class ScheduleReportRequest(BaseModel):
    report_type: str
    schedule: str = Field(..., description="Schedule: daily, weekly, monthly")
    recipients: List[str] = Field(..., min_length=1)
    config: dict = Field(default_factory=dict)


def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db)


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


# Analytics Endpoints
@router.get(
    "/dashboard",
    summary="Get dashboard metrics"
)
async def get_dashboard(
    team_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive dashboard metrics."""
    # Check permissions for viewing others' data
    if user_id and user_id != current_user.id:
        if not has_permission(current_user.role, Permission.ANALYTICS_VIEW):
            raise ForbiddenException("Not authorized to view others' analytics")

    return await service.get_dashboard_metrics(
        org_id=current_user.org_id,
        team_id=team_id,
        user_id=user_id or (current_user.id if not has_permission(current_user.role, Permission.ANALYTICS_VIEW) else None)
    )


@router.get(
    "/team/{team_id}/workload",
    summary="Get team workload"
)
async def get_team_workload(
    team_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.TEAM_LEAD
    )),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get workload distribution for a team."""
    return await service.get_team_workload(team_id, current_user.org_id)


@router.get(
    "/workload",
    summary="Get workload for current user's team"
)
async def get_my_team_workload(
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get workload distribution for the current user's team."""
    team_id = current_user.team_id or current_user.org_id
    return await service.get_team_workload(team_id, current_user.org_id)


@router.get(
    "/productivity",
    summary="Get productivity for current user's team"
)
async def get_my_team_productivity(
    period: Optional[str] = Query(None, description="Period: week, month, quarter"),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service)
):
    """Get productivity report for the current user's team."""
    team_id = current_user.team_id or current_user.org_id
    end = datetime.utcnow()
    period_days = {"week": 7, "month": 30, "quarter": 90}.get(period or "month", 30)
    start = end - timedelta(days=period_days)

    return await service.generate_team_productivity_report(
        org_id=current_user.org_id,
        team_id=team_id,
        start_date=start,
        end_date=end,
        format="json"
    )


@router.get(
    "/velocity",
    summary="Get velocity chart data"
)
async def get_velocity(
    team_id: Optional[str] = Query(None),
    weeks: int = Query(12, ge=4, le=52),
    current_user: User = Depends(get_current_active_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get velocity data for charting."""
    if not has_permission(current_user.role, Permission.ANALYTICS_VIEW):
        team_id = current_user.team_id

    return await service.get_velocity_chart_data(
        org_id=current_user.org_id,
        team_id=team_id,
        weeks=weeks
    )


@router.get(
    "/bottlenecks",
    summary="Get bottleneck analysis"
)
async def get_bottlenecks(
    team_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.TEAM_LEAD
    )),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Analyze bottlenecks in task flow."""
    return await service.get_bottleneck_analysis(
        org_id=current_user.org_id,
        team_id=team_id
    )


@router.get(
    "/checkin-summary",
    summary="Get check-in summary"
)
async def get_checkin_summary(
    team_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER, UserRole.TEAM_LEAD
    )),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get check-in activity summary."""
    return await service.get_check_in_summary(
        org_id=current_user.org_id,
        team_id=team_id,
        days=days
    )


# Report Generation Endpoints
@router.post(
    "/generate",
    summary="Generate report"
)
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: ReportService = Depends(get_report_service)
):
    """Generate a report."""
    if not has_permission(current_user.role, Permission.REPORTS_GENERATE):
        raise ForbiddenException("Not authorized to generate reports")

    # Set default dates if not provided
    end_date = request.end_date or datetime.utcnow()
    start_date = request.start_date or (end_date - timedelta(days=30))

    if request.report_type == "team_productivity":
        if not request.team_id:
            raise ForbiddenException("team_id required for team productivity report")
        return await service.generate_team_productivity_report(
            org_id=current_user.org_id,
            team_id=request.team_id,
            start_date=start_date,
            end_date=end_date,
            format=request.format
        )
    elif request.report_type == "task_completion":
        return await service.generate_task_completion_report(
            org_id=current_user.org_id,
            start_date=start_date,
            end_date=end_date,
            team_id=request.team_id,
            format=request.format
        )
    elif request.report_type == "blocker_analysis":
        return await service.generate_blocker_analysis_report(
            org_id=current_user.org_id,
            start_date=start_date,
            end_date=end_date,
            format=request.format
        )
    elif request.report_type == "executive_summary":
        days = (end_date - start_date).days
        return await service.generate_executive_summary(
            org_id=current_user.org_id,
            period_days=days
        )
    else:
        return {"error": f"Unknown report type: {request.report_type}"}


@router.get(
    "/team/{team_id}/productivity",
    summary="Get team productivity report"
)
async def get_team_productivity_report(
    team_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    format: str = Query("json"),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: ReportService = Depends(get_report_service)
):
    """Generate team productivity report."""
    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=30))

    report = await service.generate_team_productivity_report(
        org_id=current_user.org_id,
        team_id=team_id,
        start_date=start,
        end_date=end,
        format=format
    )

    if format == "xlsx" and isinstance(report, bytes):
        return Response(
            content=report,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=team_productivity_{team_id}.xlsx"}
        )
    elif format == "csv" and isinstance(report, str):
        return Response(
            content=report,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=team_productivity_{team_id}.csv"}
        )

    return report


@router.get(
    "/executive-summary",
    summary="Get executive summary"
)
async def get_executive_summary(
    period_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: ReportService = Depends(get_report_service)
):
    """Generate executive summary report."""
    if not has_permission(current_user.role, Permission.REPORTS_VIEW_EXECUTIVE):
        raise ForbiddenException("Not authorized to view executive reports")

    return await service.generate_executive_summary(
        org_id=current_user.org_id,
        period_days=period_days
    )


@router.post(
    "/schedule",
    summary="Schedule recurring report"
)
async def schedule_report(
    request: ScheduleReportRequest,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: ReportService = Depends(get_report_service)
):
    """Schedule a recurring report."""
    if not has_permission(current_user.role, Permission.REPORTS_SCHEDULE):
        raise ForbiddenException("Not authorized to schedule reports")

    return await service.schedule_report(
        org_id=current_user.org_id,
        report_type=request.report_type,
        schedule=request.schedule,
        recipients=request.recipients,
        config=request.config
    )
