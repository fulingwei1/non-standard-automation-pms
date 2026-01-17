# -*- coding: utf-8 -*-
"""
项目复盘管理端点

包含项目复盘报告的CRUD、状态管理等端点
"""

from typing import Any, List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.project_review import ProjectReview, ProjectLesson, ProjectBestPractice
from app.schemas.project_review import (
    ProjectReviewCreate,
    ProjectReviewUpdate,
    ProjectReviewResponse,
    ProjectLessonResponse,
    ProjectBestPracticeResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import generate_review_no

router = APIRouter()


@router.get("/project-reviews", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_reviews(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目复盘报告列表
    """
    from app.services.data_scope_service import DataScopeService

    query = db.query(ProjectReview).join(Project, ProjectReview.project_id == Project.id)
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if project_id:
        query = query.filter(ProjectReview.project_id == project_id)
    if start_date:
        query = query.filter(ProjectReview.review_date >= start_date)
    if end_date:
        query = query.filter(ProjectReview.review_date <= end_date)
    if status_filter:
        query = query.filter(ProjectReview.status == status_filter)

    total = query.count()
    offset = (page - 1) * page_size
    reviews = query.order_by(desc(ProjectReview.review_date)).offset(offset).limit(page_size).all()

    items = [ProjectReviewResponse.model_validate(r).model_dump() for r in reviews]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_data: ProjectReviewCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目复盘报告
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, review_data.project_id)

    if project.stage not in ["S9"] and project.status not in ["ST30"]:
        raise HTTPException(
            status_code=400,
            detail="项目未完成，无法创建复盘报告"
        )

    review_no = generate_review_no(db)

    # 获取参与人姓名
    participant_names = []
    if review_data.participants:
        users = db.query(User).filter(User.id.in_(review_data.participants)).all()
        participant_names = [u.real_name or u.username for u in users]

    reviewer = db.query(User).filter(User.id == review_data.reviewer_id).first()
    reviewer_name = reviewer.real_name or reviewer.username if reviewer else current_user.real_name or current_user.username

    review = ProjectReview(
        review_no=review_no,
        project_id=review_data.project_id,
        project_code=project.project_code,
        review_date=review_data.review_date,
        review_type=review_data.review_type,
        success_factors=review_data.success_factors,
        problems=review_data.problems,
        improvements=review_data.improvements,
        best_practices=review_data.best_practices,
        conclusion=review_data.conclusion,
        reviewer_id=review_data.reviewer_id,
        reviewer_name=reviewer_name,
        participants=review_data.participants,
        participant_names=", ".join(participant_names) if participant_names else None,
        status=review_data.status or "DRAFT"
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告创建成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.get("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_review_detail(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目复盘报告详情
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    lessons = db.query(ProjectLesson).filter(ProjectLesson.review_id == review_id).all()
    best_practices = db.query(ProjectBestPractice).filter(ProjectBestPractice.review_id == review_id).all()

    data = ProjectReviewResponse.model_validate(review).model_dump()
    data["lessons"] = [ProjectLessonResponse.model_validate(l).model_dump() for l in lessons]
    data["best_practices"] = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in best_practices]

    return ResponseModel(
        code=200,
        message="获取复盘报告详情成功",
        data=data
    )


@router.put("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    review_data: ProjectReviewUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    update_data = review_data.model_dump(exclude_unset=True)

    if "participants" in update_data and update_data["participants"]:
        users = db.query(User).filter(User.id.in_(update_data["participants"])).all()
        participant_names = [u.real_name or u.username for u in users]
        update_data["participant_names"] = ", ".join(participant_names)

    for key, value in update_data.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告更新成功",
        data=ProjectReviewResponse.model_validate(review).model_dump()
    )


@router.delete("/project-reviews/{review_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_review(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除项目复盘报告
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    if review.status == "PUBLISHED":
        raise HTTPException(status_code=400, detail="已发布的复盘报告不能删除")

    db.delete(review)
    db.commit()

    return ResponseModel(
        code=200,
        message="复盘报告删除成功"
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
