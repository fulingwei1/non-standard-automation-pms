# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_service/history.py
"""
import pytest

pytest.importorskip("app.services.performance_service.history")

from unittest.mock import MagicMock, patch

from app.services.performance_service.history import get_historical_performance


def make_db():
    return MagicMock()


# ── 1. 无历史记录时返回空列表 ────────────────────────────────────────────────
def test_no_summaries():
    db = make_db()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = get_historical_performance(db, employee_id=1, months=3)
    assert result == []


# ── 2. 有总结记录且有评分时返回历史列表 ──────────────────────────────────────
def test_with_summaries():
    db = make_db()

    summary = MagicMock()
    summary.id = 1
    summary.period = "2025-12"

    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [summary]

    with patch("app.services.performance_service.history.calculate_final_score") as mock_calc:
        mock_calc.return_value = {
            "final_score": 85.0,
            "dept_score": 80.0,
            "project_score": 90.0,
        }
        result = get_historical_performance(db, employee_id=1, months=3)

    assert len(result) == 1
    assert result[0]["period"] == "2025-12"
    assert result[0]["final_score"] == 85.0
    assert result[0]["level"] == "B+"


# ── 3. 评分返回 None 时跳过该条 ──────────────────────────────────────────────
def test_no_score_result_skipped():
    db = make_db()

    summary = MagicMock()
    summary.id = 2
    summary.period = "2025-11"

    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [summary]

    with patch("app.services.performance_service.history.calculate_final_score") as mock_calc:
        mock_calc.return_value = None
        result = get_historical_performance(db, employee_id=1, months=3)

    assert result == []


# ── 4. months 参数控制查询月份数 ─────────────────────────────────────────────
def test_months_param():
    db = make_db()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = get_historical_performance(db, employee_id=2, months=6)
    assert result == []


# ── 5. get_score_level 集成: 90+ 返回 A ──────────────────────────────────────
def test_score_level_a():
    db = make_db()

    summary = MagicMock()
    summary.id = 3
    summary.period = "2025-10"

    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [summary]

    with patch("app.services.performance_service.history.calculate_final_score") as mock_calc:
        mock_calc.return_value = {
            "final_score": 91.0,
            "dept_score": 91.0,
            "project_score": None,
        }
        result = get_historical_performance(db, employee_id=3)

    assert result[0]["level"] == "A"


# ── 6. 多条历史记录时全部返回 ────────────────────────────────────────────────
def test_multiple_summaries():
    db = make_db()

    s1 = MagicMock(); s1.id = 1; s1.period = "2025-12"
    s2 = MagicMock(); s2.id = 2; s2.period = "2025-11"

    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [s1, s2]

    scores = [
        {"final_score": 88.0, "dept_score": 88.0, "project_score": None},
        {"final_score": 72.0, "dept_score": 72.0, "project_score": None},
    ]

    with patch("app.services.performance_service.history.calculate_final_score") as mock_calc:
        mock_calc.side_effect = scores
        result = get_historical_performance(db, employee_id=4, months=2)

    assert len(result) == 2
    assert result[0]["level"] == "B+"
    assert result[1]["level"] == "C"
