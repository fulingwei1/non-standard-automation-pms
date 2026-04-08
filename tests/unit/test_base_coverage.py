# -*- coding: utf-8 -*-
"""base单元测试"""
import pytest
from unittest.mock import Mock
from app.services.statistics.base import SyncStatisticsService

class TestSyncStatisticsServiceInit:
    def test_init(self):
        service = SyncStatisticsService(Mock())
        assert service is not None
