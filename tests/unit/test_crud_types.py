# -*- coding: utf-8 -*-
"""CRUD类型单元测试"""
import pytest
from pydantic import ValidationError

from app.common.crud.types import PaginatedResult, QueryParams, SortOrder


class TestSortOrder:
    def test_sort_order_values(self):
        """测试排序枚举值"""
        assert SortOrder.ASC.value == "asc"
        assert SortOrder.DESC.value == "desc"

    def test_sort_order_from_string(self):
        """测试从字符串创建排序枚举"""
        assert SortOrder("asc") == SortOrder.ASC
        assert SortOrder("desc") == SortOrder.DESC
        # 大写的不会直接工作，需要 lower()
        assert SortOrder("ASC".lower()) == SortOrder.ASC
        assert SortOrder("DESC".lower()) == SortOrder.DESC


class TestQueryParams:
    def test_default_values(self):
        """测试默认值"""
        params = QueryParams()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.filters is None
        assert params.search is None
        assert params.sort_by is None
        assert params.sort_order == SortOrder.DESC

    def test_custom_pagination(self):
        """测试自定义分页参数"""
        params = QueryParams(page=3, page_size=50)
        
        assert params.page == 3
        assert params.page_size == 50

    def test_skip_property(self):
        """测试 skip 属性"""
        params = QueryParams(page=1, page_size=20)
        assert params.skip == 0
        
        params = QueryParams(page=2, page_size=20)
        assert params.skip == 20
        
        params = QueryParams(page=5, page_size=100)
        assert params.skip == 400

    def test_limit_property(self):
        """测试 limit 属性"""
        params = QueryParams(page_size=50)
        assert params.limit == 50

    def test_filters(self):
        """测试筛选条件"""
        params = QueryParams(filters={"status": "ACTIVE"})
        assert params.filters == {"status": "ACTIVE"}

    def test_search(self):
        """测试搜索关键词"""
        params = QueryParams(search="test", search_fields=["name", "code"])
        assert params.search == "test"
        assert params.search_fields == ["name", "code"]

    def test_sort_by(self):
        """测试排序字段"""
        params = QueryParams(sort_by="created_at", sort_order=SortOrder.ASC)
        assert params.sort_by == "created_at"
        assert params.sort_order == SortOrder.ASC

    def test_merged_filters_empty(self):
        """测试合并空筛选"""
        params = QueryParams()
        result = params.merged_filters()
        assert result == {}

    def test_merged_filters_with_filters(self):
        """测试合并筛选条件"""
        params = QueryParams(filters={"status": "ACTIVE"})
        result = params.merged_filters()
        assert result == {"status": "ACTIVE"}

    def test_merged_filters_with_extra(self):
        """测试合并额外筛选条件"""
        params = QueryParams()
        result = params.merged_filters({"type": "A"})
        assert result == {"type": "A"}

    def test_merged_filters_both(self):
        """测试合并两处筛选条件"""
        params = QueryParams(filters={"status": "ACTIVE"})
        result = params.merged_filters({"type": "A"})
        assert result == {"status": "ACTIVE", "type": "A"}

    def test_merged_filters_override(self):
        """测试额外筛选覆盖原筛选"""
        params = QueryParams(filters={"status": "ACTIVE"})
        result = params.merged_filters({"status": "INACTIVE"})
        # extra 覆盖 original
        assert result == {"status": "INACTIVE"}

    def test_sort_order_validator_accepts_asc(self):
        """测试排序验证器接受 asc"""
        params = QueryParams(sort_order="asc")
        assert params.sort_order == SortOrder.ASC

    def test_sort_order_validator_accepts_desc(self):
        """测试排序验证器接受 desc"""
        params = QueryParams(sort_order="desc")
        assert params.sort_order == SortOrder.DESC

    def test_sort_order_validator_accepts_uppercase(self):
        """测试排序验证器接受大写"""
        params = QueryParams(sort_order="ASC")
        assert params.sort_order == SortOrder.ASC

    def test_sort_order_validator_rejects_invalid(self):
        """测试排序验证器拒绝无效值"""
        with pytest.raises(ValidationError):
            QueryParams(sort_order="invalid")

    def test_page_size_max_limit(self):
        """测试每页最大条数限制"""
        # Pydantic v2 style: le=10000 in Field definition
        params = QueryParams(page_size=10000)
        assert params.page_size == 10000

    def test_page_min_value(self):
        """测试页码最小值"""
        params = QueryParams(page=1)
        assert params.page == 1


class TestPaginatedResult:
    def test_default_values(self):
        """测试默认值"""
        result = PaginatedResult()
        
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 20

    def test_pages_property(self):
        """测试总页数计算"""
        result = PaginatedResult(total=100, page_size=20)
        assert result.pages == 5
        
        result = PaginatedResult(total=101, page_size=20)
        assert result.pages == 6
        
        result = PaginatedResult(total=0, page_size=20)
        assert result.pages == 0

    def test_pages_zero_page_size(self):
        """测试 page_size 为 1 的情况（最小值）"""
        result = PaginatedResult(total=100, page_size=1)
        assert result.pages == 100

    def test_to_dict(self):
        """测试转换为字典"""
        result = PaginatedResult(
            items=[{"id": 1}, {"id": 2}],
            total=100,
            page=2,
            page_size=20
        )
        d = result.to_dict()
        
        assert d["items"] == [{"id": 1}, {"id": 2}]
        assert d["total"] == 100
        assert d["page"] == 2
        assert d["page_size"] == 20
        assert d["pages"] == 5

    def test_with_items(self):
        """测试带数据的分页结果"""
        items = ["a", "b", "c"]
        result = PaginatedResult(items=items, total=10, page=1, page_size=3)
        
        assert result.items == items
        assert result.total == 10
        assert result.pages == 4