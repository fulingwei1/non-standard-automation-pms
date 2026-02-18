# -*- coding: utf-8 -*-
"""第九批: test_strategy_service_cov9.py - strategy_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

pytest.importorskip("app.services.strategy.strategy_service")

from app.services.strategy import strategy_service as ss


@pytest.fixture
def mock_db():
    return MagicMock()


def make_strategy(id=1, code="S-2026", name="数字化转型战略", year=2026, status="DRAFT"):
    s = MagicMock()
    s.id = id
    s.code = code
    s.name = name
    s.year = year
    s.status = status
    return s


class TestCreateStrategy:
    """测试创建战略"""

    def test_create_strategy(self, mock_db):
        data = MagicMock()
        data.code = "S-2026"
        data.name = "数字化转型"
        data.vision = "领先科技"
        data.mission = "创造价值"
        data.slogan = "勇于创新"
        data.year = 2026
        data.start_date = date(2026, 1, 1)
        data.end_date = date(2026, 12, 31)
        mock_db.refresh.side_effect = lambda x: None
        result = ss.create_strategy(mock_db, data, created_by=1)
        assert mock_db.add.called
        assert mock_db.commit.called


class TestGetStrategy:
    """测试获取战略"""

    def test_get_strategy_found(self, mock_db):
        strategy = make_strategy()
        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        result = ss.get_strategy(mock_db, strategy_id=1)
        assert result is not None

    def test_get_strategy_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = ss.get_strategy(mock_db, strategy_id=9999)
        assert result is None


class TestGetStrategyByCode:
    """测试按代码获取战略"""

    def test_get_by_code(self, mock_db):
        strategy = make_strategy()
        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        result = ss.get_strategy_by_code(mock_db, code="S-2026")
        assert result is not None


class TestGetActiveStrategy:
    """测试获取活跃战略"""

    def test_get_active_strategy(self, mock_db):
        strategy = make_strategy(status="ACTIVE")
        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        result = ss.get_active_strategy(mock_db)
        assert result.status == "ACTIVE"


class TestListStrategies:
    """测试战略列表"""

    def test_list_strategies_empty(self, mock_db):
        mock_db.query.return_value.order_by.return_value.count.return_value = 0
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        result = ss.list_strategies(mock_db)
        assert result is not None


class TestPublishStrategy:
    """测试发布战略"""

    def test_publish_strategy(self, mock_db):
        strategy = make_strategy(status="DRAFT")
        # get_strategy internally calls query().filter().first()
        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        # update() call in publish_strategy
        mock_db.query.return_value.filter.return_value.update.return_value = 0
        mock_db.refresh.side_effect = lambda x: None
        # approved_by is the parameter name (not published_by)
        result = ss.publish_strategy(mock_db, strategy_id=1, approved_by=1)
        assert result is not None


class TestDeleteStrategy:
    """测试删除战略"""

    def test_delete_strategy_found(self, mock_db):
        strategy = make_strategy()
        mock_db.query.return_value.filter.return_value.first.return_value = strategy
        result = ss.delete_strategy(mock_db, strategy_id=1)
        assert result is True

    def test_delete_strategy_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = ss.delete_strategy(mock_db, strategy_id=9999)
        assert result is False
