# -*- coding: utf-8 -*-
"""hr_management单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.hr_management import HrDashboardAdapter

class TestHrDashboardAdapterInit:
    def test_init(self):
        service = HrDashboardAdapter(Mock())
        assert service is not None
