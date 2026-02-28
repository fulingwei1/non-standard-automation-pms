# -*- coding: utf-8 -*-
"""
资源冲突检测与分析 API

全局视角查看和管理资源冲突
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.project import (
    Project,
    ProjectStageResourcePlan,
    ResourceConflict,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination

router = APIRouter()


# ==================== Schemas ====================

class ConflictResolveRequest(BaseModel):
    """解决冲突请求"""
    resolution_note: str


# ==================== Project-level Endpoints ====================

@router.get("/projects/{project_id}/resource-conflicts", response_model=ResponseModel)
def get_project_conflicts(
    project_id: int,
    db: Session = Depends(get_db),
    include_resolved: bool = Query(False, description="是否包含已解决的冲突"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目的所有资源冲突
    """
    # 获取项目的所有资源计划ID
    plan_ids = db.query(ProjectStageResourcePlan.id).filter(
        ProjectStageResourcePlan.project_id == project_id
    ).subquery()

    # 查询相关冲突
    query = db.query(ResourceConflict).filter(
        or_(
            ResourceConflict.plan_a_id.in_(plan_ids),
            ResourceConflict.plan_b_id.in_(plan_ids),
        )
    )

    if not include_resolved:
        query = query.filter(ResourceConflict.is_resolved == 0)

    conflicts = query.order_by(ResourceConflict.severity.desc()).all()

    result = []
    for conflict in conflicts:
        result.append(_format_conflict(db, conflict, project_id))

    return ResponseModel(data={
        "project_id": project_id,
        "conflicts": result,
        "total_count": len(result),
        "high_count": len([c for c in result if c["severity"] == "HIGH"]),
        "medium_count": len([c for c in result if c["severity"] == "MEDIUM"]),
    })


@router.get("/projects/{project_id}/resource-conflicts/check", response_model=ResponseModel)
def check_project_conflicts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查当前分配是否有冲突（重新计算）
    """
    # 获取项目所有已分配的计划
    plans = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.project_id == project_id,
        ProjectStageResourcePlan.assigned_employee_id.isnot(None),
        ProjectStageResourcePlan.planned_start.isnot(None),
        ProjectStageResourcePlan.planned_end.isnot(None),
    ).all()

    # 按员工分组
    employee_plans = {}
    for plan in plans:
        if plan.assigned_employee_id not in employee_plans:
            employee_plans[plan.assigned_employee_id] = []
        employee_plans[plan.assigned_employee_id].append(plan)

    # 检测冲突
    new_conflicts = []
    for employee_id, emp_plans in employee_plans.items():
        for i, plan_a in enumerate(emp_plans):
            for plan_b in emp_plans[i + 1:]:
                conflict = _check_time_overlap(plan_a, plan_b)
                if conflict:
                    new_conflicts.append({
                        "employee_id": employee_id,
                        "employee_name": plan_a.assigned_employee.username if plan_a.assigned_employee else None,
                        **conflict,
                    })

    return ResponseModel(data={
        "project_id": project_id,
        "has_conflicts": len(new_conflicts) > 0,
        "new_conflicts": new_conflicts,
        "conflict_count": len(new_conflicts),
    })


# ==================== Global Analytics Endpoints ====================

@router.get("/analytics/resource-conflicts", response_model=ResponseModel)
def get_all_conflicts(
    db: Session = Depends(get_db),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    include_resolved: bool = Query(False),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    全局资源冲突列表
    """
    query = db.query(ResourceConflict)

    if not include_resolved:
        query = query.filter(ResourceConflict.is_resolved == 0)
    if severity:
        query = query.filter(ResourceConflict.severity == severity)

    total = query.count()
    conflicts = apply_pagination(query.order_by(
        ResourceConflict.severity.desc(),
        ResourceConflict.overlap_start,
    ), pagination.offset, pagination.limit).all()

    result = [_format_conflict(db, c) for c in conflicts]

    return ResponseModel(data={
        "conflicts": result,
        "total": total,
        "skip": pagination.offset,
        "limit": pagination.limit,
    })


