# -*- coding: utf-8 -*-
"""Tests for collaboration_rating/ratings.py"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestRatingManager:

    def _make_manager(self):
        from app.services.collaboration_rating.ratings import RatingManager
        db = MagicMock()
        service = MagicMock()
        return RatingManager(db, service), db, service

    def test_create_rating_invitations_auto_select(self):
        mgr, db, svc = self._make_manager()
        svc.selector.auto_select_collaborators.return_value = [2, 3]
        # No existing ratings
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit = MagicMock()
        # After commit, find the rating
        rating_mock = MagicMock()
        rating_mock.id = 100

        # For profile lookups
        profile = MagicMock()
        profile.job_type = "MECHANICAL"

        call_count = [0]
        def query_side_effect(*args):
            return db.query.return_value
        db.query.side_effect = None
        db.query.return_value.filter.return_value.first.side_effect = [
            None, profile, profile,  # for collaborator 2
            None, profile, profile,  # for collaborator 3
            rating_mock, rating_mock  # post-commit lookups
        ]

        result = mgr.create_rating_invitations(engineer_id=1, period_id=1)
        assert isinstance(result, list)

    def test_create_rating_invitations_existing_skipped(self):
        mgr, db, svc = self._make_manager()
        svc.selector.auto_select_collaborators.return_value = [2]
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        db.commit = MagicMock()

        result = mgr.create_rating_invitations(engineer_id=1, period_id=1)
        assert result == []

    def test_submit_rating_not_found(self):
        mgr, db, _ = self._make_manager()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            mgr.submit_rating(1, 1, 5, 5, 5, 5)

    def test_submit_rating_invalid_score(self):
        mgr, db, _ = self._make_manager()
        rating = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = rating
        with pytest.raises(ValueError, match="1-5"):
            mgr.submit_rating(1, 1, 6, 5, 5, 5)

    def test_submit_rating_success(self):
        mgr, db, _ = self._make_manager()
        rating = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = rating
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = mgr.submit_rating(1, 1, 4, 4, 5, 3, comment="好")
        assert rating.communication_score == 4
        assert rating.response_score == 4
        assert rating.delivery_score == 5
        assert rating.interface_score == 3
        assert rating.total_score is not None
        db.commit.assert_called()

    def test_get_pending_ratings(self):
        mgr, db, _ = self._make_manager()
        r1 = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [r1]
        result = mgr.get_pending_ratings(rater_id=1)
        assert len(result) == 1

    def test_get_pending_ratings_with_period(self):
        mgr, db, _ = self._make_manager()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = mgr.get_pending_ratings(rater_id=1, period_id=1)
        assert result == []

    def test_auto_complete_missing_ratings(self):
        mgr, db, _ = self._make_manager()
        r1 = MagicMock()
        r1.total_score = None
        r2 = MagicMock()
        r2.total_score = None
        db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        db.commit = MagicMock()

        count = mgr.auto_complete_missing_ratings(period_id=1)
        assert count == 2
        assert r1.communication_score == 3
        assert r1.total_score == Decimal("75.0")
