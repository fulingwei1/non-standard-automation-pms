# -*- coding: utf-8 -*-
"""
分页工具全面测试

测试 app/common/pagination.py 中的所有类和函数
"""
import pytest
from unittest.mock import Mock, patch
from app.common.pagination import (
    PaginationParams,
    get_pagination_params,
    paginate_list,
    get_pagination_query,
)


class TestPaginationParams:
    """测试PaginationParams数据类"""

    def test_basic_properties(self):
        """测试基本属性"""
        params = PaginationParams(page=1, page_size=20, offset=0, limit=20)
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20
    
    def test_pages_for_total_exact_match(self):
        """测试总页数计算（刚好整除）"""
        params = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        assert params.pages_for_total(100) == 10
        assert params.pages_for_total(50) == 5
    
    def test_pages_for_total_with_remainder(self):
        """测试总页数计算（有余数）"""
        params = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        assert params.pages_for_total(95) == 10  # 9.5 -> 10页
        assert params.pages_for_total(101) == 11  # 10.1 -> 11页
    
    def test_pages_for_total_zero(self):
        """测试总数为0"""
        params = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        assert params.pages_for_total(0) == 0
    
    def test_pages_for_total_small_number(self):
        """测试小于每页数的总数"""
        params = PaginationParams(page=1, page_size=20, offset=0, limit=20)
        
        assert params.pages_for_total(5) == 1
        assert params.pages_for_total(19) == 1
    
    def test_to_response(self):
        """测试构造响应体"""
        params = PaginationParams(page=2, page_size=10, offset=10, limit=10)
        items = [{"id": i} for i in range(11, 21)]
        
        response = params.to_response(items, total=95)
        
        assert response["items"] == items
        assert response["total"] == 95
        assert response["page"] == 2
        assert response["page_size"] == 10
        assert response["pages"] == 10  # 95/10 = 10页
    
    def test_to_response_empty_items(self):
        """测试空列表响应"""
        params = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        response = params.to_response([], total=0)
        
        assert response["items"] == []
        assert response["total"] == 0
        assert response["pages"] == 0
    
    def test_immutable(self):
        """测试不可变性（frozen=True）"""
        params = PaginationParams(page=1, page_size=10, offset=0, limit=10)
        
        with pytest.raises(AttributeError):
            params.page = 2


class TestGetPaginationParams:
    """测试get_pagination_params函数"""

    @patch('app.common.pagination.settings')
    def test_default_values(self, mock_settings):
        """测试默认值"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20
    
    @patch('app.common.pagination.settings')
    def test_custom_page_and_size(self, mock_settings):
        """测试自定义页码和大小"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=3, page_size=15)
        
        assert params.page == 3
        assert params.page_size == 15
        assert params.offset == 30  # (3-1) * 15
        assert params.limit == 15
    
    @patch('app.common.pagination.settings')
    def test_page_size_exceeds_max(self, mock_settings):
        """测试页大小超过最大限制"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=1, page_size=200)
        
        assert params.page_size == 100  # 被限制为最大值
    
    @patch('app.common.pagination.settings')
    def test_negative_page(self, mock_settings):
        """测试负数页码"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=-1)
        
        assert params.page == 1  # 被修正为1
        assert params.offset == 0
    
    @patch('app.common.pagination.settings')
    def test_zero_page(self, mock_settings):
        """测试零页码"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=0)
        
        assert params.page == 1
        assert params.offset == 0
    
    @patch('app.common.pagination.settings')
    def test_zero_page_size(self, mock_settings):
        """测试零页大小"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page_size=0)
        
        assert params.page_size == 20  # 使用默认值
    
    @patch('app.common.pagination.settings')
    def test_negative_page_size(self, mock_settings):
        """测试负数页大小"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page_size=-10)
        
        assert params.page_size == 20  # 使用默认值
    
    @patch('app.common.pagination.settings')
    def test_custom_default_page_size(self, mock_settings):
        """测试自定义默认页大小"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(default_page_size=50)
        
        assert params.page_size == 50
    
    @patch('app.common.pagination.settings')
    def test_custom_max_page_size(self, mock_settings):
        """测试自定义最大页大小"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page_size=200, max_page_size=150)
        
        assert params.page_size == 150
    
    @patch('app.common.pagination.settings')
    def test_offset_calculation(self, mock_settings):
        """测试offset计算"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        params1 = get_pagination_params(page=1, page_size=10)
        assert params1.offset == 0
        
        params2 = get_pagination_params(page=2, page_size=10)
        assert params2.offset == 10
        
        params3 = get_pagination_params(page=5, page_size=20)
        assert params3.offset == 80


