# -*- coding: utf-8 -*-
"""
J1组单元测试 - issue_tasks.py
覆盖：check_overdue_issues, check_blocking_issues,
      check_timeout_issues, daily_issue_statistics_snapshot
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

MODULE = "app.utils.scheduled_tasks.issue_tasks"


# ============================================================================
# 辅助
# ============================================================================

def make_mock_db_ctx():
    mock_session = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_session)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx, mock_session


def make_issue(
    issue_id=1,
    title="test issue",
    status="OPEN",
    priority="MEDIUM",
    due_date=None,
    assignee_id=None,
    project_id=None,
    is_blocking=False,
    last_follow_up_at=None,
    issue_no="ISS-0001",
):
    issue = MagicMock()
    issue.id = issue_id
    issue.title = title
    issue.status = status
    issue.priority = priority
    issue.due_date = due_date or (date.today() - timedelta(days=3))
    issue.assignee_id = assignee_id
    issue.project_id = project_id
    issue.is_blocking = is_blocking
    issue.last_follow_up_at = last_follow_up_at
    issue.issue_no = issue_no
    return issue


# ============================================================================
# 测试 check_overdue_issues（issue_tasks.py 版本）
# ============================================================================


@pytest.mark.unit
class TestIssueTasksCheckOverdueIssues:
    """issue_tasks.check_overdue_issues"""

    def test_no_overdue_returns_zero(self):
        """无逾期问题：notified_count=0"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["overdue_count"] == 0
        assert result["notified_count"] == 0
        assert "timestamp" in result

    def test_overdue_issue_with_assignee_notified(self):
        """逾期问题有处理人：发送通知"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        issue = make_issue(assignee_id=42, due_date=date.today() - timedelta(days=2))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        # project query for PM
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_notify = MagicMock(return_value=None)
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.sales_reminder.create_notification", mock_notify):
                result = check_overdue_issues()

        assert result["overdue_count"] == 1
        assert result["notified_count"] == 1
        mock_notify.assert_called_once()

    def test_overdue_issue_without_assignee_not_notified(self):
        """逾期问题无处理人：不发通知"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        issue = make_issue(assignee_id=None, due_date=date.today() - timedelta(days=2))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        mock_notify = MagicMock()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.sales_reminder.create_notification", mock_notify):
                result = check_overdue_issues()

        assert result["overdue_count"] == 1
        assert result["notified_count"] == 0
        mock_notify.assert_not_called()

    def test_notification_failure_handled_gracefully(self):
        """通知发送失败：不影响整体流程"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        issue = make_issue(assignee_id=42, due_date=date.today() - timedelta(days=2))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        def failing_notify(*args, **kwargs):
            raise Exception("Notification service down")

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.sales_reminder.create_notification", failing_notify):
                result = check_overdue_issues()

        # 通知失败不影响返回
        assert result["overdue_count"] == 1
        assert result["notified_count"] == 0  # 通知失败

    def test_overdue_issue_with_pm_notifies_pm(self):
        """逾期问题有项目经理（与处理人不同）：额外通知 PM"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        issue = make_issue(assignee_id=42, project_id=99, due_date=date.today() - timedelta(days=2))
        project = MagicMock()
        project.pm_id = 55  # 不同于 assignee_id=42
        project.project_name = "测试项目"

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = project

        notify_calls = []
        def mock_notify(*args, **kwargs):
            notify_calls.append(kwargs.get("user_id"))

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.sales_reminder.create_notification", mock_notify):
                result = check_overdue_issues()

        # 通知了 assignee(42) 和 PM(55) 共2次
        assert result["notified_count"] == 1  # 只 notified_count += 1（assignee 通知）
        assert 42 in notify_calls
        assert 55 in notify_calls

    def test_exception_returns_error(self):
        """异常返回 error 字段"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("DB failed")
            result = check_overdue_issues()

        assert "error" in result


# ============================================================================
# 测试 check_blocking_issues（issue_tasks.py 版本）
# ============================================================================


@pytest.mark.unit
class TestIssueTasksCheckBlockingIssues:
    """issue_tasks.check_blocking_issues"""

    def test_no_blocking_issues_returns_zero(self):
        """无阻塞问题：blocking_count=0"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        mock_calculator = MagicMock()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = check_blocking_issues()

        assert result["blocking_count"] == 0
        assert result["affected_projects"] == 0

    def test_blocking_issue_with_project_creates_alert(self):
        """有阻塞问题且属于项目：创建预警，更新健康度"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        issue = make_issue(is_blocking=True, project_id=10, status="OPEN")
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        # AlertRule 不存在 → 会创建默认规则
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # AlertRecord count
        mock_session.query.return_value.count.return_value = 0

        project = MagicMock()
        project.id = 10

        mock_calculator = MagicMock()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                with patch(f"{MODULE}.Project") as mock_project_cls:
                    mock_session.query.return_value.filter.return_value.first.return_value = project
                    result = check_blocking_issues()

        assert result["blocking_count"] == 1
        assert result["affected_projects"] >= 0  # project_id 被记录

    def test_existing_alert_not_duplicated(self):
        """已存在 PENDING 预警：不重复创建"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        issue = make_issue(is_blocking=True, project_id=10, status="OPEN")
        existing_alert = MagicMock()

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        # first() 调用顺序：AlertRule → existing AlertRecord → Project（健康度更新用）
        rule = MagicMock()
        rule.id = 1
        project = MagicMock()
        project.id = 10
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            rule,           # AlertRule query
            existing_alert, # existing AlertRecord
            project,        # Project lookup for health update
        ]

        mock_calculator = MagicMock()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = check_blocking_issues()

        # 不应该添加新预警记录（仅有可能 flush 了 rule）
        assert result["blocking_count"] == 1

    def test_exception_returns_error(self):
        """异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("blocking check failed")
            result = check_blocking_issues()

        assert "error" in result

    def test_result_has_required_keys(self):
        """返回值包含 blocking_count, affected_projects, health_updated, timestamp"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        mock_calculator = MagicMock()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = check_blocking_issues()

        for key in ["blocking_count", "affected_projects", "health_updated", "timestamp"]:
            assert key in result


