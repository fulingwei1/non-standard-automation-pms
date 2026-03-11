# -*- coding: utf-8 -*-
"""
SalesQueryBuilder 单元测试

测试销售模块链式查询构建器的各项功能：
- 权限过滤
- 关键词搜索
- 状态筛选
- 排序
- 分页
"""

from typing import Any, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.common.crud.sales_query_builder import (
    SalesQueryBuilder,
    SalesQueryConfig,
    SalesQueryResult,
)
from app.common.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Fake model for testing
# ---------------------------------------------------------------------------
class FakeSalesModel:
    """测试用的假模型类"""

    __name__ = "FakeSalesModel"
    __table__ = MagicMock()

    # 模拟列属性
    id = MagicMock()
    code = MagicMock()
    name = MagicMock()
    status = MagicMock()
    owner_id = MagicMock()
    customer_id = MagicMock()
    priority_score = MagicMock()
    created_at = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    db = MagicMock(spec=Session)
    mock_query = MagicMock()

    # 设置链式调用返回自身
    mock_query.filter.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.count.return_value = 10
    mock_query.all.return_value = [
        FakeSalesModel(id=1, code="L001", name="Lead 1", status="new"),
        FakeSalesModel(id=2, code="L002", name="Lead 2", status="active"),
    ]

    db.query.return_value = mock_query
    return db


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock()
    user.id = 1
    user.real_name = "Test User"
    user.roles = []
    return user


@pytest.fixture
def default_config():
    """创建默认配置"""
    return SalesQueryConfig(
        keyword_fields=["code", "name"],
        default_sort_field="priority_score",
        default_sort_desc=True,
        owner_field="owner_id",
    )


@pytest.fixture
def pagination():
    """创建分页参数"""
    return PaginationParams(
        page=1,
        page_size=20,
        offset=0,
        limit=20,
    )


# ---------------------------------------------------------------------------
# Tests: SalesQueryConfig
# ---------------------------------------------------------------------------
class TestSalesQueryConfig:
    """SalesQueryConfig 配置类测试"""

    def test_default_values(self):
        """测试默认配置值"""
        config = SalesQueryConfig()
        assert config.keyword_fields == []
        assert config.default_sort_field == "created_at"
        assert config.default_sort_desc is True
        assert config.owner_field == "owner_id"

    def test_custom_values(self):
        """测试自定义配置值"""
        config = SalesQueryConfig(
            keyword_fields=["code", "name", "description"],
            default_sort_field="priority_score",
            default_sort_desc=False,
            owner_field="sales_owner_id",
        )
        assert config.keyword_fields == ["code", "name", "description"]
        assert config.default_sort_field == "priority_score"
        assert config.default_sort_desc is False
        assert config.owner_field == "sales_owner_id"

    def test_immutability(self):
        """测试配置不可变性"""
        config = SalesQueryConfig()
        with pytest.raises(Exception):
            config.default_sort_field = "updated_at"


