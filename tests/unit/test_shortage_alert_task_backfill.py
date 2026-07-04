# -*- coding: utf-8 -*-
"""APPR-04 回填契约：缺料预警定时任务接真实扫描引擎。

1. generate_shortage_alerts 不再返回 not_implemented——调 SmartAlertEngine.scan_and_alert
   并返回 success + 生成数量；引擎异常返回 error 哨兵（调度监控记失败）。
2. 调度配置解禁该任务（stub 时代默认禁用）。
3. stub 模块不再导出该任务（避免双定义漂移）。
"""
from unittest.mock import patch


def test_generate_shortage_alerts_calls_real_engine():
    from app.utils import scheduled_tasks

    with patch(
        "app.services.shortage.smart_alert_engine.SmartAlertEngine.scan_and_alert",
        return_value=[object(), object()],
    ) as mocked:
        result = scheduled_tasks.generate_shortage_alerts()

    assert mocked.called, "任务未调用真实扫描引擎"
    assert result["status"] == "success", f"仍是桩返回: {result}"
    assert result["alerts_created"] == 2


def test_generate_shortage_alerts_reports_error_on_engine_failure():
    from app.utils import scheduled_tasks

    with patch(
        "app.services.shortage.smart_alert_engine.SmartAlertEngine.scan_and_alert",
        side_effect=RuntimeError("引擎爆炸"),
    ):
        result = scheduled_tasks.generate_shortage_alerts()

    assert result["status"] == "error", "引擎失败必须返回 error 哨兵供调度监控记失败"
    assert "引擎爆炸" in result.get("message", "")


def test_shortage_alert_task_enabled_in_config():
    from app.utils.scheduler_config.shortage import SHORTAGE_TASKS

    task = next(t for t in SHORTAGE_TASKS if t["id"] == "generate_shortage_alerts")
    assert task["enabled"] is True, "任务已回填真实现，应解除 stub 时代的默认禁用"


def test_stub_module_no_longer_exports_shortage_alerts():
    from app.utils.scheduled_tasks import stub_tasks

    assert "generate_shortage_alerts" not in stub_tasks.__all__, "stub 模块不应再导出已回填任务"


def test_auto_trigger_urgent_purchase_calls_real_service():
    from app.utils import scheduled_tasks

    with patch(
        "app.services.urgent_purchase_from_shortage_service.auto_trigger_urgent_purchase_for_alerts",
        return_value={"checked_count": 3, "created_count": 1, "skipped_count": 2, "failed_count": 0},
    ) as mocked:
        result = scheduled_tasks.auto_trigger_urgent_purchase_from_shortage_alerts()

    assert mocked.called, "任务未调用真实触发服务"
    assert result["status"] == "success", f"仍是桩返回: {result}"
    assert result["created_count"] == 1


def test_auto_trigger_urgent_purchase_reports_error_on_failure():
    from app.utils import scheduled_tasks

    with patch(
        "app.services.urgent_purchase_from_shortage_service.auto_trigger_urgent_purchase_for_alerts",
        side_effect=RuntimeError("触发失败"),
    ):
        result = scheduled_tasks.auto_trigger_urgent_purchase_from_shortage_alerts()

    assert result["status"] == "error"
    assert "触发失败" in result.get("message", "")


def test_auto_trigger_task_enabled_and_out_of_stub():
    from app.utils.scheduled_tasks import stub_tasks
    from app.utils.scheduler_config.shortage import SHORTAGE_TASKS

    assert "auto_trigger_urgent_purchase_from_shortage_alerts" not in stub_tasks.__all__
    task = next(
        t for t in SHORTAGE_TASKS if t["id"] == "auto_trigger_urgent_purchase_from_shortage_alerts"
    )
    assert task["enabled"] is True, "PROD-15 已修，自动触发任务应解禁（申请进审批池，人审仍是闸门）"
