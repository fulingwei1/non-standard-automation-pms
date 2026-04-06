# -*- coding: utf-8 -*-
"""
项目资源计划自定义端点

包含汇总、冲突检测、利用率等功能
注意：路由顺序很重要！静态路径（/summary, /conflicts 等）必须在动态路径（/{plan_id}）之前注册
"""

from typing import Any

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.resource_plan import (
    ProjectResourcePlanSummary,
    StageResourceSummary,
)
from app.services.resource_plan_service import ResourcePlanService
from app.utils.db_helpers import get_or_404
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


@router.get("/conflicts", response_model=ResponseModel)
def get_resource_conflicts(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源冲突列表"""
    check_project_access_or_raise(db, current_user, project_id)
    
    conflicts = ResourcePlanService.detect_project_conflicts(db, project_id)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "conflicts": [c.model_dump() for c in conflicts],
            "conflict_count": len(conflicts),
        },
    )


@router.get("/utilization", response_model=ResponseModel)
def get_resource_utilization(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源利用率"""
    check_project_access_or_raise(db, current_user, project_id)
    
    plans = ResourcePlanService.get_project_resource_plans(db, project_id)
    
    total_headcount = sum(p.headcount for p in plans)
    assigned_count = sum(1 for p in plans if p.assignment_status == "ASSIGNED")
    utilization_rate = (assigned_count / total_headcount * 100) if total_headcount > 0 else 0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "total_headcount": total_headcount,
            "assigned_count": assigned_count,
            "utilization_rate": round(utilization_rate, 2),
        },
    )


@router.get("/timeline", response_model=ResponseModel)
def get_resource_timeline(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源时间线"""
    check_project_access_or_raise(db, current_user, project_id)
    
    plans = ResourcePlanService.get_project_resource_plans(db, project_id)
    
    timeline = []
    for plan in plans:
        timeline.append({
            "plan_id": plan.id,
            "stage_code": plan.stage_code,
            "stage_name": STAGE_NAMES.get(plan.stage_code, plan.stage_code),
            "role_code": plan.role_code,
            "role_name": plan.role_name,
            "headcount": plan.headcount,
            "planned_start": plan.planned_start.isoformat() if plan.planned_start else None,
            "planned_end": plan.planned_end.isoformat() if plan.planned_end else None,
            "assignment_status": plan.assignment_status,
        })
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "timeline": timeline,
        },
    )


@router.get("/cost", response_model=ResponseModel)
def get_resource_cost(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源成本（简化版）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "total_cost": 0,
            "note": "成本计算功能待实现",
        },
    )


@router.get("/summary", response_model=ProjectResourcePlanSummary)
def get_resource_plan_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源计划汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    project = get_or_404(db, Project, project_id, detail="项目不存在")

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
        filled_count = sum(r.headcount for r in requirements if r.assignment_status == "ASSIGNED")
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
