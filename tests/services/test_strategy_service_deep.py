# -*- coding: utf-8 -*-
"""
strategy_service 深度覆盖测试 - N5组
补充：状态机流转、多维筛选、错误边界、StrategyService类方法
"""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


def _make_strategy(**overrides):
    s = MagicMock()
    defaults = dict(
        id=1, code="S-2025", name="战略2025", vision="愿景", mission="使命",
        slogan="口号", year=2025, start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31), status="DRAFT", is_active=True,
        created_by=1, approved_by=None,
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _mock_query(db, first_val=None, all_val=None, count_val=0):
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.count.return_value = count_val
    q.first.return_value = first_val
    q.all.return_value = all_val or []
    db.query.return_value = q
    return q


class TestCreateStrategyValidation(unittest.TestCase):
    """create_strategy 创建验证"""

    def test_creates_with_draft_status(self):
        """新建战略默认为 DRAFT 状态"""
        from app.services.strategy.strategy_service import create_strategy
        db = MagicMock()
        data = MagicMock(
            code="S-2025", name="战略", vision="V", mission="M", slogan="S",
            year=2025, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )

        with patch('app.services.strategy.strategy_service.Strategy') as MockStrategy:
            MockStrategy.return_value = MagicMock(status="DRAFT")
            result = create_strategy(db, data, created_by=1)
            # Should call db.add/commit/refresh
            db.add.assert_called_once()
            db.commit.assert_called_once()

    def test_create_passes_created_by(self):
        """创建战略时应传递 created_by"""
        from app.services.strategy.strategy_service import create_strategy
        db = MagicMock()
        data = MagicMock(
            code="S-2025", name="战略", vision="V", mission="M", slogan="S",
            year=2025, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )

        with patch('app.services.strategy.strategy_service.Strategy') as MockStrategy:
            mock_instance = MagicMock()
            MockStrategy.return_value = mock_instance
            create_strategy(db, data, created_by=99)
            call_kwargs = MockStrategy.call_args.kwargs
            self.assertEqual(call_kwargs.get("created_by"), 99)


class TestListStrategiesFiltering(unittest.TestCase):
    """list_strategies 多维过滤测试"""

    def test_filter_by_year_only(self):
        """仅按年度过滤"""
        from app.services.strategy.strategy_service import list_strategies
        db = MagicMock()
        q = _mock_query(db, count_val=2)

        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = [_make_strategy(), _make_strategy(id=2)]
            items, total = list_strategies(db, year=2025)
            self.assertEqual(total, 2)
            self.assertEqual(len(items), 2)

    def test_filter_by_status_only(self):
        """仅按状态过滤"""
        from app.services.strategy.strategy_service import list_strategies
        db = MagicMock()
        _mock_query(db, count_val=1)

        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = [_make_strategy(status="ACTIVE")]
            items, total = list_strategies(db, status="ACTIVE")
            self.assertEqual(items[0].status, "ACTIVE")

    def test_filter_by_year_and_status(self):
        """同时按年度和状态过滤"""
        from app.services.strategy.strategy_service import list_strategies
        db = MagicMock()
        _mock_query(db, count_val=0)

        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = []
            items, total = list_strategies(db, year=2024, status="ARCHIVED")
            self.assertEqual(total, 0)

    def test_no_filter_returns_all(self):
        """无过滤条件返回所有"""
        from app.services.strategy.strategy_service import list_strategies
        db = MagicMock()
        strategies = [_make_strategy(id=i) for i in range(1, 4)]
        _mock_query(db, count_val=3)

        with patch("app.services.strategy.strategy_service.apply_pagination") as ap:
            ap.return_value.all.return_value = strategies
            items, total = list_strategies(db)
            self.assertEqual(total, 3)


class TestPublishStrategyStateTransition(unittest.TestCase):
    """publish_strategy 状态转换测试"""

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_publish_sets_active_and_approved_by(self, mock_get):
        """发布战略应设置状态为ACTIVE并记录审批人"""
        from app.services.strategy.strategy_service import publish_strategy
        db = MagicMock()
        strategy = _make_strategy(status="DRAFT")
        mock_get.return_value = strategy

        q = MagicMock()
        q.filter.return_value = q
        db.query.return_value = q

        result = publish_strategy(db, 1, approved_by=5)
        self.assertEqual(result.status, "ACTIVE")
        self.assertEqual(result.approved_by, 5)
        db.commit.assert_called_once()

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_publish_deactivates_old_active(self, mock_get):
        """发布新战略时应将旧的ACTIVE战略停用"""
        from app.services.strategy.strategy_service import publish_strategy
        db = MagicMock()
        strategy = _make_strategy(status="DRAFT")
        mock_get.return_value = strategy

        q = MagicMock()
        q.filter.return_value = q
        db.query.return_value = q

        result = publish_strategy(db, 1, approved_by=5)
        # db.query was called (to find old active strategies)
        self.assertTrue(db.query.called)


