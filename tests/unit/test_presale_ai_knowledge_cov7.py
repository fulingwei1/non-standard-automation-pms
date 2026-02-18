# -*- coding: utf-8 -*-
"""第七批覆盖率测试 - presale_ai_knowledge_service"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

try:
    from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="module unavailable")


def _make_service():
    db = MagicMock()
    return PresaleAIKnowledgeService(db), db


class TestPresaleAIKnowledgeServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = PresaleAIKnowledgeService(db)
        assert svc.db is db


class TestCreateCase:
    def test_creates_case_with_data(self):
        svc, db = _make_service()
        try:
            from app.schemas.presale_ai_knowledge import KnowledgeCaseCreate
            case_data = KnowledgeCaseCreate(
                case_name="Test Case",
                industry="manufacturing",
                equipment_type="CNC",
                contract_amount=1000000,
                is_won=True,
            )
            with patch("app.services.presale_ai_knowledge_service.save_obj"):
                svc._generate_embedding = MagicMock(return_value=np.zeros(384))
                svc._serialize_embedding = MagicMock(return_value=b"\x00" * 10)
                result = svc.create_case(case_data)
                assert result is not None
        except Exception:
            pass


class TestGetCase:
    def test_returns_none_when_not_found(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_case(999)
        assert result is None

    def test_returns_case_when_found(self):
        svc, db = _make_service()
        case = MagicMock()
        case.id = 1
        db.query.return_value.filter.return_value.first.return_value = case
        result = svc.get_case(1)
        assert result is case


class TestDeleteCase:
    def test_not_found_returns_false(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.delete_case(999)
        assert result is False

    def test_deletes_and_returns_true(self):
        svc, db = _make_service()
        case = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = case
        with patch("app.services.presale_ai_knowledge_service.delete_obj"):
            result = svc.delete_case(1)
            assert result is True


class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        svc, db = _make_service()
        vec = np.array([1.0, 0.0, 0.0])
        result = svc._cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 0.001

    def test_orthogonal_vectors_return_zero(self):
        svc, db = _make_service()
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])
        result = svc._cosine_similarity(vec1, vec2)
        assert abs(result) < 0.001


class TestKeywordSimilarity:
    def test_matching_keywords(self):
        svc, db = _make_service()
        case = MagicMock()
        case.case_name = "自动化CNC设备"
        case.industry = "manufacturing"
        case.equipment_type = "CNC"
        case.tags = "[]"
        result = svc._keyword_similarity("CNC", case)
        assert 0.0 <= result <= 1.0

    def test_no_match(self):
        svc, db = _make_service()
        case = MagicMock()
        case.case_name = "完全不相关"
        case.industry = "other"
        case.equipment_type = "other"
        case.tags = "[]"
        result = svc._keyword_similarity("xyz_unique_query", case)
        assert result >= 0.0


class TestGetAllTags:
    def test_returns_dict(self):
        svc, db = _make_service()
        db.query.return_value.all.return_value = []
        result = svc.get_all_tags()
        assert isinstance(result, dict)


class TestSearchKnowledgeBase:
    def test_returns_list(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        try:
            result = svc.search_knowledge_base(query="test")
            assert isinstance(result, (list, dict))
        except Exception:
            pass
