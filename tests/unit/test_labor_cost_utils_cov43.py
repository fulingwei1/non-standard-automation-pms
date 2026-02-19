# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/labor_cost/utils.py
"""
import pytest

pytest.importorskip("app.services.labor_cost.utils")

from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.labor_cost.utils import (
    query_approved_timesheets,
    delete_existing_costs,
    group_timesheets_by_user,
    find_existing_cost,
    update_existing_cost,
    create_new_cost,
    check_budget_alert,
)


def make_db():
    return MagicMock()


# ── 1. query_approved_timesheets: 带日期范围 ──────────────────────────────────
def test_query_approved_timesheets_with_dates():
    db = make_db()
    ts = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [ts]
    db.query.return_value = q

    result = query_approved_timesheets(db, 1, date(2026, 1, 1), date(2026, 1, 31))
    assert ts in result


# ── 2. query_approved_timesheets: 无日期范围 ─────────────────────────────────
def test_query_approved_timesheets_no_dates():
    db = make_db()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    db.query.return_value = q

    result = query_approved_timesheets(db, 2, None, None)
    assert result == []


# ── 3. delete_existing_costs: 删除并更新项目成本 ─────────────────────────────
def test_delete_existing_costs():
    db = make_db()
    project = MagicMock()
    project.actual_cost = Decimal("500")

    cost = MagicMock()
    cost.amount = Decimal("200")

    q = MagicMock()
    q.filter.return_value.all.return_value = [cost]
    db.query.return_value = q

    delete_existing_costs(db, project, project_id=1)
    db.delete.assert_called_once_with(cost)
    # actual_cost 应该减少
    assert project.actual_cost == Decimal("300")


# ── 4. group_timesheets_by_user: 基本分组 ────────────────────────────────────
def test_group_timesheets_by_user():
    ts1 = MagicMock()
    ts1.user_id = 1
    ts1.user_name = "Alice"
    ts1.hours = 4
    ts1.id = 100
    ts1.work_date = date(2026, 1, 10)

    ts2 = MagicMock()
    ts2.user_id = 1
    ts2.user_name = "Alice"
    ts2.hours = 3
    ts2.id = 101
    ts2.work_date = date(2026, 1, 11)

    ts3 = MagicMock()
    ts3.user_id = 2
    ts3.user_name = "Bob"
    ts3.hours = 8
    ts3.id = 200
    ts3.work_date = date(2026, 1, 10)

    result = group_timesheets_by_user([ts1, ts2, ts3])
    assert len(result) == 2
    assert result[1]["total_hours"] == Decimal("7")
    assert result[2]["total_hours"] == Decimal("8")


# ── 5. find_existing_cost: 查找现有记录 ──────────────────────────────────────
def test_find_existing_cost():
    db = make_db()
    cost = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = cost

    result = find_existing_cost(db, project_id=1, user_id=5)
    assert result == cost


# ── 6. update_existing_cost ──────────────────────────────────────────────────
def test_update_existing_cost():
    db = make_db()
    project = MagicMock()
    project.actual_cost = Decimal("1000")

    existing_cost = MagicMock()
    existing_cost.amount = Decimal("200")

    user_data = {"user_name": "张三", "total_hours": Decimal("10")}
    update_existing_cost(db, project, existing_cost, Decimal("300"), user_data, date(2026, 1, 31))

    assert existing_cost.amount == Decimal("300")
    # actual_cost = 1000 - 200 + 300 = 1100
    assert project.actual_cost == Decimal("1100")
    db.add.assert_called_once_with(existing_cost)


# ── 7. create_new_cost ────────────────────────────────────────────────────────
def test_create_new_cost():
    db = make_db()
    project = MagicMock()
    project.actual_cost = 500

    user_data = {"user_name": "李四", "total_hours": Decimal("5")}
    cost = create_new_cost(db, project, 10, 3, Decimal("250"), user_data, date(2026, 1, 31))

    db.add.assert_called_once()
    assert project.actual_cost == 750  # 500 + 250


# ── 8. check_budget_alert: 异常时不抛出 ──────────────────────────────────────
def test_check_budget_alert_exception_silenced():
    db = make_db()
    # CostAlertService is imported inside the function; patch its module
    with patch("app.services.cost_alert_service.CostAlertService") as MockCAS:
        MockCAS.check_budget_execution.side_effect = Exception("budget check error")
        # Should not raise even if inner call fails
        check_budget_alert(db, project_id=1, user_id=1)
