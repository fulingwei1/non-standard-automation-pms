# -*- coding: utf-8 -*-
"""strategy_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.strategy.strategy_service import StrategyService

class TestStrategyServiceInit:
    def test_init(self):
        service = StrategyService(Mock())
        assert service is not None
