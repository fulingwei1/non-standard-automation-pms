# -*- coding: utf-8 -*-
"""
知识库管理 - 交互操作（点赞、有用、采用）
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import KnowledgeBase
from app.models.user import User
from app.schemas.service import KnowledgeBaseResponse
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.post("/{article_id}/like", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def like_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    点赞知识库文章
    """
    article = get_or_404(db, KnowledgeBase, article_id, "文章不存在")

    article.like_count = (article.like_count or 0) + 1
    return save_obj(db, article)


@router.post("/{article_id}/helpful", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def mark_knowledge_base_helpful(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记知识库文章为有用
    """
    article = get_or_404(db, KnowledgeBase, article_id, "文章不存在")

    article.helpful_count = (article.helpful_count or 0) + 1
    return save_obj(db, article)


@router.post("/{article_id}/adopt", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def adopt_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记采用知识库文章（表示该文档被实际应用到工作中）
    """
    article = get_or_404(db, KnowledgeBase, article_id, "文章不存在")

    article.adopt_count = (article.adopt_count or 0) + 1
    return save_obj(db, article)
