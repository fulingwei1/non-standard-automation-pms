# -*- coding: utf-8 -*-
"""
项目最佳实践管理 API
从 projects/extended.py 拆分
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.services.best_practices import BestPracticesService

router = APIRouter()


# ============ Pydantic 模型 ============


class BestPracticeResponse(BaseModel):
    """最佳实践响应模型"""

    id: int
    review_id: int
    project_id: int
    title: str
    description: str
    context: Optional[str] = None
    implementation: Optional[str] = None
    benefits: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    is_reusable: bool = True
    applicable_project_types: Optional[str] = None
    applicable_stages: Optional[str] = None
    validation_status: str = "PENDING"
    reuse_count: int = 0
    status: str = "ACTIVE"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # 关联信息
    project_code: Optional[str] = None
    project_name: Optional[str] = None

    class Config:
        from_attributes = True


class BestPracticeListResponse(BaseModel):
    """最佳实践列表响应"""

    items: List[BestPracticeResponse]
    total: int
    page: int
    page_size: int


class BestPracticeCreate(BaseModel):
    """创建最佳实践请求"""

    review_id: int
    project_id: int
    title: str
    description: str
    context: Optional[str] = None
    implementation: Optional[str] = None
    benefits: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    is_reusable: bool = True
    applicable_project_types: Optional[str] = None
    applicable_stages: Optional[str] = None


class BestPracticeApply(BaseModel):
    """应用最佳实践请求"""

    target_project_id: int
    notes: Optional[str] = None


# ============ API 端点 ============


@router.get(
    "/best-practices/popular", response_model=ResponseModel[BestPracticeListResponse]
)
def get_popular_best_practices(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取热门最佳实践列表（按复用次数排序）
    """
    try:
        service = BestPracticesService(db)
        items, total = service.get_popular_practices(pagination, category)

        # 转换为响应格式
        practice_items = [BestPracticeResponse(**item) for item in items]

        return ResponseModel(
            code=200,
            message="获取热门最佳实践成功",
            data=BestPracticeListResponse(
                items=practice_items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
            ),
        )
    except Exception as e:
        return ResponseModel(code=500, message=f"获取热门最佳实践失败: {str(e)}")


@router.get("/best-practices", response_model=ResponseModel[BestPracticeListResponse])
def get_best_practices(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    validation_status: Optional[str] = Query(None, description="验证状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取最佳实践列表
    """
    try:
        service = BestPracticesService(db)
        items, total = service.get_practices(
            pagination, project_id, category, validation_status, search
        )

        # 转换为响应格式
        practice_items = [BestPracticeResponse(**item) for item in items]

        return ResponseModel(
            code=200,
            message="获取最佳实践列表成功",
            data=BestPracticeListResponse(
                items=practice_items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
            ),
        )
    except Exception as e:
        return ResponseModel(code=500, message=f"获取最佳实践列表失败: {str(e)}")


@router.get(
    "/best-practices/{practice_id}", response_model=ResponseModel[BestPracticeResponse]
)
def get_best_practice_detail(
    practice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取最佳实践详情
    """
    try:
        service = BestPracticesService(db)
        practice = service.get_practice_by_id(practice_id)

        if not practice:
            raise HTTPException(status_code=404, detail="最佳实践不存在")

        return ResponseModel(
            code=200,
            message="获取最佳实践详情成功",
            data=BestPracticeResponse(**practice),
        )
    except HTTPException:
        raise
    except Exception as e:
        return ResponseModel(code=500, message=f"获取最佳实践详情失败: {str(e)}")


@router.post(
    "/project-reviews/best-practices/{practice_id}/apply", response_model=ResponseModel
)
def apply_best_practice(
    practice_id: int,
    apply_data: BestPracticeApply,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    将最佳实践应用到目标项目
    """
    try:
        service = BestPracticesService(db)
        service.apply_practice(
            practice_id, apply_data.target_project_id, apply_data.notes
        )

        return ResponseModel(code=200, message="最佳实践应用成功")
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        db.rollback()
        return ResponseModel(code=500, message=f"应用最佳实践失败: {str(e)}")


@router.post("/best-practices", response_model=ResponseModel[BestPracticeResponse])
def create_best_practice(
    data: BestPracticeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建最佳实践
    """
    try:
        service = BestPracticesService(db)
        practice = service.create_practice(
            review_id=data.review_id,
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            context=data.context,
            implementation=data.implementation,
            benefits=data.benefits,
            category=data.category,
            tags=data.tags,
            is_reusable=data.is_reusable,
            applicable_project_types=data.applicable_project_types,
            applicable_stages=data.applicable_stages,
        )

        return ResponseModel(
            code=200,
            message="创建最佳实践成功",
            data=BestPracticeResponse(**practice),
        )
    except Exception as e:
        db.rollback()
        return ResponseModel(code=500, message=f"创建最佳实践失败: {str(e)}")