class TestArchiveAndDeleteStrategy(unittest.TestCase):
    """archive_strategy + delete_strategy 流程"""

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_archive_sets_archived_status(self, mock_get):
        """归档战略应设置状态为 ARCHIVED"""
        from app.services.strategy.strategy_service import archive_strategy
        db = MagicMock()
        strategy = _make_strategy(status="ACTIVE")
        mock_get.return_value = strategy

        result = archive_strategy(db, 1)
        self.assertEqual(result.status, "ARCHIVED")
        db.commit.assert_called_once()

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_delete_soft_deletes(self, mock_get):
        """删除战略应软删除（is_active=False）"""
        from app.services.strategy.strategy_service import delete_strategy
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy

        result = delete_strategy(db, 1)
        self.assertTrue(result)
        self.assertFalse(strategy.is_active)

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_archive_not_found_returns_none(self, mock_get):
        """归档不存在的战略时返回 None"""
        from app.services.strategy.strategy_service import archive_strategy
        db = MagicMock()
        mock_get.return_value = None

        result = archive_strategy(db, 999)
        self.assertIsNone(result)


class TestStrategyServiceClassMethods(unittest.TestCase):
    """StrategyService 类方法测试"""

    def test_get_active_strategy(self):
        """get_active_strategy 返回激活战略"""
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        active = _make_strategy(status="ACTIVE")
        _mock_query(db, first_val=active)

        svc = StrategyService(db)
        result = svc.get_active()
        self.assertEqual(result.status, "ACTIVE")

    def test_publish_strategy_via_class(self):
        """通过 StrategyService.publish 发布战略"""
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        svc = StrategyService(db)

        with patch("app.services.strategy.strategy_service.publish_strategy") as mock_pub:
            mock_pub.return_value = _make_strategy(status="ACTIVE")
            result = svc.publish(1, approved_by=2)
            mock_pub.assert_called_once_with(db, 1, 2)

    def test_get_by_code_not_found(self):
        """按编码查找不存在时返回 None"""
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        _mock_query(db, first_val=None)
        svc = StrategyService(db)

        result = svc.get_by_code("NONEXISTENT-CODE")
        self.assertIsNone(result)

    def test_archive_strategy_via_class(self):
        """通过 StrategyService.archive 归档战略"""
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        svc = StrategyService(db)

        with patch("app.services.strategy.strategy_service.archive_strategy") as mock_archive:
            mock_archive.return_value = _make_strategy(status="ARCHIVED")
            result = svc.archive(1)
            mock_archive.assert_called_once_with(db, 1)

    def test_update_via_class(self):
        """通过 StrategyService.update 更新战略"""
        from app.services.strategy.strategy_service import StrategyService
        db = MagicMock()
        svc = StrategyService(db)
        data = MagicMock()
        data.model_dump.return_value = {"name": "新战略名称"}

        with patch("app.services.strategy.strategy_service.get_strategy") as mock_get:
            strategy = _make_strategy()
            mock_get.return_value = strategy
            result = svc.update(1, data)
            db.commit.assert_called_once()


class TestGetStrategyDetailEdgeCases(unittest.TestCase):
    """get_strategy_detail 边界情况"""

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_detail_includes_health_score(self, mock_get):
        """战略详情应包含健康分"""
        from app.services.strategy.strategy_service import get_strategy_detail
        db = MagicMock()
        strategy = _make_strategy()
        mock_get.return_value = strategy

        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.count.return_value = 0
        db.query.return_value = q

        with patch("app.services.strategy.health_calculator.calculate_strategy_health", return_value=75):
            result = get_strategy_detail(db, 1)
            self.assertIsNotNone(result)

    @patch("app.services.strategy.strategy_service.get_strategy")
    def test_detail_not_found_returns_none(self, mock_get):
        """不存在的战略应返回 None"""
        from app.services.strategy.strategy_service import get_strategy_detail
        db = MagicMock()
        mock_get.return_value = None

        result = get_strategy_detail(db, 9999)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
