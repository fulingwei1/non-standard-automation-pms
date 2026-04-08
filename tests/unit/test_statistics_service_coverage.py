# -*- coding: utf-8 -*-
"""statistics_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.exception.statistics_service import StatisticsService

class TestStatisticsServiceInit:
    def test_init(self):
        service = StatisticsService(Mock())
        assert service is not None
