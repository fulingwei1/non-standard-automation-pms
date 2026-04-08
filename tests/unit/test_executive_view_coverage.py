# -*- coding: utf-8 -*-
"""executive_view单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.executive_view import ExecutiveViewDashboardAdapter

class TestExecutiveViewDashboardAdapterInit:
    def test_init(self):
        service = ExecutiveViewDashboardAdapter(Mock())
        assert service is not None
