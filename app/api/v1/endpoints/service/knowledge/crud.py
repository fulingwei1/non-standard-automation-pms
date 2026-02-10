# -*- coding: utf-8 -*-
"""
知识库管理 - CRUD操作
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.service import KnowledgeBase
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.service import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)

from ..number_utils import generate_article_no

router = APIRouter()


@router.get("", response_model=PaginatedResponse[KnowledgeBaseResponse], status_code=status.HTTP_200_OK)
def read_knowledge_base(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_faq: Optional[bool] = Query(None, description="是否FAQ筛选"),
    article_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库文章列表
    """
    query = db.query(KnowledgeBase)

    if category:
        query = query.filter(KnowledgeBase.category == category)
    if is_faq is not None:
        query = query.filter(KnowledgeBase.is_faq == is_faq)
    if article_status:
        query = query.filter(KnowledgeBase.status == article_status)

    # 应用关键词过滤（文章编号/标题/内容）
    query = apply_keyword_filter(query, KnowledgeBase, keyword, ["article_no", "title", "content"])

    # 精选优先，然后按浏览量排序
    total = query.count()
    items = query.order_by(
        desc(KnowledgeBase.is_featured),
        desc(KnowledgeBase.view_count)
    ).offset(pagination.offset).limit(pagination.limit).all()

    # 获取作者姓名
    for item in items:
        if item.author_id:
            author = db.query(User).filter(User.id == item.author_id).first()
            if author:
                item.author_name = author.name or author.username

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_in: KnowledgeBaseCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建知识库文章
    """
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=article_in.title,
        category=article_in.category,
        content=article_in.content,
        tags=article_in.tags or [],
        is_faq=article_in.is_faq or False,
        is_featured=article_in.is_featured or False,
        status=article_in.status or "DRAFT",
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.get("/{article_id}", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def read_knowledge_base_article(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库文章详情（增加浏览量）
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 增加浏览量
    article.view_count = (article.view_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.put("/{article_id}", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def update_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    article_in: KnowledgeBaseUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    if article_in.title is not None:
        article.title = article_in.title
    if article_in.category is not None:
        article.category = article_in.category
    if article_in.content is not None:
        article.content = article_in.content
    if article_in.tags is not None:
        article.tags = article_in.tags
    if article_in.is_faq is not None:
        article.is_faq = article_in.is_faq
    if article_in.is_featured is not None:
        article.is_featured = article_in.is_featured
    if article_in.status is not None:
        article.status = article_in.status

    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.delete("/{article_id}", status_code=status.HTTP_200_OK)
def delete_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(article)
    db.commit()

    return {"message": "文章已删除"}


@router.post("", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_knowledge_entry(
    *,
    db: Session = Depends(deps.get_db),
    title: str = Body(..., description="知识条目标题"),
    content: str = Body(..., description="知识条目内容"),
    category: str = Body(..., description="分类"),
    tags: Optional[List[str]] = Body(None, description="标签列表"),
    entry_type: str = Body("article", description="条目类型：article/issue/solution"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加知识条目
    快速添加知识库文章
    """
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=title,
        category=category,
        content=content,
        tags=tags or [],
        is_faq=False,
        is_featured=False,
        status="PUBLISHED",  # 直接发布
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    return ResponseModel(
        code=200,
        message="知识条目添加成功",
        data={
            "id": article.id,
            "article_no": article.article_no,
            "title": article.title,
            "category": article.category,
            "entry_type": entry_type,
            "created_at": article.created_at.isoformat() if article.created_at else None
        }
    )
