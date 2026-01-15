# -*- coding: utf-8 -*-
"""
最佳实践 API
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
    prefix="/best-practices",
    tags=["best_practices"]
)

# ==================== 路由定义 ====================
# 共 8 个路由

    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取单个项目仪表盘数据
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.models.progress import Task
    from app.models.issue import Issue

    project = check_project_access_or_raise(db, current_user, project_id)

    today = date.today()

    # 任务统计
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    # 里程碑统计
    total_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).count()
    completed_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()

    # 风险统计
    risk_count = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.project_id == project_id,
        PmoProjectRisk.status != "CLOSED"
    ).count()

    # 问题统计
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    return ResponseModel(
        code=200,
        message="获取项目仪表盘成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage,
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "task_stats": {
                "total": total_tasks,
                "completed": completed_tasks,
                "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
            },
            "milestone_stats": {
                "total": total_milestones,
                "completed": completed_milestones,
            },
            "risk_count": risk_count,
            "issue_count": issue_count,
        }
    )


# ==================== 复盘报告状态管理 ====================

@router.put("/project-reviews/{review_id}/publish", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def publish_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    review.status = "PUBLISHED"
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告发布成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.put("/project-reviews/{review_id}/archive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def archive_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    归档项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    review.status = "ARCHIVED"
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告归档成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


# ==================== 经验教训管理 ====================

@router.get("/project-reviews/{review_id}/lessons", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_lessons(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    lesson_type: Optional[str] = Query(None, description="类型筛选：SUCCESS/FAILURE"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告的经验教训列表
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    query = db.query(ProjectLesson).filter(ProjectLesson.review_id == review_id)

    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    if status_filter:
        query = query.filter(ProjectLesson.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size
    lessons = query.order_by(desc(ProjectLesson.created_at)).offset(offset).limit(page_size).all()

    items = [ProjectLessonResponse.model_validate(l).model_dump() for l in lessons]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews/{review_id}/lessons", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    lesson_data: ProjectLessonCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建经验教训
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    if lesson_data.review_id != review_id:
        raise HTTPException(status_code=400, detail="review_id不匹配")

    lesson = ProjectLesson(**lesson_data.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训创建成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.get("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_lesson_detail(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取经验教训详情
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    return ResponseModel(
        code=200,
        message="获取经验教训详情成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.put("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    lesson_data: ProjectLessonUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新经验教训
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    update_data = lesson_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lesson, key, value)

    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训更新成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.delete("/project-reviews/lessons/{lesson_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除经验教训
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    db.delete(lesson)
    db.commit()

    return ResponseModel(
        code=200,
        message="经验教训删除成功"
    )


@router.put("/project-reviews/lessons/{lesson_id}/resolve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def resolve_project_lesson(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """

