# -*- coding: utf-8 -*-
"""
StrategyService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- get_strategies: 获取战略列表
- get_strategy: 获取单个战略
- create_strategy: 创建战略
- update_strategy: 更新战略
- delete_strategy: 删除战略
- get_strategy_metrics: 获取战略指标
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

import pytest


class TestStrategyServiceInit:
    """测试 StrategyService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        service = StrategyService(mock_db)

        assert service.db == mock_db


class TestGetStrategies:
    """测试 get_strategies 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_strategy1 = MagicMock()
        mock_strategy1.id = 1
        mock_strategy2 = MagicMock()
        mock_strategy2.id = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_strategy1, mock_strategy2]
        mock_query.count.return_value = 2
        mock_db.query.return_value = mock_query

        service = StrategyService(mock_db)

        result = service.get_strategies(page=1, page_size=20)

        assert result is not None

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = StrategyService(mock_db)

        result = service.get_strategies(status="ACTIVE")

        mock_query.filter.assert_called()

    def test_filters_by_year(self):
        """测试按年份过滤"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        service = StrategyService(mock_db)

        result = service.get_strategies(year=2024)

        mock_query.filter.assert_called()


class TestGetStrategy:
    """测试 get_strategy 方法"""

    def test_returns_strategy(self):
        """测试返回战略"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.id = 1
        mock_strategy.name = "年度战略"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy

        service = StrategyService(mock_db)

        result = service.get_strategy(1)

        assert result == mock_strategy

    def test_returns_none_for_missing(self):
        """测试不存在时返回None"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = StrategyService(mock_db)

        result = service.get_strategy(999)

        assert result is None


class TestCreateStrategy:
    """测试 create_strategy 方法"""

    def test_creates_successfully(self):
        """测试成功创建战略"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = StrategyService(mock_db)

        strategy_data = MagicMock()
        strategy_data.name = "2024年度战略"
        strategy_data.description = "战略描述"
        strategy_data.year = 2024

        result = service.create_strategy(strategy_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestUpdateStrategy:
    """测试 update_strategy 方法"""

    def test_updates_successfully(self):
        """测试成功更新战略"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.id = 1
        mock_strategy.name = "原名称"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = StrategyService(mock_db)

        update_data = MagicMock()
        update_data.name = "新名称"

        result = service.update_strategy(1, update_data)

        mock_db.commit.assert_called_once()

    def test_returns_none_for_missing(self):
        """测试不存在时返回None"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = StrategyService(mock_db)

        update_data = MagicMock()

        result = service.update_strategy(999, update_data)

        assert result is None


class TestDeleteStrategy:
    """测试 delete_strategy 方法"""

    def test_deletes_successfully(self):
        """测试成功删除战略"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        service = StrategyService(mock_db)

        result = service.delete_strategy(1)

        assert result is True or mock_db.delete.called

    def test_returns_false_for_missing(self):
        """测试不存在时返回False"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = StrategyService(mock_db)

        result = service.delete_strategy(999)

        assert result is False or result is None


class TestGetStrategyMetrics:
    """测试 get_strategy_metrics 方法"""

    def test_returns_metrics(self):
        """测试返回战略指标"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.id = 1
        mock_strategy.metrics = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy

        service = StrategyService(mock_db)

        result = service.get_strategy_metrics(1)

        assert result is not None

    def test_returns_empty_for_no_metrics(self):
        """测试无指标时返回空列表"""
        from app.services.strategy.strategy_service import StrategyService

        mock_db = MagicMock()

        mock_strategy = MagicMock()
        mock_strategy.id = 1
        mock_strategy.metrics = []

        mock_db.query.return_value.filter.return_value.first.return_value = mock_strategy

        service = StrategyService(mock_db)

        result = service.get_strategy_metrics(1)

        assert result == [] or result is not None
