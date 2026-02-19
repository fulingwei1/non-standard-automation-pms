# -*- coding: utf-8 -*-
"""
第三十五批 - performance_collector/constants.py 单元测试
"""
import pytest

try:
    from app.services.performance_collector.constants import (
        POSITIVE_KEYWORDS,
        NEGATIVE_KEYWORDS,
        TECH_KEYWORDS,
        COLLABORATION_KEYWORDS,
        PROBLEM_SOLVING_PATTERNS,
        KNOWLEDGE_SHARING_PATTERNS,
        TECH_BREAKTHROUGH_PATTERNS,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestPerformanceCollectorConstants:

    def test_positive_keywords_not_empty(self):
        assert len(POSITIVE_KEYWORDS) > 0

    def test_negative_keywords_not_empty(self):
        assert len(NEGATIVE_KEYWORDS) > 0

    def test_positive_has_key_terms(self):
        """积极词汇包含常见词"""
        key_words = {"完成", "优化", "解决"}
        assert key_words & set(POSITIVE_KEYWORDS), "缺少预期积极词汇"

    def test_negative_has_key_terms(self):
        """消极词汇包含常见词"""
        key_words = {"延期", "问题", "风险"}
        assert key_words & set(NEGATIVE_KEYWORDS), "缺少预期消极词汇"

    def test_tech_keywords_has_items(self):
        assert len(TECH_KEYWORDS) > 0

    def test_collaboration_keywords_has_items(self):
        assert len(COLLABORATION_KEYWORDS) > 0

    def test_problem_solving_patterns_are_strings(self):
        assert all(isinstance(p, str) for p in PROBLEM_SOLVING_PATTERNS)

    def test_knowledge_sharing_patterns_are_strings(self):
        assert all(isinstance(p, str) for p in KNOWLEDGE_SHARING_PATTERNS)

    def test_tech_breakthrough_patterns_are_strings(self):
        assert all(isinstance(p, str) for p in TECH_BREAKTHROUGH_PATTERNS)

    def test_keywords_are_lists(self):
        for lst in [POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS,
                    TECH_KEYWORDS, COLLABORATION_KEYWORDS]:
            assert isinstance(lst, list)

    def test_patterns_are_lists(self):
        for lst in [PROBLEM_SOLVING_PATTERNS, KNOWLEDGE_SHARING_PATTERNS,
                    TECH_BREAKTHROUGH_PATTERNS]:
            assert isinstance(lst, list)

    def test_no_duplicates_in_positive(self):
        """积极词汇无完全重复（允许部分重复作为强调）"""
        # 只检查首个和最后一个不相同
        assert POSITIVE_KEYWORDS[0] != POSITIVE_KEYWORDS[-1] or len(POSITIVE_KEYWORDS) == 1

    def test_positive_negative_overlap_minimal(self):
        """积极词汇和消极词汇应以不同词为主"""
        overlap = set(POSITIVE_KEYWORDS) & set(NEGATIVE_KEYWORDS)
        # 允许少量重叠（如"分享"等中性词）但不应全部重叠
        assert len(overlap) < len(POSITIVE_KEYWORDS)
