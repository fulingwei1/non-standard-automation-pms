# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/invoice_auto_service/creation.py
"""
import pytest

pytest.importorskip("app.services.invoice_auto_service.creation")

from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.invoice_auto_service.creation import (
    create_invoice_request,
    create_invoice_directly,
)


def make_service():
    svc = MagicMock()
    svc.db = MagicMock()
    return svc


# ── 1. create_invoice_request: 已有发票申请 ───────────────────────────────────
def test_create_invoice_request_already_exists():
    svc = make_service()
    existing = MagicMock()
    existing.id = 7
    svc.db.query.return_value.filter.return_value.first.return_value = existing

    plan = MagicMock()
    plan.id = 1
    order = MagicMock()
    milestone = MagicMock()

    result = create_invoice_request(svc, plan, order, milestone)
    assert result["success"] is False
    assert "已存在" in result["message"]
    assert result["request_id"] == 7


# ── 2. create_invoice_request: 无合同 ────────────────────────────────────────
def test_create_invoice_request_no_contract():
    svc = make_service()

    # 先返回 None（无现有申请），再返回 None（无合同）
    svc.db.query.return_value.filter.return_value.first.side_effect = [None, None]

    plan = MagicMock()
    plan.id = 2
    plan.contract_id = 99
    order = MagicMock()
    milestone = MagicMock()

    result = create_invoice_request(svc, plan, order, milestone)
    assert result["success"] is False
    assert "合同" in result["message"]


# ── 3. create_invoice_request: 成功创建 ───────────────────────────────────────
def test_create_invoice_request_success():
    svc = make_service()

    contract = MagicMock()
    contract.id = 10
    contract.customer_id = 3
    contract.customer.customer_name = "测试客户"

    project = MagicMock()
    project.project_name = "测试项目"

    plan = MagicMock()
    plan.id = 1
    plan.contract_id = 10
    plan.project_id = 5
    plan.project = project
    plan.planned_amount = Decimal("10000")
    plan.planned_date = None
    plan.invoice_id = None

    order = MagicMock()
    order.order_no = "ACC-001"
    order.created_by = 1

    milestone = MagicMock()
    milestone.milestone_name = "FAT通过"

    # query chain: first=None(no existing), then contract, then for request_no query
    q_none = MagicMock()
    q_none.filter.return_value.first.return_value = None

    q_contract = MagicMock()
    q_contract.filter.return_value.first.return_value = contract

    q_seq = MagicMock()
    q_seq.order_by.return_value.first.return_value = None

    svc.db.query.side_effect = [q_none, q_contract, q_seq]

    with patch("app.services.invoice_auto_service.creation.apply_like_filter") as mock_lf:
        mock_lf.return_value = q_seq
        result = create_invoice_request(svc, plan, order, milestone)

    assert result["success"] is True
    assert "request_no" in result
    svc.db.add.assert_called_once()
    svc.db.flush.assert_called_once()


# ── 4. create_invoice_directly: 已有发票 ─────────────────────────────────────
def test_create_invoice_directly_already_invoiced():
    svc = make_service()
    plan = MagicMock()
    plan.invoice_id = 55

    result = create_invoice_directly(svc, plan, MagicMock(), MagicMock())
    assert result["success"] is False
    assert "已开票" in result["message"]


# ── 5. create_invoice_directly: 无合同 ───────────────────────────────────────
def test_create_invoice_directly_no_contract():
    svc = make_service()
    plan = MagicMock()
    plan.invoice_id = None
    plan.contract_id = 88
    svc.db.query.return_value.filter.return_value.first.return_value = None

    result = create_invoice_directly(svc, plan, MagicMock(), MagicMock())
    assert result["success"] is False
    assert "合同" in result["message"]


# ── 6. create_invoice_directly: 成功创建 ─────────────────────────────────────
def test_create_invoice_directly_success():
    svc = make_service()
    contract = MagicMock()
    contract.id = 20
    contract.customer.customer_name = "客户A"
    contract.customer.tax_no = "123456"
    contract.owner_id = 2

    plan = MagicMock()
    plan.invoice_id = None
    plan.contract_id = 20
    plan.project_id = 3
    plan.planned_amount = Decimal("5000")
    plan.planned_date = None

    q_contract = MagicMock()
    q_contract.filter.return_value.first.return_value = contract

    q_seq = MagicMock()
    q_seq.order_by.return_value.first.return_value = None

    svc.db.query.side_effect = [q_contract, q_seq]

    mock_invoice = MagicMock()
    mock_invoice.id = 101

    with patch("app.services.invoice_auto_service.creation.apply_like_filter") as mock_lf, \
         patch("app.services.invoice_auto_service.creation.Invoice", return_value=mock_invoice):
        mock_lf.return_value = q_seq
        result = create_invoice_directly(svc, plan, MagicMock(), MagicMock())

    assert result["success"] is True
    assert "invoice_code" in result
    svc.db.add.assert_called()  # invoice was added
