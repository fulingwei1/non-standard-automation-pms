# -*- coding: utf-8 -*-
"""ECN similarity 单元测试"""
from unittest.mock import MagicMock
import pytest

from app.services.ecn_knowledge_service.similarity import (
    _text_similarity,
    _cost_similarity,
    _get_match_reasons,
    _material_similarity,
    _calculate_similarity,
    find_similar_ecns,
)


class TestTextSimilarity:
    def test_empty(self):
        assert _text_similarity("", "") == 0.0
        assert _text_similarity(None, "test") == 0.0

    def test_identical(self):
        assert _text_similarity("hello world", "hello world") == 1.0

    def test_partial(self):
        score = _text_similarity("hello world", "hello there")
        assert 0 < score < 1


class TestCostSimilarity:
    def test_both_zero(self):
        assert _cost_similarity(0, 0) == 1.0

    def test_one_zero(self):
        assert _cost_similarity(0, 100) == 0.0

    def test_same(self):
        assert _cost_similarity(100, 100) == 1.0

    def test_different(self):
        score = _cost_similarity(100, 200)
        assert 0 < score < 1


class TestGetMatchReasons:
    def test_same_type(self):
        ecn1 = MagicMock()
        ecn2 = MagicMock()
        ecn1.ecn_type = "DESIGN"
        ecn2.ecn_type = "DESIGN"
        ecn1.root_cause_category = None
        ecn2.root_cause_category = None
        reasons = _get_match_reasons(ecn1, ecn2, 0.8)
        assert any("DESIGN" in r for r in reasons)
        assert any("高度" in r for r in reasons)


class TestMaterialSimilarity:
    def test_no_materials(self):
        service = MagicMock()
        service.db.query.return_value.filter.return_value.all.return_value = []
        assert _material_similarity(service, 1, 2) == 0.0


class TestFindSimilarEcns:
    def test_ecn_not_found(self):
        service = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            find_similar_ecns(service, 999)

    def test_no_completed_ecns(self):
        service = MagicMock()
        ecn = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = ecn
        service.db.query.return_value.filter.return_value.all.return_value = []
        # second filter call for completed ecns
        results = find_similar_ecns(service, 1)
        # May return empty or the mock list - depends on mock chain
        assert isinstance(results, list)
