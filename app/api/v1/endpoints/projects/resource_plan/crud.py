# -*- coding: utf-8 -*-
"""
项目资源计划 CRUD 操作

提供资源计划的增删改查功能
路由前缀: /projects/{project_id}/resource-plan/
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.resource_plan import (
    ResourcePlanCreate,
    ResourcePlanResponse,
    ResourcePlanUpdate,
    StageResourceSummary,
    ProjectResourcePlanSummary,
)
from app.services.resource_plan_service import ResourcePlanService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()

# 阶段名称映射
STAGE_NAMES = {
    "S1": "需求进入",
    "S2": "方案设计",
    "S3": "采购备料",
    "S4": "加工制造",
    "S5": "装配调试",
    "S6": "出厂验收",
    "S7": "包装发运",
    "S8": "现场安装",
    "S9": "质保结项",
}


@router.get("/", response_model=List[ResourcePlanResponse])
def list_resource_plans(
    project_id: int = Path(..., description="项目ID"),
    stage_code: Optional[str] = Query(None, description="阶段编码筛选 (S1-S9)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取项目的资源计划列表

    支持按阶段筛选
    """
    check_project_access_or_raise(db, current_user, project_id)

    plans = ResourcePlanService.get_project_resource_plans(db, project_id, stage_code)
    return plans


@router.get("/summary", response_model=ProjectResourcePlanSummary)
def get_resource_plan_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """
    获取项目资源计划汇总

    按阶段分组，显示各阶段的资源需求和填充率
    """
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取所有资源计划
    all_plans = ResourcePlanService.get_project_resource_plans(db, project_id)

    # 按阶段分组
    stages_dict = {}
    for plan in all_plans:
        if plan.stage_code not in stages_dict:
            stages_dict[plan.stage_code] = []
        stages_dict[plan.stage_code].append(plan)

    # 构建各阶段汇总
    stages = []
    for stage_code in sorted(stages_dict.keys()):
        requirements = stages_dict[stage_code]
        total_headcount = sum(r.headcount for r in requirements)
        filled_count = sum(
            r.headcount for r in requirements if r.assignment_status == "ASSIGNED"
        )
        fill_rate = ResourcePlanService.calculate_fill_rate(requirements)

        # 获取阶段的时间范围
        planned_starts = [r.planned_start for r in requirements if r.planned_start]
        planned_ends = [r.planned_end for r in requirements if r.planned_end]

        stages.append(
            StageResourceSummary(
                stage_code=stage_code,
                stage_name=STAGE_NAMES.get(stage_code, stage_code),
                planned_start=min(planned_starts) if planned_starts else None,
                planned_end=max(planned_ends) if planned_ends else None,
                requirements=requirements,
                total_headcount=total_headcount,
                filled_count=filled_count,
                fill_rate=fill_rate,
            )
        )

    # 计算总体填充率
    overall_fill_rate = ResourcePlanService.calculate_fill_rate(all_plans)

    return ProjectResourcePlanSummary(
        project_id=project_id,
        project_name=project.project_name,
        stages=stages,
        overall_fill_rate=overall_fill_rate,
    )


@router.post("/", response_model=ResourcePlanResponse, status_code=201)
def create_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_in: ResourcePlanCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """
    创建资源计划

    为项目的指定阶段创建资源需求
    """
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限为该项目创建资源计划"
    )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    plan = ResourcePlanService.create_resource_plan(db, project_id, plan_in)
    return plan


@router.get("/{plan_id}", response_model=ResourcePlanResponse)
def get_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取单个资源计划详情"""
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

    return plan


@router.put("/{plan_id}", response_model=ResourcePlanResponse)
def update_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    plan_in: ResourcePlanUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """
    更新资源计划

    可更新角色名称、需求人数、分配比例、计划时间等
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

    update_data = plan_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(plan, field):
            setattr(plan, field, value)

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


@router.delete("/{plan_id}", status_code=200)
def delete_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """
    删除资源计划

    注意：已分配人员的计划需要先释放人员才能删除
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

    if plan.assignment_status == "ASSIGNED":
        raise HTTPException(
            status_code=400,
            detail="该资源计划已分配人员，请先释放人员后再删除",
        )

    db.delete(plan)
    db.commit()

    return ResponseModel(code=200, message="资源计划已删除")
