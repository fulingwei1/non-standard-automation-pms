# -*- coding: utf-8 -*-
"""
异常处理增强 API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.common.pagination import get_pagination_query, PaginationParams
from app.models.user import User
from app.schemas.production.exception_enhancement import (
    ExceptionEscalateRequest,
    ExceptionEscalateResponse,
    FlowTrackingResponse,
    KnowledgeCreateRequest,
    KnowledgeListResponse,
    KnowledgeResponse,
    ExceptionStatisticsResponse,
    PDCACreateRequest,
    PDCAAdvanceRequest,
    PDCAResponse,
    RecurrenceAnalysisResponse,
)
from app.services.production.exception.exception_enhancement_service import (
    ExceptionEnhancementService,
)

router = APIRouter()


# ==================== 异常升级 ====================

@router.post("/exception/escalate", response_model=ExceptionEscalateResponse)
def escalate_exception(
    request: ExceptionEscalateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    异常升级

    根据异常级别和处理时长进行升级：
    - LEVEL_1: 班组长处理（一般异常超过2小时）
    - LEVEL_2: 车间主任处理（重要异常超过4小时）
    - LEVEL_3: 生产经理处理（严重异常超过1小时）
    """
    service = ExceptionEnhancementService(db)
    return service.escalate_exception(
        exception_id=request.exception_id,
        escalation_level=request.escalation_level,
        reason=request.reason,
        escalated_to_id=request.escalated_to_id,
    )


# ==================== 处理流程跟踪 ====================

@router.get("/exception/{exception_id}/flow", response_model=FlowTrackingResponse)
def get_exception_flow(
    exception_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取异常处理流程跟踪"""
    service = ExceptionEnhancementService(db)
    return service.get_exception_flow(exception_id)


# ==================== 异常知识库 ====================

@router.post("/exception/knowledge", response_model=KnowledgeResponse)
def create_knowledge(
    request: KnowledgeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加知识库条目"""
    service = ExceptionEnhancementService(db)
    return service.create_knowledge(request, creator_id=current_user.id)


@router.get("/exception/knowledge/search", response_model=KnowledgeListResponse)
def search_knowledge(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    exception_type: Optional[str] = Query(None, description="异常类型"),
    exception_level: Optional[str] = Query(None, description="异常级别"),
    is_approved: Optional[bool] = Query(None, description="是否仅显示已审核"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """知识库搜索（支持关键词、异常类型匹配）"""
    service = ExceptionEnhancementService(db)
    return service.search_knowledge(
        keyword=keyword,
        exception_type=exception_type,
        exception_level=exception_level,
        is_approved=is_approved,
        offset=pagination.offset,
        limit=pagination.limit,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ==================== 异常统计分析 ====================

@router.get("/exception/statistics", response_model=ExceptionStatisticsResponse)
def get_exception_statistics(
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """异常统计分析"""
    service = ExceptionEnhancementService(db)
    return service.get_exception_statistics(start_date=start_date, end_date=end_date)


# ==================== PDCA管理 ====================

@router.post("/exception/pdca", response_model=PDCAResponse)
def create_pdca(
    request: PDCACreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建PDCA记录"""
    service = ExceptionEnhancementService(db)
    return service.create_pdca(request, current_user_id=current_user.id)


@router.put("/exception/pdca/{pdca_id}/advance", response_model=PDCAResponse)
def advance_pdca_stage(
    pdca_id: int,
    request: PDCAAdvanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """推进PDCA阶段"""
    service = ExceptionEnhancementService(db)
    return service.advance_pdca_stage(pdca_id, request)


# ==================== 重复异常分析 ====================

@router.get("/exception/recurrence", response_model=List[RecurrenceAnalysisResponse])
def analyze_recurrence(
    exception_type: Optional[str] = Query(None, description="异常类型"),
    days: int = Query(30, description="分析最近N天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重复异常分析"""
    service = ExceptionEnhancementService(db)
    return service.analyze_recurrence(exception_type=exception_type, days=days)
