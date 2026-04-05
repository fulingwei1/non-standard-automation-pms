# -*- coding: utf-8 -*-
"""
分页工具测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.utils.pagination import (
    PaginationParams,
    paginate_query,
    create_paginated_response,
    paginate,
)


class TestPaginationParams:
    """测试 PaginationParams 类"""

    def test_default_pagination(self):
        """测试默认分页参数"""
        params = PaginationParams(page=1, page_size=20)
        assert params.page == 1
        assert params.page_size == 20

    def test_custom_pagination(self):
        """测试自定义分页参数"""
        params = PaginationParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50

    def test_offset_calculation(self):
        """测试偏移量计算"""
        params = PaginationParams(page=1, page_size=20)
        assert params.offset == 0
        
        params = PaginationParams(page=2, page_size=20)
        assert params.offset == 20
        
        params = PaginationParams(page=3, page_size=20)
        assert params.offset == 40

    def test_limit_property(self):
        """测试 limit 属性"""
        params = PaginationParams(page=1, page_size=30)
        assert params.limit == 30

    def test_calculate_pages(self):
        """测试计算总页数"""
        params = PaginationParams(page=1, page_size=20)
        
        # 整除情况
        assert params.calculate_pages(100) == 5
        
        # 不能整除情况
        assert params.calculate_pages(101) == 6
        
        # 零记录
        assert params.calculate_pages(0) == 0
        
        # 边界情况
        assert params.calculate_pages(1) == 1


class TestPaginateQuery:
    """测试 paginate_query 函数"""

    def test_paginate_simple_query(self):
        """测试简单查询分页"""
        # 创建一个模拟的查询对象
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            MagicMock(),
            MagicMock(),
        ]

        params = PaginationParams(page=1, page_size=20)
        total, items = paginate_query(mock_query, params)

        assert total == 100
        assert len(items) == 2

    def test_paginate_with_count_query(self):
        """测试使用自定义计数查询"""
        mock_query = MagicMock()
        mock_count_query = MagicMock()
        mock_count_query.count.return_value = 50
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            MagicMock()
        ]

        params = PaginationParams(page=1, page_size=10)
        total, items = paginate_query(mock_query, params, mock_count_query)

        assert total == 50


class TestCreatePaginatedResponse:
    """测试 create_paginated_response 函数"""

    def test_create_response(self):
        """测试创建分页响应"""
        items = [MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)]
        total = 100
        params = PaginationParams(page=2, page_size=20)

        response = create_paginated_response(items, total, params)

        assert response.items == items
        assert response.total == total
        assert response.page == 2
        assert response.page_size == 20
        assert response.pages == 5


class TestPaginate:
    """测试 paginate 函数"""

    def test_paginate_function(self):
        """测试一步分页"""
        mock_query = MagicMock()
        mock_query.count.return_value = 50
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            MagicMock()
        ]

        params = PaginationParams(page=1, page_size=10)
        response = paginate(mock_query, params)

        assert response.total == 50
        assert response.page == 1
        assert response.page_size == 10
        assert response.pages == 5