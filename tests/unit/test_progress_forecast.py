from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.api.v1.endpoints import progress as progress_api


def _make_task(**kwargs):
    defaults = {
        "id": 1,
        "task_name": "Task",
        "plan_start": None,
        "plan_end": None,
        "actual_start": None,
        "actual_end": None,
        "status": "TODO",
        "progress_percent": 0,
        "weight": Decimal("1.0"),
        "progress_logs": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_calculate_task_forecast_uses_history_and_plans():
    logs = [
        SimpleNamespace(progress_percent=0, updated_at=datetime(2026, 1, 1, 8, 0, 0)),
        SimpleNamespace(progress_percent=50, updated_at=datetime(2026, 1, 6, 8, 0, 0)),
    ]
    task = _make_task(
        id=11,
        task_name="Assembly",
        plan_start=date(2026, 1, 5),
        plan_end=date(2026, 1, 15),
        actual_start=date(2026, 1, 1),
        progress_percent=50,
        status="IN_PROGRESS",
        progress_logs=logs,
    )

    forecast, used_history = progress_api._calculate_task_forecast(task, today=date(2026, 1, 10))

    assert used_history is True
    assert forecast.task_id == 11
    assert forecast.predicted_finish_date == date(2026, 1, 15)
    assert forecast.status == "OnTrack"
    assert forecast.rate_per_day == 10.0


def test_analyze_dependency_graph_reports_cycles_and_conflicts():
    task1 = _make_task(
        id=1,
        task_name="Design",
        plan_start=date(2026, 1, 1),
        plan_end=date(2026, 1, 10),
        progress_percent=80,
        status="IN_PROGRESS",
    )
    task2 = _make_task(
        id=2,
        task_name="Build",
        actual_start=date(2026, 1, 5),
        plan_start=date(2026, 1, 6),
        plan_end=date(2026, 1, 18),
        status="IN_PROGRESS",
    )
    task3 = _make_task(
        id=3,
        task_name="Test",
        actual_start=date(2026, 1, 8),
        plan_start=date(2026, 1, 9),
        plan_end=date(2026, 1, 20),
        status="IN_PROGRESS",
    )

    deps = [
        SimpleNamespace(task_id=2, depends_on_task_id=1, dependency_type="FS", lag_days=0),
        SimpleNamespace(task_id=1, depends_on_task_id=2, dependency_type="FS", lag_days=0),  # cycle
        SimpleNamespace(task_id=3, depends_on_task_id=1, dependency_type="FS", lag_days=0),
    ]

    cycle_paths, issues = progress_api._analyze_dependency_graph({1: task1, 2: task2, 3: task3}, deps)

    assert cycle_paths, "Should detect at least one cycle"
    assert any(issue.issue_type == "TIMING_CONFLICT" for issue in issues)
    assert any(issue.issue_type == "UNRESOLVED_PREDECESSOR" for issue in issues)