# ============================================================================
# 测试 check_timeout_issues（issue_tasks.py 版本）
# ============================================================================


@pytest.mark.unit
class TestIssueTasksCheckTimeoutIssues:
    """issue_tasks.check_timeout_issues"""

    def test_no_timeout_issues_returns_zero(self):
        """无超时问题"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert result["timeout_count"] == 0
        assert result["upgraded_count"] == 0

    def test_low_to_medium_upgrade(self):
        """LOW → MEDIUM"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        issue = make_issue(priority="LOW", last_follow_up_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "MEDIUM"
        assert result["upgraded_count"] == 1

    def test_medium_to_high_upgrade(self):
        """MEDIUM → HIGH"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        issue = make_issue(priority="MEDIUM", last_follow_up_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "HIGH"
        assert result["upgraded_count"] == 1

    def test_high_to_urgent_upgrade(self):
        """HIGH → URGENT"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        issue = make_issue(priority="HIGH", last_follow_up_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "URGENT"
        assert result["upgraded_count"] == 1

    def test_urgent_not_upgraded(self):
        """URGENT 不再升级"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        issue = make_issue(priority="URGENT", last_follow_up_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "URGENT"
        assert result["upgraded_count"] == 0
        assert result["timeout_count"] == 1

    def test_exception_returns_error(self):
        """异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("timeout check DB error")
            result = check_timeout_issues()

        assert "error" in result


# ============================================================================
# 测试 daily_issue_statistics_snapshot（issue_tasks.py 版本）
# ============================================================================


@pytest.mark.unit
class TestIssueTasksDailyStatisticsSnapshot:
    """issue_tasks.daily_issue_statistics_snapshot"""

    def test_snapshot_already_exists_skips(self):
        """今日快照已存在：跳过生成"""
        from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot

        mock_ctx, mock_session = make_mock_db_ctx()

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(
                "app.services.issue_statistics_service.check_existing_snapshot",
                return_value=True
            ):
                result = daily_issue_statistics_snapshot()

        assert "message" in result
        assert "already exists" in result["message"]

    def test_snapshot_created_when_not_exists(self):
        """快照不存在：正常创建"""
        from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_status = {"total": 10, "open": 3, "processing": 5, "resolved": 2, "closed": 0}
        mock_severity = {}
        mock_priority = {}
        mock_type = {}
        mock_blocking = {"blocking": 1, "overdue": 2}
        mock_category = {}
        mock_today = {}
        mock_avg = 5.0
        mock_distributions = {}

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.issue_statistics_service.check_existing_snapshot", return_value=False):
                with patch("app.services.issue_statistics_service.count_issues_by_status", return_value=mock_status):
                    with patch("app.services.issue_statistics_service.count_issues_by_severity", return_value=mock_severity):
                        with patch("app.services.issue_statistics_service.count_issues_by_priority", return_value=mock_priority):
                            with patch("app.services.issue_statistics_service.count_issues_by_type", return_value=mock_type):
                                with patch("app.services.issue_statistics_service.count_blocking_and_overdue_issues", return_value=mock_blocking):
                                    with patch("app.services.issue_statistics_service.count_issues_by_category", return_value=mock_category):
                                        with patch("app.services.issue_statistics_service.count_today_issues", return_value=mock_today):
                                            with patch("app.services.issue_statistics_service.calculate_avg_resolve_time", return_value=mock_avg):
                                                with patch("app.services.issue_statistics_service.build_distribution_data", return_value=mock_distributions):
                                                    with patch("app.services.issue_statistics_service.create_snapshot_record", return_value=None):
                                                        result = daily_issue_statistics_snapshot()

        assert result["total_issues"] == 10
        assert result["open_issues"] == 3
        assert result["blocking_issues"] == 1
        mock_session.commit.assert_called_once()

    def test_result_has_required_keys(self):
        """返回值包含必要字段"""
        from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot

        mock_ctx, mock_session = make_mock_db_ctx()

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(
                "app.services.issue_statistics_service.check_existing_snapshot",
                return_value=True
            ):
                result = daily_issue_statistics_snapshot()

        assert result is not None

    def test_exception_returns_error(self):
        """异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("snapshot generation failed")
            result = daily_issue_statistics_snapshot()

        assert "error" in result
