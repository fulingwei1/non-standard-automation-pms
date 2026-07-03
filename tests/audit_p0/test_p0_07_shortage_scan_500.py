# -*- coding: utf-8 -*-
"""
P0-7: 智能缺料预警扫描端点修复前必 500。

smart_alert_engine.py 引用不存在的模型属性 WorkOrder.is_critical_path /
WorkOrder.planned_start_date / MaterialStock.available_qty，构建查询即抛
AttributeError，POST /shortage/smart-alerts/scan 无异常包裹 -> 500。

正确行为：扫描端点应正常返回（2xx），而不是 500。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def test_smart_alert_scan_does_not_500(api):
    r = api.post("/shortage/smart-alerts/scan", json={})
    assert r.status_code != 500, (
        f"缺料智能预警扫描端点返回 500（AttributeError: WorkOrder.is_critical_path 等）："
        f"{r.text[:300]}"
    )
    assert r.status_code < 500
