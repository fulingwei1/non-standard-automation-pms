# -*- coding: utf-8 -*-
"""
Unit tests for app/services/invoice_auto_service/creation.py (cov52)
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.invoice_auto_service.creation import (
        create_invoice_request,
        create_invoice_directly,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service(query_return=None):
    """Helper: create a mock service with a mock db."""
    service = MagicMock()
    service.db = MagicMock()
    if query_return is not None:
        service.db.query.return_value.filter.return_value.first.return_value = query_return
    return service


def _make_plan(contract_id=1, project_id=10, planned_amount=Decimal("1000"),
               planned_date=None, invoice_id=None, milestone_id=None):
    plan = MagicMock()
    plan.id = 1
    plan.contract_id = contract_id
    plan.project_id = project_id
    plan.planned_amount = planned_amount
    plan.planned_date = planned_date
    plan.invoice_id = invoice_id
    plan.milestone_id = milestone_id
    plan.project = MagicMock(project_name="TestProject")
    return plan


def _make_order(order_no="ORD-001", created_by=5):
    order = MagicMock()
    order.order_no = order_no
    order.created_by = created_by
    return order


def _make_milestone(milestone_name="FAT里程碑"):
    m = MagicMock()
    m.milestone_name = milestone_name
    return m


# ──────────────────────── create_invoice_request ────────────────────────

def test_create_invoice_request_existing_request():
    """如果已有 PENDING/APPROVED 申请，返回 success=False"""
    service = _make_service()
    existing = MagicMock(id=99)
    service.db.query.return_value.filter.return_value.first.return_value = existing

    plan = _make_plan()
    result = create_invoice_request(service, plan, _make_order(), _make_milestone())

    assert result["success"] is False
    assert "已存在" in result["message"]
    assert result["request_id"] == 99


def test_create_invoice_request_no_contract():
    """收款计划无合同时返回 success=False"""
    service = _make_service()
    # 第一次查 InvoiceRequest → None（无已有申请）
    # 第二次查 Contract → None（无合同）
    service.db.query.return_value.filter.return_value.first.side_effect = [None, None]

    plan = _make_plan(contract_id=1)
    result = create_invoice_request(service, plan, _make_order(), _make_milestone())

    assert result["success"] is False
    assert "合同" in result["message"]


def test_create_invoice_request_no_contract_id():
    """plan.contract_id 为 None 时返回 success=False"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    plan = _make_plan(contract_id=None)
    result = create_invoice_request(service, plan, _make_order(), _make_milestone())

    assert result["success"] is False


@patch("app.services.invoice_auto_service.creation.apply_like_filter")
def test_create_invoice_request_success(mock_alf):
    """正常创建发票申请场景"""
    service = _make_service()
    # 第一次 filter: 无已有申请
    # 第二次 filter: 找到合同
    contract = MagicMock(id=1, customer_id=2, owner_id=3)
    contract.customer = MagicMock(customer_name="客户A", tax_no="123")
    service.db.query.return_value.filter.return_value.first.side_effect = [None, contract]

    mock_query = MagicMock()
    mock_query.order_by.return_value.first.return_value = None
    mock_alf.return_value = mock_query

    plan = _make_plan(planned_amount=Decimal("1000"))
    result = create_invoice_request(service, plan, _make_order(), _make_milestone())

    assert result["success"] is True
    assert "request_no" in result
    assert result["amount"] > 0
    service.db.add.assert_called_once()
    service.db.flush.assert_called_once()


# ──────────────────────── create_invoice_directly ────────────────────────

def test_create_invoice_directly_already_invoiced():
    """plan.invoice_id 非空时返回 success=False"""
    service = _make_service()
    plan = _make_plan(invoice_id=77)
    result = create_invoice_directly(service, plan, _make_order(), _make_milestone())

    assert result["success"] is False
    assert "已开票" in result["message"]


def test_create_invoice_directly_no_contract():
    """无合同时返回 success=False"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    plan = _make_plan(invoice_id=None)
    result = create_invoice_directly(service, plan, _make_order(), _make_milestone())

    assert result["success"] is False


@patch("app.services.invoice_auto_service.creation.desc")
@patch("app.services.invoice_auto_service.creation.Invoice")
@patch("app.services.invoice_auto_service.creation.apply_like_filter")
def test_create_invoice_directly_success(mock_alf, mock_invoice_cls, mock_desc):
    """正常直接创建发票场景"""
    service = _make_service()
    contract = MagicMock(id=1, customer_id=2, owner_id=3)
    contract.customer = MagicMock(customer_name="客户B", tax_no="456")
    service.db.query.return_value.filter.return_value.first.return_value = contract

    mock_query = MagicMock()
    mock_query.order_by.return_value.first.return_value = None
    mock_alf.return_value = mock_query

    mock_invoice = MagicMock(id=42)
    mock_invoice_cls.return_value = mock_invoice

    plan = _make_plan(invoice_id=None, planned_amount=Decimal("2000"))
    result = create_invoice_directly(service, plan, _make_order(), _make_milestone())

    assert result["success"] is True
    assert "invoice_code" in result
    assert result["amount"] > 0
    service.db.add.assert_called_once()
    service.db.flush.assert_called_once()
    # 更新收款计划字段
    assert plan.invoice_id is not None
