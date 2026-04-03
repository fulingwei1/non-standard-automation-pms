# -*- coding: utf-8 -*-
"""
知识检索与管理 API
支持按项目类型/产品/客户、风险类型、问题类型等多维检索
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.knowledge_base import KnowledgeEntryCreate, KnowledgeEntryUpdate
from app.services.knowledge.search_service import KnowledgeSearchService

router = APIRouter()


def _entry_to_dict(e) -> dict:
    """将 KnowledgeEntry 转为响应字典"""
    return {
        "id": e.id,
        "entry_code": e.entry_code,
        "knowledge_type": e.knowledge_type.value if hasattr(e.knowledge_type, "value") else str(e.knowledge_type),
        "source_type": e.source_type.value if hasattr(e.source_type, "value") else str(e.source_type),
        "title": e.title,
        "summary": e.summary,
        "detail": e.detail,
        "problem_description": e.problem_description,
        "solution": e.solution,
        "root_cause": e.root_cause,
        "impact": e.impact,
        "prevention": e.prevention,
        "source_project_id": e.source_project_id,
        "source_record_id": e.source_record_id,
        "source_record_type": e.source_record_type,
        "project_type": e.project_type,
        "product_category": e.product_category,
        "industry": e.industry,
        "customer_id": e.customer_id,
        "applicable_stages": e.applicable_stages,
        "tags": e.tags,
        "risk_type": e.risk_type,
        "issue_category": e.issue_category,
        "change_type": e.change_type,
        "view_count": e.view_count,
        "cite_count": e.cite_count,
        "usefulness_score": float(e.usefulness_score or 0),
        "vote_count": e.vote_count,
        "status": e.status.value if hasattr(e.status, "value") else str(e.status),
        "ai_generated": e.ai_generated,
        "ai_confidence": float(e.ai_confidence) if e.ai_confidence else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        "source_project_name": (
            e.source_project.project_name if e.source_project else None
        ),
        "customer_name": (
            e.customer.customer_name if e.customer else None
        ),
    }


@router.get("/search", response_model=ResponseModel)
def search_knowledge(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    knowledge_type: Optional[str] = Query(None, description="知识类型"),
    source_type: Optional[str] = Query(None, description="来源类型"),
    project_type: Optional[str] = Query(None, description="项目类型"),
    product_category: Optional[str] = Query(None, description="产品类别"),
    industry: Optional[str] = Query(None, description="行业"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    risk_type: Optional[str] = Query(None, description="风险类型"),
    issue_category: Optional[str] = Query(None, description="问题分类"),
    change_type: Optional[str] = Query(None, description="变更类型"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    知识多维检索

    支持维度：
    - 关键词搜索（标题、摘要、问题描述、解决方案）
    - 按项目类型/产品/客户检索经验
    - 按风险类型检索应对措施
    - 按问题类型检索解决方案
    - 按变更类型检索变更经验
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    service = KnowledgeSearchService(db)
    result = service.search(
        keyword=keyword,
        knowledge_type=knowledge_type,
        source_type=source_type,
        project_type=project_type,
        product_category=product_category,
        industry=industry,
        customer_id=customer_id,
        risk_type=risk_type,
        issue_category=issue_category,
        change_type=change_type,
        tags=tag_list,
        status=status,
        page=page,
        page_size=page_size,
    )

    items_data = [_entry_to_dict(e) for e in result["items"]]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "items": items_data,
        },
    )


@router.get("/entries/{entry_id}", response_model=ResponseModel)
def get_knowledge_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取知识条目详情"""
    service = KnowledgeSearchService(db)
    entry = service.get_by_id(entry_id)
    if not entry:
        return ResponseModel(code=404, message="知识条目不存在", data=None)

    return ResponseModel(code=200, message="success", data=_entry_to_dict(entry))


@router.post("/entries/{entry_id}/vote", response_model=ResponseModel)
def vote_knowledge(
    entry_id: int,
    score: float = Query(..., ge=0, le=5, description="评分 0-5"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """为知识条目投票/评分"""
    service = KnowledgeSearchService(db)
    entry = service.vote(entry_id, score)
    db.commit()
    return ResponseModel(
        code=200,
        message="投票成功",
        data={"usefulness_score": float(entry.usefulness_score), "vote_count": entry.vote_count},
    )


@router.put("/entries/{entry_id}/publish", response_model=ResponseModel)
def publish_knowledge(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """发布知识条目（将草稿状态改为已发布）"""
    from app.models.knowledge_base import KnowledgeEntry, KnowledgeStatusEnum
    from datetime import datetime

    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
    if not entry:
        return ResponseModel(code=404, message="知识条目不存在", data=None)

    entry.status = KnowledgeStatusEnum.PUBLISHED
    entry.reviewed_by = current_user.id
    entry.reviewed_at = datetime.now()
    db.commit()

    return ResponseModel(code=200, message="已发布", data={"id": entry.id, "status": "PUBLISHED"})


@router.get("/statistics", response_model=ResponseModel)
def get_knowledge_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """知识库统计概览"""
    service = KnowledgeSearchService(db)
    stats = service.get_statistics()
    return ResponseModel(code=200, message="success", data=stats)