@router.get("/analytics/resource-conflicts/by-employee/{employee_id}", response_model=ResponseModel)
def get_employee_conflicts(
    employee_id: int,
    db: Session = Depends(get_db),
    include_resolved: bool = Query(False),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    特定员工的冲突
    """
    query = db.query(ResourceConflict).filter(
        ResourceConflict.employee_id == employee_id
    )

    if not include_resolved:
        query = query.filter(ResourceConflict.is_resolved == 0)

    conflicts = query.order_by(ResourceConflict.overlap_start).all()

    # 获取员工信息
    employee = db.query(User).filter(User.id == employee_id).first()

    result = [_format_conflict(db, c) for c in conflicts]

    return ResponseModel(data={
        "employee": {
            "id": employee_id,
            "name": employee.username if employee else None,
        },
        "conflicts": result,
        "total_count": len(result),
    })


@router.get("/analytics/resource-conflicts/summary", response_model=ResponseModel)
def get_conflicts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    冲突汇总统计
    """
    # 未解决冲突统计
    unresolved = db.query(
        ResourceConflict.severity,
        func.count(ResourceConflict.id).label("count"),
    ).filter(
        ResourceConflict.is_resolved == 0
    ).group_by(ResourceConflict.severity).all()

    severity_stats = {s.severity: s.count for s in unresolved}

    # 受影响员工数
    affected_employees = db.query(
        func.count(func.distinct(ResourceConflict.employee_id))
    ).filter(ResourceConflict.is_resolved == 0).scalar()

    # 受影响项目数
    affected_plans = db.query(ResourceConflict.plan_a_id, ResourceConflict.plan_b_id).filter(
        ResourceConflict.is_resolved == 0
    ).all()

    plan_ids = set()
    for p in affected_plans:
        plan_ids.add(p.plan_a_id)
        plan_ids.add(p.plan_b_id)

    affected_projects = db.query(
        func.count(func.distinct(ProjectStageResourcePlan.project_id))
    ).filter(ProjectStageResourcePlan.id.in_(plan_ids)).scalar() if plan_ids else 0

    return ResponseModel(data={
        "total_unresolved": sum(severity_stats.values()),
        "by_severity": {
            "HIGH": severity_stats.get("HIGH", 0),
            "MEDIUM": severity_stats.get("MEDIUM", 0),
            "LOW": severity_stats.get("LOW", 0),
        },
        "affected_employees": affected_employees or 0,
        "affected_projects": affected_projects or 0,
    })


@router.post("/analytics/resource-conflicts/{conflict_id}/resolve", response_model=ResponseModel)
def resolve_conflict(
    conflict_id: int,
    request: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记冲突已解决
    """
    conflict = db.query(ResourceConflict).filter(
        ResourceConflict.id == conflict_id
    ).first()

    if not conflict:
        raise HTTPException(status_code=404, detail="冲突记录不存在")

    conflict.is_resolved = 1
    conflict.resolved_by = current_user.id
    conflict.resolved_at = date.today()
    conflict.resolution_note = request.resolution_note

    db.commit()

    return ResponseModel(data={"message": "冲突已标记为已解决"})


# ==================== Helper Functions ====================

def _format_conflict(db: Session, conflict: ResourceConflict, current_project_id: int = None) -> dict:
    """格式化冲突记录"""
    plan_a = conflict.plan_a
    plan_b = conflict.plan_b

    # 获取项目信息
    project_a = db.query(Project).filter(Project.id == plan_a.project_id).first() if plan_a else None
    project_b = db.query(Project).filter(Project.id == plan_b.project_id).first() if plan_b else None

    # 确定哪个是当前项目，哪个是冲突项目
    if current_project_id:
        if plan_a.project_id == current_project_id:
            this_plan, other_plan = plan_a, plan_b
            this_project, other_project = project_a, project_b
        else:
            this_plan, other_plan = plan_b, plan_a
            this_project, other_project = project_b, project_a
    else:
        this_plan, other_plan = plan_a, plan_b
        this_project, other_project = project_a, project_b

    return {
        "id": conflict.id,
        "employee": {
            "id": conflict.employee_id,
            "name": conflict.employee.username if conflict.employee else None,
        },
        "this_project": {
            "project_id": this_plan.project_id if this_plan else None,
            "project_name": this_project.project_name if this_project else None,
            "stage_code": this_plan.stage_code if this_plan else None,
            "allocation_pct": float(this_plan.allocation_pct) if this_plan and this_plan.allocation_pct else 100,
            "period": f"{this_plan.planned_start} ~ {this_plan.planned_end}" if this_plan else None,
        },
        "conflict_with": {
            "project_id": other_plan.project_id if other_plan else None,
            "project_name": other_project.project_name if other_project else None,
            "stage_code": other_plan.stage_code if other_plan else None,
            "allocation_pct": float(other_plan.allocation_pct) if other_plan and other_plan.allocation_pct else 100,
            "period": f"{other_plan.planned_start} ~ {other_plan.planned_end}" if other_plan else None,
        },
        "overlap_period": f"{conflict.overlap_start} ~ {conflict.overlap_end}",
        "total_allocation": float(conflict.total_allocation) if conflict.total_allocation else 0,
        "over_allocation": float(conflict.over_allocation) if conflict.over_allocation else 0,
        "severity": conflict.severity,
        "is_resolved": conflict.is_resolved == 1,
        "resolution_note": conflict.resolution_note,
    }


def _check_time_overlap(plan_a: ProjectStageResourcePlan, plan_b: ProjectStageResourcePlan) -> Optional[dict]:
    """检查两个计划的时间重叠"""
    if not all([plan_a.planned_start, plan_a.planned_end, plan_b.planned_start, plan_b.planned_end]):
        return None

    overlap_start = max(plan_a.planned_start, plan_b.planned_start)
    overlap_end = min(plan_a.planned_end, plan_b.planned_end)

    if overlap_start > overlap_end:
        return None

    alloc_a = float(plan_a.allocation_pct) if plan_a.allocation_pct else 100.0
    alloc_b = float(plan_b.allocation_pct) if plan_b.allocation_pct else 100.0
    total = alloc_a + alloc_b

    if total <= 100:
        return None

    if total > 150:
        severity = "HIGH"
    elif total > 120:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "plan_a_id": plan_a.id,
        "plan_a_stage": plan_a.stage_code,
        "plan_a_project_id": plan_a.project_id,
        "plan_b_id": plan_b.id,
        "plan_b_stage": plan_b.stage_code,
        "plan_b_project_id": plan_b.project_id,
        "overlap_start": overlap_start,
        "overlap_end": overlap_end,
        "total_allocation": total,
        "over_allocation": total - 100,
        "severity": severity,
    }
