# -*- coding: utf-8 -*-
"""
项目资源计划人员分配操作

提供人员分配和释放功能
路由前缀: /projects/{project_id}/resource-plan/
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.resource_plan import (
    ResourceAssignment,
    ResourcePlanResponse,
)
from app.services.resource_plan_service import ResourcePlanService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.post("/{plan_id}/assign", response_model=ResourcePlanResponse)
def assign_employee(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    assignment: ResourceAssignment = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """
    分配员工到资源计划

    - 自动检测资源冲突（时间重叠 + 分配比例超过100%）
    - 如果存在冲突，返回 409 状态码和冲突详情
    - 使用 force=true 可以强制分配（忽略冲突）
    """
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限为该项目分配资源"
    )

    # 验证计划存在且属于该项目
    plan = (
        db.query(ProjectStageResourcePlan)
        .filter(
            ProjectStageResourcePlan.id == plan_id,
            ProjectStageResourcePlan.project_id == project_id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")

    if plan.assignment_status == "ASSIGNED" and not assignment.force:
        raise HTTPException(
            status_code=400,
            detail="该资源计划已分配人员，如需重新分配请先释放",
        )

    # 验证员工存在
    employee = db.query(User).filter(User.id == assignment.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    try:
        updated_plan, conflict = ResourcePlanService.assign_employee(
            db, plan_id, assignment.employee_id, assignment.force
        )

        if conflict:
            # 返回冲突信息
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "存在资源冲突",
                    "conflict": conflict.model_dump(),
                    "hint": "使用 force=true 可以强制分配",
                },
            )

        return updated_plan

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plan_id}/release", response_model=ResourcePlanResponse)
def release_employee(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """
    释放资源计划中的员工分配

    将计划状态改为 RELEASED，清除分配的员工
    """
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限释放该项目的资源"
    )

    # 验证计划存在且属于该项目
    plan = (
        db.query(ProjectStageResourcePlan)
        .filter(
            ProjectStageResourcePlan.id == plan_id,
            ProjectStageResourcePlan.project_id == project_id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")

    if plan.assignment_status != "ASSIGNED":
        raise HTTPException(
            status_code=400,
            detail=f"该资源计划当前状态为 {plan.assignment_status}，无法释放",
        )

    try:
        updated_plan = ResourcePlanService.release_employee(db, plan_id)
        return updated_plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{plan_id}/check-conflict", response_model=ResponseModel)
def check_assignment_conflict(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    employee_id: int = Path(..., description="员工ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    检查分配是否会产生冲突（预检查）

    在实际分配前检查是否会有冲突，不会修改任何数据
    """
    check_project_access_or_raise(db, current_user, project_id)

    plan = (
        db.query(ProjectStageResourcePlan)
        .filter(
            ProjectStageResourcePlan.id == plan_id,
            ProjectStageResourcePlan.project_id == project_id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")

    conflict = ResourcePlanService.check_assignment_conflict(
        db,
        employee_id,
        project_id,
        plan.planned_start,
        plan.planned_end,
        plan.allocation_pct,
    )

    if conflict:
        return ResponseModel(
            code=409,
            message="存在资源冲突",
            data={"has_conflict": True, "conflict": conflict.model_dump()},
        )

    return ResponseModel(
        code=200,
        message="无冲突",
        data={"has_conflict": False},
    )
