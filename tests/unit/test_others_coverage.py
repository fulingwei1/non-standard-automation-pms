# -*- coding: utf-8 -*-
"""others单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.others import OthersDashboardAdapter

class TestOthersDashboardAdapterInit:
    def test_init(self):
        service = OthersDashboardAdapter(Mock())
        assert service is not None
