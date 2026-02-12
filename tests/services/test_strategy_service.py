# -*- coding: utf-8 -*-
"""Tests for app.services.strategy.strategy_service"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_strategy(**overrides):
    s = MagicMock()
    defaults = dict(
        id=1, code="S-2025", name="战略2025", vision="愿景", mission="使命",
        slogan="口号", year=2025, start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31), status="DRAFT", is_active=True,
        created_by=1, approved_by=None, approved_at=None, published_at=None,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _mock_db_query(db, result=None, results_list=None, count=0):
    """Configure db.query(...).filter(...) chain."""
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.first.return_value = result
    q.all.return_value = results_list or []
    q.count.return_value = count
    q.update.return_value = None
    db.query.return_value = q
    return q


# ---------------------------------------------------------------------------
# Tests – free functions
# ---------------------------------------------------------------------------

class TestCreateStrategy:
    def test_creates_and_returns(self):
        from app.services.strategy.strategy_service import create_strategy
        db = MagicMock()
        data = MagicMock()
        data.code = "S-2025"
        data.name = "战略"
        data.vision = data.mission = data.slogan = "x"
        data.year = 2025
        data.start_date = date(2025, 1, 1)
        data.end_date = date(2025, 12, 31)

        result = create_strategy(db, data, created_by=1)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()


class TestGetStrategy:
    def test_found(self):
        from app.services.strategy.strategy_service import get_strategy
        db = MagicMock()
        expected = _make_strategy()
        _mock_db_query(db, result=expected)
        assert get_strategy(db, 1) == expected

    def test_not_found(self):
        from app.services.strategy.strategy_service import get_strategy
        db = MagicMock()
        _mock_db_query(db, result=None)
        assert get_strategy(db, 999) is None


class TestGetStrategyByCode:
    def test_found(self):
        from app.services.strategy.strategy_service import get_strategy_by_code
        db = MagicMock()
        expected = _make_strategy()
        _mock_db_query(db, result=expected)
        assert get_strategy_by_code(db, "S-2025") == expected


class TestGetStrategyByYear:
    def test_found(self):
        from app.services.strategy.strategy_service import get_strategy_by_year
        db = MagicMock()
        expected = _make_strategy()
        _mock_db_query(db, result=expected)
        assert get_strategy_by_year(db, 2025) == expected


class TestGetActiveStrategy:
    def test_found(self):
        from app.services.strategy.strategy_service import get_active_strategy
        db = MagicMock()
        expected = _make_strategy(status="ACTIVE")
        _mock_db_query(db, result=expected)
        assert get_active_strategy(db) == expected


class TestListStrategies:
    def test_returns_tuple(self):
        from app.services.strategy.strategy_service import list_strategies
        db = MagicMock()
        items = [_make_strategy()]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.count.return_value = 1
        db.query.return_value = q

        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = items
            result, total = list_strategies(db)
            assert total == 1
            assert result == items

    def test_filter_by_year_and_status(self):
        from app.services.strategy.strategy_service import list_strategies
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.count.return_value = 0
        db.query.return_value = q

        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = []
            result, total = list_strategies(db, year=2025, status="ACTIVE")
            assert total == 0


class TestUpdateStrategy:
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_update_existing(self, mock_get):
        from app.services.strategy.strategy_service import update_strategy
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy
        data = MagicMock()
        data.model_dump.return_value = {"name": "新名称"}

        result = update_strategy(db, 1, data)
        assert result == strategy
        db.commit.assert_called_once()

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_update_not_found(self, mock_get):
        from app.services.strategy.strategy_service import update_strategy
        db = MagicMock()
        mock_get.return_value = None
        assert update_strategy(db, 999, MagicMock()) is None


class TestPublishStrategy:
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_publish(self, mock_get):
        from app.services.strategy.strategy_service import publish_strategy
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy
        q = MagicMock()
        q.filter.return_value = q
        db.query.return_value = q

        result = publish_strategy(db, 1, approved_by=2)
        assert result.status == "ACTIVE"
        assert result.approved_by == 2
        db.commit.assert_called_once()

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_publish_not_found(self, mock_get):
        from app.services.strategy.strategy_service import publish_strategy
        db = MagicMock()
        mock_get.return_value = None
        assert publish_strategy(db, 999, 2) is None


class TestArchiveStrategy:
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_archive(self, mock_get):
        from app.services.strategy.strategy_service import archive_strategy
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy
        result = archive_strategy(db, 1)
        assert result.status == "ARCHIVED"

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_archive_not_found(self, mock_get):
        from app.services.strategy.strategy_service import archive_strategy
        db = MagicMock()
        mock_get.return_value = None
        assert archive_strategy(db, 999) is None


class TestDeleteStrategy:
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_delete(self, mock_get):
        from app.services.strategy.strategy_service import delete_strategy
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy
        assert delete_strategy(db, 1) is True
        assert strategy.is_active is False

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_delete_not_found(self, mock_get):
        from app.services.strategy.strategy_service import delete_strategy
        db = MagicMock()
        mock_get.return_value = None
        assert delete_strategy(db, 999) is False


class TestGetStrategyDetail:
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_not_found(self, mock_get):
        from app.services.strategy.strategy_service import get_strategy_detail
        db = MagicMock()
        mock_get.return_value = None
        assert get_strategy_detail(db, 999) is None

    @patch("app.services.strategy.strategy_service.calculate_strategy_health", create=True)
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_returns_detail(self, mock_get, mock_health):
        from app.services.strategy.strategy_service import get_strategy_detail
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy

        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.count.return_value = 5
        db.query.return_value = q

        with patch("app.services.strategy.strategy_service.calculate_strategy_health", return_value=85):
            result = get_strategy_detail(db, 1)
            assert result is not None
            assert result.id == 1


class TestGetStrategyMapData:
    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_not_found(self, mock_get):
        from app.services.strategy.strategy_service import get_strategy_map_data
        db = MagicMock()
        mock_get.return_value = None
        assert get_strategy_map_data(db, 999) is None

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_returns_map(self, mock_get):
        from app.services.strategy.strategy_service import get_strategy_map_data
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = []
        q.count.return_value = 0
        db.query.return_value = q

        with patch("app.services.strategy.health_calculator.calculate_strategy_health", return_value=80), \
             patch("app.services.strategy.health_calculator.calculate_csf_health", return_value={"score": 80, "level": "GOOD", "kpi_completion_rate": 75}):
            result = get_strategy_map_data(db, 1)
            assert result is not None
            assert result.strategy_id == 1
            assert len(result.dimensions) == 4


# ---------------------------------------------------------------------------
# Tests – StrategyService wrapper class
# ---------------------------------------------------------------------------

class TestStrategyServiceClass:
    def test_create(self):
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        svc = StrategyService(db)
        data = MagicMock()
        data.code = "S"
        data.name = data.vision = data.mission = data.slogan = "x"
        data.year = 2025
        data.start_date = date(2025, 1, 1)
        data.end_date = date(2025, 12, 31)
        svc.create(data, created_by=1)
        db.add.assert_called_once()

    def test_get(self):
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        _mock_db_query(db, result=_make_strategy())
        svc = StrategyService(db)
        assert svc.get(1) is not None

    def test_get_strategies_with_page(self):
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.count.return_value = 0
        db.query.return_value = q

        svc = StrategyService(db)
        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = []
            svc.get_strategies(page=1, page_size=10)

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_delete_strategy_alias(self, mock_get):
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        mock_get.return_value = _make_strategy()
        svc = StrategyService(db)
        assert svc.delete_strategy(1) is True

    @patch("app.services.strategy.strategy_service.get_strategy_detail")
    def test_get_metrics_not_found(self, mock_detail):
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        mock_detail.return_value = None
        svc = StrategyService(db)
        assert svc.get_metrics(999) == {}

    @patch("app.services.strategy.strategy_service.get_strategy_detail")
    def test_get_metrics_ok(self, mock_detail):
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        detail = MagicMock(csf_count=3, kpi_count=10, annual_work_count=5, health_score=80)
        mock_detail.return_value = detail
        svc = StrategyService(db)
        m = svc.get_metrics(1)
        assert m["csf_count"] == 3
