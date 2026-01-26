# -*- coding: utf-8 -*-
"""
Pagination Helper - 统一的分页工具

消除109处分页逻辑重复，提供一致的分页接口。
"""

from typing import Any, Dict, TypeVar
from sqlalchemy.orm import Query

T = TypeVar("T")


class PaginationHelper:
    """通用分页工具类"""

    @staticmethod
    def paginate(
        query: Query[T], page: int = 1, page_size: int = 20, max_page_size: int = 100
    ) -> Dict[str, Any]:
        """
        对查询进行分页

        Args:
            query: SQLAlchemy查询对象
            page: 页码，从1开始
            page_size: 每页大小
            max_page_size: 最大每页大小限制

        Returns:
            包含分页信息的字典：
            {
                "items": [T],           # 当前页数据列表
                "total": int,           # 总记录数
                "page": int,            # 当前页码
                "page_size": int,       # 每页大小
                "total_pages": int,     # 总页数
                "has_next": bool,       # 是否有下一页
                "has_prev": bool        # 是否有上一页
            }
        """
        # 限制每页最大值
        if page_size > max_page_size:
            page_size = max_page_size

        if page < 1:
            page = 1

        # 计算总数
        total = query.count()

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        # 修正页码不超过总页数
        if page > total_pages:
            page = total_pages

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取当前页数据
        items = query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

    @staticmethod
    def get_page_info(total: int, page: int, page_size: int) -> Dict[str, Any]:
        """
        根据总数计算分页信息

        Args:
            total: 总记录数
            page: 当前页码
            page_size: 每页大小

        Returns:
            分页信息字典
        """
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

    @staticmethod
    def get_offset(page: int, page_size: int) -> int:
        """
        计算偏移量

        Args:
            page: 页码
            page_size: 每页大小

        Returns:
            偏移量
        """
        return (page - 1) * page_size if page > 0 else 0
