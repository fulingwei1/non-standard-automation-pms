# -*- coding: utf-8 -*-
"""
项目资源计划自定义端点

包含汇总等功能
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.resource_plan import (
    ProjectResourcePlanSummary,
    StageResourceSummary,
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


@router.get("/summary", response_model=ProjectResourcePlanSummary)
def get_resource_plan_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目资源计划汇总"""
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
