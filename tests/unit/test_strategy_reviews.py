# -*- coding: utf-8 -*-
"""Tests for strategy/review/strategy_reviews.py"""

from unittest.mock import MagicMock

import pytest


class TestStrategyReviews:
    def setup_method(self):
        self.db = MagicMock()

    @pytest.mark.skip(reason="Missing health_calculator module")
    def test_create_strategy_review(self):
        from app.services.strategy.review.strategy_reviews import create_strategy_review
        data = MagicMock()
        data.model_dump.return_value = {"title": "Review1", "strategy_id": 1}
        result = create_strategy_review(self.db, data, created_by=1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_get_strategy_review_found(self):
        from app.services.strategy.review.strategy_reviews import get_strategy_review
        review = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = review
        result = get_strategy_review(self.db, 1)
        assert result == review

    def test_get_strategy_review_not_found(self):
        from app.services.strategy.review.strategy_reviews import get_strategy_review
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_strategy_review(self.db, 999)
        assert result is None

    def test_delete_strategy_review_not_found(self):
        from app.services.strategy.review.strategy_reviews import delete_strategy_review
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = delete_strategy_review(self.db, 999)
        assert result is False
