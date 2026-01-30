# -*- coding: utf-8 -*-
"""
issue_statistics_service 综合单元测试

测试覆盖:
- check_existing_snapshot: 检查快照是否存在
- count_issues_by_status: 按状态统计问题数量
- count_issues_by_severity: 按严重程度统计问题数量
- count_issues_by_priority: 按优先级统计问题数量
- count_issues_by_type: 按类型统计问题数量
- count_blocking_and_overdue_issues: 统计阻塞和逾期问题
- count_issues_by_category: 按分类统计问题数量
- count_today_issues: 统计今日问题
- calculate_avg_resolve_time: 计算平均解决时间
- build_distribution_data: 构建分布数据
- create_snapshot_record: 创建快照记录
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestCheckExistingSnapshot:
    """测试 check_existing_snapshot 函数"""

    def test_returns_true_when_snapshot_exists(self):
        """测试快照存在时返回True"""
        from app.services.issue_statistics_service import check_existing_snapshot

        mock_db = MagicMock()
        mock_snapshot = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_snapshot

        result = check_existing_snapshot(mock_db, date.today())

        assert result is True

    def test_returns_false_when_snapshot_not_exists(self):
        """测试快照不存在时返回False"""
        from app.services.issue_statistics_service import check_existing_snapshot

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = check_existing_snapshot(mock_db, date.today())

        assert result is False


class TestCountIssuesByStatus:
    """测试 count_issues_by_status 函数"""

    def test_returns_status_counts(self):
        """测试返回状态统计"""
        from app.services.issue_statistics_service import count_issues_by_status

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            100,  # total
            30,   # open
            20,   # processing
            25,   # resolved
            15,   # closed
            5,    # cancelled
            5,    # deferred
        ]

        result = count_issues_by_status(mock_db)

        assert result["total"] == 100
        assert result["open"] == 30
        assert result["processing"] == 20
        assert result["resolved"] == 25
        assert result["closed"] == 15
        assert result["cancelled"] == 5
        assert result["deferred"] == 5

    def test_returns_zero_when_no_issues(self):
        """测试无问题时返回零"""
        from app.services.issue_statistics_service import count_issues_by_status

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_issues_by_status(mock_db)

        assert result["total"] == 0
        assert result["open"] == 0


class TestCountIssuesBySeverity:
    """测试 count_issues_by_severity 函数"""

    def test_returns_severity_counts(self):
        """测试返回严重程度统计"""
        from app.services.issue_statistics_service import count_issues_by_severity

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [10, 20, 30]

        result = count_issues_by_severity(mock_db)

        assert result["critical"] == 10
        assert result["major"] == 20
        assert result["minor"] == 30

    def test_returns_zero_for_no_issues(self):
        """测试无问题时返回零"""
        from app.services.issue_statistics_service import count_issues_by_severity

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_issues_by_severity(mock_db)

        assert result["critical"] == 0
        assert result["major"] == 0
        assert result["minor"] == 0


class TestCountIssuesByPriority:
    """测试 count_issues_by_priority 函数"""

    def test_returns_priority_counts(self):
        """测试返回优先级统计"""
        from app.services.issue_statistics_service import count_issues_by_priority

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 15, 25, 35]

        result = count_issues_by_priority(mock_db)

        assert result["urgent"] == 5
        assert result["high"] == 15
        assert result["medium"] == 25
        assert result["low"] == 35

    def test_returns_zero_for_no_issues(self):
        """测试无问题时返回零"""
        from app.services.issue_statistics_service import count_issues_by_priority

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_issues_by_priority(mock_db)

        assert result["urgent"] == 0
        assert result["high"] == 0


class TestCountIssuesByType:
    """测试 count_issues_by_type 函数"""

    def test_returns_type_counts(self):
        """测试返回类型统计"""
        from app.services.issue_statistics_service import count_issues_by_type

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [40, 30, 20]

        result = count_issues_by_type(mock_db)

        assert result["defect"] == 40
        assert result["risk"] == 30
        assert result["blocker"] == 20

    def test_returns_zero_for_no_issues(self):
        """测试无问题时返回零"""
        from app.services.issue_statistics_service import count_issues_by_type

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_issues_by_type(mock_db)

        assert result["defect"] == 0
        assert result["risk"] == 0
        assert result["blocker"] == 0


class TestCountBlockingAndOverdueIssues:
    """测试 count_blocking_and_overdue_issues 函数"""

    def test_returns_blocking_and_overdue_counts(self):
        """测试返回阻塞和逾期统计"""
        from app.services.issue_statistics_service import count_blocking_and_overdue_issues

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 10]

        result = count_blocking_and_overdue_issues(mock_db, date.today())

        assert result["blocking"] == 5
        assert result["overdue"] == 10

    def test_returns_zero_when_no_blocking_or_overdue(self):
        """测试无阻塞或逾期时返回零"""
        from app.services.issue_statistics_service import count_blocking_and_overdue_issues

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_blocking_and_overdue_issues(mock_db, date.today())

        assert result["blocking"] == 0
        assert result["overdue"] == 0


class TestCountIssuesByCategory:
    """测试 count_issues_by_category 函数"""

    def test_returns_category_counts(self):
        """测试返回分类统计"""
        from app.services.issue_statistics_service import count_issues_by_category

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [50, 30, 20]

        result = count_issues_by_category(mock_db)

        assert result["project"] == 50
        assert result["task"] == 30
        assert result["acceptance"] == 20

    def test_returns_zero_for_no_issues(self):
        """测试无问题时返回零"""
        from app.services.issue_statistics_service import count_issues_by_category

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_issues_by_category(mock_db)

        assert result["project"] == 0
        assert result["task"] == 0
        assert result["acceptance"] == 0


class TestCountTodayIssues:
    """测试 count_today_issues 函数"""

    def test_returns_today_counts(self):
        """测试返回今日统计"""
        from app.services.issue_statistics_service import count_today_issues

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 3, 2]

        result = count_today_issues(mock_db, date.today())

        assert result["new"] == 5
        assert result["resolved"] == 3
        assert result["closed"] == 2

    def test_returns_zero_for_no_today_issues(self):
        """测试今日无问题时返回零"""
        from app.services.issue_statistics_service import count_today_issues

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = count_today_issues(mock_db, date.today())

        assert result["new"] == 0
        assert result["resolved"] == 0
        assert result["closed"] == 0


class TestCalculateAvgResolveTime:
    """测试 calculate_avg_resolve_time 函数"""

    def test_returns_average_resolve_time(self):
        """测试返回平均解决时间"""
        from app.services.issue_statistics_service import calculate_avg_resolve_time

        mock_db = MagicMock()

        # 创建模拟问题
        mock_issue1 = MagicMock()
        mock_issue1.resolved_at = datetime(2026, 1, 15, 12, 0)
        mock_issue1.report_date = datetime(2026, 1, 15, 8, 0)  # 4小时

        mock_issue2 = MagicMock()
        mock_issue2.resolved_at = datetime(2026, 1, 16, 16, 0)
        mock_issue2.report_date = datetime(2026, 1, 16, 8, 0)  # 8小时

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_issue1, mock_issue2]

        result = calculate_avg_resolve_time(mock_db)

        # 平均: (4 + 8) / 2 = 6小时
        assert result == 6.0

    def test_returns_zero_when_no_resolved_issues(self):
        """测试无已解决问题时返回零"""
        from app.services.issue_statistics_service import calculate_avg_resolve_time

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = calculate_avg_resolve_time(mock_db)

        assert result == 0.0

    def test_handles_issues_without_dates(self):
        """测试处理没有日期的问题"""
        from app.services.issue_statistics_service import calculate_avg_resolve_time

        mock_db = MagicMock()

        mock_issue = MagicMock()
        mock_issue.resolved_at = None
        mock_issue.report_date = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_issue]

        result = calculate_avg_resolve_time(mock_db)

        assert result == 0.0


class TestBuildDistributionData:
    """测试 build_distribution_data 函数"""

    def test_builds_distribution_correctly(self):
        """测试正确构建分布数据"""
        from app.services.issue_statistics_service import build_distribution_data

        status_counts = {
            "open": 30, "processing": 20, "resolved": 25,
            "closed": 15, "cancelled": 5, "deferred": 5
        }
        severity_counts = {"critical": 10, "major": 20, "minor": 30}
        priority_counts = {"urgent": 5, "high": 15, "medium": 25, "low": 35}
        category_counts = {"project": 50, "task": 30, "acceptance": 20}

        result = build_distribution_data(
            status_counts, severity_counts, priority_counts, category_counts
        )

        assert result["status"]["OPEN"] == 30
        assert result["severity"]["CRITICAL"] == 10
        assert result["priority"]["URGENT"] == 5
        assert result["category"]["PROJECT"] == 50

    def test_preserves_all_status_values(self):
        """测试保留所有状态值"""
        from app.services.issue_statistics_service import build_distribution_data

        status_counts = {
            "open": 1, "processing": 2, "resolved": 3,
            "closed": 4, "cancelled": 5, "deferred": 6
        }
        severity_counts = {"critical": 0, "major": 0, "minor": 0}
        priority_counts = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        category_counts = {"project": 0, "task": 0, "acceptance": 0}

        result = build_distribution_data(
            status_counts, severity_counts, priority_counts, category_counts
        )

        assert result["status"]["OPEN"] == 1
        assert result["status"]["PROCESSING"] == 2
        assert result["status"]["RESOLVED"] == 3
        assert result["status"]["CLOSED"] == 4
        assert result["status"]["CANCELLED"] == 5
        assert result["status"]["DEFERRED"] == 6


class TestCreateSnapshotRecord:
    """测试 create_snapshot_record 函数"""

    def test_creates_snapshot_record(self):
        """测试创建快照记录"""
        from app.services.issue_statistics_service import create_snapshot_record

        mock_db = MagicMock()

        status_counts = {
            "total": 100, "open": 30, "processing": 20, "resolved": 25,
            "closed": 15, "cancelled": 5, "deferred": 5
        }
        severity_counts = {"critical": 10, "major": 20, "minor": 30}
        priority_counts = {"urgent": 5, "high": 15, "medium": 25, "low": 35}
        type_counts = {"defect": 40, "risk": 30, "blocker": 20}
        blocking_overdue = {"blocking": 5, "overdue": 10}
        category_counts = {"project": 50, "task": 30, "acceptance": 20}
        today_counts = {"new": 5, "resolved": 3, "closed": 2}
        avg_resolve_time = 6.5
        distributions = {
            "status": {"OPEN": 30, "PROCESSING": 20, "RESOLVED": 25, "CLOSED": 15, "CANCELLED": 5, "DEFERRED": 5},
            "severity": {"CRITICAL": 10, "MAJOR": 20, "MINOR": 30},
            "priority": {"URGENT": 5, "HIGH": 15, "MEDIUM": 25, "LOW": 35},
            "category": {"PROJECT": 50, "TASK": 30, "ACCEPTANCE": 20}
        }

        result = create_snapshot_record(
            mock_db,
            date.today(),
            status_counts,
            severity_counts,
            priority_counts,
            type_counts,
            blocking_overdue,
            category_counts,
            today_counts,
            avg_resolve_time,
            distributions
        )

        # 验证db.add被调用
        mock_db.add.assert_called_once()
        # 验证返回值是快照对象
        assert result is not None

    def test_sets_correct_values(self):
        """测试设置正确的值"""
        from app.services.issue_statistics_service import create_snapshot_record

        mock_db = MagicMock()

        snapshot_date = date(2026, 1, 30)
        status_counts = {
            "total": 100, "open": 30, "processing": 20, "resolved": 25,
            "closed": 15, "cancelled": 5, "deferred": 5
        }
        severity_counts = {"critical": 10, "major": 20, "minor": 30}
        priority_counts = {"urgent": 5, "high": 15, "medium": 25, "low": 35}
        type_counts = {"defect": 40, "risk": 30, "blocker": 20}
        blocking_overdue = {"blocking": 5, "overdue": 10}
        category_counts = {"project": 50, "task": 30, "acceptance": 20}
        today_counts = {"new": 5, "resolved": 3, "closed": 2}
        avg_resolve_time = 6.5
        distributions = {
            "status": {"OPEN": 30},
            "severity": {"CRITICAL": 10},
            "priority": {"URGENT": 5},
            "category": {"PROJECT": 50}
        }

        result = create_snapshot_record(
            mock_db,
            snapshot_date,
            status_counts,
            severity_counts,
            priority_counts,
            type_counts,
            blocking_overdue,
            category_counts,
            today_counts,
            avg_resolve_time,
            distributions
        )

        assert result.snapshot_date == snapshot_date
        assert result.total_issues == 100
        assert result.open_issues == 30
        assert result.critical_issues == 10
        assert result.urgent_issues == 5
        assert result.defect_issues == 40
        assert result.blocking_issues == 5
        assert result.overdue_issues == 10
        assert result.avg_resolve_time == 6.5
        assert result.new_issues_today == 5
