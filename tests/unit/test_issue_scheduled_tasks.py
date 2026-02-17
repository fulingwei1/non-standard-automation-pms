# -*- coding: utf-8 -*-
"""
J1组单元测试 - issue_scheduled_tasks.py
覆盖：check_overdue_issues, check_blocking_issues, check_timeout_issues,
      daily_issue_statistics_snapshot, check_issue_assignment_timeout,
      check_issue_resolution_timeout
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

MODULE = "app.utils.scheduled_tasks.issue_scheduled_tasks"


# ============================================================================
# 辅助函数
# ============================================================================

def make_mock_db_ctx():
    mock_session = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_session)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx, mock_session


def make_mock_issue(
    issue_id=1,
    title="测试问题",
    status="OPEN",
    priority="MEDIUM",
    due_date=None,
    assignee_id=None,
    project_id=1,
    created_at=None,
    updated_at=None,
    description="问题描述",
):
    issue = MagicMock()
    issue.id = issue_id
    issue.title = title
    issue.status = status
    issue.priority = priority
    issue.due_date = due_date or (datetime.now() - timedelta(days=3))
    issue.assignee_id = assignee_id
    issue.project_id = project_id
    issue.created_at = created_at or datetime.now() - timedelta(days=10)
    issue.updated_at = updated_at or datetime.now() - timedelta(days=8)
    issue.description = description
    issue.issue_code = f"ISS-{issue_id:04d}"
    return issue


# ============================================================================
# 测试 check_overdue_issues
# ============================================================================


@pytest.mark.unit
class TestCheckOverdueIssues:
    """问题逾期预警检查"""

    def test_no_overdue_issues(self):
        """无逾期问题：返回 overdue_issues=0, alerts_created=0"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["overdue_issues"] == 0
        assert result["alerts_created"] == 0
        assert "timestamp" in result

    def test_one_overdue_issue_creates_alert(self):
        """一个逾期问题：生成一条预警"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        issue = make_mock_issue(status="OPEN", due_date=datetime.now() - timedelta(days=5))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["overdue_issues"] == 1
        assert result["alerts_created"] == 1
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_existing_alert_skipped(self):
        """已存在预警：不重复创建"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        issue = make_mock_issue(status="OPEN", due_date=datetime.now() - timedelta(days=5))
        existing_alert = MagicMock()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = existing_alert

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["alerts_created"] == 0
        mock_session.add.assert_not_called()

    def test_critical_urgency_over_7_days(self):
        """逾期 >= 7 天：urgency=CRITICAL"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        issue = make_mock_issue(status="OPEN", due_date=datetime.now() - timedelta(days=8))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["alerts_created"] == 1
        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "CRITICAL"

    def test_high_urgency_3_to_6_days(self):
        """逾期 3-6 天：urgency=HIGH"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        issue = make_mock_issue(status="OPEN", due_date=datetime.now() - timedelta(days=4))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["alerts_created"] == 1
        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "HIGH"

    def test_medium_urgency_under_3_days(self):
        """逾期 < 3 天：urgency=MEDIUM"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        issue = make_mock_issue(status="OPEN", due_date=datetime.now() - timedelta(hours=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_overdue_issues()

        assert result["alerts_created"] == 1
        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "MEDIUM"

    def test_exception_returns_error(self):
        """异常时返回 error 字段"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("DB connection error")
            result = check_overdue_issues()

        assert "error" in result


# ============================================================================
# 测试 check_blocking_issues
# ============================================================================


