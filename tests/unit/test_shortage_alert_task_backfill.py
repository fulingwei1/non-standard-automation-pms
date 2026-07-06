# -*- coding: utf-8 -*-
"""APPR-04 回填契约：缺料预警/日报定时任务接真实业务入口。

1. generate_shortage_alerts 不再返回 not_implemented——调 SmartAlertEngine.scan_and_alert
   并返回 success + 生成数量；引擎异常返回 error 哨兵（调度监控记失败）。
2. generate_shortage_daily_report 写入 mat_shortage_daily_report，不再是 ghost table。
3. 调度配置解禁已回填任务（stub 时代默认禁用）。
4. stub 模块不再导出已回填任务（避免双定义漂移）。
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy.orm import sessionmaker

from app.models.alert import AlertRecord
from app.models.shortage import KitCheck, MaterialArrival, ShortageDailyReport, ShortageReport


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
    assert "alert_records" in task["dependencies_tables"]
    assert "mat_shortage_alert" not in task["dependencies_tables"]


def test_generate_shortage_daily_report_writes_snapshot(db_session, monkeypatch):
    from app.models import base as base_module
    from app.utils import scheduled_tasks

    target_date = date(2026, 7, 3)
    start = datetime.combine(target_date, datetime.min.time())

    db_session.add_all(
        [
            AlertRecord(
                alert_no="SHORT-DAILY-001",
                rule_id=1,
                target_type="SHORTAGE",
                target_id=1,
                alert_level="WARNING",
                alert_title="物料短缺",
                alert_content="M-001 缺料",
                alert_data={"impact_type": "stop", "estimated_delay_days": 2},
                status="PENDING",
                created_at=start + timedelta(hours=8),
                triggered_at=start + timedelta(hours=8),
                handle_start_at=start + timedelta(hours=8, minutes=20),
            ),
            AlertRecord(
                alert_no="SHORT-DAILY-002",
                rule_id=1,
                target_type="SHORTAGE",
                target_id=2,
                alert_level="URGENT",
                alert_title="紧急缺料",
                alert_content="M-002 缺料",
                status="RESOLVED",
                created_at=start - timedelta(days=1),
                triggered_at=start - timedelta(days=1),
                handle_end_at=start + timedelta(hours=9),
            ),
            ShortageReport(
                report_no="SR-DAILY-001",
                project_id=1,
                reporter_id=1,
                report_time=start + timedelta(hours=9),
                material_id=1,
                material_code="M-001",
                material_name="轴承",
                required_qty=Decimal("10"),
                shortage_qty=Decimal("4"),
            ),
            ShortageReport(
                report_no="SR-DAILY-002",
                project_id=1,
                reporter_id=1,
                report_time=start - timedelta(days=1),
                material_id=2,
                material_code="M-002",
                material_name="导轨",
                required_qty=Decimal("5"),
                shortage_qty=Decimal("2"),
                status="RESOLVED",
                resolved_at=start + timedelta(hours=10),
            ),
            KitCheck(
                check_no="KC-DAILY-001",
                check_type="work_order",
                kit_status="complete",
                kit_rate=Decimal("100"),
                check_time=start + timedelta(hours=7),
            ),
            KitCheck(
                check_no="KC-DAILY-002",
                check_type="work_order",
                kit_status="partial",
                kit_rate=Decimal("50"),
                check_time=start + timedelta(hours=7, minutes=30),
            ),
            MaterialArrival(
                arrival_no="MA-DAILY-001",
                material_id=1,
                material_code="M-001",
                material_name="轴承",
                expected_qty=Decimal("10"),
                expected_date=target_date,
                actual_date=target_date,
                is_delayed=False,
            ),
            MaterialArrival(
                arrival_no="MA-DAILY-002",
                material_id=2,
                material_code="M-002",
                material_name="导轨",
                expected_qty=Decimal("5"),
                expected_date=target_date - timedelta(days=1),
                actual_date=target_date,
                is_delayed=True,
            ),
        ]
    )
    db_session.commit()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_session.get_bind())
    monkeypatch.setattr(base_module, "get_session", TestingSessionLocal)

    result = scheduled_tasks.generate_shortage_daily_report(target_date=target_date)

    assert result["status"] == "success", f"仍是桩返回或未写表: {result}"
    assert result["report_date"] == target_date.isoformat()
    db_session.expire_all()
    report = (
        db_session.query(ShortageDailyReport)
        .filter(ShortageDailyReport.report_date == target_date)
        .one()
    )
    assert report.new_alerts == 1
    assert report.resolved_alerts == 1
    assert report.pending_alerts == 1
    assert report.level2_count == 1
    assert report.level4_count == 1
    assert report.new_reports == 1
    assert report.resolved_reports == 1
    assert report.total_work_orders == 2
    assert report.kit_complete_count == 1
    assert float(report.kit_rate) == 75.0
    assert report.expected_arrivals == 1
    assert report.actual_arrivals == 2
    assert report.delayed_arrivals == 1
    assert float(report.on_time_rate) == 50.0
    assert report.avg_response_minutes == 20
    assert float(report.stoppage_hours) == 48.0

    second = scheduled_tasks.generate_shortage_daily_report(target_date=target_date)
    assert second["status"] == "success"
    assert (
        db_session.query(ShortageDailyReport)
        .filter(ShortageDailyReport.report_date == target_date)
        .count()
        == 1
    ), "日报任务应按日期更新同一条记录，不能重复插入"


def test_shortage_daily_report_task_enabled_and_out_of_stub():
    from app.utils.scheduled_tasks import stub_tasks
    from app.utils.scheduler_config.shortage import SHORTAGE_TASKS

    assert "generate_shortage_daily_report" not in stub_tasks.__all__
    task = next(t for t in SHORTAGE_TASKS if t["id"] == "generate_shortage_daily_report")
    assert task["enabled"] is True, "缺料日报已回填真实写表入口，应解除 stub 时代禁用"
