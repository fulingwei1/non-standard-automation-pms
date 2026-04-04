# -*- coding: utf-8 -*-
"""通用分页工具单元测试"""
from unittest.mock import patch

import pytest

from app.common.pagination import (
    PaginationParams,
    get_pagination_params,
    paginate_list,
)


class TestPaginationParams:
    def test_pages_for_total(self):
        """测试总页数计算"""
        params = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        assert params.pages_for_total(0) == 0
        assert params.pages_for_total(1) == 1
        assert params.pages_for_total(10) == 1
        assert params.pages_for_total(11) == 2
        assert params.pages_for_total(25) == 3

    def test_pages_for_total_zero_page_size(self):
        """测试 page_size 为 0 的情况"""
        params = PaginationParams(page=1, page_size=0, offset=0, limit=0)
        assert params.pages_for_total(100) == 0

    def test_to_response(self):
        """测试分页响应构造"""
        params = PaginationParams(page=2, page_size=10, offset=10, limit=10)
        items = [{"id": 1}, {"id": 2}]
        response = params.to_response(items, 25)
        
        assert response["items"] == items
        assert response["total"] == 25
        assert response["page"] == 2
        assert response["page_size"] == 10
        assert response["pages"] == 3


class TestGetPaginationParams:
    @patch("app.core.config.settings")
    def test_default_values(self, mock_settings):
        """测试默认参数"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20

    @patch("app.core.config.settings")
    def test_custom_page(self, mock_settings):
        """测试自定义页码"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=5)
        
        assert params.page == 5
        assert params.offset == (5 - 1) * 20

    @patch("app.core.config.settings")
    def test_custom_page_size(self, mock_settings):
        """测试自定义每页条数"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=1, page_size=50)
        
        assert params.page_size == 50
        assert params.limit == 50

    @patch("app.core.config.settings")
    def test_page_size_exceeds_max(self, mock_settings):
        """测试每页条数超过最大值"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=1, page_size=200)
        
        assert params.page_size == 100  # 限制为最大值

    @patch("app.core.config.settings")
    def test_page_size_zero(self, mock_settings):
        """测试每页条数为0"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=1, page_size=0)
        
        assert params.page_size == 20  # 使用默认值

    @patch("app.core.config.settings")
    def test_page_size_negative(self, mock_settings):
        """测试每页条数为负数"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=1, page_size=-5)
        
        assert params.page_size == 20  # 使用默认值

    @patch("app.core.config.settings")
    def test_page_less_than_one(self, mock_settings):
        """测试页码小于1"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=0)
        
        assert params.page == 1  # 最小为1

    @patch("app.core.config.settings")
    def test_default_page_size_param(self, mock_settings):
        """测试通过参数指定默认每页条数"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(default_page_size=50)
        
        assert params.page_size == 50

    @patch("app.core.config.settings")
    def test_max_page_size_param(self, mock_settings):
        """测试通过参数指定每页最大条数"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(max_page_size=50)
        
        # 当 page_size 未指定时，使用 default_page_size
        assert params.page_size == 20
        
        # 当 page_size 超过新的最大值时
        params2 = get_pagination_params(page_size=100, max_page_size=50)
        assert params2.page_size == 50


class TestPaginateList:
    @patch("app.common.pagination.get_pagination_params")
    def test_paginate_list_basic(self, mock_get_params):
        """测试基本分页"""
        mock_get_params.return_value = PaginationParams(
            page=1, page_size=10, offset=0, limit=10
        )
        
        items = list(range(25))
        result_items, total, params = paginate_list(items, 1, 10)
        
        assert result_items == list(range(10))
        assert total == 25
        assert params.page == 1

    @patch("app.common.pagination.get_pagination_params")
    def test_paginate_list_second_page(self, mock_get_params):
        """测试第二页"""
        mock_get_params.return_value = PaginationParams(
            page=2, page_size=10, offset=10, limit=10
        )
        
        items = list(range(25))
        result_items, total, params = paginate_list(items, 2, 10)
        
        assert result_items == list(range(10, 20))
        assert total == 25
        assert params.page == 2

    @patch("app.common.pagination.get_pagination_params")
    def test_paginate_list_last_page(self, mock_get_params):
        """测试最后一页"""
        mock_get_params.return_value = PaginationParams(
            page=3, page_size=10, offset=20, limit=10
        )
        
        items = list(range(25))
        result_items, total, params = paginate_list(items, 3, 10)
        
        assert result_items == list(range(20, 25))
        assert total == 25
        assert params.page == 3

    @patch("app.common.pagination.get_pagination_params")
    def test_paginate_list_empty(self, mock_get_params):
        """测试空列表"""
        mock_get_params.return_value = PaginationParams(
            page=1, page_size=10, offset=0, limit=10
        )
        
        items = []
        result_items, total, params = paginate_list(items, 1, 10)
        
        assert result_items == []
        assert total == 0

    @patch("app.common.pagination.get_pagination_params")
    def test_paginate_list_single_page(self, mock_get_params):
        """测试单页数据"""
        mock_get_params.return_value = PaginationParams(
            page=1, page_size=10, offset=0, limit=10
        )
        
        items = [1, 2, 3]
        result_items, total, params = paginate_list(items, 1, 10)
        
        assert result_items == [1, 2, 3]
        assert total == 3