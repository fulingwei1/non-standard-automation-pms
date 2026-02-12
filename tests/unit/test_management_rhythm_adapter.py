# -*- coding: utf-8 -*-
"""Tests for dashboard_adapters/management_rhythm.py"""

from unittest.mock import MagicMock

import pytest


class TestManagementRhythmDashboardAdapter:
    def setup_method(self):
        self.db = MagicMock()
        self.user = MagicMock()

    def test_module_id(self):
        from app.services.dashboard_adapters.management_rhythm import ManagementRhythmDashboardAdapter
        adapter = ManagementRhythmDashboardAdapter(self.db, self.user)
        assert adapter.module_id == "management_rhythm"

    def test_module_name(self):
        from app.services.dashboard_adapters.management_rhythm import ManagementRhythmDashboardAdapter
        adapter = ManagementRhythmDashboardAdapter(self.db, self.user)
        assert adapter.module_name == "管理节律"

    def test_supported_roles(self):
        from app.services.dashboard_adapters.management_rhythm import ManagementRhythmDashboardAdapter
        adapter = ManagementRhythmDashboardAdapter(self.db, self.user)
        assert isinstance(adapter.supported_roles, list)
        assert len(adapter.supported_roles) > 0