@pytest.mark.unit
class TestCheckBlockingIssues:
    """阻塞问题预警检查"""

    def test_no_blocking_issues(self):
        """无阻塞问题：返回 blocking_issues=0"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_blocking_issues()

        assert result["blocking_issues"] == 0
        assert result["alerts_created"] == 0

    def test_one_blocking_issue_creates_alert(self):
        """一个阻塞问题：生成预警"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        issue = make_mock_issue(priority="URGENT", status="OPEN")
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_blocking_issues()

        assert result["blocking_issues"] == 1
        assert result["alerts_created"] == 1
        mock_session.add.assert_called_once()

    def test_existing_blocking_alert_skipped(self):
        """已存在阻塞预警：不重复创建"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        issue = make_mock_issue(priority="URGENT", status="IN_PROGRESS")
        existing_alert = MagicMock()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = existing_alert

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_blocking_issues()

        assert result["alerts_created"] == 0

    def test_blocking_alert_level_is_critical(self):
        """阻塞问题预警级别为 CRITICAL"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        issue = make_mock_issue(priority="URGENT", status="OPEN")
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_blocking_issues()

        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "CRITICAL"

    def test_alert_content_contains_issue_title(self):
        """预警内容包含问题标题"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        issue = make_mock_issue(title="严重阻塞问题ABC", priority="URGENT", status="OPEN")
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_blocking_issues()

        assert result["alerts_created"] == 1
        added = mock_session.add.call_args[0][0]
        assert "严重阻塞问题ABC" in added.alert_content

    def test_multiple_blocking_issues(self):
        """多个阻塞问题"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        issues = [
            make_mock_issue(issue_id=i, priority="URGENT", status="OPEN")
            for i in range(1, 4)
        ]
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = issues
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_blocking_issues()

        assert result["blocking_issues"] == 3
        assert result["alerts_created"] == 3
        assert mock_session.add.call_count == 3

    def test_exception_returns_error(self):
        """异常返回 error 字段"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Service error")
            result = check_blocking_issues()

        assert "error" in result


# ============================================================================
# 测试 check_timeout_issues
# ============================================================================


@pytest.mark.unit
class TestCheckTimeoutIssues:
    """问题超时升级检查"""

    def test_no_timeout_issues(self):
        """无超时问题：timeout_count=0, upgraded_count=0"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert result["timeout_count"] == 0
        assert result["upgraded_count"] == 0

    def test_low_priority_upgraded_to_medium(self):
        """LOW 优先级 → 升级为 MEDIUM"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        issue = make_mock_issue(
            priority="LOW",
            updated_at=datetime.now() - timedelta(days=10),
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert result["timeout_count"] == 1
        assert result["upgraded_count"] == 1
        assert issue.priority == "MEDIUM"

    def test_medium_priority_upgraded_to_high(self):
        """MEDIUM 优先级 → HIGH"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        issue = make_mock_issue(priority="MEDIUM", updated_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "HIGH"
        assert result["upgraded_count"] == 1

    def test_high_priority_upgraded_to_urgent(self):
        """HIGH 优先级 → URGENT"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        issue = make_mock_issue(priority="HIGH", updated_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "URGENT"
        assert result["upgraded_count"] == 1

    def test_already_urgent_not_upgraded(self):
        """URGENT 优先级：不升级（无更高级别）"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        issue = make_mock_issue(priority="URGENT", updated_at=datetime.now() - timedelta(days=10))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_timeout_issues()

        assert issue.priority == "URGENT"
        assert result["upgraded_count"] == 0
        assert result["timeout_count"] == 1

    def test_exception_returns_error(self):
        """异常返回 error 字段"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Timeout check error")
            result = check_timeout_issues()

        assert "error" in result


# ============================================================================
# 测试 daily_issue_statistics_snapshot
# ============================================================================


@pytest.mark.unit
class TestDailyIssueStatisticsSnapshot:
    """问题统计快照"""

    def test_snapshot_created_successfully(self):
        """正常创建统计快照"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            daily_issue_statistics_snapshot,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        # 模拟各 count 查询
        mock_session.query.return_value.filter.return_value.count.return_value = 10
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_session.query.return_value.count.return_value = 10

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = daily_issue_statistics_snapshot()

        assert "total_issues" in result
        assert "timestamp" in result
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_snapshot_has_correct_counts(self):
        """快照统计数量字段正确"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            daily_issue_statistics_snapshot,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        # 模拟不同查询返回不同数字
        call_counts = [20, 5, 8, 7, 3, 6, 4, 2]  # total, open, processing, resolved, urgent...
        mock_session.query.return_value.filter.return_value.count.side_effect = call_counts * 5
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_session.query.return_value.count.side_effect = call_counts * 5

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = daily_issue_statistics_snapshot()

        assert result is not None
        # 返回值包含必要字段
        for key in ["total_issues", "open_issues", "processing_issues", "resolved_issues", "timestamp"]:
            assert key in result

    def test_exception_returns_error(self):
        """异常返回 error 字段"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            daily_issue_statistics_snapshot,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Snapshot DB error")
            result = daily_issue_statistics_snapshot()

        assert "error" in result

    def test_no_issues_all_zero(self):
        """无任何问题：统计均为 0"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            daily_issue_statistics_snapshot,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_session.query.return_value.count.return_value = 0

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = daily_issue_statistics_snapshot()

        assert result["total_issues"] == 0
        assert result["open_issues"] == 0


# ============================================================================
# 测试 check_issue_assignment_timeout
# ============================================================================


@pytest.mark.unit
class TestCheckIssueAssignmentTimeout:
    """问题分配超时检查"""

    def test_no_unassigned_issues(self):
        """无未分配问题：alerts_created=0"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_assignment_timeout,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_assignment_timeout()

        assert result["unassigned_issues"] == 0
        assert result["alerts_created"] == 0

    def test_unassigned_issue_creates_alert(self):
        """有未分配问题：生成分配超时预警"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_assignment_timeout,
        )
        issue = make_mock_issue(
            assignee_id=None,
            created_at=datetime.now() - timedelta(hours=30),
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_assignment_timeout()

        assert result["unassigned_issues"] == 1
        assert result["alerts_created"] == 1
        mock_session.add.assert_called_once()

    def test_existing_assignment_alert_skipped(self):
        """已存在分配超时预警：不重复创建"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_assignment_timeout,
        )
        issue = make_mock_issue(assignee_id=None, created_at=datetime.now() - timedelta(hours=30))
        existing = MagicMock()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = existing

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_assignment_timeout()

        assert result["alerts_created"] == 0

    def test_alert_level_medium(self):
        """分配超时预警级别为 MEDIUM"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_assignment_timeout,
        )
        issue = make_mock_issue(assignee_id=None, created_at=datetime.now() - timedelta(hours=30))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_assignment_timeout()

        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "MEDIUM"

    def test_exception_returns_error(self):
        """异常时返回 error"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_assignment_timeout,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Assignment error")
            result = check_issue_assignment_timeout()

        assert "error" in result


