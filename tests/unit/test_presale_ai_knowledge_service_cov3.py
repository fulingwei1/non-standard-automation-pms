# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - presale_ai_knowledge_service"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

pytest.importorskip("app.services.presale_ai_knowledge_service")

from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService


def make_db():
    return MagicMock()


def make_case(**kw):
    c = MagicMock()
    c.id = kw.get("id", 1)
    c.case_name = kw.get("case_name", "Test Case")
    c.industry = kw.get("industry", "Manufacturing")
    c.equipment_type = kw.get("equipment_type", "CNC")
    c.project_summary = kw.get("project_summary", "Test summary for machine tool")
    c.technical_highlights = kw.get("technical_highlights", "")
    c.success_factors = kw.get("success_factors", "")
    c.lessons_learned = kw.get("lessons_learned", "")
    c.tags = kw.get("tags", ["tag1"])
    c.quality_score = kw.get("quality_score", 0.8)
    c.is_public = kw.get("is_public", True)
    c.embedding = kw.get("embedding", None)
    c.project_amount = kw.get("project_amount", 500000)
    return c


class TestCreateCase:
    def test_create_case_success(self):
        db = make_db()
        svc = PresaleAIKnowledgeService(db)

        case_data = MagicMock()
        case_data.case_name = "Test"
        case_data.industry = "Manufacturing"
        case_data.equipment_type = "CNC"
        case_data.customer_name = "Customer A"
        case_data.project_amount = 500000
        case_data.project_summary = "Test summary"
        case_data.technical_highlights = ""
        case_data.success_factors = ""
        case_data.lessons_learned = ""
        case_data.tags = ["tag1"]
        case_data.quality_score = 0.8
        case_data.is_public = True

        with patch("app.services.presale_ai_knowledge_service.save_obj"), \
             patch.object(svc, "_generate_embedding", return_value=np.array([0.1, 0.2, 0.3])), \
             patch.object(svc, "_serialize_embedding", return_value=b"mock_bytes"):
            result = svc.create_case(case_data)
        assert result is not None

    def test_create_case_no_summary(self):
        db = make_db()
        svc = PresaleAIKnowledgeService(db)

        case_data = MagicMock()
        case_data.case_name = "Test No Summary"
        case_data.industry = "Manufacturing"
        case_data.equipment_type = "CNC"
        case_data.customer_name = None
        case_data.project_amount = 0
        case_data.project_summary = None
        case_data.technical_highlights = ""
        case_data.success_factors = ""
        case_data.lessons_learned = ""
        case_data.tags = []
        case_data.quality_score = None
        case_data.is_public = True

        with patch("app.services.presale_ai_knowledge_service.save_obj"):
            result = svc.create_case(case_data)
        assert result is not None


class TestUpdateCase:
    def test_update_case_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = PresaleAIKnowledgeService(db)
        update_data = MagicMock()
        update_data.model_dump.return_value = {"case_name": "Updated"}
        result = svc.update_case(999, update_data)
        assert result is None

    def test_update_case_success(self):
        db = make_db()
        case = make_case()
        db.query.return_value.filter.return_value.first.return_value = case
        svc = PresaleAIKnowledgeService(db)

        update_data = MagicMock()
        update_data.model_dump.return_value = {"case_name": "Updated Name"}

        result = svc.update_case(1, update_data)
        assert result is not None


class TestDeleteCase:
    def test_delete_case_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = PresaleAIKnowledgeService(db)
        result = svc.delete_case(999)
        assert result is False

    def test_delete_case_success(self):
        db = make_db()
        case = make_case()
        db.query.return_value.filter.return_value.first.return_value = case
        svc = PresaleAIKnowledgeService(db)

        with patch("app.services.presale_ai_knowledge_service.delete_obj"):
            result = svc.delete_case(1)
        assert result is True


class TestSemanticSearch:
    def test_empty_results(self):
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = PresaleAIKnowledgeService(db)

        search_req = MagicMock()
        search_req.query = "machine tool"
        search_req.industry = None
        search_req.equipment_type = None
        search_req.min_amount = None
        search_req.max_amount = None
        search_req.top_k = 5

        cases, total = svc.semantic_search(search_req)
        assert cases == []
        assert total == 0

    def test_with_cases_no_embedding(self):
        db = make_db()
        case = make_case(embedding=None)
        db.query.return_value.filter.return_value.all.return_value = [case]
        svc = PresaleAIKnowledgeService(db)

        search_req = MagicMock()
        search_req.query = "machine tool"
        search_req.industry = None
        search_req.equipment_type = None
        search_req.min_amount = None
        search_req.max_amount = None
        search_req.top_k = 5

        with patch.object(svc, "_generate_embedding", return_value=np.array([0.1, 0.2])), \
             patch.object(svc, "_keyword_similarity", return_value=0.7):
            cases, total = svc.semantic_search(search_req)
        assert len(cases) == 1


class TestSimilarityHelpers:
    def test_cosine_similarity_identical(self):
        db = make_db()
        svc = PresaleAIKnowledgeService(db)
        vec = np.array([1.0, 0.0, 0.0])
        result = svc._cosine_similarity(vec, vec)
        assert abs(result - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        db = make_db()
        svc = PresaleAIKnowledgeService(db)
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        result = svc._cosine_similarity(v1, v2)
        assert abs(result) < 0.001

    def test_keyword_similarity_matching(self):
        db = make_db()
        svc = PresaleAIKnowledgeService(db)
        case = make_case(project_summary="machine CNC manufacturing tools")
        result = svc._keyword_similarity("machine CNC", case)
        assert result > 0

    def test_keyword_similarity_no_match(self):
        db = make_db()
        svc = PresaleAIKnowledgeService(db)
        case = make_case(project_summary="apple banana fruit salad")
        result = svc._keyword_similarity("machine CNC manufacturing", case)
        assert result >= 0
