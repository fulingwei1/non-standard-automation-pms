# -*- coding: utf-8 -*-
"""
知识库特定功能 API
自动生成，从 service.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime, date, timedelta

from decimal import Decimal

import os

import uuid

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, UploadFile, File, Form

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.project import Project, Customer

from app.models.service import (

from app.schemas.service import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/service/knowledge-features",
    tags=["knowledge_features"]
)

# ==================== 路由定义 ====================
# 共 4 个路由

# ==================== 知识库特定功能 ====================

@router.get("/knowledge/issues", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_knowledge_issues(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="问题分类筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    问题库列表
    从问题管理模块中提取已解决的问题，形成问题库
    """
    from app.models.issue import Issue
    
    query = db.query(Issue).filter(
        Issue.status.in_(["RESOLVED", "CLOSED"]),
        Issue.solution.isnot(None)  # 必须有解决方案
    )
    
    if category:
        query = query.filter(Issue.category == category)
    if severity:
        query = query.filter(Issue.severity == severity)
    if keyword:
        query = query.filter(
            or_(
                Issue.title.like(f"%{keyword}%"),
                Issue.description.like(f"%{keyword}%"),
                Issue.solution.like(f"%{keyword}%")
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    issues = query.order_by(desc(Issue.resolved_at), desc(Issue.created_at)).offset(offset).limit(page_size).all()
    
    # 构建问题库列表
    issue_list = []
    for issue in issues:
        issue_list.append({
            "id": issue.id,
            "issue_no": issue.issue_no,
            "title": issue.title,
            "description": issue.description,
            "category": issue.category,
            "severity": issue.severity,
            "solution": issue.solution,
            "project_id": issue.project_id,
            "project_name": issue.project.project_name if issue.project else None,
            "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
            "resolved_by_name": issue.resolved_by_name,
            "tags": issue.tags
        })
    
    return PaginatedResponse(
        items=issue_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/knowledge/solutions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_knowledge_solutions(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案库列表
    从知识库中提取标记为解决方案的文章，或从问题库中提取解决方案
    """
    # 从知识库中查找方案类文章
    query = db.query(KnowledgeBase).filter(
        KnowledgeBase.status == "PUBLISHED",
        or_(
            KnowledgeBase.category == "SOLUTION",
            KnowledgeBase.category == "TROUBLESHOOTING",
            KnowledgeBase.tags.contains(["解决方案"]) if KnowledgeBase.tags else False
        )
    )
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    if keyword:
        query = query.filter(
            or_(
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%")
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    articles = query.order_by(desc(KnowledgeBase.view_count), desc(KnowledgeBase.created_at)).offset(offset).limit(page_size).all()
    
    # 构建方案库列表
    solution_list = []
    for article in articles:
        solution_list.append({
            "id": article.id,
            "article_no": article.article_no,
            "title": article.title,
            "content": article.content[:200] if article.content else "",  # 摘要
            "category": article.category,
            "tags": article.tags or [],
            "view_count": article.view_count or 0,
            "like_count": article.like_count or 0,
            "author_name": article.author_name,
            "created_at": article.created_at.isoformat() if article.created_at else None
        })
    
    return PaginatedResponse(
        items=solution_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/knowledge/search", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_knowledge(
    *,
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    search_type: Optional[str] = Query("all", description="搜索类型：all/issues/solutions/articles"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    搜索知识库
    综合搜索问题库、方案库和知识库文章
    """
    results = []
    
    if search_type in ["all", "articles"]:
        # 搜索知识库文章
        articles = db.query(KnowledgeBase).filter(
            KnowledgeBase.status == "PUBLISHED",
            or_(
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%")
            )
        ).limit(20).all()
        
        for article in articles:
            results.append({
                "type": "article",
                "id": article.id,
                "title": article.title,
                "content": article.content[:200] if article.content else "",
                "category": article.category,
                "url": f"/knowledge-base/{article.id}"
            })
    
    if search_type in ["all", "issues"]:
        # 搜索问题库
        from app.models.issue import Issue
        issues = db.query(Issue).filter(
            Issue.status.in_(["RESOLVED", "CLOSED"]),
            Issue.solution.isnot(None),
            or_(
                Issue.title.like(f"%{keyword}%"),
                Issue.description.like(f"%{keyword}%"),
                Issue.solution.like(f"%{keyword}%")
            )
        ).limit(20).all()
        
        for issue in issues:
            results.append({
                "type": "issue",
                "id": issue.id,
                "title": issue.title,
                "content": issue.solution[:200] if issue.solution else "",
                "category": issue.category,
                "url": f"/issues/{issue.id}"
            })
    
    if search_type in ["all", "solutions"]:
        # 搜索方案库（从知识库中）
        solutions = db.query(KnowledgeBase).filter(
            KnowledgeBase.status == "PUBLISHED",
            KnowledgeBase.category.in_(["SOLUTION", "TROUBLESHOOTING"]),
            or_(
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%")
            )
        ).limit(20).all()
        
        for solution in solutions:
            results.append({
                "type": "solution",
                "id": solution.id,
                "title": solution.title,
                "content": solution.content[:200] if solution.content else "",
                "category": solution.category,
                "url": f"/knowledge-base/{solution.id}"
            })
    
    # 分页
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_results = results[start:end]
    
    return PaginatedResponse(
        items=paginated_results,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/knowledge", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
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


