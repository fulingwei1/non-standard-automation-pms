# -*- coding: utf-8 -*-
"""shortage_analytics_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.shortage_analytics.shortage_analytics_service import ShortageAnalyticsService

class TestShortageAnalyticsServiceInit:
    def test_init(self):
        service = ShortageAnalyticsService(Mock())
        assert service is not None
