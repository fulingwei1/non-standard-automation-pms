# -*- coding: utf-8 -*-
"""dept_head_view单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.dept_head_view import DeptHeadViewDashboardAdapter

class TestDeptHeadViewDashboardAdapterInit:
    def test_init(self):
        service = DeptHeadViewDashboardAdapter(Mock())
        assert service is not None
