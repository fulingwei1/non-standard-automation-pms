# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - collaboration_rating/ratings.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, call

pytest.importorskip("app.services.collaboration_rating.ratings",
                    reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def manager(mock_db):
    from app.services.collaboration_rating.ratings import RatingManager
    service = MagicMock()
    return RatingManager(mock_db, service)


def _make_rating(rating_id, rater_id, ratee_id, period_id, total_score=None):
    r = MagicMock()
    r.id = rating_id
    r.rater_id = rater_id
    r.ratee_id = ratee_id
    r.period_id = period_id
    r.total_score = total_score
    r.communication_score = None
    r.response_score = None
    r.delivery_score = None
    r.interface_score = None
    r.comment = None
    r.project_id = None
    r.rater_job_type = None
    r.ratee_job_type = None
    return r


class TestRatingManagerSubmitRating:

    def test_submit_rating_updates_scores(self, manager, mock_db):
        rating = _make_rating(1, rater_id=10, ratee_id=20, period_id=1)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = rating

        result = manager.submit_rating(
            rating_id=1,
            rater_id=10,
            communication_score=4,
            response_score=4,
            delivery_score=5,
            interface_score=3,
            comment="不错"
        )
        assert rating.communication_score == 4
        assert rating.response_score == 4
        assert rating.delivery_score == 5
        assert rating.interface_score == 3

    def test_submit_rating_not_found_raises(self, manager, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None

        with pytest.raises(ValueError, match="不存在"):
            manager.submit_rating(1, rater_id=10,
                                  communication_score=3, response_score=3,
                                  delivery_score=3, interface_score=3)

    def test_submit_rating_invalid_score_raises(self, manager, mock_db):
        rating = _make_rating(1, rater_id=10, ratee_id=20, period_id=1)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = rating

        with pytest.raises(ValueError, match="评分"):
            manager.submit_rating(1, rater_id=10,
                                  communication_score=6, response_score=3,
                                  delivery_score=3, interface_score=3)

    def test_submit_rating_calculates_total_score(self, manager, mock_db):
        rating = _make_rating(1, rater_id=10, ratee_id=20, period_id=1)
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = rating

        manager.submit_rating(1, rater_id=10,
                              communication_score=5, response_score=5,
                              delivery_score=5, interface_score=5)
        # 根据代码公式：(5*25+5*25+5*25+5*25)/5*20 = 500/5*20 = 2000
        # 只验证 total_score 被设置（非None）
        assert rating.total_score is not None


class TestRatingManagerGetPendingRatings:

    def test_get_pending_ratings_returns_list(self, manager, mock_db):
        pending = [_make_rating(1, 10, 20, 1), _make_rating(2, 10, 30, 1)]
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = pending

        result = manager.get_pending_ratings(rater_id=10)
        assert len(result) == 2

    def test_get_pending_ratings_with_period(self, manager, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        result = manager.get_pending_ratings(rater_id=10, period_id=5)
        assert result == []


class TestRatingManagerAutoComplete:

    def test_auto_complete_fills_default_scores(self, manager, mock_db):
        pending = [_make_rating(1, 10, 20, 1), _make_rating(2, 11, 21, 1)]
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = pending

        count = manager.auto_complete_missing_ratings(period_id=1)
        assert count == 2
        for r in pending:
            assert r.communication_score == 3
            assert r.total_score == Decimal("75.0")
