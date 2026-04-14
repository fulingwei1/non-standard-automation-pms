from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.utils.scheduled_tasks import issue_tasks

MODULE = "app.utils.scheduled_tasks.issue_tasks"


def make_db_ctx(mock_session):
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_session)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


@pytest.mark.unit
def test_check_overdue_issues_logs_pm_notification_failure_without_breaking_flow():
    issue = SimpleNamespace(
        id=1,
        title="逾期问题",
        issue_no="ISS-1",
        due_date=date.today() - timedelta(days=1),
        assignee_id=42,
        project_id=99,
    )
    project = SimpleNamespace(pm_id=77, project_name="测试项目")

    issue_query = MagicMock()
    issue_query.filter.return_value.all.return_value = [issue]
    project_query = MagicMock()
    project_query.filter.return_value.first.return_value = project

    db = MagicMock()
    db.query.side_effect = [issue_query, project_query]

    def notify(**kwargs):
        if kwargs["user_id"] == 77:
            raise RuntimeError("pm send failed")

    with patch(f"{MODULE}.get_db_session", return_value=make_db_ctx(db)):
        with patch("app.services.sales_reminder.create_notification", side_effect=notify):
            with patch.object(issue_tasks.logger, "error") as log_error:
                result = issue_tasks.check_overdue_issues()

    assert result["overdue_count"] == 1
    assert result["notified_count"] == 1
    log_error.assert_called_once()
    assert "发送逾期提醒给PM失败" in log_error.call_args.args[0]


@pytest.mark.unit
def test_check_blocking_issues_creates_default_rule_and_alert_when_missing():
    issue = SimpleNamespace(
        id=5,
        title="阻塞问题",
        issue_no="ISS-5",
        project_id=123,
    )
    project = SimpleNamespace(id=123)

    blocking_query = MagicMock()
    blocking_query.filter.return_value.all.return_value = [issue]
    rule_query = MagicMock()
    rule_query.filter.return_value.first.return_value = None
    existing_alert_query = MagicMock()
    existing_alert_query.filter.return_value.first.return_value = None
    count_query = MagicMock()
    count_query.count.return_value = 0
    project_query = MagicMock()
    project_query.filter.return_value.first.return_value = project

    db = MagicMock()
    db.query.side_effect = [blocking_query, rule_query, existing_alert_query, count_query, project_query]

    calculator = MagicMock()
    added_objects = []

    def add_side_effect(obj):
        if getattr(obj, "rule_code", None) == "BLOCKING_ISSUE" and getattr(obj, "id", None) is None:
            obj.id = 321
        added_objects.append(obj)

    db.add.side_effect = add_side_effect

    with patch(f"{MODULE}.get_db_session", return_value=make_db_ctx(db)):
        with patch("app.services.health_calculator.HealthCalculator", return_value=calculator):
            with patch(f"{MODULE}.apply_like_filter", return_value=count_query):
                result = issue_tasks.check_blocking_issues()

    assert result["blocking_count"] == 1
    assert result["affected_projects"] == 1
    assert result["health_updated"] == 1
    calculator.calculate_health.assert_called_once_with(project)

    rule = next(obj for obj in added_objects if getattr(obj, "rule_code", None) == "BLOCKING_ISSUE")
    alert = next(obj for obj in added_objects if getattr(obj, "alert_no", None))

    assert rule.rule_name == "阻塞问题预警"
    assert alert.alert_no.endswith("0001")
    assert alert.rule_id == 321
    assert alert.target_id == 5
    assert alert.target_no == "ISS-5"
    assert alert.project_id == 123
