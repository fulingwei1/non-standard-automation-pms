# -*- coding: utf-8 -*-
"""
查询过滤工具全面测试

测试 app/common/query_filters.py 中的所有函数
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Query

from app.common.query_filters import (
    _normalize_keywords,
    build_keyword_conditions,
    build_like_conditions,
    apply_keyword_filter,
    apply_like_filter,
    apply_pagination,
)


class TestNormalizeKeywords:
    """测试关键词规范化函数"""

    def test_none_input(self):
        """测试None输入"""
        result = _normalize_keywords(None)
        assert result == []
    
    def test_empty_string(self):
        """测试空字符串"""
        result = _normalize_keywords("")
        assert result == []
    
    def test_whitespace_string(self):
        """测试空白字符串"""
        result = _normalize_keywords("   ")
        assert result == []
    
    def test_single_keyword_string(self):
        """测试单个关键词字符串"""
        result = _normalize_keywords("test")
        assert result == ["test"]
    
    def test_list_of_keywords(self):
        """测试关键词列表"""
        result = _normalize_keywords(["test1", "test2", "test3"])
        assert result == ["test1", "test2", "test3"]
    
    def test_tuple_of_keywords(self):
        """测试关键词元组"""
        result = _normalize_keywords(("test1", "test2"))
        assert result == ["test1", "test2"]
    
    def test_set_of_keywords(self):
        """测试关键词集合"""
        result = _normalize_keywords({"test1", "test2"})
        assert set(result) == {"test1", "test2"}
    
    def test_list_with_none_values(self):
        """测试包含None值的列表"""
        result = _normalize_keywords(["test1", None, "test2"])
        assert result == ["test1", "test2"]
    
    def test_list_with_empty_strings(self):
        """测试包含空字符串的列表"""
        result = _normalize_keywords(["test1", "", "  ", "test2"])
        assert result == ["test1", "test2"]
    
    def test_number_input(self):
        """测试数字输入"""
        result = _normalize_keywords(123)
        assert result == ["123"]
    
    def test_mixed_types(self):
        """测试混合类型"""
        result = _normalize_keywords([123, "test", None, ""])
        assert result == ["123", "test"]


class TestBuildKeywordConditions:
    """测试构建关键词搜索条件函数"""

    @pytest.fixture
    def mock_model(self):
        """Mock模型类"""
        model = Mock()
        model.name = Mock()
        model.code = Mock()
        model.description = Mock()
        return model
    
    def test_single_keyword_single_field(self, mock_model):
        """测试单个关键词单个字段"""
        conditions = build_keyword_conditions(
            mock_model,
            "test",
            "name"
        )
        
        assert len(conditions) == 1
        mock_model.name.ilike.assert_called_once_with("%test%")
    
    def test_single_keyword_multiple_fields(self, mock_model):
        """测试单个关键词多个字段"""
        conditions = build_keyword_conditions(
            mock_model,
            "test",
            ["name", "code", "description"]
        )
        
        assert len(conditions) == 3
        mock_model.name.ilike.assert_called_with("%test%")
        mock_model.code.ilike.assert_called_with("%test%")
        mock_model.description.ilike.assert_called_with("%test%")
    
    def test_multiple_keywords_single_field(self, mock_model):
        """测试多个关键词单个字段"""
        conditions = build_keyword_conditions(
            mock_model,
            ["test1", "test2"],
            "name"
        )
        
        assert len(conditions) == 2
    
    def test_multiple_keywords_multiple_fields(self, mock_model):
        """测试多个关键词多个字段"""
        conditions = build_keyword_conditions(
            mock_model,
            ["test1", "test2"],
            ["name", "code"]
        )
        
        # 2个关键词 × 2个字段 = 4个条件
        assert len(conditions) == 4
    
    def test_empty_keyword(self, mock_model):
        """测试空关键词"""
        conditions = build_keyword_conditions(
            mock_model,
            "",
            "name"
        )
        
        assert len(conditions) == 0
    
    def test_none_keyword(self, mock_model):
        """测试None关键词"""
        conditions = build_keyword_conditions(
            mock_model,
            None,
            "name"
        )
        
        assert len(conditions) == 0
    
    def test_use_like_instead_of_ilike(self, mock_model):
        """测试使用like而不是ilike"""
        conditions = build_keyword_conditions(
            mock_model,
            "test",
            "name",
            use_ilike=False
        )
        
        mock_model.name.like.assert_called_once_with("%test%")
        mock_model.name.ilike.assert_not_called()
    
    def test_non_existent_field(self, mock_model):
        """测试不存在的字段"""
        conditions = build_keyword_conditions(
            mock_model,
            "test",
            "non_existent_field"
        )
        
        # 不存在的字段应该被忽略
        assert len(conditions) == 0
    
    def test_keyword_with_special_characters(self, mock_model):
        """测试包含特殊字符的关键词"""
        conditions = build_keyword_conditions(
            mock_model,
            "test@#$%",
            "name"
        )
        
        mock_model.name.ilike.assert_called_with("%test@#$%%")


class TestBuildLikeConditions:
    """测试构建LIKE条件函数"""

    @pytest.fixture
    def mock_model(self):
        """Mock模型类"""
        model = Mock()
        model.name = Mock()
        model.code = Mock()
        return model
    
    def test_single_pattern_single_field(self, mock_model):
        """测试单个模式单个字段"""
        conditions = build_like_conditions(
            mock_model,
            "test%",
            "name"
        )
        
        assert len(conditions) == 1
        mock_model.name.ilike.assert_called_once_with("test%")
    
    def test_custom_wildcard_pattern(self, mock_model):
        """测试自定义通配符模式"""
        conditions = build_like_conditions(
            mock_model,
            "%test%suffix",
            "name"
        )
        
        mock_model.name.ilike.assert_called_once_with("%test%suffix")
    
    def test_multiple_patterns(self, mock_model):
        """测试多个模式"""
        conditions = build_like_conditions(
            mock_model,
            ["%test1%", "%test2%"],
            "name"
        )
        
        assert len(conditions) == 2
    
    def test_use_like_instead_of_ilike(self, mock_model):
        """测试使用like"""
        conditions = build_like_conditions(
            mock_model,
            "test%",
            "name",
            use_ilike=False
        )
        
        mock_model.name.like.assert_called_once()
        mock_model.name.ilike.assert_not_called()


class TestApplyKeywordFilter:
    """测试应用关键词过滤函数"""

    @pytest.fixture
    def mock_query(self):
        """Mock查询对象"""
        query = Mock(spec=Query)
        query.filter = Mock(return_value=query)
        return query
    
    @pytest.fixture
    def mock_model(self):
        """Mock模型类"""
        model = Mock()
        model.name = Mock()
        model.code = Mock()
        return model
    
    def test_apply_keyword_filter_with_keyword(self, mock_query, mock_model):
        """测试应用关键词过滤"""
        result = apply_keyword_filter(
            mock_query,
            mock_model,
            "test",
            "name"
        )
        
        # 应该调用filter
        mock_query.filter.assert_called_once()
        assert result == mock_query
    
    def test_apply_keyword_filter_without_keyword(self, mock_query, mock_model):
        """测试无关键词时原样返回"""
        result = apply_keyword_filter(
            mock_query,
            mock_model,
            None,
            "name"
        )
        
        # 不应该调用filter
        mock_query.filter.assert_not_called()
        assert result == mock_query
    
    def test_apply_keyword_filter_empty_string(self, mock_query, mock_model):
        """测试空字符串关键词"""
        result = apply_keyword_filter(
            mock_query,
            mock_model,
            "",
            "name"
        )
        
        mock_query.filter.assert_not_called()
    
    def test_apply_keyword_filter_multiple_fields(self, mock_query, mock_model):
        """测试多个字段"""
        result = apply_keyword_filter(
            mock_query,
            mock_model,
            "test",
            ["name", "code"]
        )
        
        mock_query.filter.assert_called_once()


class TestApplyLikeFilter:
    """测试应用LIKE过滤函数"""

    @pytest.fixture
    def mock_query(self):
        """Mock查询对象"""
        query = Mock(spec=Query)
        query.filter = Mock(return_value=query)
        return query
    
    @pytest.fixture
    def mock_model(self):
        """Mock模型类"""
        model = Mock()
        model.name = Mock()
        return model
    
    def test_apply_like_filter_with_pattern(self, mock_query, mock_model):
        """测试应用LIKE过滤"""
        result = apply_like_filter(
            mock_query,
            mock_model,
            "test%",
            "name"
        )
        
        mock_query.filter.assert_called_once()
        assert result == mock_query
    
    def test_apply_like_filter_without_pattern(self, mock_query, mock_model):
        """测试无模式时原样返回"""
        result = apply_like_filter(
            mock_query,
            mock_model,
            None,
            "name"
        )
        
        mock_query.filter.assert_not_called()
        assert result == mock_query


class TestApplyPagination:
    """测试应用分页函数"""

    @pytest.fixture
    def mock_query(self):
        """Mock查询对象"""
        query = Mock(spec=Query)
        query.offset = Mock(return_value=query)
        query.limit = Mock(return_value=query)
        return query
    
    def test_apply_pagination_with_offset_and_limit(self, mock_query):
        """测试应用offset和limit"""
        result = apply_pagination(mock_query, offset=10, limit=20)
        
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(20)
        assert result == mock_query
    
    def test_apply_pagination_zero_offset(self, mock_query):
        """测试零offset"""
        result = apply_pagination(mock_query, offset=0, limit=20)
        
        mock_query.offset.assert_not_called()
        mock_query.limit.assert_called_once_with(20)
    
    def test_apply_pagination_negative_offset(self, mock_query):
        """测试负offset"""
        result = apply_pagination(mock_query, offset=-10, limit=20)
        
        mock_query.offset.assert_not_called()
    
    def test_apply_pagination_zero_limit(self, mock_query):
        """测试零limit"""
        result = apply_pagination(mock_query, offset=10, limit=0)
        
        mock_query.offset.assert_called_once()
        mock_query.limit.assert_not_called()
    
    def test_apply_pagination_negative_limit(self, mock_query):
        """测试负limit"""
        result = apply_pagination(mock_query, offset=10, limit=-20)
        
        mock_query.limit.assert_not_called()
    
    def test_apply_pagination_both_zero(self, mock_query):
        """测试offset和limit都为0"""
        result = apply_pagination(mock_query, offset=0, limit=0)
        
        mock_query.offset.assert_not_called()
        mock_query.limit.assert_not_called()


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_search_and_pagination_workflow(self):
        """测试搜索和分页工作流"""
        mock_query = Mock(spec=Query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        
        mock_model = Mock()
        mock_model.name = Mock()
        mock_model.code = Mock()
        
        # 1. 应用关键词过滤
        query = apply_keyword_filter(
            mock_query,
            mock_model,
            "test",
            ["name", "code"]
        )
        
        # 2. 应用分页
        query = apply_pagination(query, offset=10, limit=20)
        
        # 验证调用顺序
        assert mock_query.filter.called
        assert mock_query.offset.called
        assert mock_query.limit.called
    
    def test_multiple_filters_chaining(self):
        """测试多个过滤器链式调用"""
        mock_query = Mock(spec=Query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        
        mock_model = Mock()
        mock_model.name = Mock()
        mock_model.code = Mock()
        mock_model.status = Mock()
        
        # 多次过滤
        query = apply_keyword_filter(mock_query, mock_model, "test1", "name")
        query = apply_keyword_filter(query, mock_model, "test2", "code")
        query = apply_pagination(query, offset=0, limit=10)
        
        # 验证filter被调用了两次
        assert mock_query.filter.call_count == 2
    
    def test_empty_search_with_pagination(self):
        """测试空搜索但有分页"""
        mock_query = Mock(spec=Query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        
        mock_model = Mock()
        mock_model.name = Mock()
        
        # 空关键词搜索
        query = apply_keyword_filter(mock_query, mock_model, None, "name")
        
        # 但仍应用分页
        query = apply_pagination(query, offset=10, limit=20)
        
        # filter不应该被调用
        mock_query.filter.assert_not_called()
        # 但分页应该被调用
        mock_query.offset.assert_called_once()
        mock_query.limit.assert_called_once()


class TestEdgeCases:
    """边界情况测试"""

    def test_very_long_keyword(self):
        """测试非常长的关键词"""
        mock_model = Mock()
        mock_model.name = Mock()
        
        long_keyword = "a" * 1000
        conditions = build_keyword_conditions(
            mock_model,
            long_keyword,
            "name"
        )
        
        assert len(conditions) == 1
        mock_model.name.ilike.assert_called_with(f"%{long_keyword}%")
    
    def test_special_sql_characters(self):
        """测试SQL特殊字符"""
        mock_model = Mock()
        mock_model.name = Mock()
        
        # SQL通配符
        keyword = "test%_"
        conditions = build_keyword_conditions(
            mock_model,
            keyword,
            "name"
        )
        
        # 应该被传递给ilike，不做转义
        mock_model.name.ilike.assert_called_with(f"%{keyword}%")
    
    def test_unicode_keywords(self):
        """测试Unicode关键词"""
        mock_model = Mock()
        mock_model.name = Mock()
        
        keyword = "测试中文关键词"
        conditions = build_keyword_conditions(
            mock_model,
            keyword,
            "name"
        )
        
        mock_model.name.ilike.assert_called_with(f"%{keyword}%")
    
    def test_pagination_with_large_numbers(self):
        """测试大数字分页"""
        mock_query = Mock(spec=Query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        
        result = apply_pagination(mock_query, offset=1000000, limit=1000)
        
        mock_query.offset.assert_called_with(1000000)
        mock_query.limit.assert_called_with(1000)
