# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - approval_engine/adapters/purchase.py
"""
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.approval_engine.adapters.purchase",
                    reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def adapter(mock_db):
    from app.services.approval_engine.adapters.purchase import PurchaseOrderApprovalAdapter
    return PurchaseOrderApprovalAdapter(mock_db)


def _make_order(**kwargs):
    order = MagicMock()
    order.id = kwargs.get("id", 1)
    order.order_no = kwargs.get("order_no", "PO2024001")
    order.order_title = kwargs.get("order_title", "测试采购订单")
    order.order_type = kwargs.get("order_type", "NORMAL")
    order.status = kwargs.get("status", "DRAFT")
    order.total_amount = kwargs.get("total_amount", 10000)
    order.tax_rate = kwargs.get("tax_rate", 13)
    order.tax_amount = kwargs.get("tax_amount", 1300)
    order.amount_with_tax = kwargs.get("amount_with_tax", 11300)
    order.currency = "CNY"
    order.order_date = kwargs.get("order_date", date(2024, 1, 1))
    order.required_date = kwargs.get("required_date", date(2024, 3, 1))
    order.promised_date = None
    order.payment_terms = "30天"
    order.project_id = kwargs.get("project_id", None)
    order.supplier_id = kwargs.get("supplier_id", 10)
    order.source_request_id = None
    order.created_by = 1
    order.contract_no = None
    order.vendor_id = kwargs.get("vendor_id", 10)
    order.submitted_at = None
    order.approved_by = None
    order.approved_at = None
    order.approval_note = None
    return order


class TestPurchaseAdapterGetEntity:

    def test_get_entity_returns_order(self, adapter, mock_db):
        order = _make_order()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = order

        result = adapter.get_entity(1)
        assert result is order

    def test_get_entity_returns_none(self, adapter, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = adapter.get_entity(999)
        assert result is None


class TestPurchaseAdapterGetEntityData:

    def test_get_entity_data_returns_dict(self, adapter, mock_db):
        order = _make_order(vendor_id=10)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = order
        mock_query.count.return_value = 3

        vendor = MagicMock(vendor_name="供应商A", vendor_code="V001")
        mock_db.query.side_effect = [mock_query, mock_query, mock_query, mock_query]

        with patch.object(adapter, "get_entity", return_value=order):
            # item_count
            item_mock = MagicMock()
            mock_db.query.return_value = item_mock
            item_mock.filter.return_value = item_mock
            item_mock.count.return_value = 3
            item_mock.first.return_value = vendor

            data = adapter.get_entity_data(1)
            assert "order_no" in data
            assert data["order_no"] == "PO2024001"

    def test_get_entity_data_empty_when_no_order(self, adapter, mock_db):
        with patch.object(adapter, "get_entity", return_value=None):
            data = adapter.get_entity_data(999)
            assert data == {}


class TestPurchaseAdapterCallbacks:

    def test_on_submit_sets_pending(self, adapter, mock_db):
        order = _make_order()
        instance = MagicMock()
        with patch.object(adapter, "get_entity", return_value=order):
            adapter.on_submit(1, instance)
            assert order.status == "PENDING_APPROVAL"

    def test_on_approved_sets_approved(self, adapter, mock_db):
        order = _make_order()
        instance = MagicMock(approved_by=2)
        with patch.object(adapter, "get_entity", return_value=order):
            adapter.on_approved(1, instance)
            assert order.status == "APPROVED"

    def test_on_rejected_sets_rejected(self, adapter, mock_db):
        order = _make_order()
        instance = MagicMock()
        with patch.object(adapter, "get_entity", return_value=order):
            adapter.on_rejected(1, instance)
            assert order.status == "REJECTED"

    def test_on_withdrawn_resets_to_draft(self, adapter, mock_db):
        order = _make_order(status="PENDING_APPROVAL")
        instance = MagicMock()
        with patch.object(adapter, "get_entity", return_value=order):
            adapter.on_withdrawn(1, instance)
            assert order.status == "DRAFT"


class TestPurchaseAdapterValidateSubmit:

    def test_validate_no_order(self, adapter):
        with patch.object(adapter, "get_entity", return_value=None):
            ok, msg = adapter.validate_submit(999)
            assert not ok
            assert "不存在" in msg

    def test_validate_invalid_status(self, adapter):
        order = _make_order(status="APPROVED")
        with patch.object(adapter, "get_entity", return_value=order):
            ok, msg = adapter.validate_submit(1)
            assert not ok

    def test_validate_no_supplier(self, adapter, mock_db):
        order = _make_order(status="DRAFT", supplier_id=None)
        order.supplier_id = None
        with patch.object(adapter, "get_entity", return_value=order):
            ok, msg = adapter.validate_submit(1)
            assert not ok
            assert "供应商" in msg

    def test_generate_title_includes_order_no(self, adapter):
        order = _make_order()
        with patch.object(adapter, "get_entity", return_value=order):
            title = adapter.generate_title(1)
            assert "PO2024001" in title
