# -*- coding: utf-8 -*-
"""
财务成本 API
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
    prefix="/financial-costs",
    tags=["costs"]
)

# ==================== 路由定义 ====================
# 共 9 个路由

    """
    标记经验教训已解决
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    lesson.status = "RESOLVED"
    lesson.resolved_date = date.today()
    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训已标记为已解决",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.put("/project-reviews/lessons/{lesson_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_lesson_status(
    *,
    db: Session = Depends(deps.get_db),
    lesson_id: int,
    new_status: str = Body(..., description="新状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新经验教训状态
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, lesson.project_id)

    if new_status not in ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    lesson.status = new_status
    if new_status in ["RESOLVED", "CLOSED"]:
        lesson.resolved_date = date.today()

    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训状态更新成功",
        data=ProjectLessonResponse.model_validate(lesson).model_dump()
    )


@router.post("/project-reviews/lessons/batch-update", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_lessons(
    *,
    db: Session = Depends(deps.get_db),
    lesson_ids: List[int] = Body(..., description="经验教训ID列表"),
    update_data: Dict[str, Any] = Body(..., description="更新数据"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新经验教训
    """
    lessons = db.query(ProjectLesson).filter(ProjectLesson.id.in_(lesson_ids)).all()

    if not lessons:
        raise HTTPException(status_code=404, detail="未找到经验教训")

    from app.utils.permission_helpers import check_project_access_or_raise
    for lesson in lessons:
        check_project_access_or_raise(db, current_user, lesson.project_id)

    updated_count = 0
    for lesson in lessons:
        for key, value in update_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)
        updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"成功更新{updated_count}条经验教训",
        data={"updated_count": updated_count}
    )


# ==================== 最佳实践管理 ====================

@router.get("/project-reviews/{review_id}/best-practices", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_reusable: Optional[bool] = Query(None, description="是否可复用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取复盘报告的最佳实践列表
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    query = db.query(ProjectBestPractice).filter(ProjectBestPractice.review_id == review_id)

    if category:
        query = query.filter(ProjectBestPractice.category == category)
    if is_reusable is not None:
        query = query.filter(ProjectBestPractice.is_reusable == is_reusable)

    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(desc(ProjectBestPractice.created_at)).offset(offset).limit(page_size).all()

    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/project-reviews/{review_id}/best-practices", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    review_id: int,
    practice_data: ProjectBestPracticeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建最佳实践
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, review.project_id)

    if practice_data.review_id != review_id:
        raise HTTPException(status_code=400, detail="review_id不匹配")

    practice = ProjectBestPractice(**practice_data.model_dump())
    db.add(practice)
    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践创建成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.get("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_best_practice_detail(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取最佳实践详情
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    return ResponseModel(
        code=200,
        message="获取最佳实践详情成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.put("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    practice_data: ProjectBestPracticeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    update_data = practice_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(practice, key, value)

    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践更新成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.delete("/project-reviews/best-practices/{practice_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    db.delete(practice)
    db.commit()

    return ResponseModel(
        code=200,
        message="最佳实践删除成功"
    )


@router.put("/project-reviews/best-practices/{practice_id}/validate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def validate_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    validation_status: str = Body(..., description="验证状态：VALIDATED/REJECTED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证最佳实践
    """
    practice = db.query(ProjectBestPractice).filter(ProjectBestPractice.id == practice_id).first()

    if not practice:
        raise HTTPException(status_code=404, detail="最佳实践不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, practice.project_id)

    if validation_status not in ["VALIDATED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="验证状态必须是VALIDATED或REJECTED")

    practice.validation_status = validation_status
    practice.validation_date = date.today()
    practice.validated_by = current_user.id
    db.commit()
    db.refresh(practice)

    return ResponseModel(
        code=200,
        message="最佳实践验证成功",
        data=ProjectBestPracticeResponse.model_validate(practice).model_dump()
    )


@router.post("/project-reviews/best-practices/{practice_id}/reuse", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reuse_project_best_practice(
    *,
    db: Session = Depends(deps.get_db),
    practice_id: int,
    current_user: User = Depends(security.get_current_active_user),

