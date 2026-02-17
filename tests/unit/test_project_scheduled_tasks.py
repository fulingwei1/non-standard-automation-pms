# -*- coding: utf-8 -*-
"""
J1组单元测试 - project_scheduled_tasks.py
覆盖：check_project_deadline_alerts, check_project_cost_overrun,
      calculate_progress_summary, daily_spec_match_check,
      calculate_project_health, daily_health_snapshot
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

import pytest


# ============================================================================
# 辅助函数：构造 mock db session 上下文
# ============================================================================

def make_mock_db_ctx():
    """返回 (mock_ctx, mock_session) 对"""
    mock_session = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_session)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx, mock_session


def make_mock_project(
    project_id=1,
    project_code="PJ-001",
    project_name="测试项目",
    planned_end_date=None,
    budget_amount=100000.0,
    progress_pct=50.0,
    is_active=True,
    status="active",
):
    p = MagicMock()
    p.id = project_id
    p.project_code = project_code
    p.project_name = project_name
    p.planned_end_date = planned_end_date or (date.today() + timedelta(days=5))
    p.budget_amount = budget_amount
    p.progress_pct = progress_pct
    p.is_active = is_active
    p.status = status
    return p


# ============================================================================
# 测试 check_project_deadline_alerts
# ============================================================================

MODULE = "app.utils.scheduled_tasks.project_scheduled_tasks"


@pytest.mark.unit
class TestCheckProjectDeadlineAlerts:
    """项目截止日期预警检查"""

    def test_no_upcoming_projects_returns_empty(self):
        """无即将到期项目：alerts_created=0"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_deadline_alerts()

        assert result["upcoming_projects"] == 0
        assert result["alerts_created"] == 0
        assert "timestamp" in result

    def test_single_project_creates_alert(self):
        """一个将到期项目：生成一条预警"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        project = make_mock_project(planned_end_date=date.today() + timedelta(days=5))
        mock_ctx, mock_session = make_mock_db_ctx()

        # projects 查询
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        # 无已存在的 alert
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_deadline_alerts()

        assert result["upcoming_projects"] == 1
        assert result["alerts_created"] == 1
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_existing_alert_skipped(self):
        """已存在相同预警：不重复创建"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        project = make_mock_project(planned_end_date=date.today() + timedelta(days=3))
        existing_alert = MagicMock()

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.first.return_value = existing_alert

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_deadline_alerts()

        assert result["upcoming_projects"] == 1
        assert result["alerts_created"] == 0
        mock_session.add.assert_not_called()

    def test_critical_urgency_for_3_days_remaining(self):
        """剩余<=3天：urgency=CRITICAL"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        project = make_mock_project(planned_end_date=date.today() + timedelta(days=2))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_deadline_alerts()

        assert result["alerts_created"] == 1
        # 验证添加的 alert 级别为 CRITICAL
        added_alert = mock_session.add.call_args[0][0]
        assert added_alert.alert_level == "CRITICAL"

    def test_high_urgency_for_more_than_3_days(self):
        """剩余4-7天：urgency=HIGH"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        project = make_mock_project(planned_end_date=date.today() + timedelta(days=6))
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_deadline_alerts()

        assert result["alerts_created"] == 1
        added_alert = mock_session.add.call_args[0][0]
        assert added_alert.alert_level == "HIGH"

    def test_multiple_projects_mixed_alerts(self):
        """多个项目：部分跳过，部分新建预警"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        p1 = make_mock_project(project_id=1, planned_end_date=date.today() + timedelta(days=3))
        p2 = make_mock_project(project_id=2, planned_end_date=date.today() + timedelta(days=7))

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [p1, p2]
        # p1 已有 alert，p2 没有
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(),  # p1 → existing alert
            None,         # p2 → no alert
        ]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_deadline_alerts()

        assert result["upcoming_projects"] == 2
        assert result["alerts_created"] == 1

    def test_exception_returns_error_key(self):
        """异常时返回 error 字段"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_deadline_alerts,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("DB connection failed")
            result = check_project_deadline_alerts()

        assert "error" in result
        assert "DB connection failed" in result["error"]


# ============================================================================
# 测试 check_project_cost_overrun
# ============================================================================


