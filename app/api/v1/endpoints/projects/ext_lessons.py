# -*- coding: utf-8 -*-
"""
项目经验教训管理
包含：经验教训CRUD、分类筛选、知识复用
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.project_review import ProjectLesson
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/projects/{project_id}/lessons", response_model=ResponseModel)
def get_project_lessons(
    project_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    lesson_type: Optional[str] = Query(None, description="类型：SUCCESS/FAILURE"),
    category: Optional[str] = Query(None, description="分类"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目经验教训列表

    Args:
        project_id: 项目ID
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        lesson_type: 类型筛选
        category: 分类筛选
        status: 状态筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 经验教训列表
    """
    query = db.query(ProjectLesson).filter(ProjectLesson.project_id == project_id)

    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    if category:
        query = query.filter(ProjectLesson.category == category)
    if status:
        query = query.filter(ProjectLesson.status == status)

    total = query.count()
    lessons = apply_pagination(query.order_by(desc(ProjectLesson.created_at)), pagination.offset, pagination.limit).all()

    lessons_data = [{
        "id": l.id,
        "review_id": l.review_id,
        "lesson_type": l.lesson_type,
        "title": l.title,
        "description": l.description,
        "root_cause": l.root_cause,
        "impact": l.impact,
        "improvement_action": l.improvement_action,
        "responsible_person": l.responsible_person,
        "due_date": l.due_date.isoformat() if l.due_date else None,
        "category": l.category,
        "tags": l.tags,
        "priority": l.priority,
        "status": l.status,
        "resolved_date": l.resolved_date.isoformat() if l.resolved_date else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in lessons]

    return ResponseModel(
        code=200,
        message="获取经验教训列表成功",
        data={"total": total, "items": lessons_data}
    )


@router.get("/projects/lessons/{lesson_id}", response_model=ResponseModel)
def get_lesson_detail(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取经验教训详情

    Args:
        lesson_id: 经验教训ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 经验教训详情
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    return ResponseModel(
        code=200,
        message="获取经验教训详情成功",
        data={
            "id": lesson.id,
            "review_id": lesson.review_id,
            "project_id": lesson.project_id,
            "lesson_type": lesson.lesson_type,
            "title": lesson.title,
            "description": lesson.description,
            "root_cause": lesson.root_cause,
            "impact": lesson.impact,
            "improvement_action": lesson.improvement_action,
            "responsible_person": lesson.responsible_person,
            "due_date": lesson.due_date.isoformat() if lesson.due_date else None,
            "category": lesson.category,
            "tags": lesson.tags,
            "priority": lesson.priority,
            "status": lesson.status,
            "resolved_date": lesson.resolved_date.isoformat() if lesson.resolved_date else None,
            "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
        }
    )


@router.post("/projects/{project_id}/lessons", response_model=ResponseModel)
def create_project_lesson(
    project_id: int,
    lesson_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建项目经验教训

    Args:
        project_id: 项目ID
        lesson_data: 经验教训数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    lesson = ProjectLesson(
        project_id=project_id,
        review_id=lesson_data.get("review_id"),
        lesson_type=lesson_data.get("lesson_type", "SUCCESS"),
        title=lesson_data.get("title"),
        description=lesson_data.get("description"),
        root_cause=lesson_data.get("root_cause"),
        impact=lesson_data.get("impact"),
        improvement_action=lesson_data.get("improvement_action"),
        responsible_person=lesson_data.get("responsible_person"),
        due_date=date.fromisoformat(lesson_data["due_date"]) if lesson_data.get("due_date") else None,
        category=lesson_data.get("category"),
        tags=lesson_data.get("tags"),
        priority=lesson_data.get("priority", "MEDIUM"),
        status="OPEN",
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return ResponseModel(
        code=200,
        message="经验教训创建成功",
        data={"id": lesson.id}
    )


@router.put("/projects/lessons/{lesson_id}", response_model=ResponseModel)
def update_project_lesson(
    lesson_id: int,
    lesson_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新经验教训

    Args:
        lesson_id: 经验教训ID
        lesson_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    updatable = [
        "lesson_type", "title", "description", "root_cause", "impact",
        "improvement_action", "responsible_person", "category", "tags",
        "priority", "status"
    ]
    for field in updatable:
        if field in lesson_data:
            setattr(lesson, field, lesson_data[field])

    if "due_date" in lesson_data:
        lesson.due_date = date.fromisoformat(lesson_data["due_date"]) if lesson_data["due_date"] else None

    if lesson_data.get("status") == "RESOLVED" and not lesson.resolved_date:
        lesson.resolved_date = date.today()

    db.commit()

    return ResponseModel(code=200, message="经验教训更新成功", data={"id": lesson.id})


@router.delete("/projects/lessons/{lesson_id}", response_model=ResponseModel)
def delete_project_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除经验教训

    Args:
        lesson_id: 经验教训ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    lesson = db.query(ProjectLesson).filter(ProjectLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="经验教训不存在")

    db.delete(lesson)
    db.commit()

    return ResponseModel(code=200, message="经验教训删除成功", data={"id": lesson_id})


@router.get("/projects/lessons/search", response_model=ResponseModel)
def search_lessons(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    lesson_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    搜索经验教训（跨项目）

    Args:
        keyword: 搜索关键词
        lesson_type: 类型筛选
        category: 分类筛选
        skip: 跳过记录数
        limit: 返回记录数
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 搜索结果
    """
    query = db.query(ProjectLesson)
    query = apply_keyword_filter(query, ProjectLesson, keyword, ["title", "description", "improvement_action"])

    if lesson_type:
        query = query.filter(ProjectLesson.lesson_type == lesson_type)
    if category:
        query = query.filter(ProjectLesson.category == category)

    total = query.count()
    lessons = apply_pagination(query.order_by(desc(ProjectLesson.created_at)), pagination.offset, pagination.limit).all()

    results = [{
        "id": l.id,
        "project_id": l.project_id,
        "lesson_type": l.lesson_type,
        "title": l.title,
        "category": l.category,
        "priority": l.priority,
        "status": l.status,
    } for l in lessons]

    return ResponseModel(
        code=200,
        message="搜索完成",
        data={"total": total, "items": results}
    )
