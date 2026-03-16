# -*- coding: utf-8 -*-
"""
项目成员 CRUD 操作（重构版本 - 薄控制器）

使用服务层处理业务逻辑，endpoint 仅负责请求处理和响应
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.pmo import PmoResourceAllocation
from app.models.progress import Task
from app.models.project import ProjectMemberContribution
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import ProjectMemberCreate, ProjectMemberResponse, ProjectMemberUpdate
from app.services.project_contribution_service import ProjectContributionService
from app.services.project_members import ProjectMembersService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


# ==================== Helpers ====================


def _calculate_workdays(start_date: date, end_date: date) -> int:
    """计算工作日数量（排除周末）"""
    if start_date > end_date:
        return 0

    days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def _serialize_contribution(contribution: ProjectMemberContribution) -> dict:
    user = getattr(contribution, "user", None)
    return {
        "id": contribution.id,
        "project_id": contribution.project_id,
        "user_id": contribution.user_id,
        "username": user.username if user else None,
        "real_name": user.real_name if user else None,
        "period": contribution.period,
        "task_count": contribution.task_count or 0,
        "task_hours": float(contribution.task_hours or 0),
        "actual_hours": float(contribution.actual_hours or 0),
        "deliverable_count": contribution.deliverable_count or 0,
        "issue_count": contribution.issue_count or 0,
        "issue_resolved": contribution.issue_resolved or 0,
        "contribution_score": float(contribution.contribution_score or 0),
        "pm_rating": contribution.pm_rating,
        "bonus_amount": float(contribution.bonus_amount or 0),
    }


# ==================== 列表/创建 ====================


@router.get("/", response_model=PaginatedResponse[ProjectMemberResponse])
def list_project_members(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: str = Query(None, description="关键词搜索"),
    order_by: str = Query(None, description="排序字段"),
    order_direction: str = Query("desc", description="排序方向 (asc/desc)"),
    role: str = Query(None, description="角色筛选"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员列表（支持分页、搜索、排序、筛选）"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    members, total = service.list_members(
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.limit,
        keyword=keyword,
        order_by=order_by,
        order_direction=order_direction,
        role=role,
    )

    return PaginatedResponse(
        items=members,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post("/", response_model=ProjectMemberResponse, status_code=201)
def add_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_in: ProjectMemberCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """为项目添加成员"""
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    service = ProjectMembersService(db)
    member = service.create_member(
        project_id=project_id,
        user_id=member_in.user_id,
        role_code=member_in.role_code,
        allocation_pct=member_in.allocation_pct,
        start_date=member_in.start_date,
        end_date=member_in.end_date,
        commitment_level=member_in.commitment_level,
        reporting_to_pm=member_in.reporting_to_pm,
        remark=member_in.remark,
        created_by=current_user.id,
    )

    return member


# ==================== 静态扩展路由（必须放在动态 /{member_id} 之前） ====================


@router.get("/conflicts", response_model=dict)
def check_member_conflicts(
    project_id: int = Path(..., description="项目ID"),
    user_id: int = Query(..., description="用户ID"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """检查成员分配冲突"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    return service.check_member_conflicts(user_id, start_date, end_date, project_id)


class BatchAddMemberItem(BaseModel):
    """兼容逐成员配置的批量添加请求项"""

    user_id: int
    role_code: str = Field(..., max_length=50)
    allocation_pct: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    commitment_level: Optional[str] = None
    reporting_to_pm: bool = True
    remark: Optional[str] = None


class BatchAddMembersRequest(BaseModel):
    """批量添加成员请求

    同时兼容两种 payload：
    1. 现有接口：{"user_ids": [...], "role_code": "DEV", ...}
    2. 旧测试接口：{"members": [{"user_id": 1, "role_code": "DEV", ...}]}
    """

    user_ids: Optional[List[int]] = None
    role_code: Optional[str] = None
    allocation_pct: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    commitment_level: Optional[str] = None
    reporting_to_pm: bool = True
    members: Optional[List[BatchAddMemberItem]] = None


