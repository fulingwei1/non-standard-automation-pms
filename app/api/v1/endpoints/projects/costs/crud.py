# -*- coding: utf-8 -*-
"""
项目成本 CRUD 操作

适配自 app/api/v1/endpoints/costs/basic.py
变更: 路由从 /costs/ 改为 /projects/{project_id}/costs/
"""
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import ProjectCostCreate, ProjectCostResponse, ProjectCostUpdate
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=List[ProjectCostResponse])
def list_project_costs(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """获取项目成本列表"""
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)

    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)

    costs = query.order_by(ProjectCost.created_at.desc()).all()
    return costs


@router.get("/summary", response_model=ResponseModel)
def get_project_cost_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """获取项目成本汇总"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 按类型汇总
    type_summary = (
        db.query(ProjectCost.cost_type, func.sum(ProjectCost.amount).label("total"))
        .filter(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_type)
        .all()
    )

    # 总成本
    total_cost = (
        db.query(func.sum(ProjectCost.amount))
        .filter(ProjectCost.project_id == project_id)
        .scalar()
        or Decimal("0")
    )

    return ResponseModel(
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "total_cost": float(total_cost),
            "by_type": {t.cost_type: float(t.total) for t in type_summary},
            "budget": float(project.budget) if project.budget else None,
            "budget_used_pct": (
                round(float(total_cost) / float(project.budget) * 100, 2)
                if project.budget and project.budget > 0
                else None
            ),
        }
    )


@router.post("/", response_model=ProjectCostResponse, status_code=201)
def create_project_cost(
    project_id: int = Path(..., description="项目ID"),
    cost_in: ProjectCostCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:create")),
) -> Any:
    """添加项目成本记录"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限在该项目中添加成本"
    )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    cost_data = cost_in.model_dump()
    cost_data["project_id"] = project_id
    cost_data["created_by"] = current_user.id

    cost = ProjectCost(**cost_data)
    db.add(cost)
    db.commit()
    db.refresh(cost)

    return cost


@router.get("/{cost_id}", response_model=ProjectCostResponse)
def get_project_cost(
    project_id: int = Path(..., description="项目ID"),
    cost_id: int = Path(..., description="成本ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """获取成本详情"""
    check_project_access_or_raise(db, current_user, project_id)

    cost = (
        db.query(ProjectCost)
        .filter(ProjectCost.id == cost_id, ProjectCost.project_id == project_id)
        .first()
    )

    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    return cost


@router.put("/{cost_id}", response_model=ProjectCostResponse)
def update_project_cost(
    project_id: int = Path(..., description="项目ID"),
    cost_id: int = Path(..., description="成本ID"),
    cost_in: ProjectCostUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:update")),
) -> Any:
    """更新成本记录"""
    check_project_access_or_raise(db, current_user, project_id)

    cost = (
        db.query(ProjectCost)
        .filter(ProjectCost.id == cost_id, ProjectCost.project_id == project_id)
        .first()
    )

    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    update_data = cost_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(cost, field):
            setattr(cost, field, value)

    db.add(cost)
    db.commit()
    db.refresh(cost)

    return cost


@router.delete("/{cost_id}", status_code=200)
def delete_project_cost(
    project_id: int = Path(..., description="项目ID"),
    cost_id: int = Path(..., description="成本ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:delete")),
) -> Any:
    """删除成本记录"""
    check_project_access_or_raise(db, current_user, project_id)

    cost = (
        db.query(ProjectCost)
        .filter(ProjectCost.id == cost_id, ProjectCost.project_id == project_id)
        .first()
    )

    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    db.delete(cost)
    db.commit()

    return ResponseModel(code=200, message="成本记录已删除")
