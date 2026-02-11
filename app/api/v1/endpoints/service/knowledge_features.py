# -*- coding: utf-8 -*-
"""
知识库高级功能 API endpoints
问题库、方案库、综合搜索
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.issue import Issue
from app.models.service import KnowledgeBase
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/issues", response_model=PaginatedResponse, status_code=200)
def get_knowledge_issues(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    category: Optional[str] = Query(None, description="问题分类筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    问题库列表
    从问题管理模块中提取已解决的问题，形成问题库
    """
    query = db.query(Issue).filter(
        Issue.status.in_(["RESOLVED", "CLOSED"]),
        Issue.solution.isnot(None)  # 必须有解决方案
    )

    if category:
        query = query.filter(Issue.category == category)
    if severity:
        query = query.filter(Issue.severity == severity)

    # 应用关键词过滤（标题/描述/解决方案）
    query = apply_keyword_filter(query, Issue, keyword, ["title", "description", "solution"])

    total = query.count()
    issues = query.order_by(desc(Issue.resolved_at), apply_pagination(desc(Issue.created_at)), pagination.offset, pagination.limit).all()

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
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/solutions", response_model=PaginatedResponse, status_code=200)
def get_knowledge_solutions(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
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

    # 应用关键词过滤（标题/内容）
    query = apply_keyword_filter(query, KnowledgeBase, keyword, ["title", "content"])

    total = query.count()
    articles = query.order_by(desc(KnowledgeBase.view_count), apply_pagination(desc(KnowledgeBase.created_at)), pagination.offset, pagination.limit).all()

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
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/search", response_model=PaginatedResponse, status_code=200)
def search_knowledge(
    *,
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., description="搜索关键词"),
    pagination: PaginationParams = Depends(get_pagination_query),
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
        article_query = db.query(KnowledgeBase).filter(KnowledgeBase.status == "PUBLISHED")
        article_query = apply_keyword_filter(article_query, KnowledgeBase, keyword, ["title", "content"], use_ilike=False)
        articles = article_query.limit(20).all()

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
        issue_query = db.query(Issue).filter(
            Issue.status.in_(["RESOLVED", "CLOSED"]),
            Issue.solution.isnot(None),
        )
        issue_query = apply_keyword_filter(issue_query, Issue, keyword, ["title", "description", "solution"], use_ilike=False)
        issues = issue_query.limit(20).all()

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
        solution_query = db.query(KnowledgeBase).filter(
            KnowledgeBase.status == "PUBLISHED",
            KnowledgeBase.category.in_(["SOLUTION", "TROUBLESHOOTING"]),
        )
        solution_query = apply_keyword_filter(solution_query, KnowledgeBase, keyword, ["title", "content"], use_ilike=False)
        solutions = solution_query.limit(20).all()

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
    paginated_results = results[pagination.offset:pagination.offset + pagination.limit]

    return PaginatedResponse(
        items=paginated_results,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )
