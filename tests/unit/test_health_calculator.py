# -*- coding: utf-8 -*-
"""
健康度计算服务单元测试

测试 HealthCalculator 类的所有公共和私有方法
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.alert import AlertRecord
from app.models import ProjectHealthEnum
from app.models.issue import Issue
from app.models.progress import Task
from app.models import Project, ProjectMilestone
from app.services.health_calculator import HealthCalculator


@pytest.mark.unit
class TestHealthCalculator:
    """健康度计算器测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def health_calculator(self, db_session):
        """创建健康度计算器实例"""
        return HealthCalculator(db_session)

    @pytest.fixture
    def mock_project(self):
        """创建模拟项目对象"""
        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PJ-TEST-001"
        project.project_name = "测试项目"
        project.status = "ST01"
        project.stage = "S1"
        project.health = "H1"
        project.progress_pct = Decimal("50.00")
        project.planned_start_date = date.today() - timedelta(days=30)
        project.planned_end_date = date.today() + timedelta(days=60)
        project.actual_start_date = date.today() - timedelta(days=30)
        project.is_active = True
        project.is_archived = False
        return project

    # ==================== 测试 calculate_health() ====================

    def test_calculate_health_h4_closed_project(self, health_calculator, mock_project):
        """测试 H4 健康度 - 已完结项目"""
        mock_project.status = "ST30"  # 已结项

        with patch.object(health_calculator, "_is_closed", return_value=True):
            result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H4.value

    def test_calculate_health_h4_cancelled_project(
        self, health_calculator, mock_project
    ):
        """测试 H4 健康度 - 已取消项目"""
        mock_project.status = "ST99"  # 项目取消

        with patch.object(health_calculator, "_is_closed", return_value=True):
            result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H4.value

    def test_calculate_health_h3_blocked_by_status(
        self, health_calculator, mock_project
    ):
        """测试 H3 健康度 - 状态为阻塞"""
        mock_project.status = "ST14"  # 缺料阻塞

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=True):
                result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H3.value

    def test_calculate_health_h3_blocked_by_status_technical(
        self, health_calculator, mock_project
    ):
        """测试 H3 健康度 - 技术阻塞"""
        mock_project.status = "ST19"  # 技术阻塞

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=True):
                result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H3.value

    def test_calculate_health_h3_blocked_by_tasks(
        self, health_calculator, mock_project
    ):
        """测试 H3 健康度 - 关键任务阻塞"""
        mock_project.status = "ST01"

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=True):
                result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H3.value

    def test_calculate_health_h2_at_risk_by_rectification(
        self, health_calculator, mock_project
    ):
        """测试 H2 健康度 - 整改中"""
        mock_project.status = "ST22"  # FAT整改中

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=False):
                with patch.object(health_calculator, "_has_risks", return_value=True):
                    result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H2.value

    def test_calculate_health_h2_sat_rectification(
        self, health_calculator, mock_project
    ):
        """测试 H2 健康度 - SAT整改中"""
        mock_project.status = "ST26"  # SAT整改中

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=False):
                with patch.object(health_calculator, "_has_risks", return_value=True):
                    result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H2.value

    def test_calculate_health_h2_risk_factors(self, health_calculator, mock_project):
        """测试 H2 健康度 - 各种风险因素"""
        mock_project.status = "ST01"

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=False):
                with patch.object(health_calculator, "_has_risks", return_value=True):
                    result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H2.value

    def test_calculate_health_h1_normal(self, health_calculator, mock_project):
        """测试 H1 健康度 - 正常项目"""
        mock_project.status = "ST01"

        with patch.object(health_calculator, "_is_closed", return_value=False):
            with patch.object(health_calculator, "_is_blocked", return_value=False):
                with patch.object(health_calculator, "_has_risks", return_value=False):
                    result = health_calculator.calculate_health(mock_project)

        assert result == ProjectHealthEnum.H1.value

    # ==================== 测试 _is_closed() ====================

    def test_is_closed_status_st30(self, health_calculator, mock_project):
        """测试判断已完结 - ST30 已结项"""
        mock_project.status = "ST30"
        result = health_calculator._is_closed(mock_project)
        assert result is True

    def test_is_closed_status_st99(self, health_calculator, mock_project):
        """测试判断已完结 - ST99 项目取消"""
        mock_project.status = "ST99"
        result = health_calculator._is_closed(mock_project)
        assert result is True

    def test_is_closed_other_status(self, health_calculator, mock_project):
        """测试判断已完结 - 其他状态"""
        for status in ["ST01", "ST02", "ST10", "ST22", "ST26"]:
            mock_project.status = status
            result = health_calculator._is_closed(mock_project)
            assert result is False

    # ==================== 测试 _is_blocked() ====================

    def test_is_blocked_by_status_st14(self, health_calculator, mock_project):
        """测试判断阻塞 - ST14 缺料阻塞"""
        mock_project.status = "ST14"
        result = health_calculator._is_blocked(mock_project)
        assert result is True

    def test_is_blocked_by_status_st19(self, health_calculator, mock_project):
        """测试判断阻塞 - ST19 技术阻塞"""
        mock_project.status = "ST19"
        result = health_calculator._is_blocked(mock_project)
        assert result is True

    def test_is_blocked_by_critical_tasks(
        self, health_calculator, mock_project, db_session
    ):
        """测试判断阻塞 - 有关键任务阻塞"""
        mock_project.status = "ST01"
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1  # 有1个阻塞任务
        db_session.query.return_value = mock_query

        with patch.object(
            health_calculator, "_has_blocked_critical_tasks", return_value=True
        ):
            result = health_calculator._is_blocked(mock_project)

        assert result is True

    def test_is_blocked_by_blocking_issues(self, health_calculator, mock_project):
        """测试判断阻塞 - 有阻塞问题"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_has_blocked_critical_tasks", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_blocking_issues", return_value=True
            ):
                result = health_calculator._is_blocked(mock_project)

        assert result is True

    def test_is_blocked_by_critical_shortage(self, health_calculator, mock_project):
        """测试判断阻塞 - 有严重缺料预警"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_has_blocked_critical_tasks", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_blocking_issues", return_value=False
            ):
                with patch.object(
                    health_calculator,
                    "_has_critical_shortage_alerts",
                    return_value=True,
                ):
                    result = health_calculator._is_blocked(mock_project)

        assert result is True

    def test_is_not_blocked(self, health_calculator, mock_project):
        """测试判断阻塞 - 不阻塞"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_has_blocked_critical_tasks", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_blocking_issues", return_value=False
            ):
                with patch.object(
                    health_calculator,
                    "_has_critical_shortage_alerts",
                    return_value=False,
                ):
                    result = health_calculator._is_blocked(mock_project)

        assert result is False

    # ==================== 测试 _has_blocked_critical_tasks() ====================

    def test_has_blocked_critical_tasks_true(
        self, health_calculator, mock_project, db_session
    ):
        """测试有关键任务阻塞 - 有阻塞任务"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        db_session.query.return_value = mock_query

        result = health_calculator._has_blocked_critical_tasks(mock_project)
        assert result is True
        db_session.query.assert_called_once_with(Task)

    def test_has_blocked_critical_tasks_false(
        self, health_calculator, mock_project, db_session
    ):
        """测试有关键任务阻塞 - 无阻塞任务"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator._has_blocked_critical_tasks(mock_project)
        assert result is False

    # ==================== 测试 _has_blocking_issues() ====================

    def test_has_blocking_issues_true(
        self, health_calculator, mock_project, db_session
    ):
        """测试有阻塞问题 - 有开放阻塞问题"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        db_session.query.return_value = mock_query

        result = health_calculator._has_blocking_issues(mock_project)
        assert result is True
        db_session.query.assert_called_once_with(Issue)

    def test_has_blocking_issues_false(
        self, health_calculator, mock_project, db_session
    ):
        """测试有阻塞问题 - 无阻塞问题"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator._has_blocking_issues(mock_project)
        assert result is False

    # ==================== 测试 _has_critical_shortage_alerts() ====================

    def test_has_critical_shortage_alerts_true(
        self, health_calculator, mock_project, db_session
    ):
        """测试有严重缺料预警 - 有预警"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        db_session.query.return_value = mock_query

        result = health_calculator._has_critical_shortage_alerts(mock_project)
        assert result is True
        db_session.query.assert_called_once_with(AlertRecord)

    def test_has_critical_shortage_alerts_false(
        self, health_calculator, mock_project, db_session
    ):
        """测试有严重缺料预警 - 无预警"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator._has_critical_shortage_alerts(mock_project)
        assert result is False

    # ==================== 测试 _has_risks() ====================

    def test_has_risks_by_rectification_st22(self, health_calculator, mock_project):
        """测试有风险 - FAT整改中"""
        mock_project.status = "ST22"

        result = health_calculator._has_risks(mock_project)
        assert result is True

    def test_has_risks_by_rectification_st26(self, health_calculator, mock_project):
        """测试有风险 - SAT整改中"""
        mock_project.status = "ST26"

        result = health_calculator._has_risks(mock_project)
        assert result is True

    def test_has_risks_by_deadline_approaching(self, health_calculator, mock_project):
        """测试有风险 - 交期临近"""
        mock_project.status = "ST01"
        mock_project.planned_end_date = date.today() + timedelta(days=5)

        with patch.object(
            health_calculator, "_is_deadline_approaching", return_value=True
        ):
            result = health_calculator._has_risks(mock_project)

        assert result is True

    def test_has_risks_by_overdue_milestones(self, health_calculator, mock_project):
        """测试有风险 - 有逾期里程碑"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_is_deadline_approaching", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_overdue_milestones", return_value=True
            ):
                result = health_calculator._has_risks(mock_project)

        assert result is True

    def test_has_risks_by_shortage_warnings(self, health_calculator, mock_project):
        """测试有风险 - 有缺料预警"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_is_deadline_approaching", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_overdue_milestones", return_value=False
            ):
                with patch.object(
                    health_calculator, "_has_shortage_warnings", return_value=True
                ):
                    result = health_calculator._has_risks(mock_project)

        assert result is True

    def test_has_risks_by_high_priority_issues(self, health_calculator, mock_project):
        """测试有风险 - 有高优先级问题"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_is_deadline_approaching", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_overdue_milestones", return_value=False
            ):
                with patch.object(
                    health_calculator, "_has_shortage_warnings", return_value=False
                ):
                    with patch.object(
                        health_calculator,
                        "_has_high_priority_issues",
                        return_value=True,
                    ):
                        result = health_calculator._has_risks(mock_project)

        assert result is True

    def test_has_risks_by_schedule_variance(self, health_calculator, mock_project):
        """测试有风险 - 进度偏差"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_is_deadline_approaching", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_overdue_milestones", return_value=False
            ):
                with patch.object(
                    health_calculator, "_has_shortage_warnings", return_value=False
                ):
                    with patch.object(
                        health_calculator,
                        "_has_high_priority_issues",
                        return_value=False,
                    ):
                        with patch.object(
                            health_calculator,
                            "_has_schedule_variance",
                            return_value=True,
                        ):
                            result = health_calculator._has_risks(mock_project)

        assert result is True

    def test_has_no_risks(self, health_calculator, mock_project):
        """测试有风险 - 无风险"""
        mock_project.status = "ST01"

        with patch.object(
            health_calculator, "_is_deadline_approaching", return_value=False
        ):
            with patch.object(
                health_calculator, "_has_overdue_milestones", return_value=False
            ):
                with patch.object(
                    health_calculator, "_has_shortage_warnings", return_value=False
                ):
                    with patch.object(
                        health_calculator,
                        "_has_high_priority_issues",
                        return_value=False,
                    ):
                        with patch.object(
                            health_calculator,
                            "_has_schedule_variance",
                            return_value=False,
                        ):
                            result = health_calculator._has_risks(mock_project)

        assert result is False

    # ==================== 测试 _is_deadline_approaching() ====================

    def test_is_deadline_approaching_true(self, health_calculator, mock_project):
        """测试交期临近 - 5天后"""
        mock_project.planned_end_date = date.today() + timedelta(days=5)
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is True

    def test_is_deadline_approaching_today(self, health_calculator, mock_project):
        """测试交期临近 - 今天"""
        mock_project.planned_end_date = date.today()
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is True

    def test_is_deadline_approaching_false_future(
        self, health_calculator, mock_project
    ):
        """测试交期临近 - 未来（超过7天）"""
        mock_project.planned_end_date = date.today() + timedelta(days=10)
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_is_deadline_approaching_false_past(self, health_calculator, mock_project):
        """测试交期临近 - 已过期"""
        mock_project.planned_end_date = date.today() - timedelta(days=1)
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    def test_is_deadline_approaching_no_end_date(self, health_calculator, mock_project):
        """测试交期临近 - 无结束日期"""
        mock_project.planned_end_date = None
        result = health_calculator._is_deadline_approaching(mock_project, days=7)
        assert result is False

    # ==================== 测试 _has_overdue_milestones() ====================

    def test_has_overdue_milestones_true(
        self, health_calculator, mock_project, db_session
    ):
        """测试有逾期里程碑 - 有逾期"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        db_session.query.return_value = mock_query

        result = health_calculator._has_overdue_milestones(mock_project)
        assert result is True
        db_session.query.assert_called_once_with(ProjectMilestone)

    def test_has_overdue_milestones_false(
        self, health_calculator, mock_project, db_session
    ):
        """测试有逾期里程碑 - 无逾期"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator._has_overdue_milestones(mock_project)
        assert result is False

    # ==================== 测试 _has_shortage_warnings() ====================

    def test_has_shortage_warnings_true(
        self, health_calculator, mock_project, db_session
    ):
        """测试有缺料预警 - 有预警"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        db_session.query.return_value = mock_query

        result = health_calculator._has_shortage_warnings(mock_project)
        assert result is True

    def test_has_shortage_warnings_false(
        self, health_calculator, mock_project, db_session
    ):
        """测试有缺料预警 - 无预警"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator._has_shortage_warnings(mock_project)
        assert result is False

    # ==================== 测试 _has_high_priority_issues() ====================

    def test_has_high_priority_issues_true(
        self, health_calculator, mock_project, db_session
    ):
        """测试有高优先级问题 - 有高优先级"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        db_session.query.return_value = mock_query

        result = health_calculator._has_high_priority_issues(mock_project)
        assert result is True
        db_session.query.assert_called_once_with(Issue)

    def test_has_high_priority_issues_false(
        self, health_calculator, mock_project, db_session
    ):
        """测试有高优先级问题 - 无高优先级"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        db_session.query.return_value = mock_query

        result = health_calculator._has_high_priority_issues(mock_project)
        assert result is False

    # ==================== 测试 _has_schedule_variance() ====================

    def test_has_schedule_variance_true(self, health_calculator, mock_project):
        """测试进度偏差 - 超过阈值"""
        mock_project.planned_start_date = date.today() - timedelta(days=60)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=60)
        mock_project.progress_pct = Decimal("20.00")  # 实际进度20%，计划进度66.67%

        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is True

    def test_has_schedule_variance_false(self, health_calculator, mock_project):
        """测试进度偏差 - 未超过阈值"""
        mock_project.planned_start_date = date.today() - timedelta(days=60)
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.actual_start_date = date.today() - timedelta(days=60)
        mock_project.progress_pct = Decimal("60.00")  # 实际进度60%，计划进度66.67%

        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_no_end_date(self, health_calculator, mock_project):
        """测试进度偏差 - 无结束日期"""
        mock_project.planned_end_date = None
        mock_project.actual_start_date = date.today()

        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_no_start_date(self, health_calculator, mock_project):
        """测试进度偏差 - 无开始日期"""
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.planned_start_date = date.today()
        mock_project.actual_start_date = None

        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    def test_has_schedule_variance_zero_total_days(
        self, health_calculator, mock_project
    ):
        """测试进度偏差 - 总天数为0"""
        mock_project.planned_start_date = date.today()
        mock_project.planned_end_date = date.today()
        mock_project.actual_start_date = date.today()

        result = health_calculator._has_schedule_variance(mock_project, threshold=10)
        assert result is False

    # ==================== 测试 calculate_and_update() ====================

    def test_calculate_and_update_no_change(self, health_calculator, mock_project):
        """测试计算并更新 - 无变化"""
        mock_project.health = "H1"

        with patch.object(health_calculator, "calculate_health", return_value="H1"):
            result = health_calculator.calculate_and_update(
                mock_project, auto_save=False
            )

        assert result["old_health"] == "H1"
        assert result["new_health"] == "H1"
        assert result["changed"] is False
        assert "calculation_time" in result

    def test_calculate_and_update_with_change_no_save(
        self, health_calculator, mock_project
    ):
        """测试计算并更新 - 有变化但不保存"""
        mock_project.health = "H1"

        with patch.object(health_calculator, "calculate_health", return_value="H2"):
            result = health_calculator.calculate_and_update(
                mock_project, auto_save=False
            )

        assert result["old_health"] == "H1"
        assert result["new_health"] == "H2"
        assert result["changed"] is True
        assert result["project_code"] == mock_project.project_code

    def test_calculate_and_update_with_change_save(
        self, health_calculator, mock_project, db_session
    ):
        """测试计算并更新 - 有变化并保存"""
        mock_project.health = "H1"

        with patch.object(health_calculator, "calculate_health", return_value="H2"):
            result = health_calculator.calculate_and_update(
                mock_project, auto_save=True
            )

        assert result["changed"] is True
        assert mock_project.health == "H2"
        db_session.add.assert_called()
        db_session.commit.assert_called()

    # ==================== 测试 batch_calculate() ====================

    def test_batch_calculate_all_projects(self, health_calculator, db_session):
        """测试批量计算 - 所有项目"""
        project1 = Mock(spec=Project)
        project1.id = 1
        project1.is_active = True
        project1.is_archived = False
        project1.health = "H1"

        project2 = Mock(spec=Project)
        project2.id = 2
        project2.is_active = True
        project2.is_archived = False
        project2.health = "H1"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [project1, project2]
        db_session.query.return_value = mock_query

        with patch.object(health_calculator, "calculate_and_update") as mock_calc:
            mock_calc.side_effect = [
                {"project_id": 1, "changed": False},
                {"project_id": 2, "changed": True},
            ]

            result = health_calculator.batch_calculate(project_ids=None, batch_size=100)

        assert result["total"] == 2
        assert result["updated"] == 1
        assert result["unchanged"] == 1
        assert len(result["details"]) == 2

    def test_batch_calculate_specific_projects(self, health_calculator, db_session):
        """测试批量计算 - 指定项目"""
        project1 = Mock(spec=Project)
        project1.id = 1
        project1.is_active = True
        project1.is_archived = False
        project1.health = "H1"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [project1]
        db_session.query.return_value = mock_query

        with patch.object(health_calculator, "calculate_and_update") as mock_calc:
            mock_calc.return_value = {"project_id": 1, "changed": False}

            result = health_calculator.batch_calculate(project_ids=[1], batch_size=100)

        assert result["total"] == 1
        mock_query.filter.assert_called()

    def test_batch_calculate_with_error(self, health_calculator, db_session):
        """测试批量计算 - 处理错误"""
        project = Mock(spec=Project)
        project.id = 1
        project.is_active = True
        project.is_archived = False
        project.health = "H1"

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [project]
        db_session.query.return_value = mock_query

        db_session.commit.side_effect = Exception("Database error")

        with patch.object(health_calculator, "calculate_and_update") as mock_calc:
            mock_calc.return_value = {"project_id": 1, "changed": True}

            result = health_calculator.batch_calculate(project_ids=[1], batch_size=100)

        assert result["total"] == 1
        db_session.rollback.assert_called()

    # ==================== 测试 get_health_details() ====================

    def test_get_health_details(self, health_calculator, mock_project, db_session):
        """测试获取健康度详情"""
        mock_project.health = "H1"

        task_query = Mock()
        task_query.filter.return_value = task_query
        task_query.count.return_value = 0

        issue_query = Mock()
        issue_query.filter.return_value = issue_query
        issue_query.count.return_value = 0

        milestone_query = Mock()
        milestone_query.filter.return_value = milestone_query
        milestone_query.count.return_value = 0

        alert_query = Mock()
        alert_query.filter.return_value = alert_query
        alert_query.count.return_value = 0

        def query_side_effect(model):
            if model == Task:
                return task_query
            elif model == Issue:
                return issue_query
            elif model == ProjectMilestone:
                return milestone_query
            elif model == AlertRecord:
                return alert_query
            return Mock()

        db_session.query.side_effect = query_side_effect

        with patch.object(health_calculator, "calculate_health", return_value="H1"):
            with patch.object(health_calculator, "_is_closed", return_value=False):
                with patch.object(health_calculator, "_is_blocked", return_value=False):
                    with patch.object(
                        health_calculator, "_has_risks", return_value=False
                    ):
                        with patch.object(
                            health_calculator,
                            "_has_blocked_critical_tasks",
                            return_value=False,
                        ):
                            with patch.object(
                                health_calculator,
                                "_has_blocking_issues",
                                return_value=False,
                            ):
                                with patch.object(
                                    health_calculator,
                                    "_has_critical_shortage_alerts",
                                    return_value=False,
                                ):
                                    with patch.object(
                                        health_calculator,
                                        "_is_deadline_approaching",
                                        return_value=False,
                                    ):
                                        with patch.object(
                                            health_calculator,
                                            "_has_overdue_milestones",
                                            return_value=False,
                                        ):
                                            with patch.object(
                                                health_calculator,
                                                "_has_shortage_warnings",
                                                return_value=False,
                                            ):
                                                with patch.object(
                                                    health_calculator,
                                                    "_has_high_priority_issues",
                                                    return_value=False,
                                                ):
                                                    with patch.object(
                                                        health_calculator,
                                                        "_has_schedule_variance",
                                                        return_value=False,
                                                    ):
                                                        result = health_calculator.get_health_details(
                                                            mock_project
                                                        )

        assert result["project_id"] == 1
        assert result["project_code"] == "PJ-TEST-001"
        assert result["current_health"] == "H1"
        assert result["calculated_health"] == "H1"
        assert "checks" in result
        assert "statistics" in result
        assert result["statistics"]["blocked_tasks"] == 0
        assert result["statistics"]["blocking_issues"] == 0
        assert result["statistics"]["overdue_milestones"] == 0
        assert result["statistics"]["active_alerts"] == 0
