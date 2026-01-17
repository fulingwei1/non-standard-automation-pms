# -*- coding: utf-8 -*-
"""
经验教训管理端点

包含经验教训的CRUD、状态管理、搜索统计等端点
"""

from typing import Any, List, Optional, Dict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.project_review import ProjectReview, ProjectLesson
from app.schemas.project_review import (
    ProjectLessonCreate,
    ProjectLessonUpdate,
    ProjectLessonResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 项目经验教训 ====================

@router.get("/{project_id}/lessons-learned", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_lessons_learned(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目经验教训
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    from app.models.pmo import PmoProjectClosure
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()

    lessons_from_closure = {
        "lessons_learned": closure.lessons_learned if closure else None,
        "improvement_suggestions": closure.improvement_suggestions if closure else None,
        "achievement": closure.achievement if closure else None,
    }

    from app.models.issue import Issue
    issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.in_(["RESOLVED", "CLOSED"])
    ).order_by(desc(Issue.resolved_at)).all()

    lessons_by_category = {}
    for issue in issues:
        category = issue.category or "OTHER"
        if category not in lessons_by_category:
            lessons_by_category[category] = []

        lessons_by_category[category].append({
            "issue_no": issue.issue_no,
            "title": issue.title,
            "solution": issue.solution,
            "severity": issue.severity,
        })

    return ResponseModel(
        code=200,
        message="获取经验教训成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "lessons_from_closure": lessons_from_closure,
            "lessons_by_category": lessons_by_category,
        }
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
