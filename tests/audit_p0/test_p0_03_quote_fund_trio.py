# -*- coding: utf-8 -*-
"""
P0-3: 报价资金三连。

3a 状态直改端点绕审批：POST /quotes/{id}/status 无权限门禁，任意登录用户可
    DRAFT -> PENDING_APPROVAL -> APPROVED 自助批准（quote_status.py:119-153）。
3b 审批后仍可改明细：PUT /quotes/items/{id} 对已 APPROVED 版本无状态门禁
    （quote_items.py），改后版本总额也不重算。
3c 成本汇总漏乘数量：cost-breakdown 的 total_cost = Σ item_cost（未乘 qty），
    而售价侧 Σ qty*unit_price 已乘，导致毛利虚高（quote_costs.py:431）。

三条都断言“正确行为”，当前必然失败。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def _first_where(conn, sql):
    row = conn.execute(sql).fetchone()
    return row


# ---------------------------------------------------------------- 3a
def test_quote_status_endpoint_must_not_self_approve(api, sandbox_conn):
    row = _first_where(sandbox_conn, "SELECT id FROM quotes WHERE status='DRAFT' LIMIT 1")
    if not row:
        pytest.skip("沙箱库无 DRAFT 报价")
    qid = row[0]

    r1 = api.post(f"/sales/quotes/{qid}/status", json={"new_status": "PENDING_APPROVAL"})
    assert r1.status_code == 200, r1.text  # 进入待审批本身允许

    r2 = api.post(f"/sales/quotes/{qid}/status", json={"new_status": "APPROVED"})
    # 正确行为：PENDING_APPROVAL -> APPROVED 必须经审批引擎，直改端点应拒绝
    assert r2.status_code >= 400, (
        f"报价状态直改端点允许 PENDING_APPROVAL->APPROVED 自助批准（HTTP {r2.status_code}），"
        f"绕过审批工作流：{r2.text[:200]}"
    )


# ---------------------------------------------------------------- 3b
def test_items_of_approved_quote_must_be_locked(api, sandbox_conn):
    row = _first_where(
        sandbox_conn,
        "SELECT qi.id FROM quote_items qi JOIN quote_versions qv "
        "ON qv.id=qi.quote_version_id WHERE qv.status='APPROVED' LIMIT 1",
    )
    if not row:
        pytest.skip("沙箱库无 APPROVED 版本明细")
    item_id = row[0]

    r = api.put(f"/sales/quotes/items/{item_id}", json={"unit_price": 123456})
    # 正确行为：已审批版本的明细应被冻结，编辑请求应被拒绝
    assert r.status_code >= 400, (
        f"已 APPROVED 版本的明细仍可被 PUT 修改（HTTP {r.status_code}），"
        f"审批金额/明细/合同额可脱节：{r.text[:200]}"
    )


# ---------------------------------------------------------------- 3c
def test_cost_breakdown_multiplies_by_quantity(api, sandbox_conn):
    row = _first_where(
        sandbox_conn,
        "SELECT qv.quote_id FROM quote_items qi JOIN quote_versions qv "
        "ON qv.id=qi.quote_version_id WHERE qi.qty>1 AND qi.cost>0 "
        "GROUP BY qv.quote_id LIMIT 1",
    )
    if not row:
        pytest.skip("沙箱库无 qty>1 且有成本的报价明细")
    qid = row[0]

    r = api.get(f"/sales/quotes/{qid}/cost-breakdown")
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    items = [it for cat in data.get("breakdown", []) for it in cat.get("items", [])]
    assert items, f"cost-breakdown 无明细项: {data}"

    reported = round(float(data["total_cost"]), 2)
    expected_with_qty = round(sum((it.get("qty") or 0) * (it.get("cost") or 0) for it in items), 2)
    sum_without_qty = round(sum(it.get("cost") or 0 for it in items), 2)

    # 正确行为：汇总成本应乘以数量
    assert reported == pytest.approx(expected_with_qty, rel=0.01), (
        f"total_cost 漏乘 qty：接口返回 {reported}，应为 Σ(qty*cost)={expected_with_qty}，"
        f"实际等于 Σ(cost)={sum_without_qty} -> 成本被低估、毛利虚高"
    )
