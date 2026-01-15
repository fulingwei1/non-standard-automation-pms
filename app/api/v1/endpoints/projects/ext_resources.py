# -*- coding: utf-8 -*-
"""
资源管理 API
从 projects/extended.py 拆分
"""

from typing import Any, List, Optional, Dict

from datetime import date, datetime, timedelta

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.project import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/resources",
    tags=["resources"]
)

# ==================== 路由定义 ====================
# 共 5 个路由

    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复用最佳实践（增加复用计数）
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    if not practice.is_reusable:
        raise HTTPException(status_code=400, detail="该最佳实践不可复用")

    practice.reuse_count = (practice.reuse_count or 0) + 1
    practice.last_reused_at = datetime.now()
    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践复用成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.post("/project-reviews/best-practices/{practice_id}/apply", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def apply_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    target_project_id: int = Body(..., description="目标项目ID"),
    notes: Optional[str] = Body(None, description="应用备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用最佳实践到项目（增加复用计数）
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    if not practice.is_reusable:
        raise HTTPException(status_code=400, detail="该最佳实践不可复用")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, target_project_id)

    practice.reuse_count = (practice.reuse_count or 0) + 1
    practice.last_reused_at = datetime.now()

    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践应用成功",
        data={
            "practice": ProjectBestPracticeResponse.model_validate(practice).model_dump(),
            "applied_to_project_id": target_project_id,
            "notes": notes
        }
    )


# ==================== 最佳实践库高级功能 ====================

@router.get("/best-practices/categories", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_best_practice_categories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践分类列表
    """
    categories = db.query(ProjectBestPractice.category).filter(
        ProjectBestPractice.category.isnot(None),
        ProjectBestPractice.is_reusable == True
    ).distinct().all()

    category_list = [cat[0] for cat in categories if cat[0]]

    return ResponseModel(
        code=200,
        message="获取分类列表成功",
        data={"categories": category_list}
    )


@router.get("/best-practices/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_best_practice_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践统计信息
    """
    total = db.query(ProjectBestPractice).filter(ProjectBestPractice.is_reusable == True).count()
    validated = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED"
    ).count()
    pending = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "PENDING"
    ).count()

    total_reuse = db.query(func.sum(ProjectBestPractice.reuse_count)).filter(
        ProjectBestPractice.is_reusable == True
    ).scalar() or 0

    return ResponseModel(
        code=200,
        message="获取统计信息成功",
        data={
            "total": total,
            "validated": validated,
            "pending": pending,
            "total_reuse": total_reuse,
        }
    )


@router.get("/best-practices/popular", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_popular_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取热门最佳实践（按复用次数排序）
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    ).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED",
        ProjectBestPractice.status == "ACTIVE"
    )

    if category:
        query = query.filter(ProjectBestPractice.category == category)

    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(
        desc(ProjectBestPractice.reuse_count),
        desc(ProjectBestPractice.created_at)
    ).offset(offset).limit(page_size).all()

    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 经验教训库高级功能 ====================

@router.get("/lessons-learned", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_lessons_learned(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    lesson_type: Optional[str] = Query(None, description="类型筛选：SUCCESS/FAILURE"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    跨项目搜索经验教训库
    """
    query = db.query(ProjectLesson).join(
        ProjectReview, ProjectLesson.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    )

    if keyword:
        query = query.filter(
            or_(
                ProjectLesson.title.like(f"%{keyword}%"),
                ProjectLesson.description.like(f"%{keyword}%")
            )
        )

    if lesson_type:

