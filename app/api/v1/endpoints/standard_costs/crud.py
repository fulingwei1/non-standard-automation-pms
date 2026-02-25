# -*- coding: utf-8 -*-
"""
标准成本CRUD端点
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.standard_cost import StandardCost, StandardCostHistory
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.standard_cost import (
    StandardCostCreate,
    StandardCostResponse,
    StandardCostUpdate,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/", response_model=StandardCostResponse, status_code=status.HTTP_201_CREATED)
def create_standard_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: StandardCostCreate,
    current_user: User = Depends(security.require_permission("cost:manage")),
) -> Any:
    """
    创建标准成本
    
    权限要求：cost:manage
    """
    # 检查成本编码是否已存在
    existing = db.query(StandardCost).filter(
        StandardCost.cost_code == cost_in.cost_code,
        StandardCost.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"成本编码 {cost_in.cost_code} 已存在且有效"
        )
    
    # 创建标准成本
    cost_data = cost_in.model_dump()
    cost_data['created_by'] = current_user.id
    cost_data['version'] = 1
    cost_data['is_active'] = True
    
    cost = StandardCost(**cost_data)
    db.add(cost)
    db.flush()
    
    # 创建历史记录
    history = StandardCostHistory(
        standard_cost_id=cost.id,
        change_type="CREATE",
        change_date=date.today(),
        new_cost=cost.standard_cost,
        new_effective_date=cost.effective_date,
        change_reason="创建标准成本",
        change_description=f"创建成本项：{cost.cost_name}",
        changed_by=current_user.id,
        changed_by_name=current_user.real_name
    )
    db.add(history)
    db.commit()
    db.refresh(cost)
    
    return cost


@router.get("/", response_model=PaginatedResponse[StandardCostResponse])
def list_standard_costs(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    cost_category: Optional[str] = Query(None, description="成本类别筛选"),
    cost_source: Optional[str] = Query(None, description="成本来源筛选"),
    is_active: Optional[bool] = Query(None, description="是否有效"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取标准成本列表（支持分页、筛选）
    
    权限要求：cost:read
    """
    query = db.query(StandardCost)
    
    # 应用筛选
    if cost_category:
        query = query.filter(StandardCost.cost_category == cost_category)
    if cost_source:
        query = query.filter(StandardCost.cost_source == cost_source)
    if is_active is not None:
        query = query.filter(StandardCost.is_active == is_active)
    
    total = query.count()
    costs = apply_pagination(
        query.order_by(desc(StandardCost.created_at)),
        pagination.offset,
        pagination.limit
    ).all()
    
    return pagination.to_response(costs, total)


@router.get("/search", response_model=List[StandardCostResponse])
def search_standard_costs(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词（编码或名称）"),
    cost_category: Optional[str] = Query(None, description="成本类别筛选"),
    cost_source: Optional[str] = Query(None, description="成本来源筛选"),
    is_active: Optional[bool] = Query(True, description="是否有效"),
    effective_date_from: Optional[date] = Query(None, description="生效日期起"),
    effective_date_to: Optional[date] = Query(None, description="生效日期止"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    搜索标准成本
    
    支持多条件组合搜索
    权限要求：cost:read
    """
    query = db.query(StandardCost)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                StandardCost.cost_code.like(f"%{keyword}%"),
                StandardCost.cost_name.like(f"%{keyword}%"),
                StandardCost.specification.like(f"%{keyword}%")
            )
        )
    
    # 分类筛选
    if cost_category:
        query = query.filter(StandardCost.cost_category == cost_category)
    if cost_source:
        query = query.filter(StandardCost.cost_source == cost_source)
    if is_active is not None:
        query = query.filter(StandardCost.is_active == is_active)
    
    # 日期范围筛选
    if effective_date_from:
        query = query.filter(StandardCost.effective_date >= effective_date_from)
    if effective_date_to:
        query = query.filter(
            or_(
                StandardCost.expiry_date == None,
                StandardCost.expiry_date <= effective_date_to
            )
        )
    
    costs = query.order_by(StandardCost.cost_code, desc(StandardCost.version)).limit(100).all()
    
    return costs


@router.get("/{cost_id}", response_model=StandardCostResponse)
def get_standard_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取标准成本详情
    
    权限要求：cost:read
    """
    cost = get_or_404(db, StandardCost, cost_id, "标准成本不存在")
    
    return cost


@router.put("/{cost_id}", response_model=StandardCostResponse)
def update_standard_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    cost_in: StandardCostUpdate,
    current_user: User = Depends(security.require_permission("cost:manage")),
) -> Any:
    """
    更新标准成本
    
    创建新版本，保留历史版本
    权限要求：cost:manage
    """
    old_cost = get_or_404(db, StandardCost, cost_id, "标准成本不存在")
    
    # 停用旧版本
    old_cost.is_active = False
    old_cost.updated_by = current_user.id
    
    # 创建新版本
    new_cost_data = old_cost.__dict__.copy()
    new_cost_data.pop('_sa_instance_state', None)
    new_cost_data.pop('id', None)
    new_cost_data.pop('created_at', None)
    new_cost_data.pop('updated_at', None)
    
    # 应用更新
    update_data = cost_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        new_cost_data[field] = value
    
    new_cost_data['version'] = old_cost.version + 1
    new_cost_data['parent_id'] = old_cost.id
    new_cost_data['is_active'] = True
    new_cost_data['updated_by'] = current_user.id
    
    new_cost = StandardCost(**new_cost_data)
    db.add(new_cost)
    db.flush()
    
    # 创建历史记录
    history = StandardCostHistory(
        standard_cost_id=new_cost.id,
        change_type="UPDATE",
        change_date=date.today(),
        old_cost=old_cost.standard_cost,
        new_cost=new_cost.standard_cost,
        old_effective_date=old_cost.effective_date,
        new_effective_date=new_cost.effective_date,
        change_reason=update_data.get('notes', '更新标准成本'),
        change_description=f"从版本 {old_cost.version} 更新到 {new_cost.version}",
        changed_by=current_user.id,
        changed_by_name=current_user.real_name
    )
    db.add(history)
    db.commit()
    db.refresh(new_cost)
    
    return new_cost


@router.delete("/{cost_id}", response_model=ResponseModel)
def deactivate_standard_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.require_permission("cost:manage")),
) -> Any:
    """
    停用标准成本（软删除）
    
    权限要求：cost:manage
    """
    cost = get_or_404(db, StandardCost, cost_id, "标准成本不存在")
    
    if not cost.is_active:
        raise HTTPException(status_code=400, detail="标准成本已停用")
    
    cost.is_active = False
    cost.updated_by = current_user.id
    cost.expiry_date = date.today()
    
    # 创建历史记录
    history = StandardCostHistory(
        standard_cost_id=cost.id,
        change_type="DEACTIVATE",
        change_date=date.today(),
        change_reason="停用标准成本",
        change_description=f"停用成本项：{cost.cost_name}",
        changed_by=current_user.id,
        changed_by_name=current_user.real_name
    )
    db.add(history)
    db.commit()
    
    return ResponseModel(code=200, message="标准成本已停用", data={"id": cost_id})