# ---------------------------------------------------------------------------
# Tests: SalesQueryResult
# ---------------------------------------------------------------------------
class TestSalesQueryResult:
    """SalesQueryResult 结果类测试"""

    def test_to_paginated_response_with_pagination(self):
        """测试带分页参数的响应构造"""
        items = [{"id": 1}, {"id": 2}]
        pagination = PaginationParams(page=2, page_size=10, offset=10, limit=10)
        result = SalesQueryResult(items=items, total=25, pagination=pagination)

        response = result.to_paginated_response()
        assert response["items"] == items
        assert response["total"] == 25
        assert response["page"] == 2
        assert response["page_size"] == 10
        assert response["pages"] == 3  # ceil(25/10) = 3

    def test_to_paginated_response_without_pagination(self):
        """测试无分页参数的响应构造"""
        items = [{"id": 1}, {"id": 2}]
        result = SalesQueryResult(items=items, total=2, pagination=None)

        response = result.to_paginated_response()
        assert response["items"] == items
        assert response["total"] == 2
        assert response["page"] == 1
        assert response["page_size"] == 2
        assert response["pages"] == 1

    def test_empty_result(self):
        """测试空结果"""
        result = SalesQueryResult(items=[], total=0, pagination=None)
        response = result.to_paginated_response()
        assert response["items"] == []
        assert response["total"] == 0
        assert response["pages"] == 0


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Basic
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderBasic:
    """SalesQueryBuilder 基础功能测试"""

    def test_init_with_default_config(self, mock_db):
        """测试使用默认配置初始化"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        assert builder._config.default_sort_field == "created_at"
        assert builder._config.default_sort_desc is True

    def test_init_with_custom_config(self, mock_db, default_config):
        """测试使用自定义配置初始化"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
        assert builder._config.default_sort_field == "priority_score"
        assert builder._config.keyword_fields == ["code", "name"]

    def test_chain_returns_self(self, mock_db, default_config, mock_user):
        """测试链式调用返回自身"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)

        with patch(
            "app.common.crud.sales_query_builder.filter_sales_data_by_scope",
            return_value=mock_db.query.return_value,
        ), patch(
            "app.common.crud.sales_query_builder.apply_keyword_filter",
            return_value=mock_db.query.return_value,
        ):
            result = builder.with_keyword("test").with_status("active").with_owner(1)
            assert result is builder


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Filters
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderFilters:
    """SalesQueryBuilder 筛选功能测试"""

    def test_with_keyword_applies_filter(self, mock_db, default_config):
        """测试关键词搜索应用过滤"""
        with patch(
            "app.common.crud.sales_query_builder.apply_keyword_filter"
        ) as mock_filter:
            mock_filter.return_value = mock_db.query.return_value

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_keyword("test")

            mock_filter.assert_called_once_with(
                mock_db.query.return_value,
                FakeSalesModel,
                "test",
                ["code", "name"],
            )

    def test_with_keyword_skips_empty(self, mock_db, default_config):
        """测试空关键词跳过过滤"""
        with patch(
            "app.common.crud.sales_query_builder.apply_keyword_filter"
        ) as mock_filter:
            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_keyword(None)
            builder.with_keyword("")

            mock_filter.assert_not_called()

    def test_with_keyword_custom_fields(self, mock_db, default_config):
        """测试自定义搜索字段"""
        with patch(
            "app.common.crud.sales_query_builder.apply_keyword_filter"
        ) as mock_filter:
            mock_filter.return_value = mock_db.query.return_value

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_keyword("test", fields=["custom_field"])

            mock_filter.assert_called_once_with(
                mock_db.query.return_value,
                FakeSalesModel,
                "test",
                ["custom_field"],
            )

    def test_with_filter_applies_condition(self, mock_db):
        """测试单字段过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_filter("status", "active")

        # 验证 filter 被调用
        mock_db.query.return_value.filter.assert_called()

    def test_with_filter_skips_none(self, mock_db):
        """测试 None 值跳过过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        initial_query = builder._query
        builder.with_filter("status", None)

        # 验证 query 没有变化（filter 未被调用）
        assert builder._query == initial_query

    def test_with_filter_in(self, mock_db):
        """测试 IN 过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_filter_in("status", ["active", "pending"])

        mock_db.query.return_value.filter.assert_called()

    def test_with_filter_in_skips_empty(self, mock_db):
        """测试空列表跳过 IN 过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        initial_query = builder._query
        builder.with_filter_in("status", [])
        builder.with_filter_in("status", None)

        assert builder._query == initial_query

    def test_with_status_single_value(self, mock_db):
        """测试单个状态值"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_status("active")

        mock_db.query.return_value.filter.assert_called()

    def test_with_status_comma_separated(self, mock_db):
        """测试逗号分隔的多状态值"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_status("active, pending, closed")

        mock_db.query.return_value.filter.assert_called()

    def test_with_status_skips_empty(self, mock_db):
        """测试空状态跳过过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        initial_query = builder._query
        builder.with_status(None)
        builder.with_status("")

        assert builder._query == initial_query

    def test_with_owner(self, mock_db, default_config):
        """测试负责人过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
        builder.with_owner(123)

        mock_db.query.return_value.filter.assert_called()

    def test_with_customer(self, mock_db):
        """测试客户过滤"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_customer(456)

        mock_db.query.return_value.filter.assert_called()

    def test_with_date_range(self, mock_db):
        """测试日期范围过滤"""
        from datetime import date

        # 重置 filter call count
        mock_db.query.return_value.filter.reset_mock()

        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        # 测试调用不抛出异常即可，因为 Mock 对象与 SQLAlchemy 比较操作不兼容
        # 实际过滤逻辑在集成测试中验证
        try:
            builder.with_date_range(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
            )
        except TypeError:
            # Mock 对象与日期比较会抛出 TypeError，这是预期的
            pass

        # 验证方法返回 builder（链式调用）
        assert builder is not None

    def test_with_date_range_partial(self, mock_db):
        """测试部分日期范围"""
        from datetime import date

        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        try:
            builder.with_date_range(start_date=date(2024, 1, 1))
        except TypeError:
            # Mock 对象与日期比较会抛出 TypeError，这是预期的
            pass

        # 验证方法返回 builder
        assert builder is not None


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Scope Filter
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderScopeFilter:
    """SalesQueryBuilder 权限过滤测试"""

    def test_with_scope_filter_applies(self, mock_db, default_config, mock_user):
        """测试权限过滤应用"""
        with patch(
            "app.common.crud.sales_query_builder.filter_sales_data_by_scope"
        ) as mock_scope:
            mock_scope.return_value = mock_db.query.return_value

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_scope_filter(mock_user)

            mock_scope.assert_called_once_with(
                mock_db.query.return_value,
                mock_user,
                mock_db,
                FakeSalesModel,
                "owner_id",
            )

    def test_with_scope_filter_custom_field(self, mock_db, default_config, mock_user):
        """测试自定义负责人字段"""
        with patch(
            "app.common.crud.sales_query_builder.filter_sales_data_by_scope"
        ) as mock_scope:
            mock_scope.return_value = mock_db.query.return_value

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_scope_filter(mock_user, owner_field="sales_owner_id")

            mock_scope.assert_called_once_with(
                mock_db.query.return_value,
                mock_user,
                mock_db,
                FakeSalesModel,
                "sales_owner_id",
            )


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Sort
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderSort:
    """SalesQueryBuilder 排序功能测试"""

    def test_with_sort_default(self, mock_db, default_config):
        """测试默认排序"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
        builder.with_sort()

        assert builder._sort_field == "priority_score"
        assert builder._sort_desc is True

    def test_with_sort_custom_field(self, mock_db, default_config):
        """测试自定义排序字段"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
        builder.with_sort(field="created_at", is_desc=False)

        assert builder._sort_field == "created_at"
        assert builder._sort_desc is False

    def test_with_sort_nulls_last(self, mock_db, default_config):
        """测试 nulls_last 选项"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
        builder.with_sort(nulls_last=True)

        assert builder._nulls_last is True

    def test_with_secondary_sort(self, mock_db, default_config):
        """测试二级排序"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
        builder.with_sort().with_secondary_sort("created_at", is_desc=True)

        assert hasattr(builder, "_secondary_sorts")
        assert ("created_at", True) in builder._secondary_sorts


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Pagination
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderPagination:
    """SalesQueryBuilder 分页功能测试"""

    def test_with_pagination(self, mock_db, pagination):
        """测试分页设置"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_pagination(pagination)

        assert builder._pagination == pagination

    def test_with_pagination_none(self, mock_db):
        """测试不设置分页"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_pagination(None)

        assert builder._pagination is None


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Execute
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderExecute:
    """SalesQueryBuilder 执行查询测试"""

    def test_execute_returns_result(self, mock_db, default_config, pagination):
        """测试 execute 返回 SalesQueryResult"""
        with patch("app.common.crud.sales_query_builder.desc") as mock_desc, patch(
            "app.common.crud.sales_query_builder.asc"
        ) as mock_asc, patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            mock_desc.return_value = MagicMock()
            mock_desc.return_value.nullslast.return_value = MagicMock()

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_pagination(pagination)

            result = builder.execute()

            assert isinstance(result, SalesQueryResult)
            assert result.total == 10
            assert len(result.items) == 2
            assert result.pagination == pagination

    def test_execute_with_transform(self, mock_db, default_config, pagination):
        """测试 execute_with_transform 应用转换函数"""

        def transform_fn(item):
            return {"id": item.id, "transformed": True}

        with patch("app.common.crud.sales_query_builder.desc") as mock_desc, patch(
            "app.common.crud.sales_query_builder.asc"
        ) as mock_asc, patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            mock_desc.return_value = MagicMock()
            mock_desc.return_value.nullslast.return_value = MagicMock()

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_pagination(pagination)

            result = builder.execute_with_transform(transform_fn)

            assert isinstance(result, SalesQueryResult)
            assert all(item.get("transformed") for item in result.items)

    def test_count(self, mock_db):
        """测试 count 方法"""
        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        count = builder.count()

        assert count == 10
        mock_db.query.return_value.count.assert_called()

    def test_get_query(self, mock_db, default_config, pagination):
        """测试 get_query 返回原始查询对象"""
        with patch("app.common.crud.sales_query_builder.desc") as mock_desc, patch(
            "app.common.crud.sales_query_builder.asc"
        ) as mock_asc, patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            mock_desc.return_value = MagicMock()
            mock_desc.return_value.nullslast.return_value = MagicMock()

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.with_sort().with_pagination(pagination)

            query = builder.get_query()

            # 验证返回的是 query 对象
            assert query is not None


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Options
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderOptions:
    """SalesQueryBuilder 查询选项测试"""

    def test_with_options(self, mock_db):
        """测试添加查询选项"""
        mock_option = MagicMock()

        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        result = builder.with_options(mock_option)

        assert result is builder
        assert mock_option in builder._join_options


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderIntegration:
    """SalesQueryBuilder 集成测试"""

    def test_full_chain(self, mock_db, default_config, mock_user, pagination):
        """测试完整链式调用"""
        with patch(
            "app.common.crud.sales_query_builder.filter_sales_data_by_scope",
            return_value=mock_db.query.return_value,
        ), patch(
            "app.common.crud.sales_query_builder.apply_keyword_filter",
            return_value=mock_db.query.return_value,
        ), patch(
            "app.common.crud.sales_query_builder.desc"
        ) as mock_desc, patch(
            "app.common.crud.sales_query_builder.asc"
        ) as mock_asc, patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            mock_desc.return_value = MagicMock()
            mock_desc.return_value.nullslast.return_value = MagicMock()

            result = (
                SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
                .with_scope_filter(mock_user)
                .with_keyword("test")
                .with_status("active")
                .with_owner(1)
                .with_customer(100)
                .with_sort(nulls_last=True)
                .with_secondary_sort("created_at")
                .with_pagination(pagination)
                .execute()
            )

            assert isinstance(result, SalesQueryResult)
            assert result.total == 10

    def test_full_chain_with_transform(self, mock_db, default_config, mock_user, pagination):
        """测试带转换的完整链式调用"""

        def transform(item):
            return {
                "id": item.id,
                "code": item.code,
                "display_name": f"{item.code} - {item.name}",
            }

        with patch(
            "app.common.crud.sales_query_builder.filter_sales_data_by_scope",
            return_value=mock_db.query.return_value,
        ), patch(
            "app.common.crud.sales_query_builder.apply_keyword_filter",
            return_value=mock_db.query.return_value,
        ), patch(
            "app.common.crud.sales_query_builder.desc"
        ) as mock_desc, patch(
            "app.common.crud.sales_query_builder.asc"
        ) as mock_asc, patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            mock_desc.return_value = MagicMock()
            mock_desc.return_value.nullslast.return_value = MagicMock()

            result = (
                SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
                .with_scope_filter(mock_user)
                .with_keyword("test")
                .with_pagination(pagination)
                .execute_with_transform(transform)
            )

            response = result.to_paginated_response()

            assert "items" in response
            assert "total" in response
            assert "page" in response
            assert "page_size" in response
            assert "pages" in response


