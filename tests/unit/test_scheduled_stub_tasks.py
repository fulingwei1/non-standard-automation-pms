# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：存根任务 (stub_tasks.py)
L2组覆盖率提升
"""
import sys
from unittest.mock import MagicMock

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


# ================================================================
#  所有存根任务
# 存根任务通过 @_stub_task 装饰器实现，直接调用即可
# 每个函数应返回含 status='stub' 的字典
# ================================================================

class TestStubTasks:
    """测试所有存根任务的基本行为"""

    def _assert_stub_result(self, result, expected_task: str):
        """通用断言：结果是 stub 字典"""
        assert isinstance(result, dict), "结果应为字典"
        assert result.get("status") == "stub", f"status 应为 'stub'，得到: {result.get('status')}"
        assert result.get("task") == expected_task, (
            f"task 字段应为 '{expected_task}'，得到: {result.get('task')}"
        )
        assert "timestamp" in result, "应包含 timestamp 字段"
        assert "message" in result, "应包含 message 字段"

    def test_check_issue_timeout_escalation(self):
        from app.utils.scheduled_tasks.stub_tasks import check_issue_timeout_escalation
        result = check_issue_timeout_escalation()
        self._assert_stub_result(result, "check_issue_timeout_escalation")

    def test_generate_shortage_alerts(self):
        from app.utils.scheduled_tasks.stub_tasks import generate_shortage_alerts
        result = generate_shortage_alerts()
        self._assert_stub_result(result, "generate_shortage_alerts")

    def test_auto_trigger_urgent_purchase_from_shortage_alerts(self):
        from app.utils.scheduled_tasks.stub_tasks import (
            auto_trigger_urgent_purchase_from_shortage_alerts,
        )
        result = auto_trigger_urgent_purchase_from_shortage_alerts()
        self._assert_stub_result(result, "auto_trigger_urgent_purchase_from_shortage_alerts")

    def test_daily_kit_check(self):
        from app.utils.scheduled_tasks.stub_tasks import daily_kit_check
        result = daily_kit_check()
        self._assert_stub_result(result, "daily_kit_check")

    def test_generate_shortage_daily_report(self):
        from app.utils.scheduled_tasks.stub_tasks import generate_shortage_daily_report
        result = generate_shortage_daily_report()
        self._assert_stub_result(result, "generate_shortage_daily_report")

    def test_check_equipment_maintenance_reminder(self):
        from app.utils.scheduled_tasks.stub_tasks import check_equipment_maintenance_reminder
        result = check_equipment_maintenance_reminder()
        self._assert_stub_result(result, "check_equipment_maintenance_reminder")

    def test_check_cost_overrun_alerts(self):
        from app.utils.scheduled_tasks.stub_tasks import check_cost_overrun_alerts
        result = check_cost_overrun_alerts()
        self._assert_stub_result(result, "check_cost_overrun_alerts")

    def test_check_task_delay_alerts(self):
        from app.utils.scheduled_tasks.stub_tasks import check_task_delay_alerts
        result = check_task_delay_alerts()
        self._assert_stub_result(result, "check_task_delay_alerts")

    def test_check_task_deadline_reminder(self):
        from app.utils.scheduled_tasks.stub_tasks import check_task_deadline_reminder
        result = check_task_deadline_reminder()
        self._assert_stub_result(result, "check_task_deadline_reminder")

    def test_generate_monthly_reports_task(self):
        from app.utils.scheduled_tasks.stub_tasks import generate_monthly_reports_task
        result = generate_monthly_reports_task()
        self._assert_stub_result(result, "generate_monthly_reports_task")

    def test_check_workload_overload_alerts(self):
        from app.utils.scheduled_tasks.stub_tasks import check_workload_overload_alerts
        result = check_workload_overload_alerts()
        self._assert_stub_result(result, "check_workload_overload_alerts")

    def test_check_delivery_delay(self):
        from app.utils.scheduled_tasks.stub_tasks import check_delivery_delay
        result = check_delivery_delay()
        self._assert_stub_result(result, "check_delivery_delay")

    def test_check_outsourcing_delivery_alerts(self):
        from app.utils.scheduled_tasks.stub_tasks import check_outsourcing_delivery_alerts
        result = check_outsourcing_delivery_alerts()
        self._assert_stub_result(result, "check_outsourcing_delivery_alerts")

    def test_generate_job_duty_tasks(self):
        from app.utils.scheduled_tasks.stub_tasks import generate_job_duty_tasks
        result = generate_job_duty_tasks()
        self._assert_stub_result(result, "generate_job_duty_tasks")

    def test_check_presale_workorder_timeout(self):
        from app.utils.scheduled_tasks.stub_tasks import check_presale_workorder_timeout
        result = check_presale_workorder_timeout()
        self._assert_stub_result(result, "check_presale_workorder_timeout")


class TestStubTasksReturnStructure:
    """额外验证 stub 返回值的字段内容"""

    def test_message_contains_stub_hint(self):
        """message 字段应包含 '待实现' 提示"""
        from app.utils.scheduled_tasks.stub_tasks import check_issue_timeout_escalation
        result = check_issue_timeout_escalation()
        assert "待实现" in result["message"]

    def test_all_stubs_callable_multiple_times(self):
        """多次调用存根任务应始终返回相同结构"""
        from app.utils.scheduled_tasks.stub_tasks import daily_kit_check
        r1 = daily_kit_check()
        r2 = daily_kit_check()
        assert r1["status"] == r2["status"] == "stub"
        assert r1["task"] == r2["task"]
