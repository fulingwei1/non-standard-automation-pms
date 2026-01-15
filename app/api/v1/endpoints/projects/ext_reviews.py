# -*- coding: utf-8 -*-
"""
项目复盘 API
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
    prefix="/project-reviews",
    tags=["reviews"]
)

# ==================== 路由定义 ====================
# 共 9 个路由

# ==================== 项目复盘模块 ====================

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


# 注: 数据同步和ERP集成端点已迁移至 sync.py

# ==================== 经验教训 ====================

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


# ==================== 最佳实践 ====================

@router.get("/best-practices", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_reusable: Optional[bool] = Query(True, description="是否可复用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    搜索最佳实践库
    """
    query = db.query(ProjectBestPractice).join(
        ProjectReview, ProjectBestPractice.review_id == ProjectReview.id
    ).join(
        Project, ProjectReview.project_id == Project.id
    )

    if is_reusable:
        query = query.filter(ProjectBestPractice.is_reusable == True)

    if keyword:
        query = query.filter(
            or_(
                ProjectBestPractice.title.like(f"%{keyword}%"),
                ProjectBestPractice.description.like(f"%{keyword}%")
            )
        )

    if category:
        query = query.filter(ProjectBestPractice.category == category)

    total = query.count()
    offset = (page - 1) * page_size
    practices = query.order_by(desc(ProjectBestPractice.reuse_count)).offset(offset).limit(page_size).all()

    items = [ProjectBestPracticeResponse.model_validate(bp).model_dump() for bp in practices]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/best-practices/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def recommend_best_practices(
    *,
    db: Session = Depends(deps.get_db),
    request: BestPracticeRecommendationRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    推荐最佳实践
    """
    query = db.query(ProjectBestPractice).filter(
        ProjectBestPractice.is_reusable == True,
        ProjectBestPractice.validation_status == "VALIDATED",
        ProjectBestPractice.status == "ACTIVE"
    )

    if request.category:
        query = query.filter(ProjectBestPractice.category == request.category)

    practices = query.all()

    recommendations = []
    for practice in practices:
        score = 0.0
        reasons = []

        if request.project_type and practice.applicable_project_types:
            if request.project_type in practice.applicable_project_types:
                score += 0.4
                reasons.append("项目类型匹配")

        if request.current_stage and practice.applicable_stages:
            if request.current_stage in practice.applicable_stages:
                score += 0.4
                reasons.append("阶段匹配")

        if practice.reuse_count:
            score += min(0.2, practice.reuse_count * 0.01)
            if practice.reuse_count > 5:
                reasons.append("高复用率")

        if score > 0:
            recommendations.append({
                "practice": ProjectBestPracticeResponse.model_validate(practice).model_dump(),
                "match_score": round(score, 2),
                "match_reasons": reasons
            })

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    recommendations = recommendations[:request.limit]

    return ResponseModel(
        code=200,
        message="推荐最佳实践成功",
        data={"recommendations": recommendations}
    )


# ==================== 项目资源分配优化 ====================

@router.get("/{project_id}/resource-optimization", response_model=dict)
def get_resource_optimization(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期（默认：项目开始日期）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认：项目结束日期）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目资源分配优化分析
    分析项目资源分配情况，提供优化建议
    """
    from app.models.progress import Task
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    if not start_date:
        start_date = project.planned_start_date or date.today()
    if not end_date:
        end_date = project.planned_end_date or (date.today() + timedelta(days=90))

    # 获取项目资源分配
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.project_id == project_id,
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date,
        PmoResourceAllocation.status != 'CANCELLED'
    ).all()

    # 获取项目任务
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.plan_start <= end_date,
        Task.plan_end >= start_date,
        Task.status != 'CANCELLED'
    ).all()

    # 分析资源负荷
    resource_load = {}
    for alloc in allocations:
        resource_id = alloc.resource_id
        if resource_id not in resource_load:
            resource_load[resource_id] = {
                'resource_id': resource_id,
                'resource_name': alloc.resource_name,
                'resource_dept': alloc.resource_dept,
                'total_allocation': 0,
                'allocations': [],
            }

        resource_load[resource_id]['total_allocation'] += alloc.allocation_percent
        resource_load[resource_id]['allocations'].append({
            'id': alloc.id,
            'start_date': alloc.start_date.isoformat() if alloc.start_date else None,
            'end_date': alloc.end_date.isoformat() if alloc.end_date else None,
            'allocation_percent': alloc.allocation_percent,
            'planned_hours': alloc.planned_hours,
            'status': alloc.status,
        })

