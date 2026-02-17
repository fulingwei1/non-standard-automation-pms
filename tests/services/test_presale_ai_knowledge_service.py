# -*- coding: utf-8 -*-
"""售前AI知识库服务单元测试 (PresaleAIKnowledgeService)"""
import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch


def _make_db():
    return MagicMock()


def _make_case(**kw):
    case = MagicMock()
    defaults = dict(
        id=1,
        case_name="比亚迪ADAS ICT测试系统案例",
        industry="汽车",
        equipment_type="ICT测试设备",
        customer_name="比亚迪股份有限公司",
        project_amount=1500000.0,
        project_summary="为比亚迪提供ADAS系统ICT测试解决方案",
        technical_highlights="自动化测试、AI辅助分析",
        success_factors="良好沟通",
        tags=["汽车", "ICT", "ADAS"],
        quality_score=0.8,
        is_public=True,
        embedding=None,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(case, k, v)
    return case


class TestPresaleAIKnowledgeServiceInit:
    def test_init_sets_db(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        svc = PresaleAIKnowledgeService(db)
        assert svc.db is db


class TestGetCase:
    def test_get_existing_case(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        case = _make_case(id=1)
        db.query.return_value.filter.return_value.first.return_value = case
        svc = PresaleAIKnowledgeService(db)
        result = svc.get_case(1)
        assert result is case

    def test_get_nonexistent_case_returns_none(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = PresaleAIKnowledgeService(db)
        result = svc.get_case(999)
        assert result is None


class TestDeleteCase:
    def test_delete_existing_case_returns_true(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        case = _make_case(id=1)
        svc = PresaleAIKnowledgeService(db)
        svc.get_case = MagicMock(return_value=case)
        with patch('app.services.presale_ai_knowledge_service.delete_obj') as mock_delete:
            result = svc.delete_case(1)
        assert result is True
        mock_delete.assert_called_once_with(db, case)

    def test_delete_nonexistent_case_returns_false(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        svc = PresaleAIKnowledgeService(db)
        svc.get_case = MagicMock(return_value=None)
        result = svc.delete_case(999)
        assert result is False


class TestSearchKnowledgeBase:
    def test_search_with_keyword(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        case1 = _make_case(id=1)
        case2 = _make_case(id=2)
        # Mock chain: query -> filter -> count -> ...
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [case1, case2]

        svc = PresaleAIKnowledgeService(db)
        cases, total = svc.search_knowledge_base(keyword="ADAS")
        assert total == 2
        assert len(cases) == 2

    def test_search_returns_empty_when_no_match(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        svc = PresaleAIKnowledgeService(db)
        cases, total = svc.search_knowledge_base(keyword="不存在的关键词")
        assert total == 0
        assert cases == []


class TestGetAllTags:
    def test_get_all_tags_from_cases(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        case1 = MagicMock(tags=["汽车", "ICT", "ADAS"])
        case2 = MagicMock(tags=["ICT", "测试"])
        db.query.return_value.all.return_value = [case1, case2]

        svc = PresaleAIKnowledgeService(db)
        result = svc.get_all_tags()
        assert "tags" in result
        assert "tag_counts" in result
        assert "ICT" in result["tags"]
        assert result["tag_counts"]["ICT"] == 2

    def test_get_all_tags_empty(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        db = _make_db()
        db.query.return_value.all.return_value = []

        svc = PresaleAIKnowledgeService(db)
        result = svc.get_all_tags()
        assert result["tags"] == []
        assert result["tag_counts"] == {}


class TestSemanticSearch:
    def test_no_cases_returns_empty(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        from app.schemas.presale_ai_knowledge import SemanticSearchRequest
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []

        svc = PresaleAIKnowledgeService(db)
        req = SemanticSearchRequest(query="ADAS测试", top_k=5)
        cases, total = svc.semantic_search(req)
        assert cases == []
        assert total == 0

    def test_keyword_similarity_fallback(self):
        from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService
        from app.schemas.presale_ai_knowledge import SemanticSearchRequest
        db = _make_db()
        case = _make_case(embedding=None)  # no embedding → keyword fallback
        db.query.return_value.filter.return_value.all.return_value = [case]

        svc = PresaleAIKnowledgeService(db)
        svc._generate_embedding = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
        svc._keyword_similarity = MagicMock(return_value=0.7)

        req = SemanticSearchRequest(query="ADAS测试", top_k=5)
        cases, total = svc.semantic_search(req)
        assert len(cases) == 1
        assert total == 1
