# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 知识贡献数据收集器
tests/unit/test_knowledge_collector_cov37.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.performance_collector.knowledge_collector")

from app.services.performance_collector.knowledge_collector import KnowledgeCollector


def _make_collector(contributions=None, code_count=0, plc_count=0):
    db = MagicMock()

    if contributions is None:
        contributions = []

    def query_side(model):
        q = MagicMock()
        from app.models.engineer_performance import (
            KnowledgeContribution, CodeModule, PlcModuleLibrary
        )
        if model is KnowledgeContribution:
            q.filter.return_value.all.return_value = contributions
        elif model is CodeModule:
            q.filter.return_value.count.return_value = code_count
        elif model is PlcModuleLibrary:
            q.filter.return_value.count.return_value = plc_count
        return q

    db.query.side_effect = query_side

    collector = KnowledgeCollector.__new__(KnowledgeCollector)
    collector.db = db
    return collector


def _make_contribution(ctype="document", reuse=3):
    c = MagicMock()
    c.contribution_type = ctype
    c.reuse_count = reuse
    c.status = "approved"
    return c


class TestKnowledgeCollector:
    def test_returns_dict_with_expected_keys(self):
        collector = _make_collector()
        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        expected_keys = {
            "total_contributions", "document_count", "template_count",
            "module_count", "total_reuse_count", "code_modules", "plc_modules"
        }
        assert expected_keys.issubset(result.keys())

    def test_counts_total_contributions(self):
        contribs = [
            _make_contribution("document"),
            _make_contribution("template"),
            _make_contribution("module"),
        ]
        collector = _make_collector(contributions=contribs)
        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["total_contributions"] == 3

    def test_sums_reuse_count(self):
        contribs = [
            _make_contribution(reuse=5),
            _make_contribution(reuse=3),
        ]
        collector = _make_collector(contributions=contribs)
        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["total_reuse_count"] == 8

    def test_counts_document_type(self):
        contribs = [
            _make_contribution("document"),
            _make_contribution("document"),
            _make_contribution("template"),
        ]
        collector = _make_collector(contributions=contribs)
        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["document_count"] == 2
        assert result["template_count"] == 1

    def test_includes_code_module_count(self):
        collector = _make_collector(code_count=4, plc_count=2)
        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["code_modules"] == 4
        assert result["plc_modules"] == 2

    def test_returns_zeros_on_exception(self):
        collector = KnowledgeCollector.__new__(KnowledgeCollector)
        collector.db = MagicMock()
        collector.db.query.side_effect = Exception("DB error")

        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["total_contributions"] == 0
        assert "error" in result

    def test_handles_none_reuse_count(self):
        c = _make_contribution(reuse=None)
        collector = _make_collector(contributions=[c])
        result = collector.collect_knowledge_contribution_data(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )
        assert result["total_reuse_count"] == 0
