# -*- coding: utf-8 -*-
"""
通用分页工具

统一分页参数解析、offset/limit 计算与响应格式，替代各处手写
offset = (page - 1) * page_size 的重复代码。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, List, Optional

from fastapi import Query


@dataclass(frozen=True)
class PaginationParams:
    """
    分页参数

    由 page / page_size 计算得到 offset / limit，供查询与响应使用。
    """

    page: int
    page_size: int
    offset: int
    limit: int

    def pages_for_total(self, total: int) -> int:
        """根据总条数计算总页数。"""
        if self.page_size <= 0:
            return 0
        return max(0, int(ceil(total / self.page_size)))

    def to_response(self, items: List[Any], total: int) -> Dict[str, Any]:
        """构造列表接口常用的分页响应体。"""
        return {
            "items": items,
            "total": total,
            "page": self.page,
            "page_size": self.page_size,
            "pages": self.pages_for_total(total),
        }


def get_pagination_params(
    page: int = 1,
    page_size: Optional[int] = None,
    default_page_size: Optional[int] = None,
    max_page_size: Optional[int] = None,
) -> PaginationParams:
    """
    根据 page / page_size 计算分页参数。

    Args:
        page: 页码，从 1 开始。
        page_size: 每页条数；未传时使用 default_page_size。
        default_page_size: 默认每页条数；未传时从 settings 读取。
        max_page_size: 每页条数上限；未传时从 settings 读取。

    Returns:
        PaginationParams: 包含 page, page_size, offset, limit。
    """
    from app.core.config import settings

    default = default_page_size if default_page_size is not None else settings.DEFAULT_PAGE_SIZE
    maximum = max_page_size if max_page_size is not None else settings.MAX_PAGE_SIZE

    page = max(1, page)
    size = default if page_size is None or page_size < 1 else min(page_size, maximum)
    offset = (page - 1) * size

    return PaginationParams(page=page, page_size=size, offset=offset, limit=size)


def paginate_list(
    items: List[Any],
    page: int,
    page_size: int,
    default_page_size: Optional[int] = None,
    max_page_size: Optional[int] = None,
) -> tuple[List[Any], int, PaginationParams]:
    """
    对内存列表做分页（常用于先查全量再过滤的场景）。

    Args:
        items: 全量列表。
        page: 页码。
        page_size: 每页条数。
        default_page_size: 默认每页条数。
        max_page_size: 每页条数上限。

    Returns:
        (当前页子列表, 总条数, PaginationParams)
    """
    params = get_pagination_params(
        page=page,
        page_size=page_size,
        default_page_size=default_page_size,
        max_page_size=max_page_size,
    )
    total = len(items)
    start = params.offset
    end = start + params.limit
    return items[start:end], total, params


# ------------------------------ FastAPI 依赖 ------------------------------


def get_pagination_query(
    page: int = Query(1, ge=1, description="页码"),
    page_size: Optional[int] = Query(
        None,
        ge=1,
        description="每页条数，不传则使用默认值",
    ),
) -> PaginationParams:
    """
    FastAPI 依赖：从 Query 解析分页参数。

    使用示例:
        @router.get("/list")
        def list_items(
            pagination: PaginationParams = Depends(get_pagination_query),
            db: Session = Depends(get_db),
        ):
            q = db.query(Model).offset(pagination.offset).limit(pagination.limit)
            total = db.query(func.count(Model.id)).scalar() or 0
            return pagination.to_response(q.all(), total)
    """
    return get_pagination_params(page=page, page_size=page_size)
