# -*- coding: utf-8 -*-
"""PmoDashboardAdapter 单元测试"""
from unittest.mock import MagicMock, patch
import pytest

from app.services.dashboard_adapters.pmo import PmoDashboardAdapter


class TestPmoDashboardAdapter:
    def _make_adapter(self):
        db = MagicMock()
        user = MagicMock()
        adapter = PmoDashboardAdapter.__new__(PmoDashboardAdapter)
        adapter.db = db
        adapter.current_user = user
        return adapter

    def test_module_id(self):
        adapter = self._make_adapter()
        assert adapter.module_id == "pmo"

    def test_module_name(self):
        adapter = self._make_adapter()
        assert adapter.module_name == "项目管理办公室"

    def test_supported_roles(self):
        adapter = self._make_adapter()
        assert "pmo" in adapter.supported_roles
        assert "admin" in adapter.supported_roles

    @patch("app.services.data_scope_service.DataScopeService.apply_data_scope")
    def test_get_stats(self, mock_apply):
        adapter = self._make_adapter()
        p1 = MagicMock(); p1.health = "H1"
        p2 = MagicMock(); p2.health = "H2"
        mock_apply.return_value = adapter.db.query.return_value.filter.return_value
        mock_apply.return_value.all.return_value = [p1, p2]

        stats = adapter.get_stats()
        assert len(stats) == 5
        keys = {s.key for s in stats}
        assert "active_projects" in keys

    @patch("app.services.data_scope_service.DataScopeService.apply_data_scope")
    def test_get_widgets(self, mock_apply):
        adapter = self._make_adapter()
        mock_apply.return_value = adapter.db.query.return_value.filter.return_value
        mock_apply.return_value.limit.return_value.all.return_value = []

        widgets = adapter.get_widgets()
        assert len(widgets) == 1
        assert widgets[0].widget_id == "risk_projects"