@pytest.mark.unit
class TestCheckProjectCostOverrun:
    """项目成本超支检查"""

    def test_no_projects_no_alerts(self):
        """无活跃项目：overrun_projects=0"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 0
        assert "timestamp" in result

    def test_project_under_budget_no_alert(self):
        """实际成本 < 预算：不生成预警"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        project = make_mock_project(budget_amount=100000.0)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        # 实际成本 = 80000（低于预算）
        mock_session.query.return_value.filter.return_value.scalar.return_value = 80000.0

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 0
        mock_session.add.assert_not_called()

    def test_project_over_budget_creates_alert(self):
        """实际成本 > 预算：生成预警"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        project = make_mock_project(budget_amount=100000.0)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.scalar.return_value = 115000.0
        mock_session.query.return_value.filter.return_value.first.return_value = None  # 无已存在 alert

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 1
        mock_session.add.assert_called_once()

    def test_critical_overrun_over_20_percent(self):
        """超支 > 20%：urgency=CRITICAL"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        project = make_mock_project(budget_amount=100000.0)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.scalar.return_value = 125000.0  # 25% overrun
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 1
        added_alert = mock_session.add.call_args[0][0]
        assert added_alert.alert_level == "CRITICAL"

    def test_high_overrun_under_20_percent(self):
        """超支 <= 20%：urgency=HIGH"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        project = make_mock_project(budget_amount=100000.0)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.scalar.return_value = 115000.0  # 15% overrun
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 1
        added_alert = mock_session.add.call_args[0][0]
        assert added_alert.alert_level == "HIGH"

    def test_existing_alert_skipped(self):
        """已存在成本超支预警：不重复创建"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        project = make_mock_project(budget_amount=100000.0)
        existing_alert = MagicMock()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.scalar.return_value = 120000.0
        mock_session.query.return_value.filter.return_value.first.return_value = existing_alert

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 0
        mock_session.add.assert_not_called()

    def test_no_budget_set_no_alert(self):
        """未设置预算（budget_amount=None）：不生成预警"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        project = make_mock_project(budget_amount=None)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]
        mock_session.query.return_value.filter.return_value.scalar.return_value = 50000.0

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = check_project_cost_overrun()

        assert result["overrun_projects"] == 0

    def test_exception_returns_error_key(self):
        """异常时返回 error 字段"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            check_project_cost_overrun,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = RuntimeError("Connection reset")
            result = check_project_cost_overrun()

        assert "error" in result
        assert "Connection reset" in result["error"]


# ============================================================================
# 测试 calculate_progress_summary
# ============================================================================


