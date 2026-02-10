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
        from sqlalchemy import text

        # 构建查询
        query = """
            SELECT
                bp.*,
                p.project_code,
                p.project_name as project_name
            FROM project_best_practices bp
            LEFT JOIN projects p ON bp.project_id = p.id
            WHERE bp.status = 'ACTIVE' AND bp.is_reusable = 1
        """
        params = {}

        if category:
            query += " AND bp.category = :category"
            params["category"] = category

        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) as subq"
        total = db.execute(text(count_query), params).scalar() or 0

        # 分页查询（按复用次数降序）
        query += " ORDER BY bp.reuse_count DESC, bp.created_at DESC"
        # 使用参数绑定防止 SQL 注入
        query += " LIMIT :page_size OFFSET :offset"
        params["page_size"] = pagination.limit
        params["offset"] = pagination.offset

        result = db.execute(text(query), params)
        rows = result.fetchall()

        # 转换为响应格式
        items = []
        for row in rows:
            items.append(
                BestPracticeResponse(
                    id=row.id,
                    review_id=row.review_id,
                    project_id=row.project_id,
                    title=row.title,
                    description=row.description,
                    context=row.context,
                    implementation=row.implementation,
                    benefits=row.benefits,
                    category=row.category,
                    tags=row.tags,
                    is_reusable=bool(row.is_reusable),
                    applicable_project_types=row.applicable_project_types,
                    applicable_stages=row.applicable_stages,
                    validation_status=row.validation_status or "PENDING",
                    reuse_count=row.reuse_count or 0,
                    status=row.status or "ACTIVE",
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    project_code=row.project_code,
                    project_name=row.project_name,
                )
            )

        return ResponseModel(
            code=200,
            message="获取热门最佳实践成功",
            data=BestPracticeListResponse(
                items=items, total=total, page=pagination.page, page_size=pagination.page_size
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
    获取最佳实践列���
    """
    try:
        from sqlalchemy import text

        query = """
            SELECT
                bp.*,
                p.project_code,
                p.project_name as project_name
            FROM project_best_practices bp
            LEFT JOIN projects p ON bp.project_id = p.id
            WHERE bp.status = 'ACTIVE'
        """
        params = {}

        if project_id:
            query += " AND bp.project_id = :project_id"
            params["project_id"] = project_id

        if category:
            query += " AND bp.category = :category"
            params["category"] = category

        if validation_status:
            query += " AND bp.validation_status = :validation_status"
            params["validation_status"] = validation_status

        if search:
            query += " AND (bp.title LIKE :search OR bp.description LIKE :search)"
            params["search"] = f"%{search}%"

        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) as subq"
        total = db.execute(text(count_query), params).scalar() or 0

        # 分页查询
        query += " ORDER BY bp.created_at DESC"
        # 使用参数绑定防止 SQL 注入
        query += " LIMIT :page_size OFFSET :offset"
        params["page_size"] = pagination.limit
        params["offset"] = pagination.offset

        result = db.execute(text(query), params)
        rows = result.fetchall()

        items = []
        for row in rows:
            items.append(
                BestPracticeResponse(
                    id=row.id,
                    review_id=row.review_id,
                    project_id=row.project_id,
                    title=row.title,
                    description=row.description,
                    context=row.context,
                    implementation=row.implementation,
                    benefits=row.benefits,
                    category=row.category,
                    tags=row.tags,
                    is_reusable=bool(row.is_reusable),
                    applicable_project_types=row.applicable_project_types,
                    applicable_stages=row.applicable_stages,
                    validation_status=row.validation_status or "PENDING",
                    reuse_count=row.reuse_count or 0,
                    status=row.status or "ACTIVE",
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    project_code=row.project_code,
                    project_name=row.project_name,
                )
            )

        return ResponseModel(
            code=200,
            message="获取最佳实践列表成功",
            data=BestPracticeListResponse(
                items=items, total=total, page=pagination.page, page_size=pagination.page_size
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
        from sqlalchemy import text

        query = """
            SELECT
                bp.*,
                p.project_code,
                p.project_name as project_name
            FROM project_best_practices bp
            LEFT JOIN projects p ON bp.project_id = p.id
            WHERE bp.id = :practice_id
        """

        result = db.execute(text(query), {"practice_id": practice_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="最佳实践不存在")

        return ResponseModel(
            code=200,
            message="获取最佳实践详情成功",
            data=BestPracticeResponse(
                id=row.id,
                review_id=row.review_id,
                project_id=row.project_id,
                title=row.title,
                description=row.description,
                context=row.context,
                implementation=row.implementation,
                benefits=row.benefits,
                category=row.category,
                tags=row.tags,
                is_reusable=bool(row.is_reusable),
                applicable_project_types=row.applicable_project_types,
                applicable_stages=row.applicable_stages,
                validation_status=row.validation_status or "PENDING",
                reuse_count=row.reuse_count or 0,
                status=row.status or "ACTIVE",
                created_at=row.created_at,
                updated_at=row.updated_at,
                project_code=row.project_code,
                project_name=row.project_name,
            ),
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
        from sqlalchemy import text

        # 检查最佳实践是否存在
        check_query = (
            "SELECT id, reuse_count FROM project_best_practices WHERE id = :practice_id"
        )
        result = db.execute(text(check_query), {"practice_id": practice_id})
        practice = result.fetchone()

        if not practice:
            raise HTTPException(status_code=404, detail="最佳实践不存在")

        # 检查目标项目是否存在
        project_check = "SELECT id FROM projects WHERE id = :project_id"
        project_result = db.execute(
            text(project_check), {"project_id": apply_data.target_project_id}
        )
        if not project_result.fetchone():
            raise HTTPException(status_code=404, detail="目标项目不存在")

        # 更新复用次数
        update_query = """
            UPDATE project_best_practices
            SET reuse_count = reuse_count + 1,
                last_reused_at = :now,
                updated_at = :now
            WHERE id = :practice_id
        """
        db.execute(
            text(update_query), {"practice_id": practice_id, "now": datetime.now()}
        )
        db.commit()

        return ResponseModel(code=200, message="最佳实践应用成功")
    except HTTPException:
        raise
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
        from sqlalchemy import text

        insert_query = """
            INSERT INTO project_best_practices (
                review_id, project_id, title, description, context,
                implementation, benefits, category, tags, is_reusable,
                applicable_project_types, applicable_stages, created_at, updated_at
            ) VALUES (
                :review_id, :project_id, :title, :description, :context,
                :implementation, :benefits, :category, :tags, :is_reusable,
                :applicable_project_types, :applicable_stages, :now, :now
            )
        """

        now = datetime.now()
        result = db.execute(
            text(insert_query),
            {
                "review_id": data.review_id,
                "project_id": data.project_id,
                "title": data.title,
                "description": data.description,
                "context": data.context,
                "implementation": data.implementation,
                "benefits": data.benefits,
                "category": data.category,
                "tags": data.tags,
                "is_reusable": data.is_reusable,
                "applicable_project_types": data.applicable_project_types,
                "applicable_stages": data.applicable_stages,
                "now": now,
            },
        )
        db.commit()

        # 获取新创建的记录
        new_id = result.lastrowid

        return ResponseModel(
            code=200,
            message="创建最佳实践成功",
            data=BestPracticeResponse(
                id=new_id,
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
                validation_status="PENDING",
                reuse_count=0,
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            ),
        )
    except Exception as e:
        db.rollback()
        return ResponseModel(code=500, message=f"创建最佳实践失败: {str(e)}")
