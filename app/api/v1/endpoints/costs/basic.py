"""
成本基础 CRUD 操作

提供成本记录的创建、读取、更新、删除等基础操作。
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import FinancialProjectCost, Machine, Project, ProjectCost
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    ProjectCostCreate,
    ProjectCostResponse,
    ProjectCostUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectCostResponse])
def read_costs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    cost_category: Optional[str] = Query(None, description="成本分类筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取成本记录列表（支持分页、筛选）
    """
    query = db.query(ProjectCost)

    if project_id:
        query = query.filter(ProjectCost.project_id == project_id)
    if machine_id:
        query = query.filter(ProjectCost.machine_id == machine_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)
    if cost_category:
        query = query.filter(ProjectCost.cost_category == cost_category)
    if start_date:
        try:
            start = date.fromisoformat(start_date)
            query = query.filter(ProjectCost.cost_date >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误，请使用YYYY-MM-DD格式")
    if end_date:
        try:
            end = date.fromisoformat(end_date)
            query = query.filter(ProjectCost.cost_date <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，请使用YYYY-MM-DD格式")

    total = query.count()
    offset = (page - 1) * page_size
    costs = query.order_by(desc(ProjectCost.cost_date)).offset(offset).limit(page_size).all()

    cost_items = [ProjectCostResponse.model_validate(c) for c in costs]

    return PaginatedResponse(
        items=cost_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/projects/{project_id}/costs", response_model=List[ProjectCostResponse])
def get_project_costs(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目的成本记录列表
    包含普通成本和财务修正成本，财务修正成本优先显示
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取普通成本
    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)

    if machine_id:
        query = query.filter(ProjectCost.machine_id == machine_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)

    costs = query.order_by(desc(ProjectCost.cost_date)).all()

    # 获取财务修正成本
    financial_query = db.query(FinancialProjectCost).filter(
        FinancialProjectCost.project_id == project_id
    )

    if machine_id:
        financial_query = financial_query.filter(FinancialProjectCost.machine_id == machine_id)
    if cost_type:
        financial_query = financial_query.filter(FinancialProjectCost.cost_type == cost_type)

    financial_costs = financial_query.order_by(desc(FinancialProjectCost.cost_date)).all()

    result = []

    # 先添加财务修正成本（优先）
    for fc in financial_costs:
        cost_dict = {
            "id": fc.id,
            "project_id": fc.project_id,
            "machine_id": fc.machine_id,
            "cost_type": fc.cost_type,
            "cost_category": fc.cost_category,
            "amount": float(fc.amount) if fc.amount else 0,
            "tax_amount": float(fc.tax_amount) if fc.tax_amount else 0,
            "cost_date": fc.cost_date,
            "description": fc.description or f"{fc.cost_item}（财务修正）",
            "source_type": "FINANCIAL_UPLOAD",
            "source_no": fc.source_no,
            "created_at": fc.created_at,
            "updated_at": fc.updated_at,
            "is_financial_correction": True,
            "upload_batch_no": fc.upload_batch_no,
        }
        result.append(ProjectCostResponse(**cost_dict))

    # 添加普通成本（排除已被财务修正覆盖的类型）
    financial_cost_types = {fc.cost_type for fc in financial_costs}
    for cost in costs:
        if cost.cost_type not in financial_cost_types:
            cost_response = ProjectCostResponse.model_validate(cost)
            cost_response.is_financial_correction = False
            cost_response.upload_batch_no = None
            result.append(cost_response)

    # 按日期倒序排序
    result.sort(key=lambda x: x.cost_date, reverse=True)

    return result


@router.post("/", response_model=ProjectCostResponse)
def create_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: ProjectCostCreate,
    current_user: User = Depends(security.require_permission("cost:create")),
) -> Any:
    """
    创建成本记录
    """
    project = db.query(Project).filter(Project.id == cost_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 如果指定了机台ID，验证机台是否存在且属于该项目
    if cost_in.machine_id:
        machine = db.query(Machine).filter(
            Machine.id == cost_in.machine_id,
            Machine.project_id == cost_in.project_id
        ).first()
        if not machine:
            raise HTTPException(
                status_code=404,
                detail="机台不存在或不属于该项目"
            )

    cost_data = cost_in.model_dump()
    cost_data['created_by'] = current_user.id

    cost = ProjectCost(**cost_data)
    db.add(cost)

    # 更新项目的实际成本
    project.actual_cost = (project.actual_cost or 0) + cost.amount
    db.add(project)

    db.commit()
    db.refresh(cost)
    return cost


@router.post("/projects/{project_id}/costs", response_model=ProjectCostResponse)
def create_project_cost(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    cost_in: ProjectCostCreate,
    current_user: User = Depends(security.require_permission("cost:create")),
) -> Any:
    """
    为项目创建成本记录
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 确保project_id一致
    cost_data = cost_in.model_dump()
    cost_data['project_id'] = project_id
    cost_data['created_by'] = current_user.id

    # 如果指定了机台ID，验证机台是否存在且属于该项目
    if cost_data.get('machine_id'):
        machine = db.query(Machine).filter(
            Machine.id == cost_data['machine_id'],
            Machine.project_id == project_id
        ).first()
        if not machine:
            raise HTTPException(
                status_code=404,
                detail="机台不存在或不属于该项目"
            )

    cost = ProjectCost(**cost_data)
    db.add(cost)

    # 更新项目的实际成本
    project.actual_cost = (project.actual_cost or 0) + cost.amount
    db.add(project)

    db.commit()
    db.refresh(cost)
    return cost


@router.get("/{cost_id}", response_model=ProjectCostResponse)
def read_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取成本记录详情
    """
    cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")
    return cost


@router.put("/{cost_id}", response_model=ProjectCostResponse)
def update_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    cost_in: ProjectCostUpdate,
    current_user: User = Depends(security.require_permission("cost:update")),
) -> Any:
    """
    更新成本记录
    """
    cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    # 记录旧金额，用于更新项目实际成本
    old_amount = cost.amount

    update_data = cost_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(cost, field):
            setattr(cost, field, value)

    # 更新项目的实际成本（减去旧金额，加上新金额）
    project = db.query(Project).filter(Project.id == cost.project_id).first()
    if project:
        project.actual_cost = (project.actual_cost or 0) - old_amount + cost.amount
        db.add(project)

    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


@router.delete("/{cost_id}", status_code=200)
def delete_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.require_permission("cost:delete")),
) -> Any:
    """
    删除成本记录
    """
    cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    # 更新项目的实际成本（减去删除的金额）
    project = db.query(Project).filter(Project.id == cost.project_id).first()
    if project:
        project.actual_cost = max(0, (project.actual_cost or 0) - cost.amount)
        db.add(project)

    db.delete(cost)
    db.commit()

    return ResponseModel(code=200, message="成本记录已删除")