@pytest.mark.unit
class TestCalculateProgressSummary:
    """项目进度汇总计算"""

    def test_no_active_projects(self):
        """无活跃项目：updated_projects=0"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_progress_summary,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = calculate_progress_summary()

        assert result["updated_projects"] == 0
        assert "timestamp" in result

    def test_project_with_tasks_updates_progress(self):
        """有任务和里程碑的项目：计算并更新进度"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_progress_summary,
        )
        project = make_mock_project()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]

        # task_progress_summary
        task_summary = MagicMock()
        task_summary.avg_completion = 60.0
        task_summary.total_tasks = 10
        task_summary.completed_tasks = 6

        # milestone_progress_summary
        milestone_summary = MagicMock()
        milestone_summary.total_milestones = 5
        milestone_summary.completed_milestones = 3

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            task_summary, milestone_summary
        ]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = calculate_progress_summary()

        assert result["updated_projects"] == 1
        mock_session.commit.assert_called_once()

    def test_project_with_no_tasks_no_update(self):
        """项目无任务和里程碑：不更新"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_progress_summary,
        )
        project = make_mock_project()
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]

        task_summary = MagicMock()
        task_summary.total_tasks = 0
        task_summary.completed_tasks = 0
        task_summary.avg_completion = 0.0

        milestone_summary = MagicMock()
        milestone_summary.total_milestones = 0
        milestone_summary.completed_milestones = 0

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            task_summary, milestone_summary
        ]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = calculate_progress_summary()

        assert result["updated_projects"] == 0

    def test_exception_returns_error_key(self):
        """异常时返回 error"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_progress_summary,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Query failed")
            result = calculate_progress_summary()

        assert "error" in result

    def test_multiple_projects_all_updated(self):
        """两个有任务的项目：都应被更新"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_progress_summary,
        )
        p1 = make_mock_project(project_id=1)
        p2 = make_mock_project(project_id=2)

        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [p1, p2]

        def make_task_summary(n_tasks, n_done):
            s = MagicMock()
            s.total_tasks = n_tasks
            s.completed_tasks = n_done
            s.avg_completion = (n_done / n_tasks * 100) if n_tasks > 0 else 0
            return s

        def make_ms_summary(n_ms, n_done):
            s = MagicMock()
            s.total_milestones = n_ms
            s.completed_milestones = n_done
            return s

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            make_task_summary(5, 3), make_ms_summary(2, 1),
            make_task_summary(8, 4), make_ms_summary(4, 2),
        ]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            result = calculate_progress_summary()

        assert result["updated_projects"] == 2


# ============================================================================
# 测试 daily_spec_match_check
# ============================================================================


@pytest.mark.unit
class TestDailySpecMatchCheck:
    """每日规格匹配检查"""

    def test_no_active_projects_returns_zero(self):
        """无活跃项目：checked=0, mismatched=0"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_spec_match_check,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(f"{MODULE}.SpecMatchService") as mock_svc:
                result = daily_spec_match_check()

        assert result["checked"] == 0
        assert result["mismatched"] == 0
        assert "timestamp" in result

    def test_exception_on_db_error(self):
        """DB 异常时应 raise（非返回 error dict）"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_spec_match_check,
        )
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(side_effect=Exception("DB error"))
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(f"{MODULE}.SpecMatchService"):
                with pytest.raises(Exception, match="DB error"):
                    daily_spec_match_check()

    def test_project_with_no_purchase_orders(self):
        """有项目但无采购订单：checked=0"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_spec_match_check,
        )
        project = make_mock_project()
        mock_ctx, mock_session = make_mock_db_ctx()
        # 第一次 all() 返回 projects，后续全空
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [project],  # active projects
            [],         # purchase_orders for project
            [],         # bom_headers for project
        ]

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(f"{MODULE}.SpecMatchService"):
                result = daily_spec_match_check()

        assert result["checked"] == 0
        mock_session.commit.assert_called_once()

    def test_result_has_required_keys(self):
        """返回值包含必要字段"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_spec_match_check,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch(f"{MODULE}.SpecMatchService"):
                result = daily_spec_match_check()

        assert "checked" in result
        assert "mismatched" in result
        assert "timestamp" in result


# ============================================================================
# 测试 calculate_project_health（在 project_scheduled_tasks.py 中）
# ============================================================================


@pytest.mark.unit
class TestCalculateProjectHealthInProjectScheduled:
    """项目健康度计算（project_scheduled_tasks 中）"""

    def test_returns_result_dict(self):
        """正常执行：返回健康度计算结果"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_project_health,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_calculator = MagicMock()
        mock_calculator.batch_calculate.return_value = {
            "total": 5, "updated": 3, "unchanged": 2
        }

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator",
                       return_value=mock_calculator):
                result = calculate_project_health()

        assert result["total"] == 5
        assert result["updated"] == 3

    def test_exception_returns_error(self):
        """DB 异常：返回 error 字段"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_project_health,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Health calc failed")
            result = calculate_project_health()

        assert "error" in result


# ============================================================================
# 测试 daily_health_snapshot（在 project_scheduled_tasks.py 中）
# ============================================================================


@pytest.mark.unit
class TestDailyHealthSnapshotInProjectScheduled:
    """每日健康度快照（project_scheduled_tasks 中）"""

    def test_no_active_projects_snapshot_count_zero(self):
        """无活跃项目：snapshot_count=0"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_health_snapshot,
        )
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_calculator = MagicMock()

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator",
                       return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 0

    def test_active_projects_generates_snapshots(self):
        """有活跃项目：生成快照"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_health_snapshot,
        )
        p1 = make_mock_project(project_id=1)
        p2 = make_mock_project(project_id=2)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [p1, p2]

        mock_calculator = MagicMock()
        mock_calculator.calculate_and_update.return_value = {"new_health": "H1"}

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator",
                       return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 2
        assert mock_session.add.call_count == 2
        mock_session.commit.assert_called_once()

    def test_exception_returns_error(self):
        """异常时返回 error 字段"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_health_snapshot,
        )
        with patch(f"{MODULE}.get_db_session") as mock_db:
            mock_db.side_effect = Exception("Snapshot error")
            result = daily_health_snapshot()

        assert "error" in result

    def test_h2_health_score_is_70(self):
        """H2 健康度快照的 health_score = 70"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            daily_health_snapshot,
        )
        project = make_mock_project(project_id=1)
        mock_ctx, mock_session = make_mock_db_ctx()
        mock_session.query.return_value.filter.return_value.all.return_value = [project]

        mock_calculator = MagicMock()
        mock_calculator.calculate_and_update.return_value = {"new_health": "H2"}

        with patch(f"{MODULE}.get_db_session", return_value=mock_ctx):
            with patch("app.services.health_calculator.HealthCalculator",
                       return_value=mock_calculator):
                result = daily_health_snapshot()

        assert result["snapshot_count"] == 1
        # 验证 snapshot 的 health_score = 70
        snapshot_obj = mock_session.add.call_args[0][0]
        assert snapshot_obj.health_score == 70
