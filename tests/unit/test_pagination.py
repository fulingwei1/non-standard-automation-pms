# -*- coding: utf-8 -*-
"""
分页工具测试
"""

import pytest


class TestPaginationParams:
    """测试分页参数类"""

    def test_pagination_params_creation(self):
        """测试分页参数创建"""
        from app.utils.pagination import PaginationParams

        params = PaginationParams(page=1, page_size=10)
        assert params.page == 1
        assert params.page_size == 10

    def test_pagination_params_offset(self):
        """测试偏移量计算"""
        from app.utils.pagination import PaginationParams

        params = PaginationParams(page=2, page_size=10)
        assert params.offset == 10  # (page-1) * page_size

    def test_pagination_params_offset_first_page(self):
        """测试第一页偏移量为0"""
        from app.utils.pagination import PaginationParams

        params = PaginationParams(page=1, page_size=20)
        assert params.offset == 0

    def test_pagination_params_limit(self):
        """测试限制数量"""
        from app.utils.pagination import PaginationParams

        params = PaginationParams(page=1, page_size=10)
        assert params.limit == 10


class TestPaginateQuery:
    """测试分页查询函数"""

    def test_paginate_query_import(self):
        """测试导入分页查询函数"""
        from app.utils.pagination import paginate_query

        assert callable(paginate_query)


class TestCreatePaginatedResponse:
    """测试创建分页响应"""

    def test_create_paginated_response_import(self):
        """测试导入创建分页响应函数"""
        from app.utils.pagination import create_paginated_response

        assert callable(create_paginated_response)