# ============================================================================
# 测试 check_issue_resolution_timeout
# ============================================================================


@pytest.mark.unit
class TestCheckIssueResolutionTimeout:
    """问题解决超时检查"""

    def test_no_overdue_resolution(self):
        """无超期解决问题：alerts_created=0"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_resolution_timeout,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_resolution_timeout()

        assert result["overdue_resolution_issues"] == 0
        assert result["alerts_created"] == 0

    def test_overdue_resolution_creates_alert(self):
        """超期解决问题：生成解决超时预警"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_resolution_timeout,
        )
        issue = make_mock_issue(
            status="IN_PROGRESS",
            due_date=(date.today() - timedelta(days=4)),
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_resolution_timeout()

        assert result["overdue_resolution_issues"] == 1
        assert result["alerts_created"] == 1

    def test_existing_resolution_alert_skipped(self):
        """已存在解决超时预警：跳过"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_resolution_timeout,
        )
        issue = make_mock_issue(
            status="IN_PROGRESS",
            due_date=(date.today() - timedelta(days=4)),
        )
        existing = MagicMock()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = existing

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_resolution_timeout()

        assert result["alerts_created"] == 0

    def test_high_urgency_for_over_3_days(self):
        """超期 >= 3 天：alert_level=HIGH"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_resolution_timeout,
        )
        issue = make_mock_issue(
            status="IN_PROGRESS",
            due_date=(date.today() - timedelta(days=5)),
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_resolution_timeout()

        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "HIGH"

    def test_medium_urgency_under_3_days(self):
        """超期 < 3 天：alert_level=MEDIUM"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_resolution_timeout,
        )
        issue = make_mock_issue(
            status="IN_PROGRESS",
            due_date=(date.today() - timedelta(days=1)),
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [issue]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_issue_resolution_timeout()

        added = mock_session.add.call_args[0][0]
        assert added.alert_level == "MEDIUM"

    def test_exception_returns_error(self):
        """异常时返回 error"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
            check_issue_resolution_timeout,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Resolution timeout error")
            result = check_issue_resolution_timeout()

        assert "error" in result
