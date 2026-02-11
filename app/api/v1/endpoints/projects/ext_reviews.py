# -*- coding: utf-8 -*-
"""
项目复盘管理
包含：复盘报告CRUD、复盘统计
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core import security
from app.models.project import Project
from app.models.project_review import ProjectReview
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/projects/{project_id}/reviews", response_model=ResponseModel)
def get_project_reviews(
    project_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    review_type: Optional[str] = Query(None, description="复盘类型"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目复盘列表

    Args:
        project_id: 项目ID
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        review_type: 复盘类型筛选
        status: 状态筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 复盘列表
    """
    query = db.query(ProjectReview).filter(ProjectReview.project_id == project_id)

    if review_type:
        query = query.filter(ProjectReview.review_type == review_type)
    if status:
        query = query.filter(ProjectReview.status == status)

    total = query.count()
    reviews = query.order_by(desc(ProjectReview.review_date)).offset(pagination.offset).limit(pagination.limit).all()

    reviews_data = [{
        "id": r.id,
        "review_no": r.review_no,
        "review_date": r.review_date.isoformat() if r.review_date else None,
        "review_type": r.review_type,
        "reviewer_name": r.reviewer_name,
        "participant_names": r.participant_names,
        "schedule_variance": r.schedule_variance,
        "cost_variance": float(r.cost_variance) if r.cost_variance else None,
        "customer_satisfaction": r.customer_satisfaction,
        "status": r.status,
        "lessons_count": len(r.lessons) if r.lessons else 0,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in reviews]

    return ResponseModel(
        code=200,
        message="获取复盘列表成功",
        data={"total": total, "items": reviews_data}
    )


@router.get("/projects/reviews/{review_id}", response_model=ResponseModel)
def get_review_detail(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取复盘详情

    Args:
        review_id: 复盘ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 复盘详情
    """
    review = db.query(ProjectReview).options(
        joinedload(ProjectReview.lessons),
        joinedload(ProjectReview.best_practices_list)
    ).filter(ProjectReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    lessons_data = [{
        "id": l.id,
        "lesson_type": l.lesson_type,
        "title": l.title,
        "category": l.category,
        "priority": l.priority,
        "status": l.status,
    } for l in review.lessons] if review.lessons else []

    practices_data = [{
        "id": p.id,
        "title": p.title,
        "category": p.category,
        "is_reusable": p.is_reusable,
        "validation_status": p.validation_status,
    } for p in review.best_practices_list] if review.best_practices_list else []

    return ResponseModel(
        code=200,
        message="获取复盘详情成功",
        data={
            "id": review.id,
            "review_no": review.review_no,
            "project_id": review.project_id,
            "project_code": review.project_code,
            "review_date": review.review_date.isoformat() if review.review_date else None,
            "review_type": review.review_type,
            "plan_duration": review.plan_duration,
            "actual_duration": review.actual_duration,
            "schedule_variance": review.schedule_variance,
            "budget_amount": float(review.budget_amount) if review.budget_amount else None,
            "actual_cost": float(review.actual_cost) if review.actual_cost else None,
            "cost_variance": float(review.cost_variance) if review.cost_variance else None,
            "quality_issues": review.quality_issues,
            "change_count": review.change_count,
            "customer_satisfaction": review.customer_satisfaction,
            "success_factors": review.success_factors,
            "problems": review.problems,
            "improvements": review.improvements,
            "best_practices": review.best_practices,
            "conclusion": review.conclusion,
            "reviewer_name": review.reviewer_name,
            "participant_names": review.participant_names,
            "status": review.status,
            "lessons": lessons_data,
            "best_practices_list": practices_data,
        }
    )


@router.post("/projects/{project_id}/reviews", response_model=ResponseModel)
def create_project_review(
    project_id: int,
    review_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建项目复盘

    Args:
        project_id: 项目ID
        review_data: 复盘数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 生成复盘编号
    count = db.query(ProjectReview).filter(ProjectReview.project_id == project_id).count()
    review_no = f"REV-{project.project_code}-{count + 1:02d}"

    review = ProjectReview(
        review_no=review_no,
        project_id=project_id,
        project_code=project.project_code,
        review_date=date.fromisoformat(review_data["review_date"]) if review_data.get("review_date") else date.today(),
        review_type=review_data.get("review_type", "POST_MORTEM"),
        plan_duration=review_data.get("plan_duration"),
        actual_duration=review_data.get("actual_duration"),
        schedule_variance=review_data.get("schedule_variance"),
        budget_amount=review_data.get("budget_amount"),
        actual_cost=review_data.get("actual_cost"),
        cost_variance=review_data.get("cost_variance"),
        quality_issues=review_data.get("quality_issues", 0),
        change_count=review_data.get("change_count", 0),
        customer_satisfaction=review_data.get("customer_satisfaction"),
        success_factors=review_data.get("success_factors"),
        problems=review_data.get("problems"),
        improvements=review_data.get("improvements"),
        best_practices=review_data.get("best_practices"),
        conclusion=review_data.get("conclusion"),
        reviewer_id=current_user.id,
        reviewer_name=current_user.real_name or current_user.username,
        participants=review_data.get("participants"),
        participant_names=review_data.get("participant_names"),
        status="DRAFT",
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return ResponseModel(
        code=200,
        message="复盘报告创建成功",
        data={"id": review.id, "review_no": review_no}
    )


@router.put("/projects/reviews/{review_id}", response_model=ResponseModel)
def update_project_review(
    review_id: int,
    review_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新复盘报告

    Args:
        review_id: 复盘ID
        review_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    if review.status == "ARCHIVED":
        raise HTTPException(status_code=400, detail="已归档的复盘报告不能修改")

    updatable = [
        "review_type", "plan_duration", "actual_duration", "schedule_variance",
        "budget_amount", "actual_cost", "cost_variance", "quality_issues",
        "change_count", "customer_satisfaction", "success_factors", "problems",
        "improvements", "best_practices", "conclusion", "participant_names", "status"
    ]
    for field in updatable:
        if field in review_data:
            setattr(review, field, review_data[field])

    if "review_date" in review_data:
        review.review_date = date.fromisoformat(review_data["review_date"]) if review_data["review_date"] else None

    db.commit()

    return ResponseModel(code=200, message="复盘报告更新成功", data={"id": review.id})


@router.post("/projects/reviews/{review_id}/publish", response_model=ResponseModel)
def publish_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    发布复盘报告

    Args:
        review_id: 复盘ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 发布结果
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    if review.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的复盘报告可以发布")

    review.status = "PUBLISHED"
    db.commit()

    return ResponseModel(code=200, message="复盘报告已发布", data={"id": review.id})


@router.delete("/projects/reviews/{review_id}", response_model=ResponseModel)
def delete_project_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除复盘报告

    Args:
        review_id: 复盘ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    review = db.query(ProjectReview).filter(ProjectReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘报告不存在")

    if review.status == "PUBLISHED":
        raise HTTPException(status_code=400, detail="已发布的复盘报告不能删除")

    db.delete(review)
    db.commit()

    return ResponseModel(code=200, message="复盘报告删除成功", data={"id": review_id})
