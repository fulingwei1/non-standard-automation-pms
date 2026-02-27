# -*- coding: utf-8 -*-
"""
排产建议 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models import (
    Machine,
    Project,
    SchedulingSuggestion,
    User,
)
from app.schemas.assembly_kit import (  # Stage; Template; Category Mapping; BOM Assembly Attrs; Readiness; Shortage; Alert Rule; Suggestion; Dashboard
    SchedulingSuggestionAccept,
    SchedulingSuggestionReject,
    SchedulingSuggestionResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter
from app.utils.db_helpers import get_or_404

router = APIRouter(
    prefix="/assembly-kit/scheduling",
    tags=["scheduling"]
)

# 共 4 个路由

# ==================== 排产建议 ====================

@router.post("/suggestions/generate", response_model=ResponseModel)
async def generate_scheduling_suggestions(
    db: Session = Depends(deps.get_db),
    scope: str = Query("WEEKLY", description="排产范围：WEEKLY/MONTHLY"),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔")
):
    """生成智能排产建议"""
    from app.services.scheduling_suggestion_service import SchedulingSuggestionService

    project_id_list = None
    if project_ids:
        project_id_list = [int(x.strip()) for x in project_ids.split(",") if x.strip().isdigit()]

    suggestions = SchedulingSuggestionService.generate_scheduling_suggestions(
        db, scope=scope, project_ids=project_id_list
    )

    return ResponseModel(
        code=200,
        message="排产建议生成成功",
        data={"suggestions": suggestions, "total": len(suggestions)}
    )


@router.get("/suggestions", response_model=ResponseModel)
async def get_scheduling_suggestions(
    db: Session = Depends(deps.get_db),
    suggestion_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    project_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_query)
):
    """获取排产建议列表"""
    query = db.query(SchedulingSuggestion)

    if suggestion_status:
        query = query.filter(SchedulingSuggestion.status == suggestion_status)
    if project_id:
        query = query.filter(SchedulingSuggestion.project_id == project_id)

    total = query.count()
    suggestions = apply_pagination(query.order_by(
        SchedulingSuggestion.priority_score.desc(),
        SchedulingSuggestion.created_at.desc()
    ), pagination.offset, pagination.limit).all()

    result = []
    for s in suggestions:
        project = db.query(Project).filter(Project.id == s.project_id).first()
        machine = db.query(Machine).filter(Machine.id == s.machine_id).first() if s.machine_id else None

        data = SchedulingSuggestionResponse.model_validate(s)
        data.project_no = project.project_no if project else None
        data.project_name = project.name if project else None
        data.machine_no = machine.machine_no if machine else None
        result.append(data)

    return ResponseModel(
        code=200,
        message="success",
        data={"total": total, "items": result, "page": pagination.page, "page_size": pagination.page_size}
    )


@router.post("/suggestions/{suggestion_id}/accept", response_model=ResponseModel)
async def accept_suggestion(
    suggestion_id: int,
    accept_data: SchedulingSuggestionAccept,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """接受排产建议"""
    suggestion = get_or_404(db, SchedulingSuggestion, suggestion_id, "排产建议不存在")

    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="该建议已处理")

    suggestion.status = "accepted"
    suggestion.accepted_by = current_user.id
    suggestion.accepted_at = datetime.now()
    if accept_data.actual_start_date:
        suggestion.suggested_start_date = accept_data.actual_start_date
    suggestion.updated_at = datetime.now()

    db.commit()
    db.refresh(suggestion)

    return ResponseModel(code=200, message="已接受建议", data=SchedulingSuggestionResponse.model_validate(suggestion))


@router.post("/suggestions/{suggestion_id}/reject", response_model=ResponseModel)
async def reject_suggestion(
    suggestion_id: int,
    reject_data: SchedulingSuggestionReject,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:read"))
):
    """拒绝排产建议"""
    suggestion = get_or_404(db, SchedulingSuggestion, suggestion_id, "排产建议不存在")

    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="该建议已处理")

    suggestion.status = "rejected"
    suggestion.reject_reason = reject_data.reject_reason
    suggestion.updated_at = datetime.now()

    db.commit()
    db.refresh(suggestion)

    return ResponseModel(code=200, message="已拒绝建议", data=SchedulingSuggestionResponse.model_validate(suggestion))



