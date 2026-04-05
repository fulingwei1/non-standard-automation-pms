# -*- coding: utf-8 -*-
"""
知识库管理 - 统计和配额
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import KnowledgeBase
from app.models.service.enums import KnowledgeBaseStatusEnum
from app.models.user import User

from .utils import USER_UPLOAD_QUOTA, get_user_total_upload_size

router = APIRouter()


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_knowledge_base_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取知识库统计
    """
    total = db.query(KnowledgeBase).count()
    published = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.status == KnowledgeBaseStatusEnum.PUBLISHED.value)
        .count()
    )
    faq = db.query(KnowledgeBase).filter(KnowledgeBase.is_faq).count()
    featured = db.query(KnowledgeBase).filter(KnowledgeBase.is_featured).count()

    # 总浏览量
    total_views = db.query(func.sum(KnowledgeBase.view_count)).scalar() or 0

    return {
        "total": total,
        "published": published,
        "faq": faq,
        "featured": featured,
        "total_views": int(total_views),
    }


@router.get("/quota", response_model=dict, status_code=status.HTTP_200_OK)
def get_upload_quota(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取当前用户的上传配额使用情况
    """
    used = get_user_total_upload_size(db, current_user.id)
    return {
        "quota": USER_UPLOAD_QUOTA,
        "used": used,
        "remaining": USER_UPLOAD_QUOTA - used,
        "quota_gb": USER_UPLOAD_QUOTA / (1024 * 1024 * 1024),
        "used_gb": used / (1024 * 1024 * 1024),
        "remaining_gb": (USER_UPLOAD_QUOTA - used) / (1024 * 1024 * 1024),
        "usage_percent": (used / USER_UPLOAD_QUOTA * 100) if USER_UPLOAD_QUOTA > 0 else 0,
    }


@router.get("/categories", response_model=list, status_code=status.HTTP_200_OK)
def get_knowledge_base_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取知识库分类列表（兼容前端下拉）
    """
    rows = db.query(
        KnowledgeBase.category,
        func.count(KnowledgeBase.id).label("count")
    ).filter(
        KnowledgeBase.category.isnot(None),
        KnowledgeBase.category != ""
    ).group_by(
        KnowledgeBase.category
    ).order_by(
        desc("count"), KnowledgeBase.category.asc()
    ).all()

    return [row.category for row in rows]
