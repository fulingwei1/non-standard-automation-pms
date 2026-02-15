# -*- coding: utf-8 -*-
"""
标准成本历史记录端点
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.standard_cost import StandardCost, StandardCostHistory
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.standard_cost import StandardCostHistoryResponse

router = APIRouter()


@router.get("/history", response_model=PaginatedResponse[StandardCostHistoryResponse])
def get_standard_cost_history(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    cost_id: Optional[int] = Query(None, description="标准成本ID筛选"),
    change_type: Optional[str] = Query(None, description="变更类型筛选"),
    date_from: Optional[date] = Query(None, description="变更日期起"),
    date_to: Optional[date] = Query(None, description="变更日期止"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取标准成本历史变动记录
    
    支持按成本ID、变更类型、日期范围筛选
    权限要求：cost:read
    """
    query = db.query(StandardCostHistory)
    
    # 应用筛选
    if cost_id:
        query = query.filter(StandardCostHistory.standard_cost_id == cost_id)
    if change_type:
        query = query.filter(StandardCostHistory.change_type == change_type)
    if date_from:
        query = query.filter(StandardCostHistory.change_date >= date_from)
    if date_to:
        query = query.filter(StandardCostHistory.change_date <= date_to)
    
    total = query.count()
    history_records = apply_pagination(
        query.order_by(desc(StandardCostHistory.change_date)),
        pagination.offset,
        pagination.limit
    ).all()
    
    return pagination.to_response(history_records, total)


@router.get("/{cost_id}/history", response_model=List[StandardCostHistoryResponse])
def get_cost_history_by_id(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取特定标准成本的历史记录
    
    权限要求：cost:read
    """
    # 检查成本是否存在
    cost = db.query(StandardCost).filter(StandardCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="标准成本不存在")
    
    history_records = db.query(StandardCostHistory).filter(
        StandardCostHistory.standard_cost_id == cost_id
    ).order_by(desc(StandardCostHistory.change_date)).all()
    
    return history_records


@router.get("/{cost_id}/versions", response_model=List[dict])
def get_cost_versions(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取标准成本的所有版本
    
    返回包括当前版本和所有历史版本
    权限要求：cost:read
    """
    # 获取当前成本
    cost = db.query(StandardCost).filter(StandardCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="标准成本不存在")
    
    # 获取所有版本（当前成本和其所有父级）
    versions = []
    current = cost
    
    while current:
        versions.append({
            "id": current.id,
            "version": current.version,
            "cost_code": current.cost_code,
            "cost_name": current.cost_name,
            "standard_cost": current.standard_cost,
            "currency": current.currency,
            "unit": current.unit,
            "effective_date": current.effective_date,
            "expiry_date": current.expiry_date,
            "is_active": current.is_active,
            "created_at": current.created_at,
            "updated_at": current.updated_at,
            "created_by": current.created_by,
            "updated_by": current.updated_by
        })
        
        # 获取父版本
        if current.parent_id:
            current = db.query(StandardCost).filter(StandardCost.id == current.parent_id).first()
        else:
            current = None
    
    return versions
