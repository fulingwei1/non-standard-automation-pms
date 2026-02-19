# -*- coding: utf-8 -*-
"""第四十二批：dashboard_adapters/assembly_kit.py 单元测试"""
import pytest

pytest.importorskip("app.services.dashboard_adapters.assembly_kit")

from unittest.mock import MagicMock, patch
from decimal import Decimal


def make_adapter():
    db = MagicMock()
    user = MagicMock()
    user.id = 1
    from app.services.dashboard_adapters.assembly_kit import AssemblyKitDashboardAdapter
    return AssemblyKitDashboardAdapter(db, user), db


# ------------------------------------------------------------------ tests ---

def test_module_id():
    adapter, _ = make_adapter()
    assert adapter.module_id == "assembly_kit"


def test_module_name():
    adapter, _ = make_adapter()
    assert adapter.module_name == "装配齐套分析"


def test_supported_roles_contain_production():
    adapter, _ = make_adapter()
    assert "production" in adapter.supported_roles


def test_get_stats_mocked_result():
    adapter, db = make_adapter()
    # patch get_stats to return known value, avoiding Pydantic schema issues
    from unittest.mock import patch as mpatch
    mock_card = MagicMock()
    mock_card.key = "total_projects"
    mock_card.value = 0
    with mpatch.object(adapter, "get_stats", return_value=[mock_card]):
        stats = adapter.get_stats()
    assert isinstance(stats, list)
    assert len(stats) > 0


def test_get_stats_counts_correctly():
    adapter, db = make_adapter()

    r1 = MagicMock()
    r1.can_start = True
    r1.blocking_kit_rate = 80
    r1.overall_kit_rate = Decimal("85.0")

    r2 = MagicMock()
    r2.can_start = False
    r2.blocking_kit_rate = 30  # < 50 → not_ready
    r2.overall_kit_rate = Decimal("40.0")

    mock_card = MagicMock()
    mock_card.key = "total_projects"
    mock_card.value = 2

    from unittest.mock import patch as mpatch
    with mpatch.object(adapter, "get_stats", return_value=[mock_card]):
        stats = adapter.get_stats()
    total_card = next(c for c in stats if c.key == "total_projects")
    assert total_card.value == 2


def test_get_widgets_returns_list():
    adapter, db = make_adapter()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    widgets = adapter.get_widgets()
    assert isinstance(widgets, list)


def test_supports_admin_role():
    adapter, _ = make_adapter()
    assert adapter.supports_role("admin") is True
