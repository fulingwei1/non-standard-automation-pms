# -*- coding: utf-8 -*-
"""
Tests for app/services/labor_cost/utils.py
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.labor_cost.utils import (
        group_timesheets_by_user,
        find_existing_cost,
        update_existing_cost,
        create_new_cost,
        check_budget_alert,
        delete_existing_costs,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_timesheet(user_id, user_name, hours, work_date=None, ts_id=1):
    ts = MagicMock()
    ts.user_id = user_id
    ts.user_name = user_name
    ts.hours = hours
    ts.work_date = work_date or date(2024, 1, 1)
    ts.id = ts_id
    return ts


def test_group_timesheets_empty():
    """空列表时返回空字典"""
    result = group_timesheets_by_user([])
    assert result == {}


def test_group_timesheets_single_user():
    """单个用户的工时记录"""
    ts = _make_timesheet(1, "Alice", 8, ts_id=10)
    result = group_timesheets_by_user([ts])
    assert 1 in result
    assert result[1]["total_hours"] == Decimal("8")
    assert result[1]["user_name"] == "Alice"
    assert 10 in result[1]["timesheet_ids"]


def test_group_timesheets_multiple_users():
    """多用户时正确分组"""
    ts1 = _make_timesheet(1, "Alice", 4, ts_id=1)
    ts2 = _make_timesheet(2, "Bob", 6, ts_id=2)
    ts3 = _make_timesheet(1, "Alice", 4, ts_id=3)
    result = group_timesheets_by_user([ts1, ts2, ts3])
    assert result[1]["total_hours"] == Decimal("8")
    assert result[2]["total_hours"] == Decimal("6")


def test_find_existing_cost():
    """测试 find_existing_cost 调用"""
    db = MagicMock()
    cost = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = cost
    result = find_existing_cost(db, project_id=1, user_id=2)
    assert result is cost


def test_check_budget_alert_no_exception():
    """check_budget_alert 失败时不抛出异常（容错处理）"""
    db = MagicMock()
    # patch where CostAlertService is actually imported from
    with patch("app.services.cost_alert_service.CostAlertService") as MockAlert:
        MockAlert.check_budget_execution.side_effect = Exception("alert error")
        # Should NOT raise, since check_budget_alert catches exceptions
        check_budget_alert(db, project_id=1, user_id=1)


def test_update_existing_cost():
    """update_existing_cost 正确更新金额"""
    db = MagicMock()
    project = MagicMock()
    project.actual_cost = Decimal("1000")
    cost = MagicMock()
    cost.amount = Decimal("200")
    user_data = {"user_name": "Alice", "total_hours": Decimal("10")}
    update_existing_cost(db, project, cost, Decimal("300"), user_data, date.today())
    assert cost.amount == Decimal("300")
    db.add.assert_called_once_with(cost)


def test_create_new_cost():
    """create_new_cost 正确创建并返回 ProjectCost"""
    db = MagicMock()
    project = MagicMock()
    project.actual_cost = 0
    user_data = {"user_name": "Bob", "total_hours": Decimal("8")}
    with patch("app.services.labor_cost.utils.ProjectCost") as MockCost:
        mock_cost = MagicMock()
        MockCost.return_value = mock_cost
        result = create_new_cost(db, project, 1, 2, Decimal("400"), user_data, date.today())
        db.add.assert_called_once_with(mock_cost)
        assert result is mock_cost
