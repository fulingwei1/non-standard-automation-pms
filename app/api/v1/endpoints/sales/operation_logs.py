# -*- coding: utf-8 -*-
"""
销售业务操作日志 API

提供操作日志的查询接口。
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.services.sales.operation_log_service import SalesOperationLogService

router = APIRouter(prefix="/operation-logs", tags=["销售操作日志"])


# ==================== 响应模型 ====================


class OperationLogResponse(BaseModel):
    """操作日志响应"""

    id: int
    entity_type: str
    entity_id: int
    entity_code: Optional[str] = None
    operation_type: str
    operation_desc: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    changed_fields: Optional[List[str]] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    operator_dept: Optional[str] = None
    operation_time: datetime
    remark: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== API 端点 ====================


@router.get("/{entity_type}/{entity_id}", response_model=PaginatedResponse[OperationLogResponse])
def get_entity_operation_logs(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取指定实体的操作日志

    - entity_type: LEAD/OPPORTUNITY/QUOTE/CONTRACT/INVOICE/CUSTOMER
    - entity_id: 实体ID
    """
    logs, total = SalesOperationLogService.get_entity_logs(
        db,
        entity_type=entity_type.upper(),
        entity_id=entity_id,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    return PaginatedResponse(
        items=[OperationLogResponse.model_validate(log) for log in logs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get("/", response_model=PaginatedResponse[OperationLogResponse])
def search_operation_logs(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    entity_type: Optional[str] = Query(None, description="实体类型筛选"),
    operation_type: Optional[str] = Query(None, description="操作类型筛选"),
    operator_id: Optional[int] = Query(None, description="操作人ID筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    搜索操作日志

    支持按实体类型、操作类型、操作人、时间范围筛选
    """
    logs, total = SalesOperationLogService.search_logs(
        db,
        entity_type=entity_type.upper() if entity_type else None,
        operation_type=operation_type.upper() if operation_type else None,
        operator_id=operator_id,
        start_time=start_time,
        end_time=end_time,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    return PaginatedResponse(
        items=[OperationLogResponse.model_validate(log) for log in logs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )
