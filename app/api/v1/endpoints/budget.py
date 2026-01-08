# -*- coding: utf-8 -*-
"""
项目预算管理 API
"""

from typing import Any, List, Optional
from decimal import Decimal
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.budget import ProjectBudget, ProjectBudgetItem, ProjectCostAllocationRule
from app.schemas.budget import (
    ProjectBudgetCreate, ProjectBudgetUpdate, ProjectBudgetResponse,
    ProjectBudgetItemCreate, ProjectBudgetItemUpdate, ProjectBudgetItemResponse,
    ProjectBudgetApproveRequest,
    ProjectCostAllocationRuleCreate, ProjectCostAllocationRuleUpdate,
    ProjectCostAllocationRuleResponse, ProjectCostAllocationRequest
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


def generate_budget_no(db: Session) -> str:
    """生成预算编号：BUD-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_budget = (
        db.query(ProjectBudget)
        .filter(ProjectBudget.budget_no.like(f"BUD-{today}-%"))
        .order_by(desc(ProjectBudget.budget_no))
        .first()
    )
    
    if max_budget:
        seq = int(max_budget.budget_no.split("-")[-1]) + 1
    else:
        seq = 1
    
    return f"BUD-{today}-{seq:03d}"


def generate_budget_version(db: Session, project_id: int) -> str:
    """生成预算版本号"""
    max_version = (
        db.query(ProjectBudget)
        .filter(ProjectBudget.project_id == project_id)
        .order_by(desc(ProjectBudget.version))
        .first()
    )
    
    if max_version:
        # 提取版本号并递增
        version_parts = max_version.version.split('.')
        if len(version_parts) == 2:
            major = int(version_parts[0].replace('V', ''))
            minor = int(version_parts[1])
            return f"V{major + 1}.0"
    
    return "V1.0"


# ==================== 项目预算管理 ====================

@router.get("/", response_model=PaginatedResponse[ProjectBudgetResponse])
def list_budgets(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    budget_type: Optional[str] = Query(None, description="预算类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预算列表（支持分页、筛选）
    """
    query = db.query(ProjectBudget)
    
    if project_id:
        query = query.filter(ProjectBudget.project_id == project_id)
    if status:
        query = query.filter(ProjectBudget.status == status)
    if budget_type:
        query = query.filter(ProjectBudget.budget_type == budget_type)
    
    total = query.count()
    offset = (page - 1) * page_size
    budgets = query.order_by(desc(ProjectBudget.created_at)).offset(offset).limit(page_size).all()
    
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
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/projects/{project_id}/budgets", response_model=List[ProjectBudgetResponse])
def get_project_budgets(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目的预算列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(ProjectBudget).filter(ProjectBudget.project_id == project_id)
    if status:
        query = query.filter(ProjectBudget.status == status)
    
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
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
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批预算
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    
    if budget.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只能审批已提交的预算")
    
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
    current_user: User = Depends(security.get_current_active_user),
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


# ==================== 预算明细管理 ====================

@router.get("/{budget_id}/items", response_model=List[ProjectBudgetItemResponse])
def get_budget_items(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取预算明细列表
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    
    items = db.query(ProjectBudgetItem).filter(
        ProjectBudgetItem.budget_id == budget_id
    ).order_by(ProjectBudgetItem.item_no).all()
    
    return [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) 
            for item in items]


@router.post("/{budget_id}/items", response_model=ProjectBudgetItemResponse, status_code=status.HTTP_201_CREATED)
def create_budget_item(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    item_in: ProjectBudgetItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建预算明细
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    
    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能为草稿状态的预算添加明细")
    
    item = ProjectBudgetItem(budget_id=budget_id, **item_in.model_dump())
    db.add(item)
    
    # 更新预算总额
    budget.total_amount = (budget.total_amount or 0) + item.budget_amount
    db.add(budget)
    
    db.commit()
    db.refresh(item)
    
    return ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.put("/items/{item_id}", response_model=ProjectBudgetItemResponse)
def update_budget_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    item_in: ProjectBudgetItemUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新预算明细
    """
    item = db.query(ProjectBudgetItem).filter(ProjectBudgetItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="预算明细不存在")
    
    if item.budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能更新草稿状态预算的明细")
    
    old_amount = item.budget_amount
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(item, field):
            setattr(item, field, value)
    
    # 更新预算总额
    if item_in.budget_amount is not None:
        budget = item.budget
        budget.total_amount = (budget.total_amount or 0) - old_amount + item.budget_amount
        db.add(budget)
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def delete_budget_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除预算明细
    """
    item = db.query(ProjectBudgetItem).filter(ProjectBudgetItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="预算明细不存在")
    
    if item.budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态预算的明细")
    
    budget = item.budget
    budget.total_amount = max(0, (budget.total_amount or 0) - item.budget_amount)
    db.add(budget)
    
    db.delete(item)
    db.commit()
    
    return ResponseModel(code=200, message="预算明细已删除")


# ==================== 成本分摊规则管理 ====================

@router.get("/allocation-rules", response_model=PaginatedResponse[ProjectCostAllocationRuleResponse])
def list_allocation_rules(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本分摊规则列表
    """
    query = db.query(ProjectCostAllocationRule)
    
    if is_active is not None:
        query = query.filter(ProjectCostAllocationRule.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    rules = query.order_by(desc(ProjectCostAllocationRule.created_at)).offset(offset).limit(page_size).all()
    
    items = [ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns}) 
             for rule in rules]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/allocation-rules", response_model=ProjectCostAllocationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: ProjectCostAllocationRuleCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建成本分摊规则
    """
    rule_data = rule_in.model_dump()
    rule_data['created_by'] = current_user.id
    
    rule = ProjectCostAllocationRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})


@router.get("/allocation-rules/{rule_id}", response_model=ProjectCostAllocationRuleResponse)
def get_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本分摊规则详情
    """
    rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")
    
    return ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})


@router.put("/allocation-rules/{rule_id}", response_model=ProjectCostAllocationRuleResponse)
def update_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    rule_in: ProjectCostAllocationRuleUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新成本分摊规则
    """
    rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")
    
    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(rule, field):
            setattr(rule, field, value)
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})


@router.delete("/allocation-rules/{rule_id}", status_code=status.HTTP_200_OK)
def delete_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除成本分摊规则
    """
    rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")
    
    db.delete(rule)
    db.commit()
    
    return ResponseModel(code=200, message="分摊规则已删除")