@router.post("/batch", response_model=dict)
def batch_add_project_members(
    project_id: int = Path(..., description="项目ID"),
    request: BatchAddMembersRequest = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """批量添加项目成员（兼容新旧两种请求格式）"""
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中添加成员")

    service = ProjectMembersService(db)

    if request.members:
        added_count = 0
        skipped_count = 0
        conflicts = []
        created_member_ids = []

        for member in request.members:
            if service.check_member_exists(project_id, member.user_id):
                skipped_count += 1
                continue

            conflict_info = service.check_member_conflicts(
                user_id=member.user_id,
                start_date=member.start_date,
                end_date=member.end_date,
                exclude_project_id=project_id,
            )
            if conflict_info.get("has_conflict"):
                conflicts.append(
                    {
                        "user_id": member.user_id,
                        "user_name": conflict_info.get("user_name", f"User {member.user_id}"),
                        "conflicting_projects": conflict_info.get("conflicting_projects", []),
                    }
                )
                continue

            created = service.create_member(
                project_id=project_id,
                user_id=member.user_id,
                role_code=member.role_code,
                allocation_pct=member.allocation_pct,
                start_date=member.start_date,
                end_date=member.end_date,
                commitment_level=member.commitment_level,
                reporting_to_pm=member.reporting_to_pm,
                remark=member.remark,
                created_by=current_user.id,
                enrich=False,
            )
            added_count += 1
            created_member_ids.append(created.id)

        return {
            "added_count": added_count,
            "skipped_count": skipped_count,
            "conflicts": conflicts,
            "created_member_ids": created_member_ids,
            "message": (
                f"成功添加 {added_count} 位成员，"
                f"跳过 {skipped_count} 位，"
                f"发现 {len(conflicts)} 个时间冲突"
            ),
        }

    if not request.user_ids or not request.role_code:
        raise HTTPException(status_code=422, detail="user_ids 和 role_code 不能为空")

    return service.batch_add_members(
        project_id=project_id,
        user_ids=request.user_ids,
        role_code=request.role_code,
        allocation_pct=request.allocation_pct,
        start_date=request.start_date,
        end_date=request.end_date,
        commitment_level=request.commitment_level,
        reporting_to_pm=request.reporting_to_pm,
        created_by=current_user.id,
    )


@router.get("/contribution", response_model=dict)
def get_project_member_contribution(
    project_id: int = Path(..., description="项目ID"),
    period: Optional[str] = Query(None, description="统计周期 YYYY-MM"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员贡献度（兼容旧成员端点）"""
    check_project_access_or_raise(db, current_user, project_id)

    contribution_service = ProjectContributionService(db)
    contributions = contribution_service.get_project_contributions(project_id, period)

    return {
        "project_id": project_id,
        "period": period,
        "items": [_serialize_contribution(item) for item in contributions],
        "total": len(contributions),
    }


# ==================== 动态成员路由 ====================


@router.get("/{member_id}", response_model=ProjectMemberResponse)
def get_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目成员详情"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    return service.get_member_by_id(project_id, member_id)


@router.put("/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    member_in: ProjectMemberUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """更新项目成员信息"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    update_data = member_in.model_dump(exclude_unset=True)
    return service.update_member(project_id, member_id, update_data)


@router.delete("/{member_id}", status_code=204)
def remove_project_member(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
):
    """移除项目成员"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    service.delete_member(project_id, member_id)


@router.get("/{member_id}/workload", response_model=dict)
def get_member_workload(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取成员工作量摘要（兼容旧成员端点）"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    member = service.get_member_by_id(project_id, member_id)

    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    tasks = (
        db.query(Task)
        .filter(
            Task.project_id == project_id,
            Task.owner_id == member.user_id,
            Task.plan_start <= end_date,
            Task.plan_end >= start_date,
            Task.status != "CANCELLED",
        )
        .all()
    )

    assigned_hours = 0.0
    completed_task_count = 0
    overdue_task_count = 0

    for task in tasks:
        if task.status in ["DONE", "COMPLETED"]:
            completed_task_count += 1

        if task.plan_end and task.plan_end < today and task.status not in [
            "DONE",
            "COMPLETED",
            "CANCELLED",
        ]:
            overdue_task_count += 1

        if task.plan_start and task.plan_end:
            task_start = max(task.plan_start, start_date)
            task_end = min(task.plan_end, end_date)
            if task_start <= task_end:
                assigned_hours += ((task_end - task_start).days + 1) * 8.0

    allocations = (
        db.query(PmoResourceAllocation)
        .filter(
            PmoResourceAllocation.project_id == project_id,
            PmoResourceAllocation.resource_id == member.user_id,
            PmoResourceAllocation.start_date <= end_date,
            PmoResourceAllocation.end_date >= start_date,
            PmoResourceAllocation.status != "CANCELLED",
        )
        .all()
    )

    planned_hours = 0.0
    for allocation in allocations:
        planned_hours += float(allocation.planned_hours or 0)

    if planned_hours > 0:
        assigned_hours = planned_hours

    standard_hours = _calculate_workdays(start_date, end_date) * 8.0
    allocation_rate = (assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0

    return {
        "project_id": project_id,
        "member_id": member.id,
        "user_id": member.user_id,
        "username": member.username,
        "real_name": member.real_name,
        "role_code": member.role_code,
        "task_count": len(tasks),
        "completed_task_count": completed_task_count,
        "overdue_task_count": overdue_task_count,
        "assigned_hours": round(assigned_hours, 2),
        "planned_hours": round(planned_hours, 2),
        "standard_hours": round(standard_hours, 2),
        "allocation_rate": round(allocation_rate, 2),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


# ==================== 扩展功能 ====================


@router.post("/{member_id}/notify-dept-manager", response_model=ResponseModel)
def notify_dept_manager(
    project_id: int = Path(..., description="项目ID"),
    member_id: int = Path(..., description="成员ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """通知部门经理（成员加入项目）"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    result = service.notify_dept_manager(project_id, member_id)

    return ResponseModel(code=200, message=result["message"])


@router.get("/from-dept/{dept_id}", response_model=dict)
def get_dept_users_for_project(
    project_id: int = Path(..., description="项目ID"),
    dept_id: int = Path(..., description="部门ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取部门用户列表（用于批量添加成员）"""
    check_project_access_or_raise(db, current_user, project_id)

    service = ProjectMembersService(db)
    return service.get_dept_users_for_project(project_id, dept_id)
