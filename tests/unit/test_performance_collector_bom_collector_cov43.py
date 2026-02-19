# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_collector/bom_collector.py
"""
import pytest

pytest.importorskip("app.services.performance_collector.bom_collector")

from datetime import date
from unittest.mock import MagicMock

from app.services.performance_collector.bom_collector import BomCollector


def make_collector():
    db = MagicMock()
    return BomCollector(db)


# ── 1. 工程师没有参与项目时返回零值 ─────────────────────────────────────────
def test_collect_bom_data_no_projects():
    c = make_collector()
    c.db.query.return_value.filter.return_value.all.return_value = []

    result = c.collect_bom_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_bom"] == 0
    assert result["bom_timeliness_rate"] == 0.0
    assert result["standard_part_rate"] == 0.0


# ── 2. 有项目但无 BOM 时返回零值 ─────────────────────────────────────────────
def test_collect_bom_data_no_boms():
    c = make_collector()
    pm = MagicMock()
    pm.project_id = 1

    q_pm = MagicMock()
    q_pm.filter.return_value.all.return_value = [pm]

    q_bom = MagicMock()
    q_bom.filter.return_value.all.return_value = []

    c.db.query.side_effect = [q_pm, q_bom]

    result = c.collect_bom_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_bom"] == 0
    assert result["on_time_bom"] == 0


# ── 3. 有按时提交的 BOM ───────────────────────────────────────────────────────
def test_collect_bom_data_on_time():
    c = make_collector()
    pm = MagicMock()
    pm.project_id = 10

    due_date = date(2026, 1, 20)
    submitted_at = date(2026, 1, 15)

    bom = MagicMock()
    bom.due_date = due_date
    bom.submitted_at = submitted_at

    q_pm = MagicMock()
    q_pm.filter.return_value.all.return_value = [pm]

    q_bom = MagicMock()
    q_bom.filter.return_value.all.return_value = [bom]

    q_item = MagicMock()
    q_item.join.return_value.filter.return_value.all.return_value = []

    c.db.query.side_effect = [q_pm, q_bom, q_item]

    result = c.collect_bom_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_bom"] == 1
    assert result["on_time_bom"] == 1
    assert result["bom_timeliness_rate"] == 100.0


# ── 4. BOM 超时提交 ───────────────────────────────────────────────────────────
def test_collect_bom_data_late():
    c = make_collector()
    pm = MagicMock()
    pm.project_id = 11

    bom = MagicMock()
    bom.due_date = date(2026, 1, 10)
    bom.submitted_at = date(2026, 1, 20)

    q_pm = MagicMock()
    q_pm.filter.return_value.all.return_value = [pm]

    q_bom = MagicMock()
    q_bom.filter.return_value.all.return_value = [bom]

    q_item = MagicMock()
    q_item.join.return_value.filter.return_value.all.return_value = []

    c.db.query.side_effect = [q_pm, q_bom, q_item]

    result = c.collect_bom_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_bom"] == 1
    assert result["on_time_bom"] == 0
    assert result["bom_timeliness_rate"] == 0.0


# ── 5. 标准件使用率计算 ───────────────────────────────────────────────────────
def test_collect_bom_data_standard_part_rate():
    c = make_collector()
    pm = MagicMock()
    pm.project_id = 12

    bom = MagicMock()
    bom.due_date = None
    bom.submitted_at = None

    item_std = MagicMock()
    item_std.is_standard = True
    item_non = MagicMock()
    item_non.is_standard = False

    q_pm = MagicMock()
    q_pm.filter.return_value.all.return_value = [pm]

    q_bom = MagicMock()
    q_bom.filter.return_value.all.return_value = [bom]

    q_item = MagicMock()
    q_item.join.return_value.filter.return_value.all.return_value = [item_std, item_non]

    c.db.query.side_effect = [q_pm, q_bom, q_item]

    result = c.collect_bom_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["standard_part_rate"] == 50.0


# ── 6. 数据库异常时返回默认值 ─────────────────────────────────────────────────
def test_collect_bom_data_exception():
    c = make_collector()
    c.db.query.side_effect = Exception("DB error")

    result = c.collect_bom_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert "error" in result
    assert result["total_bom"] == 0
