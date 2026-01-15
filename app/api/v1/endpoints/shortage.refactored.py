# -*- coding: utf-8 -*-
"""
缺料管理 API endpoints (重构版)
"""

from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse

# 导入重构后的服务
from app.services.shortage.shortage_management_service import ShortageManagementService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
def read_shortage_list(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取缺料列表"""
    service = ShortageManagementService(db)
    return service.get_shortage_list(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status
    )


@router.post("/", response_model=ResponseModel)
def create_shortage_record(
    data: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """创建缺料记录"""
    service = ShortageManagementService(db)
    result = service.create_shortage_record(data, current_user)
    return ResponseModel(message="缺料记录创建成功", data=result)


@router.get("/statistics")
def get_shortage_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """获取缺料统计"""
    service = ShortageManagementService(db)
    return service.get_shortage_statistics()


# 其他接口可以根据需要添加...