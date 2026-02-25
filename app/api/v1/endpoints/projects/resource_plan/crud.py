# -*- coding: utf-8 -*-
"""
项目资源计划 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
复杂逻辑通过覆盖端点实现
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.resource_plan import (
    ResourcePlanCreate,
    ResourcePlanUpdate,
    ResourcePlanResponse,
)
from app.services.resource_plan_service import ResourcePlanService
from app.utils.permission_helpers import check_project_access_or_raise
from app.utils.db_helpers import delete_obj, get_or_404, save_obj


def filter_by_stage(query, stage_code: str):
    """自定义阶段筛选器"""
    return query.filter(ProjectStageResourcePlan.stage_code == stage_code)


# 使用项目中心CRUD路由基类创建路由
base_router = create_project_crud_router(
    model=ProjectStageResourcePlan,
    create_schema=ResourcePlanCreate,
    update_schema=ResourcePlanUpdate,
    response_schema=ResourcePlanResponse,
    permission_prefix="project",
    project_id_field="project_id",
    keyword_fields=["role_name", "remark"],
    default_order_by="stage_code",
    default_order_direction="asc",
    custom_filters={
        "stage_code": filter_by_stage,  # 支持 ?stage_code=S1 筛选
    },
)

# 创建新的router，先添加覆盖的端点，再添加基类的其他端点
router = APIRouter()


# 覆盖创建端点，使用服务层创建资源计划
@router.post("/", response_model=ResourcePlanResponse, status_code=201)
def create_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_in: ResourcePlanCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """创建资源计划（覆盖基类端点，使用服务层）"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限为该项目创建资源计划"
    )
    
    get_or_404(db, Project, project_id, detail="项目不存在")
    
    plan = ResourcePlanService.create_resource_plan(db, project_id, plan_in)
    return plan


# 覆盖删除端点，添加业务逻辑检查
@router.delete("/{plan_id}", status_code=204, response_model=None)
def delete_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """删除资源计划（覆盖基类端点，添加业务逻辑检查）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    plan = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.id == plan_id,
        ProjectStageResourcePlan.project_id == project_id,
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")
    
    if plan.assignment_status == "ASSIGNED":
        raise HTTPException(
            status_code=400,
            detail="该资源计划已分配人员，请先释放人员后再删除",
        )
    
    delete_obj(db, plan)


# 覆盖列表端点，使用服务层获取资源计划
@router.get("/", response_model=List[ResourcePlanResponse])
def list_resource_plans(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    stage_code: Optional[str] = Query(None, description="阶段编码筛选 (S1-S9)"),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取项目的资源计划列表（覆盖基类端点，使用服务层）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    plans = ResourcePlanService.get_project_resource_plans(db, project_id, stage_code)
    return plans


# 覆盖详情端点，使用正确的路径参数名
@router.get("/{plan_id}", response_model=ResourcePlanResponse)
def get_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:read")),
) -> Any:
    """获取单个资源计划详情"""
    check_project_access_or_raise(db, current_user, project_id)
    
    plan = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.id == plan_id,
        ProjectStageResourcePlan.project_id == project_id,
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")
    
    return plan


# 覆盖更新端点，使用正确的路径参数名
@router.put("/{plan_id}", response_model=ResourcePlanResponse)
def update_resource_plan(
    project_id: int = Path(..., description="项目ID"),
    plan_id: int = Path(..., description="资源计划ID"),
    plan_in: ResourcePlanUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:update")),
) -> Any:
    """更新资源计划"""
    check_project_access_or_raise(db, current_user, project_id)
    
    plan = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.id == plan_id,
        ProjectStageResourcePlan.project_id == project_id,
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="资源计划不存在")
    
    update_data = plan_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(plan, field):
            setattr(plan, field, value)
    
    save_obj(db, plan)
    
    return plan
