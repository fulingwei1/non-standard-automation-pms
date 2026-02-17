# -*- coding: utf-8 -*-
"""
J1组单元测试 - project_health_tasks.py
覆盖：calculate_project_health, daily_health_snapshot
"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

MODULE = "app.utils.scheduled_tasks.project_health_tasks"


# ============================================================================
# 辅助
# ============================================================================

def make_mock_db_ctx():
    mock_session = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_session)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx, mock_session


def make_mock_project(project_id=1, is_active=True, is_archived=False):
    p = MagicMock()
    p.id = project_id
    p.is_active = is_active
    p.is_archived = is_archived
    return p


# ============================================================================
# 测试 calculate_project_health
# ============================================================================


@pytest.mark.unit
class TestCalculateProjectHealth:
    """project_health_tasks.calculate_project_health"""

    def test_returns_batch_calculate_result(self):
        """正常执行：返回 batch_calculate 结果"""
        from app.utils.scheduled_tasks.project_health_tasks import calculate_project_health

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_calculator = MagicMock()
        mock_calculator.batch_calculate.return_value = {
            "total": 8,
            "updated": 5,
            "unchanged": 3,
        }

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = calculate_project_health()

        assert result["total"] == 8
        assert result["updated"] == 5
        assert result["unchanged"] == 3
        mock_calculator.batch_calculate.assert_called_once()

    def test_returns_error_on_exception(self):
        """异常时返回 error 字段"""
        from app.utils.scheduled_tasks.project_health_tasks import calculate_project_health

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Health DB error")
            result = calculate_project_health()

        assert "error" in result
        assert "Health DB error" in result["error"]

    def test_calculator_initialized_with_db_session(self):
        """HealthCalculator 使用 db session 初始化"""
        from app.utils.scheduled_tasks.project_health_tasks import calculate_project_health

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_calculator_cls = MagicMock()
        mock_calculator_inst = MagicMock()
        mock_calculator_inst.batch_calculate.return_value = {"total": 0, "updated": 0, "unchanged": 0}
        mock_calculator_cls.return_value = mock_calculator_inst

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", mock_calculator_cls):
                result = calculate_project_health()

        mock_calculator_cls.assert_called_once_with(mock_session)

    def test_result_structure_on_success(self):
        """正常结果包含 total, updated, unchanged 字段"""
        from app.utils.scheduled_tasks.project_health_tasks import calculate_project_health

        mock_ctx, _ = make_mock_db_ctx()
        mock_calculator = MagicMock()
        mock_calculator.batch_calculate.return_value = {
            "total": 3, "updated": 2, "unchanged": 1
        }

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = calculate_project_health()

        assert "total" in result
        assert "updated" in result
        assert "unchanged" in result

    def test_zero_projects_returns_zero_stats(self):
        """无项目：total=0"""
        from app.utils.scheduled_tasks.project_health_tasks import calculate_project_health

        mock_ctx, _ = make_mock_db_ctx()
        mock_calculator = MagicMock()
        mock_calculator.batch_calculate.return_value = {"total": 0, "updated": 0, "unchanged": 0}

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = calculate_project_health()

        assert result["total"] == 0
        assert result["updated"] == 0

    def test_health_calculator_import_error_returns_error(self):
        """HealthCalculator 导入失败：返回 error"""
        from app.utils.scheduled_tasks.project_health_tasks import calculate_project_health

        mock_ctx, _ = make_mock_db_ctx()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(
                "app.services.health_calculator.HealthCalculator",
                side_effect=ImportError("module not found")
            ):
                result = calculate_project_health()

        assert "error" in result


# ============================================================================
# 测试 daily_health_snapshot
# ============================================================================


@pytest.mark.unit
class TestDailyHealthSnapshot:
    """project_health_tasks.daily_health_snapshot"""

    def test_no_active_projects_returns_zero_snapshots(self):
        """无活跃项目：snapshot_count=0"""
        from app.utils.scheduled_tasks.project_health_tasks import daily_health_snapshot

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_calculator = MagicMock()

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 0
        assert "timestamp" in result

    def test_active_project_creates_snapshot(self):
        """有活跃项目：为每个项目创建快照"""
        from app.utils.scheduled_tasks.project_health_tasks import daily_health_snapshot

        p1 = make_mock_project(project_id=1)
        p2 = make_mock_project(project_id=2)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [p1, p2]

        # 无已存在快照
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_calculator = MagicMock()
        mock_calculator.get_health_details.return_value = {
            "calculated_health": "H1",
            "statistics": {
                "active_alerts": 0,
                "blocking_issues": 0,
                "overdue_milestones": 0,
            },
        }

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 2
        assert mock_session.add.call_count == 2
        mock_session.commit.assert_called_once()

    def test_existing_snapshot_skipped(self):
        """今日快照已存在：不重复创建"""
        from app.utils.scheduled_tasks.project_health_tasks import daily_health_snapshot

        p1 = make_mock_project(project_id=1)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [p1]

        existing_snapshot = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_snapshot

        mock_calculator = MagicMock()
        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 0
        mock_session.add.assert_not_called()

    def test_exception_returns_error(self):
        """异常时返回 error 字段"""
        from app.utils.scheduled_tasks.project_health_tasks import daily_health_snapshot

        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("snapshot failed")
            result = daily_health_snapshot()

        assert "error" in result
        assert "snapshot failed" in result["error"]

    def test_snapshot_uses_health_details(self):
        """快照中包含 get_health_details 的数据"""
        from app.utils.scheduled_tasks.project_health_tasks import daily_health_snapshot

        p1 = make_mock_project(project_id=1)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [p1]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_calculator = MagicMock()
        mock_calculator.get_health_details.return_value = {
            "calculated_health": "H3",
            "statistics": {
                "active_alerts": 5,
                "blocking_issues": 2,
                "overdue_milestones": 1,
            },
        }

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 1
        snapshot_obj = mock_session.add.call_args[0][0]
        assert snapshot_obj.overall_health == "H3"
        assert snapshot_obj.open_alerts == 5
        assert snapshot_obj.blocking_issues == 2
        assert snapshot_obj.milestone_delayed == 1

    def test_calculator_called_with_each_project(self):
        """每个项目都调用 get_health_details"""
        from app.utils.scheduled_tasks.project_health_tasks import daily_health_snapshot

        projects = [make_mock_project(i) for i in range(1, 4)]
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = projects
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_calculator = MagicMock()
        mock_calculator.get_health_details.return_value = {
            "calculated_health": "H2",
            "statistics": {"active_alerts": 0, "blocking_issues": 0, "overdue_milestones": 0},
        }

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator", return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 3
        assert mock_calculator.get_health_details.call_count == 3
