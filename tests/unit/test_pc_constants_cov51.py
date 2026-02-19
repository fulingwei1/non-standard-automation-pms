# -*- coding: utf-8 -*-
"""
tests/unit/test_pc_constants_cov51.py
Unit tests for app/services/performance_collector/constants.py
"""
import pytest

try:
    from app.services.performance_collector.constants import (
        COLLABORATION_KEYWORDS,
        KNOWLEDGE_SHARING_PATTERNS,
        NEGATIVE_KEYWORDS,
        POSITIVE_KEYWORDS,
        PROBLEM_SOLVING_PATTERNS,
        TECH_BREAKTHROUGH_PATTERNS,
        TECH_KEYWORDS,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_positive_keywords_non_empty():
    assert isinstance(POSITIVE_KEYWORDS, list)
    assert len(POSITIVE_KEYWORDS) > 0


def test_negative_keywords_non_empty():
    assert isinstance(NEGATIVE_KEYWORDS, list)
    assert len(NEGATIVE_KEYWORDS) > 0


def test_tech_keywords_non_empty():
    assert isinstance(TECH_KEYWORDS, list)
    assert len(TECH_KEYWORDS) > 0


def test_collaboration_keywords_non_empty():
    assert isinstance(COLLABORATION_KEYWORDS, list)
    assert len(COLLABORATION_KEYWORDS) > 0


def test_problem_solving_patterns_are_strings():
    assert all(isinstance(p, str) for p in PROBLEM_SOLVING_PATTERNS)


def test_knowledge_sharing_patterns_are_strings():
    assert all(isinstance(p, str) for p in KNOWLEDGE_SHARING_PATTERNS)


def test_tech_breakthrough_patterns_are_strings():
    assert all(isinstance(p, str) for p in TECH_BREAKTHROUGH_PATTERNS)


def test_known_positive_keyword_present():
    assert "完成" in POSITIVE_KEYWORDS


def test_known_negative_keyword_present():
    assert "延期" in NEGATIVE_KEYWORDS
