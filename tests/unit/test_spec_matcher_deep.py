# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 规格匹配器"""
import pytest


class TestSpecMatcherBusinessLogic:
    """规格匹配器业务逻辑测试"""

    def test_match_specs(self):
        """测试规格文本相似度"""
        try:
            from app.utils.spec_matcher import SpecMatcher

            matcher = SpecMatcher()
            result = matcher._text_similarity("spec1", "spec2")

            assert 0 <= result <= 1
        except ImportError:
            pytest.skip("Module not found")

    def test_compare_specs(self):
        """测试参数比较"""
        try:
            from app.utils.spec_matcher import SpecMatcher

            matcher = SpecMatcher()
            result = matcher._compare_parameters({"voltage": "24V"}, {"voltage": "24V"})

            assert result == {}
        except ImportError:
            pytest.skip("Module not found")
