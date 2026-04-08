# -*- coding: utf-8 -*-
"""presales单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.presales import PresalesDashboardAdapter

class TestPresalesDashboardAdapterInit:
    def test_init(self):
        service = PresalesDashboardAdapter(Mock())
        assert service is not None
