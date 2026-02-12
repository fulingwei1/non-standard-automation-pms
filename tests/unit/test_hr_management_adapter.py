# -*- coding: utf-8 -*-
"""Tests for dashboard_adapters/hr_management.py"""

from unittest.mock import MagicMock

import pytest


class TestHrDashboardAdapter:
    def setup_method(self):
        self.db = MagicMock()
        self.user = MagicMock()

    def test_module_id(self):
        from app.services.dashboard_adapters.hr_management import HrDashboardAdapter
        adapter = HrDashboardAdapter(self.db, self.user)
        assert adapter.module_id == "hr_management"

    def test_module_name(self):
        from app.services.dashboard_adapters.hr_management import HrDashboardAdapter
        adapter = HrDashboardAdapter(self.db, self.user)
        assert adapter.module_name == "人事管理"

    def test_supported_roles(self):
        from app.services.dashboard_adapters.hr_management import HrDashboardAdapter
        adapter = HrDashboardAdapter(self.db, self.user)
        roles = adapter.supported_roles
        assert "hr" in roles or "admin" in roles
