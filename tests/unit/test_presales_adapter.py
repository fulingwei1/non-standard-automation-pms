# -*- coding: utf-8 -*-
"""Tests for dashboard_adapters/presales.py"""

from unittest.mock import MagicMock

import pytest


class TestPresalesDashboardAdapter:
    def setup_method(self):
        self.db = MagicMock()
        self.user = MagicMock()

    def test_module_id(self):
        from app.services.dashboard_adapters.presales import PresalesDashboardAdapter
        adapter = PresalesDashboardAdapter(self.db, self.user)
        assert adapter.module_id == "presales"

    def test_module_name(self):
        from app.services.dashboard_adapters.presales import PresalesDashboardAdapter
        adapter = PresalesDashboardAdapter(self.db, self.user)
        assert adapter.module_name == "售前分析"

    def test_supported_roles(self):
        from app.services.dashboard_adapters.presales import PresalesDashboardAdapter
        adapter = PresalesDashboardAdapter(self.db, self.user)
        roles = adapter.supported_roles
        assert isinstance(roles, list)
        assert "presales" in roles or "sales" in roles or "admin" in roles
