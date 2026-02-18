# -*- coding: utf-8 -*-
"""第十五批: knowledge_contribution_service 单元测试"""
import pytest

pytest.importorskip("app.services.knowledge_contribution_service")

from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.knowledge_contribution_service import KnowledgeContributionService


def make_db():
    return MagicMock()


def test_create_contribution_basic():
    db = make_db()
    with patch("app.services.knowledge_contribution_service.save_obj") as mock_save:
        svc = KnowledgeContributionService(db)
        data = MagicMock()
        data.contribution_type = "code"
        data.job_type = "backend"
        data.title = "Test"
        data.description = "desc"
        data.file_path = None
        data.tags = []
        result = svc.create_contribution(data, contributor_id=1)
        assert result.contributor_id == 1
        assert result.status == "draft"
        mock_save.assert_called_once()


def test_get_contribution_found():
    db = make_db()
    mock_contrib = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_contrib
    svc = KnowledgeContributionService(db)
    result = svc.get_contribution(42)
    assert result == mock_contrib


def test_get_contribution_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = KnowledgeContributionService(db)
    assert svc.get_contribution(99) is None


def test_update_contribution_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = KnowledgeContributionService(db)
    data = MagicMock()
    data.status = None
    result = svc.update_contribution(99, data, user_id=1)
    assert result is None


def test_update_contribution_permission_error():
    db = make_db()
    contrib = MagicMock()
    contrib.contributor_id = 5
    db.query.return_value.filter.return_value.first.return_value = contrib
    svc = KnowledgeContributionService(db)
    data = MagicMock()
    data.status = None
    data.model_dump.return_value = {}
    with pytest.raises(PermissionError):
        svc.update_contribution(1, data, user_id=99)


def test_get_contributor_stats_no_contributions():
    db = make_db()
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    svc = KnowledgeContributionService(db)
    stats = svc.get_contributor_stats(user_id=1)
    assert stats["total_contributions"] == 0
    assert stats["total_reuse"] == 0


def test_get_contributor_stats_with_data():
    db = make_db()
    c1 = MagicMock()
    c1.contribution_type = "code"
    c1.reuse_count = 3
    c1.rating_score = Decimal("4.5")
    c1.rating_count = 2
    c2 = MagicMock()
    c2.contribution_type = "code"
    c2.reuse_count = 1
    c2.rating_score = None
    c2.rating_count = 0
    # KnowledgeContribution.contributor_id == user_id AND status == 'approved'
    # Both filters use chained .filter() calls
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = [c1, c2]
    db.query.return_value.filter.return_value.all.return_value = [c1, c2]
    svc = KnowledgeContributionService(db)
    # Patch the actual DB call to return expected data
    from unittest.mock import patch
    with patch.object(svc.db, "query") as mock_q:
        chain = MagicMock()
        chain.filter.return_value.filter.return_value.all.return_value = [c1, c2]
        chain.filter.return_value.all.return_value = [c1, c2]
        mock_q.return_value = chain
        stats = svc.get_contributor_stats(user_id=1)
    assert stats["total_contributions"] == 2
    assert stats["total_reuse"] == 4
