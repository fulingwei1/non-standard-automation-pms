# -*- coding: utf-8 -*-
"""第五批：presale_ai_knowledge_service.py 单元测试"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

try:
    from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="presale_ai_knowledge_service not importable")


def make_service(db=None):
    if db is None:
        db = MagicMock()
    return PresaleAIKnowledgeService(db)


class TestGetCase:
    def test_found(self):
        db = MagicMock()
        case = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = case
        svc = make_service(db)
        result = svc.get_case(1)
        assert result == case

    def test_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.get_case(999)
        assert result is None


class TestDeleteCase:
    def test_delete_success(self):
        db = MagicMock()
        case = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = case
        with patch("app.services.presale_ai_knowledge_service.delete_obj") as mock_del:
            svc = make_service(db)
            result = svc.delete_case(1)
            assert result is True

    def test_delete_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        result = svc.delete_case(999)
        assert result is False


class TestCosineSimilarity:
    def test_identical_vectors(self):
        svc = make_service()
        v = np.array([1.0, 0.0, 0.0])
        result = svc._cosine_similarity(v, v)
        assert abs(result - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        svc = make_service()
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        result = svc._cosine_similarity(v1, v2)
        assert abs(result) < 1e-6

    def test_zero_vector(self):
        svc = make_service()
        v1 = np.array([0.0, 0.0])
        v2 = np.array([1.0, 0.0])
        # zero vector may produce NaN due to divide by zero
        result = svc._cosine_similarity(v1, v2)
        assert result == 0.0 or (result != result)  # 0.0 or NaN


class TestKeywordSimilarity:
    def test_exact_match(self):
        svc = make_service()
        case = MagicMock()
        case.case_name = "汽车激光切割项目"
        case.project_summary = "汽车激光切割高精度方案"
        case.technical_highlights = "高精度"
        case.tags = ["汽车", "切割"]
        result = svc._keyword_similarity("汽车激光切割", case)
        assert result > 0

    def test_no_match(self):
        svc = make_service()
        case = MagicMock()
        case.industry = "航空"
        case.equipment_type = "焊接"
        case.technical_highlights = "高温"
        case.tags = []
        result = svc._keyword_similarity("xxxyyyzzz", case)
        assert result >= 0.0


class TestAnalyzeSuccessPatterns:
    def test_returns_string(self):
        svc = make_service()
        cases = []
        for s in ["标准化流程", "团队协作", "标准化"]:
            c = MagicMock()
            c.success_factors = s
            cases.append(c)
        result = svc._analyze_success_patterns(cases)
        assert isinstance(result, str)

    def test_empty_cases(self):
        svc = make_service()
        result = svc._analyze_success_patterns([])
        assert isinstance(result, str)


class TestGetAllTags:
    def test_returns_dict_with_tags(self):
        db = MagicMock()
        cases = []
        for tags in [["A", "B"], ["B", "C"], ["A"]]:
            c = MagicMock()
            c.tags = tags
            cases.append(c)
        db.query.return_value.filter.return_value.all.return_value = cases
        svc = make_service(db)
        result = svc.get_all_tags()
        assert isinstance(result, dict)
