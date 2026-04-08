# -*- coding: utf-8 -*-
"""management_rhythm单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.management_rhythm import ManagementRhythmDashboardAdapter

class TestManagementRhythmDashboardAdapterInit:
    def test_init(self):
        service = ManagementRhythmDashboardAdapter(Mock())
        assert service is not None
