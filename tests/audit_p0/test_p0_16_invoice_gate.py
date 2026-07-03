# -*- coding: utf-8 -*-
"""
P0-16: 发票门禁形同虚设。

16a 未审批可开票：/issue 门禁查旧轨空表 ApprovalRecord，查不到就放行
    （invoices/operations.py:47-58）——无审批实例的发票可直接开票。
16b 通用 PUT 绕状态机：PUT /invoices/{id} 直接 setattr status，作废(CANCELLED)发票
    可被改回 ISSUED（basic.py:302-340）。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def test_issue_requires_an_approved_instance(api, sandbox_conn):
    row = sandbox_conn.execute(
        "SELECT id FROM invoices WHERE approval_instance_id IS NULL "
        "AND (status IS NULL OR status NOT IN ('ISSUED','PAID','CANCELLED')) "
        "ORDER BY id LIMIT 1"
    ).fetchone()
    if not row:
        pytest.skip("沙箱库无『无审批实例且未开票』的发票")
    inv_id = row[0]

    r = api.post(f"/sales/invoices/{inv_id}/issue", json={"issue_date": "2026-07-03"})
    # 正确行为：无已通过审批实例的发票不得开票
    assert r.status_code >= 400, (
        f"发票 {inv_id} 无审批实例仍开票成功（HTTP {r.status_code}）："
        f"{r.text[:200]} -> 资金前置校验形同虚设"
    )


def test_cancelled_invoice_cannot_be_revived_to_issued(api, sandbox_conn):
    row = sandbox_conn.execute(
        "SELECT id FROM invoices WHERE approval_instance_id IS NULL "
        "AND (status IS NULL OR status NOT IN ('CANCELLED')) "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        pytest.skip("沙箱库无可用发票")
    inv_id = row[0]

    r1 = api.put(f"/sales/invoices/{inv_id}", json={"status": "CANCELLED"})
    assert r1.status_code == 200, f"作废失败无法继续验证: {r1.text[:200]}"

    r2 = api.put(f"/sales/invoices/{inv_id}", json={"status": "ISSUED"})
    # 正确行为：已作废发票不允许通过通用 PUT 改回 ISSUED
    assert r2.status_code >= 400, (
        f"作废发票 {inv_id} 被 PUT 改回 ISSUED 成功（HTTP {r2.status_code}）："
        f"{r2.text[:200]} -> 通用 PUT 击穿状态机"
    )
