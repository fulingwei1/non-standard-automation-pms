# -*- coding: utf-8 -*-
"""通用查询过滤工具单元测试"""
from unittest.mock import MagicMock

import pytest

from app.common.query_filters import (
    _normalize_keywords,
    build_keyword_conditions,
    build_like_conditions,
)


class TestNormalizeKeywords:
    def test_none(self):
        """测试 None 输入"""
        assert _normalize_keywords(None) == []

    def test_empty_string(self):
        """测试空字符串"""
        assert _normalize_keywords("") == []
        assert _normalize_keywords("   ") == []

    def test_single_string(self):
        """测试单个字符串"""
        result = _normalize_keywords("test")
        assert result == ["test"]

    def test_string_with_whitespace(self):
        """测试带空格的字符串（只检查是否全空，保留原值）"""
        result = _normalize_keywords("  test  ")
        assert result == ["  test  "]

    def test_list_of_strings(self):
        """测试字符串列表"""
        result = _normalize_keywords(["test1", "test2"])
        assert result == ["test1", "test2"]

    def test_list_with_empty_strings(self):
        """测试包含空字符串的列表"""
        result = _normalize_keywords(["test1", "", "  ", "test2"])
        assert result == ["test1", "test2"]

    def test_list_with_none(self):
        """测试包含 None 的列表"""
        result = _normalize_keywords(["test1", None, "test2"])
        assert result == ["test1", "test2"]

    def test_tuple_of_strings(self):
        """测试元组"""
        result = _normalize_keywords(("test1", "test2"))
        assert result == ["test1", "test2"]

    def test_set_of_strings(self):
        """测试集合"""
        result = _normalize_keywords({"test1", "test2"})
        assert set(result) == {"test1", "test2"}

    def test_non_string_value(self):
        """测试非字符串值"""
        result = _normalize_keywords(123)
        assert result == ["123"]

    def test_non_string_value_in_list(self):
        """测试列表中的非字符串值"""
        result = _normalize_keywords(["test", 456, None])
        assert result == ["test", "456"]


class TestBuildKeywordConditions:
    def test_no_keyword(self):
        """测试无关键词"""
        model = MagicMock()
        model.name = MagicMock()
        model.code = MagicMock()
        
        result = build_keyword_conditions(model, None, "name")
        assert result == []

    def test_single_keyword_single_field(self):
        """测试单个关键词单个字段"""
        model = MagicMock()
        model.name = MagicMock()
        
        result = build_keyword_conditions(model, "test", "name")
        assert len(result) == 1

    def test_single_keyword_multiple_fields(self):
        """测试单个关键词多个字段"""
        model = MagicMock()
        model.name = MagicMock()
        model.code = MagicMock()
        
        result = build_keyword_conditions(model, "test", ["name", "code"])
        assert len(result) == 2

    def test_multiple_keywords_multiple_fields(self):
        """测试多个关键词多个字段"""
        model = MagicMock()
        model.name = MagicMock()
        model.code = MagicMock()
        
        result = build_keyword_conditions(model, ["test1", "test2"], ["name", "code"])
        assert len(result) == 4  # 2 keywords * 2 fields

    def test_use_ilike(self):
        """测试使用 ilike"""
        model = MagicMock()
        model.name = MagicMock()
        
        result = build_keyword_conditions(model, "test", "name", use_ilike=True)
        assert len(result) == 1

    def test_use_like(self):
        """测试使用 like"""
        model = MagicMock()
        model.name = MagicMock()
        
        result = build_keyword_conditions(model, "test", "name", use_ilike=False)
        assert len(result) == 1

    def test_invalid_field_name(self):
        """测试无效字段名"""
        model = MagicMock()
        model.name = MagicMock()
        # 不存在的字段
        model.nonexistent = None
        
        result = build_keyword_conditions(model, "test", ["name", "nonexistent"])
        # 只返回有效字段的条件
        assert len(result) == 1


class TestBuildLikeConditions:
    def test_no_pattern(self):
        """测试无模式"""
        model = MagicMock()
        model.name = MagicMock()
        
        result = build_like_conditions(model, None, "name")
        assert result == []

    def test_single_pattern_single_field(self):
        """测试单个模式单个字段"""
        model = MagicMock()
        model.name = MagicMock()
        
        result = build_like_conditions(model, "test%", "name")
        assert len(result) == 1

    def test_pattern_with_wildcards(self):
        """测试带通配符的模式"""
        model = MagicMock()
        model.name = MagicMock()
        model.code = MagicMock()
        
        result = build_like_conditions(model, "%test%", ["name", "code"])
        assert len(result) == 2

    def test_multiple_patterns(self):
        """测试多个模式"""
        model = MagicMock()
        model.name = MagicMock()
        
        result = build_like_conditions(model, ["test1%", "test2%"], "name")
        assert len(result) == 2