class TestPaginateList:
    """测试paginate_list函数"""

    @patch('app.common.pagination.settings')
    def test_normal_pagination(self, mock_settings):
        """测试正常分页"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        items = list(range(1, 101))  # 1-100
        page_items, total, params = paginate_list(items, page=1, page_size=10)
        
        assert page_items == list(range(1, 11))
        assert total == 100
        assert params.page == 1
        assert params.page_size == 10
    
    @patch('app.common.pagination.settings')
    def test_second_page(self, mock_settings):
        """测试第二页"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        items = list(range(1, 101))
        page_items, total, params = paginate_list(items, page=2, page_size=10)
        
        assert page_items == list(range(11, 21))
        assert total == 100
    
    @patch('app.common.pagination.settings')
    def test_last_page_partial(self, mock_settings):
        """测试最后一页（不足）"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        items = list(range(1, 96))  # 1-95
        page_items, total, params = paginate_list(items, page=10, page_size=10)
        
        assert page_items == list(range(91, 96))  # 只有5个元素
        assert total == 95
    
    @patch('app.common.pagination.settings')
    def test_page_beyond_range(self, mock_settings):
        """测试超出范围的页码"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        items = list(range(1, 51))
        page_items, total, params = paginate_list(items, page=100, page_size=10)
        
        assert page_items == []
        assert total == 50
    
    @patch('app.common.pagination.settings')
    def test_empty_list(self, mock_settings):
        """测试空列表"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        page_items, total, params = paginate_list([], page=1, page_size=10)
        
        assert page_items == []
        assert total == 0
    
    @patch('app.common.pagination.settings')
    def test_single_item(self, mock_settings):
        """测试单个元素"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        items = [{"id": 1, "name": "test"}]
        page_items, total, params = paginate_list(items, page=1, page_size=10)
        
        assert page_items == items
        assert total == 1


class TestGetPaginationQuery:
    """测试get_pagination_query FastAPI依赖"""

    @patch('app.common.pagination.settings')
    def test_default_query_params(self, mock_settings):
        """测试默认查询参数"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        # 模拟FastAPI的Query默认值
        params = get_pagination_query(page=1, page_size=None)
        
        assert params.page == 1
        assert params.page_size == 20


class TestIntegrationScenarios:
    """集成测试场景"""

    @patch('app.common.pagination.settings')
    def test_api_list_scenario(self, mock_settings):
        """测试API列表接口场景"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        # 模拟数据库查询结果
        all_items = [{"id": i, "name": f"Item {i}"} for i in range(1, 101)]
        
        # 第一页
        page1_items, total, params1 = paginate_list(all_items, page=1, page_size=10)
        response1 = params1.to_response(page1_items, total)
        
        assert len(response1["items"]) == 10
        assert response1["total"] == 100
        assert response1["page"] == 1
        assert response1["pages"] == 10
        
        # 最后一页
        page10_items, total, params10 = paginate_list(all_items, page=10, page_size=10)
        response10 = params10.to_response(page10_items, total)
        
        assert len(response10["items"]) == 10
        assert response10["page"] == 10
    
    @patch('app.common.pagination.settings')
    def test_search_with_pagination(self, mock_settings):
        """测试搜索结果分页场景"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        # 模拟搜索结果
        search_results = [{"id": i, "title": f"Result {i}"} for i in range(1, 46)]
        
        # 分页展示搜索结果
        page_items, total, params = paginate_list(search_results, page=1, page_size=20)
        response = params.to_response(page_items, total)
        
        assert len(response["items"]) == 20
        assert response["total"] == 45
        assert response["pages"] == 3  # ceil(45/20) = 3


class TestEdgeCases:
    """边界情况测试"""

    @patch('app.common.pagination.settings')
    def test_large_page_number(self, mock_settings):
        """测试非常大的页码"""
        mock_settings.DEFAULT_PAGE_SIZE = 10
        mock_settings.MAX_PAGE_SIZE = 100
        
        params = get_pagination_params(page=999999)
        
        assert params.page == 999999
        assert params.offset == 9999980  # (999999-1) * 10
    
    @patch('app.common.pagination.settings')
    def test_page_size_boundary(self, mock_settings):
        """测试页大小边界值"""
        mock_settings.DEFAULT_PAGE_SIZE = 20
        mock_settings.MAX_PAGE_SIZE = 100
        
        # 刚好等于最大值
        params1 = get_pagination_params(page_size=100)
        assert params1.page_size == 100
        
        # 超过最大值1
        params2 = get_pagination_params(page_size=101)
        assert params2.page_size == 100
    
    @patch('app.common.pagination.settings')
    def test_single_page_result(self, mock_settings):
        """测试单页结果"""
        mock_settings.DEFAULT_PAGE_SIZE = 100
        mock_settings.MAX_PAGE_SIZE = 100
        
        items = list(range(1, 51))  # 50个元素
        page_items, total, params = paginate_list(items, page=1, page_size=100)
        
        assert len(page_items) == 50
        assert params.pages_for_total(total) == 1
