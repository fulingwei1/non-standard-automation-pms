# -*- coding: utf-8 -*-
"""
项目预算CRUD端点
"""

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.approval import ApprovalInstance, ApprovalTask
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
from app.services.approval_engine import ApprovalEngineService
from app.utils.db_helpers import get_or_404

from .utils import generate_budget_no, generate_budget_version

router = APIRouter()
PROJECT_BUDGET_APPROVAL_ENTITY_TYPE = "PROJECT_BUDGET"
PROJECT_BUDGET_APPROVAL_TEMPLATE_CODE = "TPL_PROJECT_BUDGET"
ACTIVE_APPROVAL_STATUSES = {"PENDING", "IN_PROGRESS"}


def calculate_budget_items_total(budget: ProjectBudget) -> Decimal:
    return sum((item.budget_amount or Decimal("0")) for item in budget.items)


def sync_budget_total_from_items(db: Session, budget: ProjectBudget) -> Decimal:
    if budget.items:
        budget.total_amount = calculate_budget_items_total(budget)
        db.add(budget)
    return Decimal(str(budget.total_amount or 0))


def build_budget_response(budget: ProjectBudget, project: Optional[Project] = None) -> ProjectBudgetResponse:
    project = project or budget.project
    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "submitter_name": budget.submitter.real_name if budget.submitter else None,
        "approver_name": budget.approver.real_name if budget.approver else None,
        "items": [
            ProjectBudgetItemResponse(
                **{c.name: getattr(item, c.name) for c in item.__table__.columns}
            )
            for item in budget.items
        ],
    }
    return ProjectBudgetResponse(**budget_dict)


def build_budget_approval_form_data(budget: ProjectBudget) -> dict[str, Any]:
    item_total = calculate_budget_items_total(budget)
    return {
        "budget_id": budget.id,
        "budget_no": budget.budget_no,
        "project_id": budget.project_id,
        "budget_name": budget.budget_name,
        "budget_type": budget.budget_type,
        "version": budget.version,
        "total_amount": float(budget.total_amount or 0),
        "item_total": float(item_total),
    }


def get_active_budget_approval_instance(
    db: Session, budget_id: int
) -> Optional[ApprovalInstance]:
    return (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == PROJECT_BUDGET_APPROVAL_ENTITY_TYPE,
            ApprovalInstance.entity_id == budget_id,
            ApprovalInstance.status.in_(ACTIVE_APPROVAL_STATUSES),
        )
        .order_by(desc(ApprovalInstance.created_at), desc(ApprovalInstance.id))
        .first()
    )


