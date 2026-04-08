# -*- coding: utf-8 -*-
"""member_view单元测试"""
import pytest
from unittest.mock import Mock
from app.services.dashboard.adapters.member_view import MemberViewDashboardAdapter

class TestMemberViewDashboardAdapterInit:
    def test_init(self):
        service = MemberViewDashboardAdapter(Mock())
        assert service is not None
