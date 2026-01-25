# -*- coding: utf-8 -*-
"""
分页工具

提供统一的分页参数处理和响应生成，消除重复代码。

使用示例：
    from app.utils.pagination import PaginationParams, paginate_query, create_paginated_response

    @router.get("/items", response_model=PaginatedResponse)
    def list_items(
        db: Session = Depends(deps.get_db),
        pagination: PaginationParams = Depends(),
    ):
        query = db.query(Item)
        total, items = paginate_query(query, pagination)
        return create_paginated_response(items, total, pagination)
"""

from typing import Any, List, Tuple, TypeVar

from fastapi import Query
from sqlalchemy.orm import Query as SQLQuery

from app.core.config import settings
from app.schemas.common import PaginatedResponse

T = TypeVar('T')


class PaginationParams:
    """
    分页参数依赖类

    使用方式：
        @router.get("/items")
        def list_items(pagination: PaginationParams = Depends()):
            # pagination.page, pagination.page_size, pagination.offset
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(
            default=settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description="每页数量"
        ),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """返回每页数量（别名）"""
        return self.page_size

    def calculate_pages(self, total: int) -> int:
        """计算总页数"""
        return (total + self.page_size - 1) // self.page_size if total > 0 else 0


def paginate_query(
    query: SQLQuery,
    pagination: PaginationParams,
    count_query: SQLQuery = None
) -> Tuple[int, List[Any]]:
    """
    对查询应用分页

    Args:
        query: SQLAlchemy 查询对象
        pagination: 分页参数
        count_query: 可选的自定义计数查询（用于复杂查询优化）

    Returns:
        Tuple[int, List]: (总记录数, 当前页数据列表)

    使用示例：
        query = db.query(User).filter(User.is_active == True)
        total, users = paginate_query(query, pagination)
    """
    # 计算总数
    if count_query is not None:
        total = count_query.count()
    else:
        total = query.count()

    # 应用分页
    items = query.offset(pagination.offset).limit(pagination.page_size).all()

    return total, items


def create_paginated_response(
    items: List[Any],
    total: int,
    pagination: PaginationParams,
) -> PaginatedResponse:
    """
    创建分页响应

    Args:
        items: 数据列表
        total: 总记录数
        pagination: 分页参数

    Returns:
        PaginatedResponse: 分页响应对象

    使用示例：
        return create_paginated_response(users, total, pagination)
    """
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.calculate_pages(total)
    )


def paginate(
    query: SQLQuery,
    pagination: PaginationParams,
    count_query: SQLQuery = None
) -> PaginatedResponse:
    """
    一步完成分页查询和响应生成

    Args:
        query: SQLAlchemy 查询对象
        pagination: 分页参数
        count_query: 可选的自定义计数查询

    Returns:
        PaginatedResponse: 分页响应对象

    使用示例：
        query = db.query(User).filter(User.is_active == True)
        return paginate(query, pagination)
    """
    total, items = paginate_query(query, pagination, count_query)
    return create_paginated_response(items, total, pagination)


__all__ = [
    'PaginationParams',
    'paginate_query',
    'create_paginated_response',
    'paginate',
]
