# -*- coding: utf-8 -*-
"""
tests/unit/test_pc_base_cov51.py
Unit tests for app/services/performance_collector/base.py
"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.performance_collector.base import PerformanceDataCollectorBase
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_collector():
    db = MagicMock()
    return PerformanceDataCollectorBase(db), db


def test_base_collector_init():
    """Collector stores db reference."""
    collector, db = _make_collector()
    assert collector.db is db


def test_positive_keywords_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.POSITIVE_KEYWORDS, list)
    assert len(collector.POSITIVE_KEYWORDS) > 0


def test_negative_keywords_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.NEGATIVE_KEYWORDS, list)
    assert len(collector.NEGATIVE_KEYWORDS) > 0


def test_tech_keywords_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.TECH_KEYWORDS, list)
    assert len(collector.TECH_KEYWORDS) > 0


def test_collaboration_keywords_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.COLLABORATION_KEYWORDS, list)
    assert len(collector.COLLABORATION_KEYWORDS) > 0


def test_problem_solving_patterns_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.PROBLEM_SOLVING_PATTERNS, list)
    assert len(collector.PROBLEM_SOLVING_PATTERNS) > 0


def test_knowledge_sharing_patterns_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.KNOWLEDGE_SHARING_PATTERNS, list)
    assert len(collector.KNOWLEDGE_SHARING_PATTERNS) > 0


def test_tech_breakthrough_patterns_is_list():
    collector, _ = _make_collector()
    assert isinstance(collector.TECH_BREAKTHROUGH_PATTERNS, list)
    assert len(collector.TECH_BREAKTHROUGH_PATTERNS) > 0
