# -*- coding: utf-8 -*-
"""
P0-10: 14/56 定时任务是 stub 假实现，且被监控记成功。

stub_tasks.py 的 @_stub_task 装饰器只打 [STUB] 日志返回 {"status":"stub"}，但被
scheduler_config 正式注册为 enabled cron，正常 return 被 record_job_success 记成功。

正确行为：这些被注册为 enabled 的定时任务不应是返回 {"status":"stub"} 的空壳。
当前必然失败 -> 证明预警体系名存实亡。
"""
import importlib

import pytest

pytestmark = pytest.mark.audit_p0

# stub_tasks.py 中 @_stub_task 装饰的 14 个函数
STUB_FUNCS = [
    "check_issue_timeout_escalation",
    "generate_shortage_alerts",
    "auto_trigger_urgent_purchase_from_shortage_alerts",
    "generate_shortage_daily_report",
    "check_equipment_maintenance_reminder",
    "check_cost_overrun_alerts",
    "check_task_delay_alerts",
    "check_task_deadline_reminder",
    "generate_monthly_reports_task",
    "check_workload_overload_alerts",
    "check_delivery_delay",
    "check_outsourcing_delivery_alerts",
    "generate_job_duty_tasks",
    "check_presale_workorder_timeout",
]


def _is_stub_result(result):
    return isinstance(result, dict) and result.get("status") == "stub"


@pytest.mark.parametrize("fname", STUB_FUNCS)
def test_registered_task_is_not_a_stub(fname):
    mod = importlib.import_module("app.utils.scheduled_tasks.stub_tasks")
    func = getattr(mod, fname)
    result = func()
    # 正确行为：真实定时任务不应返回 stub 哨兵
    assert not _is_stub_result(result), (
        f"定时任务 {fname} 是 stub 假实现，调用返回 {result} —— "
        f"却被 scheduler_config 注册为 enabled cron 且监控记成功"
    )


def test_no_enabled_scheduler_job_is_backed_by_a_stub():
    """枚举全部注册任务，统计有多少 enabled 任务的 callable 落在 stub_tasks 模块。"""
    cfg = importlib.import_module("app.utils.scheduler_config")
    stub_backed = []
    for task in cfg.SCHEDULER_TASKS:
        if not task.get("enabled", True):
            continue
        try:
            module = importlib.import_module(task["module"])
            func = getattr(module, task["callable"])
        except Exception:
            continue
        if getattr(func, "__module__", "").endswith("stub_tasks"):
            stub_backed.append(task.get("id") or task.get("callable"))
    # 正确行为：不应有任何 enabled 定时任务由 stub 支撑
    assert not stub_backed, (
        f"{len(stub_backed)} 个 enabled 定时任务由 stub 假实现支撑："
        f"{stub_backed}"
    )
