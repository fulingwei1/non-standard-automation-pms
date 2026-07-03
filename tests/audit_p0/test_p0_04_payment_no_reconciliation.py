# -*- coding: utf-8 -*-
"""
P0-4: 回款登记无勾稽、无上限。

payment_records.py:312-314 `new_paid = current_paid + amount` 无上限校验，
按合同取第一张 ISSUED 发票登记，可把 paid_amount 累加到远超发票额（unpaid 变负）。

注意与静态报告的偏差：负数金额现已被 schema `Field(gt=0)` 拦截（见
test_negative_amount_is_rejected 通过），但“超额无上限”仍成立。
"""
import pytest

pytestmark = pytest.mark.audit_p0


def _contract_with_issued_invoice(conn):
    return conn.execute(
        "SELECT i.contract_id, i.id, i.total_amount FROM invoices i "
        "WHERE i.status='ISSUED' AND i.contract_id IS NOT NULL "
        "AND i.total_amount IS NOT NULL AND i.total_amount>0 "
        "ORDER BY i.contract_id, i.id LIMIT 1"
    ).fetchone()


def test_overpayment_beyond_invoice_amount_is_rejected(api, sandbox_conn):
    row = _contract_with_issued_invoice(sandbox_conn)
    if not row:
        pytest.skip("沙箱库无带金额的 ISSUED 发票")
    contract_id, invoice_id, invoice_total = row
    over = float(invoice_total) * 100 + 1_000_000

    r = api.post(
        "/sales/payments/records",
        json={"contract_id": contract_id, "payment_date": "2026-07-03", "amount": over},
    )
    # 正确行为：累计回款超过发票金额应被拒绝（勾稽上限）
    assert r.status_code >= 400, (
        f"回款 {over} 远超发票额 {invoice_total} 仍登记成功（HTTP {r.status_code}）："
        f"{r.text[:250]} -> 无金额勾稽/无上限"
    )


def test_negative_amount_is_rejected(api, sandbox_conn):
    """偏差记录：负数金额现已被 schema 拦截（此用例现在就应通过）。"""
    row = _contract_with_issued_invoice(sandbox_conn)
    if not row:
        pytest.skip("沙箱库无带金额的 ISSUED 发票")
    contract_id = row[0]
    r = api.post(
        "/sales/payments/records",
        json={"contract_id": contract_id, "payment_date": "2026-07-03", "amount": -1000},
    )
    assert r.status_code >= 400, f"负数回款竟被接受: HTTP {r.status_code} {r.text[:200]}"
