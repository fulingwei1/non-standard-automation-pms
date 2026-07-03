# -*- coding: utf-8 -*-
"""外出服务工作日志自动生成测试"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.services.field_service_work_log_service import (
    build_field_service_context_item,
    build_work_log_create_from_dispatch_orders,
)


def _order(**overrides):
    project = SimpleNamespace(id=12, project_name="售后外出项目")
    machine = SimpleNamespace(id=34, machine_name="ATE-01", machine_code="MC-01")
    base = {
        "id": 56,
        "order_no": "INST-LOG-001",
        "project_id": project.id,
        "project": project,
        "machine_id": machine.id,
        "machine": machine,
        "customer_id": 78,
        "customer": SimpleNamespace(id=78, customer_name="测试客户"),
        "task_type": "INSTALLATION",
        "task_title": "现场安装调试",
        "task_description": "完成安装、接线、通电检查",
        "location": "深圳客户现场",
        "scheduled_date": date(2035, 1, 12),
        "estimated_hours": Decimal("7.5"),
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "progress": 35,
        "execution_notes": "已到场并完成设备定位",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_build_field_service_context_item_links_dispatch_project_and_machine():
    item = build_field_service_context_item(_order())

    assert item["dispatch_order_id"] == 56
    assert item["order_no"] == "INST-LOG-001"
    assert item["project_id"] == 12
    assert item["project_name"] == "售后外出项目"
    assert item["machine_id"] == 34
    assert item["machine_name"] == "ATE-01"
    assert "现场安装调试" in item["default_content"]
    assert "已到场并完成设备定位" in item["default_content"]


def test_build_work_log_create_from_dispatch_orders_auto_mentions_and_content():
    payload = build_work_log_create_from_dispatch_orders(
        [_order()],
        work_date=date(2035, 1, 12),
        today_progress="完成电气接线和通电检查",
        issues_found="暂无异常",
        next_plan="明天进行联机调试",
        work_hours=Decimal("7.5"),
    )

    assert payload.work_date == date(2035, 1, 12)
    assert payload.mentioned_projects == [12]
    assert payload.mentioned_machines == [34]
    assert payload.project_id == 12
    assert payload.work_hours == Decimal("7.5")
    assert "INST-LOG-001" in payload.content
    assert "完成电气接线和通电检查" in payload.content
    assert len(payload.content) <= 300