def get_pending_budget_approval_task(
    db: Session, instance_id: int, user_id: int
) -> Optional[ApprovalTask]:
    return (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.assignee_id == user_id,
            ApprovalTask.status == "PENDING",
        )
        .order_by(ApprovalTask.id.asc())
        .first()
    )


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
    budgets = apply_pagination(
        query.order_by(desc(ProjectBudget.created_at)), pagination.offset, pagination.limit
    ).all()

    # 构建响应数据
    items = []
    for budget in budgets:
        budget_dict = {
            **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
            "project_code": budget.project.project_code if budget.project else None,
            "project_name": budget.project.project_name if budget.project else None,
            "submitter_name": budget.submitter.real_name if budget.submitter else None,
            "approver_name": budget.approver.real_name if budget.approver else None,
            "items": [
                ProjectBudgetItemResponse(
                    **{c.name: getattr(item, c.name) for c in item.__table__.columns}
                )
                for item in budget.items
            ],
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
    project = get_or_404(db, Project, project_id, "项目不存在")

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
            "items": [
                ProjectBudgetItemResponse(
                    **{c.name: getattr(item, c.name) for c in item.__table__.columns}
                )
                for item in budget.items
            ],
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
    budget_data = budget_in.model_dump(exclude={"items"})
    budget_data["budget_no"] = budget_no
    budget_data["version"] = version
    budget_data["created_by"] = current_user.id
    if budget_in.items:
        budget_data["total_amount"] = sum(
            (item_data.budget_amount or Decimal("0")) for item_data in budget_in.items
        )

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
        "items": [
            ProjectBudgetItemResponse(
                **{c.name: getattr(item, c.name) for c in item.__table__.columns}
            )
            for item in budget.items
        ],
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
    budget = get_or_404(db, ProjectBudget, budget_id, "预算不存在")

    budget_dict = {
        **{c.name: getattr(budget, c.name) for c in budget.__table__.columns},
        "project_code": budget.project.project_code if budget.project else None,
        "project_name": budget.project.project_name if budget.project else None,
        "submitter_name": budget.submitter.real_name if budget.submitter else None,
        "approver_name": budget.approver.real_name if budget.approver else None,
        "items": [
            ProjectBudgetItemResponse(
                **{c.name: getattr(item, c.name) for c in item.__table__.columns}
            )
            for item in budget.items
        ],
    }

    return ProjectBudgetResponse(**budget_dict)


@router.put("/{budget_id}", response_model=ProjectBudgetResponse)
def update_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    budget_in: ProjectBudgetUpdate,
    current_user: User = Depends(security.require_permission("budget:update")),
) -> Any:
    """
    更新预算（只能更新草稿状态的预算）
    """
    budget = get_or_404(db, ProjectBudget, budget_id, "预算不存在")

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
        "items": [
            ProjectBudgetItemResponse(
                **{c.name: getattr(item, c.name) for c in item.__table__.columns}
            )
            for item in budget.items
        ],
    }

    return ProjectBudgetResponse(**budget_dict)


@router.post("/{budget_id}/submit", response_model=ProjectBudgetResponse)
def submit_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.require_permission("budget:update")),
) -> Any:
    """
    提交预算审批
    """
    budget = get_or_404(db, ProjectBudget, budget_id, "预算不存在")

    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的预算")

    sync_budget_total_from_items(db, budget)
    existing = get_active_budget_approval_instance(db, budget_id)
    if existing:
        return build_budget_response(budget)

    try:
        engine = ApprovalEngineService(db)
        engine.submit(
            template_code=PROJECT_BUDGET_APPROVAL_TEMPLATE_CODE,
            entity_type=PROJECT_BUDGET_APPROVAL_ENTITY_TYPE,
            entity_id=budget_id,
            form_data=build_budget_approval_form_data(budget),
            initiator_id=current_user.id,
            title=f"项目预算审批 - {budget.budget_no}",
            summary=f"{budget.project.project_name if budget.project else '未指定项目'} / {budget.budget_name}",
            urgency="NORMAL",
            cc_user_ids=None,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    db.refresh(budget)

    return build_budget_response(budget)


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
    budget = get_or_404(db, ProjectBudget, budget_id, "预算不存在")

    instance = get_active_budget_approval_instance(db, budget_id)
    if not instance:
        raise HTTPException(
            status_code=400,
            detail="预算必须先提交统一审批，不能在模块内直接审批",
        )

    task = get_pending_budget_approval_task(db, instance.id, current_user.id)
    if not task:
        raise HTTPException(status_code=403, detail="当前用户没有该预算的待审批任务")

    engine = ApprovalEngineService(db)
    try:
        if approve_request.approved:
            engine.approve(
                task_id=task.id,
                approver_id=current_user.id,
                comment=approve_request.approval_note,
            )
        else:
            engine.reject(
                task_id=task.id,
                approver_id=current_user.id,
                comment=approve_request.approval_note or "预算审批驳回",
            )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    db.refresh(budget)

    return build_budget_response(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_200_OK)
def delete_budget(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.require_permission("budget:delete")),
) -> Any:
    """
    删除预算（只能删除草稿状态的预算）
    """
    budget = get_or_404(db, ProjectBudget, budget_id, "预算不存在")

    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态的预算")

    db.delete(budget)
    db.commit()

    return ResponseModel(code=200, message="预算已删除")
