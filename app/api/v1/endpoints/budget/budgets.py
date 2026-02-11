# -*- coding: utf-8 -*-
"""
项目预算CRUD端点
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.project import Project
from app.models.user import User
from app.schemas.budget import (
    ProjectBudgetApproveRequest,
    ProjectBudgetCreate,
    ProjectBudgetItemResponse,
    ProjectBudgetResponse,
    ProjectBudgetUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import generate_budget_no, generate_budget_version

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectBudgetResponse])
def list_budgets(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    budget_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    budget_type: Optional[str] = Query(None, description="预算类型筛选"),
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    获取预算列表（支持分页、筛选）
    """
    query = db.query(ProjectBudget)

    if project_id:
        query = query.filter(ProjectBudget.project_id == project_id)
    if budget_status:
        query = query.filter(ProjectBudget.status == budget_status)
    if budget_type:
        query = query.filter(ProjectBudget.budget_type == budget_type)

    total = query.count()
    budgets = apply_pagination(query.order_by(desc(ProjectBudget.created_at)), pagination.offset, pagination.limit).all()

    # 构建响应数据
    items = []
    for budget in budgets:
        budget_dict = {
            **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
            "project_code": budget.project.project_code if budget.project else None,
            "project_name": budget.project.project_name if budget.project else None,
            "submitter_name": budget.submitter.real_name if budget.submitter else None,
            "approver_name": budget.approver.real_name if budget.approver else None,
            "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                     for item in budget.items]
        }
        items.append(ProjectBudgetResponse(**budget_dict))

    return pagination.to_response(items, total)


@router.get("/projects/{project_id}/budgets", response_model=List[ProjectBudgetResponse])
def get_project_budgets(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    budget_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    获取项目的预算列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(ProjectBudget).filter(ProjectBudget.project_id == project_id)
    if budget_status:
        query = query.filter(ProjectBudget.status == budget_status)

    budgets = query.order_by(desc(ProjectBudget.version)).all()

    items = []
    for budget in budgets:
        budget_dict = {
            **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
            "project_code": project.project_code,
            "project_name": project.project_name,
            "submitter_name": budget.submitter.real_name if budget.submitter else None,
            "approver_name": budget.approver.real_name if budget.approver else None,
            "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                     for item in budget.items]
        }
        items.append(ProjectBudgetResponse(**budget_dict))

    return items


@router.post("/", response_model=ProjectBudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_in: ProjectBudgetCreate,
    current_user: User = Depends(security.require_permission("budget:create")),
) -> Any:
    """
    创建项目预算
    """
    project = db.query(Project).filter(Project.id == budget_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 生成预算编号和版本号
    budget_no = generate_budget_no(db)
    version = generate_budget_version(db, budget_in.project_id)

    # 创建预算
    budget_data = budget_in.model_dump(exclude={'items'})
    budget_data['budget_no'] = budget_no
    budget_data['version'] = version
    budget_data['created_by'] = current_user.id

    budget = ProjectBudget(**budget_data)
    db.add(budget)
    db.flush()

    # 创建预算明细
    if budget_in.items:
        for item_data in budget_in.items:
            item = ProjectBudgetItem(budget_id=budget.id, **item_data.model_dump())
            db.add(item)

    # 如果是初始预算且审批通过，更新项目预算金额
    if budget_in.budget_type == "INITIAL" and budget.status == "APPROVED":
        project.budget_amount = budget.total_amount
        db.add(project)

    db.commit()
    db.refresh(budget)

    # 构建响应
    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": project.project_code,
        "project_name": project.project_name,
        "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                 for item in budget.items]
    }

    return ProjectBudgetResponse(**budget_dict)


@router.get("/{budget_id}", response_model=ProjectBudgetResponse)
def get_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    获取预算详情
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": budget.project.project_code if budget.project else None,
        "project_name": budget.project.project_name if budget.project else None,
        "submitter_name": budget.submitter.real_name if budget.submitter else None,
        "approver_name": budget.approver.real_name if budget.approver else None,
        "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                 for item in budget.items]
    }

    return ProjectBudgetResponse(**budget_dict)


@router.put("/{budget_id}", response_model=ProjectBudgetResponse)
def update_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    budget_in: ProjectBudgetUpdate,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    更新预算（只能更新草稿状态的预算）
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能更新草稿状态的预算")

    update_data = budget_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(budget, field):
            setattr(budget, field, value)

    db.add(budget)
    db.commit()
    db.refresh(budget)

    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": budget.project.project_code if budget.project else None,
        "project_name": budget.project.project_name if budget.project else None,
        "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                 for item in budget.items]
    }

    return ProjectBudgetResponse(**budget_dict)


@router.post("/{budget_id}/submit", response_model=ProjectBudgetResponse)
def submit_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    提交预算审批
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的预算")

    budget.status = "SUBMITTED"
    budget.submitted_at = datetime.now()
    budget.submitted_by = current_user.id

    db.add(budget)
    db.commit()
    db.refresh(budget)

    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": budget.project.project_code if budget.project else None,
        "project_name": budget.project.project_name if budget.project else None,
        "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                 for item in budget.items]
    }

    return ProjectBudgetResponse(**budget_dict)


@router.post("/{budget_id}/approve", response_model=ProjectBudgetResponse)
def approve_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    approve_request: ProjectBudgetApproveRequest,
    current_user: User = Depends(security.require_permission("budget:approve")),
) -> Any:
    """
    审批预算
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    if budget.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只���审批已提交的预算")

    if approve_request.approved:
        budget.status = "APPROVED"
        budget.approved_at = datetime.now()
        budget.approved_by = current_user.id

        # 如果是初始预算或修订预算，更新项目预算金额
        if budget.budget_type in ["INITIAL", "REVISED"]:
            project = db.query(Project).filter(Project.id == budget.project_id).first()
            if project:
                project.budget_amount = budget.total_amount
                db.add(project)

        # 将其他版本的预算设为非生效
        db.query(ProjectBudget).filter(
            ProjectBudget.project_id == budget.project_id,
            ProjectBudget.id != budget_id,
            ProjectBudget.is_active == True
        ).update({"is_active": False})

        budget.is_active = True
    else:
        budget.status = "REJECTED"
        budget.approved_at = datetime.now()
        budget.approved_by = current_user.id

    if approve_request.approval_note:
        budget.approval_note = approve_request.approval_note

    db.add(budget)
    db.commit()
    db.refresh(budget)

    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": budget.project.project_code if budget.project else None,
        "project_name": budget.project.project_name if budget.project else None,
        "items": [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
                 for item in budget.items]
    }

    return ProjectBudgetResponse(**budget_dict)


@router.delete("/{budget_id}", status_code=status.HTTP_200_OK)
def delete_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    删除预算（只能删除草稿状态的预算）
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态的预算")

    db.delete(budget)
    db.commit()

    return ResponseModel(code=200, message="预算已删除")
