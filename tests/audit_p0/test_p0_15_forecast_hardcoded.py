# -*- coding: utf-8 -*-
"""
P0-15: 销售预测线上接口整文件硬编码，真算法服务是死代码。

sales/sales_forecast.py 全文件 0 次 db 查询：actual_revenue 写死 28500000、
团队写死『华南大区』等常量，与沙箱库真实数据无关。

正确行为：预测接口应基于真实数据，返回值不应等于这些写死常量。
"""
import pytest

pytestmark = pytest.mark.audit_p0

HARDCODED_REVENUE = 28500000
HARDCODED_TEAM = "华南大区"


def test_company_overview_is_not_hardcoded(api):
    r = api.get("/sales/forecast/forecast/company-overview")
    assert r.status_code == 200, r.text
    data = r.json()
    actual = data.get("targets", {}).get("actual_revenue")
    assert actual != HARDCODED_REVENUE, (
        f"company-overview 的 actual_revenue 恒为写死常量 {HARDCODED_REVENUE}，与沙箱库无关"
    )


def test_executive_dashboard_is_not_hardcoded(api):
    r = api.get("/sales/forecast/forecast/executive-dashboard")
    assert r.status_code == 200, r.text
    text = r.text
    hits = [c for c in (str(HARDCODED_REVENUE), HARDCODED_TEAM) if c in text]
    assert not hits, (
        f"executive-dashboard 含写死常量 {hits}（如 {HARDCODED_REVENUE}/{HARDCODED_TEAM}）"
        f" -> 管理层看板为编造数字"
    )
