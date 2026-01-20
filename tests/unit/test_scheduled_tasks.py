# -*- coding: utf-8 -*-
"""定时任务模块单元测试"""


import pytest

from app.utils.scheduled_tasks.alert_tasks import (
    check_alert_escalation,
    retry_failed_notifications,
)
from app.utils.scheduled_tasks.milestone_tasks import (
    check_milestone_alerts,
    check_milestone_risk_alerts,
)
from app.utils.scheduled_tasks.project_scheduled_tasks import (
    calculate_project_health,
    check_project_deadline_alerts,
)
from app.utils.scheduled_tasks.issue_scheduled_tasks import (
    check_overdue_issues,
    check_blocking_issues,
)


@pytest.mark.unit
class TestAlertTasks:
    """预警任务测试类"""

    def test_check_alert_escalation_callable(self):
        """测试预警升级函数可调用"""
        assert callable(check_alert_escalation)

    def test_retry_failed_notifications_callable(self):
        """测试通知重试函数可调用"""
        assert callable(retry_failed_notifications)


@pytest.mark.unit
class TestMilestoneTasks:
    """里程碑任务测试类"""

    def test_check_milestone_alerts_callable(self):
        """测试里程碑预警函数可调用"""
        assert callable(check_milestone_alerts)

    def test_check_milestone_risk_alerts_callable(self):
        """测试里程碑风险预警函数可调用"""
        assert callable(check_milestone_risk_alerts)


@pytest.mark.unit
class TestProjectScheduledTasks:
    """项目定时任务测试类"""

    def test_calculate_project_health_callable(self):
        """测试项目健康度计算函数可调用"""
        assert callable(calculate_project_health)

    def test_check_project_deadline_alerts_callable(self):
        """测试截止日期预警函数可调用"""
        assert callable(check_project_deadline_alerts)


@pytest.mark.unit
class TestIssueScheduledTasks:
    """问题定时任务测试类"""

    def test_check_overdue_issues_callable(self):
        """测试逾期问题检查函数可调用"""
        assert callable(check_overdue_issues)

    def test_check_blocking_issues_callable(self):
        """测试阻塞问题检查函数可调用"""
        assert callable(check_blocking_issues)


@pytest.mark.unit
class TestTaskIntegration:
    """任务集成测试类"""

    def test_all_tasks_callable(self):
        """测试所有任务函数可调用"""
        assert all(
            callable(f)
            for f in [
                check_alert_escalation,
                retry_failed_notifications,
                check_milestone_alerts,
                check_milestone_risk_alerts,
                calculate_project_health,
                check_project_deadline_alerts,
                check_overdue_issues,
                check_blocking_issues,
            ]
        )