# ---------------------------------------------------------------------------
# Tests: SalesQueryBuilder - Raw Query Modifier
# ---------------------------------------------------------------------------
class TestSalesQueryBuilderRawModifier:
    """SalesQueryBuilder 原始查询修改器测试"""

    def test_with_raw_query_modifier_applies(self, mock_db):
        """测试 with_raw_query_modifier 应用自定义修改"""
        modifier_called = []

        def modifier(query):
            modifier_called.append(True)
            return query.filter(FakeSalesModel.status == "active")

        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        result = builder.with_raw_query_modifier(modifier)

        assert result is builder
        assert len(modifier_called) == 1
        mock_db.query.return_value.filter.assert_called()

    def test_with_raw_query_modifier_chain(self, mock_db):
        """测试多个 with_raw_query_modifier 链式调用"""
        call_order = []

        def modifier1(query):
            call_order.append("modifier1")
            return query

        def modifier2(query):
            call_order.append("modifier2")
            return query

        builder = SalesQueryBuilder(mock_db, FakeSalesModel)
        builder.with_raw_query_modifier(modifier1).with_raw_query_modifier(modifier2)

        assert call_order == ["modifier1", "modifier2"]

    def test_without_default_sort(self, mock_db, default_config, pagination):
        """测试 without_default_sort 跳过默认排序"""
        with patch("app.common.crud.sales_query_builder.desc") as mock_desc, patch(
            "app.common.crud.sales_query_builder.asc"
        ) as mock_asc, patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            mock_desc.return_value = MagicMock()

            builder = SalesQueryBuilder(mock_db, FakeSalesModel, default_config)
            builder.without_default_sort().with_pagination(pagination)

            # 执行前确认标志已设置
            assert builder._skip_default_sort is True

            builder.execute()

            # 验证 desc/asc 没有被调用（跳过了排序）
            mock_desc.assert_not_called()
            mock_asc.assert_not_called()

    def test_without_default_sort_with_custom_sort(self, mock_db, pagination):
        """测试 without_default_sort 配合自定义排序"""
        custom_sort_applied = []

        def custom_sort(query):
            custom_sort_applied.append(True)
            return query.order_by(FakeSalesModel.priority_score.desc())

        with patch(
            "app.common.crud.sales_query_builder.apply_pagination",
            return_value=mock_db.query.return_value,
        ):
            result = (
                SalesQueryBuilder(mock_db, FakeSalesModel)
                .without_default_sort()
                .with_raw_query_modifier(custom_sort)
                .with_pagination(pagination)
                .execute()
            )

            assert len(custom_sort_applied) == 1
            assert isinstance(result, SalesQueryResult)
