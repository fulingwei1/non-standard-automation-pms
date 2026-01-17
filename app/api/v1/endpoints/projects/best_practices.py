# -*- coding: utf-8 -*-
"""
最佳实践管理端点

包含最佳实践的CRUD、验证、复用、搜索统计等端点
"""

from typing import Any, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.project_review import ProjectReview, ProjectBestPractice
from app.schemas.project_review import (
    ProjectBestPracticeCreate,
    ProjectBestPracticeUpdate,
    ProjectBestPracticeResponse,
    BestPracticeRecommendationRequest,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 最佳实践搜索 ====================

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
