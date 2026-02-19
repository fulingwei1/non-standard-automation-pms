# -*- coding: utf-8 -*-
"""第四十六批 - 战略审视单元测试"""
import pytest

pytest.importorskip("app.services.strategy.review.strategy_reviews",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.strategy.review.strategy_reviews import (
    create_strategy_review,
    get_strategy_review,
    list_strategy_reviews,
    update_strategy_review,
    delete_strategy_review,
    get_latest_review,
)


def _make_db():
    return MagicMock()


def _make_review(review_id=1):
    r = MagicMock()
    r.id = review_id
    r.is_active = True
    r.strategy_id = 1
    return r


class TestCreateStrategyReview:
    def test_creates_review_and_commits(self):
        db = _make_db()
        data = MagicMock()
        data.strategy_id = 1
        data.review_date = None
        data.review_period = "2024-Q1"
        data.review_type = "QUARTERLY"
        data.summary = "测试"
        data.achievements = ""
        data.issues = ""
        data.action_items = ""
        data.next_steps = ""

        health_mock = {"score": 80}
        with patch("app.services.strategy.review.strategy_reviews.calculate_strategy_health",
                   return_value=80), \
             patch("app.services.strategy.review.strategy_reviews.calculate_dimension_health",
                   return_value=health_mock):
            create_strategy_review(db, data, created_by=1)

        db.add.assert_called_once()
        db.commit.assert_called_once()


class TestGetStrategyReview:
    def test_returns_review_when_found(self):
        db = _make_db()
        review = _make_review()
        db.query.return_value.filter.return_value.first.return_value = review
        result = get_strategy_review(db, 1)
        assert result is review

    def test_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = get_strategy_review(db, 99)
        assert result is None


class TestListStrategyReviews:
    def test_returns_items_and_total(self):
        db = _make_db()
        db.query.return_value.filter.return_value.count.return_value = 5

        with patch("app.services.strategy.review.strategy_reviews.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [_make_review()]
            items, total = list_strategy_reviews(db, strategy_id=1)

        assert total == 5

    def test_filters_by_review_type(self):
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 2
        with patch("app.services.strategy.review.strategy_reviews.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            list_strategy_reviews(db, strategy_id=1, review_type="QUARTERLY")


class TestUpdateStrategyReview:
    def test_returns_none_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = update_strategy_review(db, 99, MagicMock())
        assert result is None

    def test_updates_fields_and_commits(self):
        db = _make_db()
        review = _make_review()
        db.query.return_value.filter.return_value.first.return_value = review
        data = MagicMock()
        data.model_dump.return_value = {"summary": "更新的摘要"}

        update_strategy_review(db, 1, data)
        assert review.summary == "更新的摘要"
        db.commit.assert_called_once()


class TestDeleteStrategyReview:
    def test_returns_false_when_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        assert delete_strategy_review(db, 99) is False

    def test_soft_deletes_and_returns_true(self):
        db = _make_db()
        review = _make_review()
        db.query.return_value.filter.return_value.first.return_value = review
        result = delete_strategy_review(db, 1)
        assert result is True
        assert review.is_active is False
        db.commit.assert_called_once()


class TestGetLatestReview:
    def test_returns_none_when_no_review(self):
        db = _make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_latest_review(db, strategy_id=1)
        assert result is None
