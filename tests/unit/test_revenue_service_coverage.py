# -*- coding: utf-8 -*-
"""revenue_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.revenue_service import RevenueService

class TestRevenueServiceInit:
    def test_init(self):
        service = RevenueService(Mock())
        assert service is not None
