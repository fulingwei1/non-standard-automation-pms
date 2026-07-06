# -*- coding: utf-8 -*-
"""
经验教训库兼容路由。

项目复盘模块已经有 `/projects/.../lessons` 的业务路由；这里承接旧前端
`/lessons/*` 调用，避免页面进入时落到占位 router。
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.project_review import ProjectLesson, ProjectReview
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _to_ui_lesson_type(value: Optional[str]) -> str:
    mapping = {
        "SUCCESS": "success",
        "FAILURE": "failure",
        "IMPROVEMENT": "improvement",
    }
    if not value:
        return "improvement"
    return mapping.get(value.upper(), value.lower())


def _to_db_lesson_type(value: Optional[str]) -> Optional[str]:
    mapping = {
        "success": "SUCCESS",
        "failure": "FAILURE",
        "improvement": "IMPROVEMENT",
    }
    if not value:
        return None
    return mapping.get(value.lower(), value.upper())


def _serialize_lesson(lesson: ProjectLesson) -> dict:
    tags = lesson.tags or []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    return {
        "id": lesson.id,
        "review_id": lesson.review_id,
        "project_id": lesson.project_id,
        "project_name": getattr(lesson.project, "project_name", None),
        "lesson_type": _to_ui_lesson_type(lesson.lesson_type),
        "title": lesson.title,
        "description": lesson.description,
        "root_cause": lesson.root_cause,
        "impact": lesson.impact,
        "impact_level": (lesson.priority or "").lower(),
        "action_taken": lesson.improvement_action,
        "recommendation": lesson.improvement_action,
        "improvement_action": lesson.improvement_action,
        "responsible_person": lesson.responsible_person,
        "due_date": lesson.due_date.isoformat() if lesson.due_date else None,
        "category": (lesson.category or "").lower(),
        "tags": ",".join(tags) if isinstance(tags, list) else tags,
        "priority": lesson.priority,
        "status": lesson.status,
        "resolved_date": lesson.resolved_date.isoformat() if lesson.resolved_date else None,
        "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
        "updated_at": lesson.updated_at.isoformat() if lesson.updated_at else None,
    }


def _apply_lesson_filters(
    query,
    keyword: Optional[str] = None,
    lesson_type: Optional[str] = None,
    category: Optional[str] = None,
    impact_level: Optional[str] = None,
):
    query = apply_keyword_filter(
        query, ProjectLesson, keyword, ["title", "description", "improvement_action"]
    )

    db_lesson_type = _to_db_lesson_type(lesson_type)
    if db_lesson_type:
        query = query.filter(ProjectLesson.lesson_type == db_lesson_type)
    if category:
        query = query.filter(func.lower(ProjectLesson.category) == category.lower())
    if impact_level:
        query = query.filter(ProjectLesson.priority == impact_level.upper())
    return query


@router.get("/list", response_model=ResponseModel)
def list_lessons(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None),
    lesson_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    impact_level: Optional[str] = Query(None),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
):
    query = _apply_lesson_filters(
        db.query(ProjectLesson),
        keyword=keyword,
        lesson_type=lesson_type,
        category=category,
        impact_level=impact_level,
    )

    total = query.count()
    lessons = apply_pagination(
        query.order_by(desc(ProjectLesson.created_at)), pagination.offset, pagination.limit
    ).all()

    return ResponseModel(
        code=200,
        message="获取经验教训列表成功",
        data={
            "items": [_serialize_lesson(lesson) for lesson in lessons],
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
        },
    )


@router.get("/stats", response_model=ResponseModel)
def lesson_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
):
    total = db.query(ProjectLesson).count()

    by_category = [
        {"category": (category or "uncategorized").lower(), "count": count}
        for category, count in db.query(ProjectLesson.category, func.count(ProjectLesson.id))
        .group_by(ProjectLesson.category)
        .all()
    ]
    by_type = [
        {"lesson_type": _to_ui_lesson_type(lesson_type), "count": count}
        for lesson_type, count in db.query(ProjectLesson.lesson_type, func.count(ProjectLesson.id))
        .group_by(ProjectLesson.lesson_type)
        .all()
    ]
    by_status = [
        {"status": status_value or "OPEN", "count": count}
        for status_value, count in db.query(ProjectLesson.status, func.count(ProjectLesson.id))
        .group_by(ProjectLesson.status)
        .all()
    ]

    return ResponseModel(
        code=200,
        message="获取经验教训统计成功",
        data={
            "total": total,
            "by_category": by_category,
            "by_type": by_type,
            "by_status": by_status,
        },
    )


@router.get("/search", response_model=ResponseModel)
def search_lessons(
    q: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    lesson_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
):
    search_keyword = keyword or q
    query = _apply_lesson_filters(
        db.query(ProjectLesson),
        keyword=search_keyword,
        lesson_type=lesson_type,
        category=category,
    )
    total = query.count()
    lessons = apply_pagination(
        query.order_by(desc(ProjectLesson.created_at)), pagination.offset, pagination.limit
    ).all()

    return ResponseModel(
        code=200,
        message="搜索完成",
        data={"items": [_serialize_lesson(lesson) for lesson in lessons], "total": total},
    )


@router.get("/{lesson_id:int}", response_model=ResponseModel)
def lesson_detail(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
):
    lesson = get_or_404(db, ProjectLesson, lesson_id, detail="经验教训不存在")
    return ResponseModel(code=200, message="获取经验教训详情成功", data=_serialize_lesson(lesson))


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_lesson(
    lesson_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:create")),
):
    project_id = lesson_data.get("project_id")
    review_id = lesson_data.get("review_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id 不能为空")

    if not review_id:
        review = (
            db.query(ProjectReview)
            .filter(ProjectReview.project_id == int(project_id))
            .order_by(desc(ProjectReview.created_at))
            .first()
        )
        if not review:
            raise HTTPException(status_code=400, detail="缺少可关联的项目复盘 review_id")
        review_id = review.id

    lesson = ProjectLesson(
        project_id=int(project_id),
        review_id=int(review_id),
        lesson_type=_to_db_lesson_type(lesson_data.get("lesson_type")) or "IMPROVEMENT",
        title=lesson_data.get("title") or "未命名经验教训",
        description=lesson_data.get("description") or "",
        root_cause=lesson_data.get("root_cause"),
        impact=lesson_data.get("impact") or lesson_data.get("impact_level"),
        improvement_action=lesson_data.get("recommendation") or lesson_data.get("action_taken"),
        category=lesson_data.get("category"),
        tags=lesson_data.get("tags"),
        priority=(lesson_data.get("impact_level") or lesson_data.get("priority") or "MEDIUM").upper(),
        status=lesson_data.get("status") or "OPEN",
    )
    if lesson_data.get("due_date"):
        lesson.due_date = date.fromisoformat(lesson_data["due_date"])

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return ResponseModel(code=200, message="经验教训创建成功", data=_serialize_lesson(lesson))


@router.put("/{lesson_id:int}", response_model=ResponseModel)
def update_lesson(
    lesson_id: int,
    lesson_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
):
    lesson = get_or_404(db, ProjectLesson, lesson_id, detail="经验教训不存在")

    field_map = {
        "title": "title",
        "description": "description",
        "root_cause": "root_cause",
        "category": "category",
        "status": "status",
        "responsible_person": "responsible_person",
    }
    for source, target in field_map.items():
        if source in lesson_data:
            setattr(lesson, target, lesson_data[source])

    if "lesson_type" in lesson_data:
        lesson.lesson_type = _to_db_lesson_type(lesson_data.get("lesson_type")) or lesson.lesson_type
    if "impact_level" in lesson_data:
        lesson.priority = (lesson_data.get("impact_level") or "MEDIUM").upper()
    if "recommendation" in lesson_data or "action_taken" in lesson_data:
        lesson.improvement_action = lesson_data.get("recommendation") or lesson_data.get("action_taken")
    if "tags" in lesson_data:
        lesson.tags = lesson_data["tags"]
    if "due_date" in lesson_data:
        lesson.due_date = date.fromisoformat(lesson_data["due_date"]) if lesson_data["due_date"] else None
    if lesson_data.get("status") == "RESOLVED" and not lesson.resolved_date:
        lesson.resolved_date = date.today()

    db.commit()
    db.refresh(lesson)

    return ResponseModel(code=200, message="经验教训更新成功", data=_serialize_lesson(lesson))


@router.delete("/{lesson_id:int}", response_model=ResponseModel)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
):
    lesson = get_or_404(db, ProjectLesson, lesson_id, detail="经验教训不存在")
    db.delete(lesson)
    db.commit()
    return ResponseModel(code=200, message="经验教训删除成功", data={"id": lesson_id})


__all__ = ["router"]
