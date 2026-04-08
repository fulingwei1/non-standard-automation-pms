# -*- coding: utf-8 -*-
"""pm_view单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.pm_view import PmViewDashboardAdapter

class TestPmViewDashboardAdapterInit:
    def test_init(self):
        service = PmViewDashboardAdapter(Mock())
        assert service is not None
