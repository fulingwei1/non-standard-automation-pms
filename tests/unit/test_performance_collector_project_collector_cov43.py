# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_collector/project_collector.py
"""
import pytest

pytest.importorskip("app.services.performance_collector.project_collector")

from datetime import date
from unittest.mock import MagicMock

from app.services.performance_collector.project_collector import ProjectCollector


def make_collector():
    db = MagicMock()
    return ProjectCollector(db)


# ── 1. 无任务时返回零值 ───────────────────────────────────────────────────────
def test_collect_task_completion_no_tasks():
    c = make_collector()
    c.db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    result = c.collect_task_completion_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_tasks"] == 0
    assert result["completion_rate"] == 0.0


# ── 2. 有任务时计算完成率 ────────────────────────────────────────────────────
def test_collect_task_completion_with_tasks():
    c = make_collector()

    t_done = MagicMock()
    t_done.status = "COMPLETED"
    t_done.actual_end_date = date(2026, 1, 15)
    t_done.due_date = date(2026, 1, 20)

    t_late = MagicMock()
    t_late.status = "COMPLETED"
    t_late.actual_end_date = date(2026, 1, 25)
    t_late.due_date = date(2026, 1, 20)

    t_open = MagicMock()
    t_open.status = "IN_PROGRESS"
    t_open.actual_end_date = None
    t_open.due_date = None

    c.db.query.return_value.join.return_value.filter.return_value.all.return_value = [
        t_done, t_late, t_open
    ]

    result = c.collect_task_completion_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_tasks"] == 3
    assert result["completed_tasks"] == 2
    assert result["on_time_tasks"] == 1
    assert result["completion_rate"] == round(2 / 3 * 100, 2)
    assert result["on_time_rate"] == 50.0


# ── 3. 任务查询异常时返回默认值 ─────────────────────────────────────────────
def test_collect_task_completion_exception():
    c = make_collector()
    c.db.query.side_effect = Exception("query error")

    result = c.collect_task_completion_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert "error" in result
    assert result["total_tasks"] == 0


# ── 4. 无参与项目时返回零值 ─────────────────────────────────────────────────
def test_collect_project_participation_no_projects():
    c = make_collector()
    c.db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    result = c.collect_project_participation_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_projects"] == 0
    assert result["project_ids"] == []


# ── 5. 有参与项目时统计正确 ─────────────────────────────────────────────────
def test_collect_project_participation_with_projects():
    c = make_collector()

    p1 = MagicMock()
    p1.id = 100
    p2 = MagicMock()
    p2.id = 200

    eval1 = MagicMock()
    eval1.status = "CONFIRMED"
    eval1.difficulty_score = 4.0
    eval1.workload_score = 3.5

    q_project = MagicMock()
    q_project.join.return_value.filter.return_value.all.return_value = [p1, p2]

    q_eval1 = MagicMock()
    q_eval1.filter.return_value.first.return_value = eval1

    q_eval2 = MagicMock()
    q_eval2.filter.return_value.first.return_value = None

    c.db.query.side_effect = [q_project, q_eval1, q_eval2]

    result = c.collect_project_participation_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_projects"] == 2
    assert 100 in result["project_ids"]
    assert result["evaluated_projects"] == 1


# ── 6. 项目评估查询异常时静默处理 ──────────────────────────────────────────
def test_collect_project_participation_eval_exception():
    c = make_collector()

    p1 = MagicMock()
    p1.id = 100

    q_project = MagicMock()
    q_project.join.return_value.filter.return_value.all.return_value = [p1]

    q_eval = MagicMock()
    q_eval.filter.return_value.first.side_effect = Exception("eval error")

    c.db.query.side_effect = [q_project, q_eval]

    result = c.collect_project_participation_data(1, date(2026, 1, 1), date(2026, 1, 31))
    assert result["total_projects"] == 1
    assert result["evaluated_projects"] == 0
