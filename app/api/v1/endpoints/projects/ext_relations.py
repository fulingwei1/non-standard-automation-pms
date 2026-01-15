# -*- coding: utf-8 -*-
"""
关联分析 API
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
    prefix="/relations",
    tags=["relations"]
)

# ==================== 路由定义 ====================
# 共 4 个路由

    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)

    if category:
        query = query.filter(ProjectLesson.category == category)

    if status_filter:
        query = query.filter(ProjectLesson.status == status_filter)

    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)

    total = query.count()
    offset = (page - 1) * page_size
    lessons = query.order_by(desc(ProjectLesson.created_at)).offset(offset).limit(page_size).all()

    items = [ProjectLessonResponse.model_validate(lesson).model_dump() for lesson in lessons]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/lessons-learned/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_lessons_statistics(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训统计信息
    """
    query = db.query(ProjectLesson)

    if project_id:
        query = query.filter(ProjectLesson.project_id == project_id)

    total = query.count()
    success_count = query.filter(ProjectLesson.lesson_type == "SUCCESS").count()
    failure_count = query.filter(ProjectLesson.lesson_type == "FAILURE").count()

    resolved_count = query.filter(ProjectLesson.status.in_(["RESOLVED", "CLOSED"])).count()
    unresolved_count = total - resolved_count

    today = date.today()
    overdue_count = query.filter(
        ProjectLesson.due_date.isnot(None),
        ProjectLesson.due_date < today,
        ProjectLesson.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    return ResponseModel(
        code=200,
        message="获取统计信息成功",
        data={
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "overdue_count": overdue_count
        }
    )


@router.get("/lessons-learned/categories", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_lesson_categories(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训分类列表
    """
    categories = db.query(ProjectLesson.category).filter(
        ProjectLesson.category.isnot(None)
    ).distinct().all()

    category_list = [cat[0] for cat in categories if cat[0]]

    return ResponseModel(
        code=200,
        message="获取分类列表成功",
        data={"categories": category_list}
    )


@router.get("/projects/{project_id}/best-practices/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_best_practice_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目推荐的最佳实践（基于项目信息自动匹配）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    request = BestPracticeRecommendationRequest(
        project_id=project_id,
        project_type=project.project_type if hasattr(project, 'project_type') else None,
        current_stage=project.stage if hasattr(project, 'stage') else None,
        limit=limit
    )

    return recommend_best_practices(db=db, request=request, current_user=current_user)


# ==================== 项目成本管理 ====================

@router.get("/projects/{project_id}/cost-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目成本汇总
    获取项目的成本汇总统计信息
    """
    from app.models.project import ProjectCost
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    # 总成本统计
    total_result = db.query(
        func.sum(ProjectCost.amount).label('total_amount'),
        func.sum(ProjectCost.tax_amount).label('total_tax'),
        func.count(ProjectCost.id).label('total_count')
    ).filter(ProjectCost.project_id == project_id).first()

    total_amount = float(total_result.total_amount) if total_result.total_amount else 0
    total_tax = float(total_result.total_tax) if total_result.total_tax else 0
    total_count = total_result.total_count or 0

    # 按成本类型统计
    type_stats = db.query(
        ProjectCost.cost_type,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(

