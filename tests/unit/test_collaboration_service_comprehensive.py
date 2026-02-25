# -*- coding: utf-8 -*-
"""CollaborationService 综合测试"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.collaboration_service import CollaborationService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def svc(mock_db):
    return CollaborationService(mock_db)


class TestInit:
    def test_init(self, mock_db):
        svc = CollaborationService(mock_db)
        assert svc.db is mock_db


class TestGetRating:
    def test_found(self, svc, mock_db):
        rating = MagicMock()
        rating.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = rating
        result = svc.get_rating(1)
        assert result is not None

    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_rating(999)
        assert result is None


class TestGetCollaborationMatrix:
    def test_returns_dict(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = svc.get_collaboration_matrix(period_id=1)
        assert isinstance(result, dict)


class TestGetCollaborationStats:
    def test_returns_dict(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = svc.get_collaboration_stats(user_id=1)
        assert isinstance(result, dict)


class TestGroupByRaterType:
    def test_empty_list(self, svc):
        result = svc._group_by_rater_type([])
        assert isinstance(result, dict)

    def test_with_ratings(self, svc):
        r1 = MagicMock(rater_type="peer", score=Decimal("4.0"))
        r2 = MagicMock(rater_type="peer", score=Decimal("5.0"))
        r3 = MagicMock(rater_type="manager", score=Decimal("3.0"))
        result = svc._group_by_rater_type([r1, r2, r3])
        assert isinstance(result, dict)
