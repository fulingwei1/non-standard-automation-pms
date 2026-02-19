# -*- coding: utf-8 -*-
"""第四十二批：dashboard_adapter.py 单元测试"""
import pytest

pytest.importorskip("app.services.dashboard_adapter")

from unittest.mock import MagicMock
from app.services.dashboard_adapter import DashboardAdapter, DashboardRegistry


class MinimalAdapter(DashboardAdapter):
    @property
    def module_id(self): return "test_module"
    @property
    def module_name(self): return "测试模块"
    @property
    def supported_roles(self): return ["admin", "user"]
    def get_stats(self): return []
    def get_widgets(self): return []


def make_registry():
    return DashboardRegistry()


# ------------------------------------------------------------------ tests ---

def test_registry_register_and_get():
    reg = make_registry()
    reg.register(MinimalAdapter)
    db = MagicMock()
    user = MagicMock()
    adapter = reg.get_adapter("test_module", db, user)
    assert adapter is not None
    assert adapter.module_id == "test_module"


def test_registry_get_unknown_returns_none():
    reg = make_registry()
    adapter = reg.get_adapter("unknown", MagicMock(), MagicMock())
    assert adapter is None


def test_registry_duplicate_raises():
    reg = make_registry()
    reg.register(MinimalAdapter)
    with pytest.raises(ValueError, match="already registered"):
        reg.register(MinimalAdapter)


def test_get_adapters_for_role():
    reg = make_registry()
    reg.register(MinimalAdapter)
    adapters = reg.get_adapters_for_role("admin", MagicMock(), MagicMock())
    assert len(adapters) == 1


def test_get_adapters_for_role_not_in_list():
    reg = make_registry()
    reg.register(MinimalAdapter)
    adapters = reg.get_adapters_for_role("guest", MagicMock(), MagicMock())
    assert len(adapters) == 0


def test_list_modules():
    reg = make_registry()
    reg.register(MinimalAdapter)
    modules = reg.list_modules()
    assert len(modules) == 1
    assert modules[0]["module_id"] == "test_module"
    assert "supported_roles" in modules[0]


def test_supports_role():
    adapter = MinimalAdapter(MagicMock(), MagicMock())
    assert adapter.supports_role("admin") is True
    assert adapter.supports_role("nobody") is False


def test_get_detailed_data_not_implemented():
    adapter = MinimalAdapter(MagicMock(), MagicMock())
    with pytest.raises(NotImplementedError):
        adapter.get_detailed_data()
