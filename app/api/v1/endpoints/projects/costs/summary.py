# -*- coding: utf-8 -*-
"""
项目成本汇总（使用统一统计服务）

使用统一统计服务重构，减少代码重复
"""

from typing import Any
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.project_statistics_service import CostStatisticsService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/summary", response_model=ResponseModel)
def get_project_cost_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """获取项目成本汇总（使用统一统计服务）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = CostStatisticsService(db)
    summary = service.get_summary(project_id)
    
    return ResponseModel(data=summary)
