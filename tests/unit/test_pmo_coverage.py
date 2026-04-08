# -*- coding: utf-8 -*-
"""pmo单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.pmo import PmoDashboardAdapter

class TestPmoDashboardAdapterInit:
    def test_init(self):
        service = PmoDashboardAdapter(Mock())
        assert service is not None
