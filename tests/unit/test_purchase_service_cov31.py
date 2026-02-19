# -*- coding: utf-8 -*-
"""
Unit tests for PurchaseService (第三十一批)
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.purchase.purchase_service import PurchaseService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return PurchaseService(db=mock_db)


def _make_query_chain(mock_db, return_value):
    """Helper: db.query(...).options(...).filter(...).order_by(...).all() → return_value"""
    chain = MagicMock()
    mock_db.query.return_value = chain
    chain.options.return_value = chain
    chain.filter.return_value = chain
    chain.order_by.return_value = chain

    with patch(
        "app.services.purchase.purchase_service.apply_pagination",
        return_value=chain,
    ):
        chain.all.return_value = return_value
    return chain


# ---------------------------------------------------------------------------
# get_purchase_orders
# ---------------------------------------------------------------------------

class TestGetPurchaseOrders:
    def test_returns_list_no_filters(self, service, mock_db):
        order = MagicMock()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.options.return_value = chain
        chain.order_by.return_value = chain

        with patch(
            "app.services.purchase.purchase_service.apply_pagination",
            return_value=chain,
        ):
            chain.all.return_value = [order]
            result = service.get_purchase_orders()

        assert result == [order]

    def test_applies_project_id_filter(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.options.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain

        with patch(
            "app.services.purchase.purchase_service.apply_pagination",
            return_value=chain,
        ):
            chain.all.return_value = []
            result = service.get_purchase_orders(project_id=10)

        assert chain.filter.called
        assert result == []

    def test_applies_status_filter(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.options.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain

        with patch(
            "app.services.purchase.purchase_service.apply_pagination",
            return_value=chain,
        ):
            chain.all.return_value = []
            service.get_purchase_orders(status="APPROVED")

        assert chain.filter.called


# ---------------------------------------------------------------------------
# get_purchase_order_by_id
# ---------------------------------------------------------------------------

class TestGetPurchaseOrderById:
    def test_returns_order_when_found(self, service, mock_db):
        order = MagicMock()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.options.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = order

        result = service.get_purchase_order_by_id(1)
        assert result == order

    def test_returns_none_when_not_found(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.options.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None

        result = service.get_purchase_order_by_id(999)
        assert result is None


# ---------------------------------------------------------------------------
# create_purchase_order
# ---------------------------------------------------------------------------

class TestCreatePurchaseOrder:
    def test_creates_order_and_adds_to_db(self, service, mock_db):
        order_data = {
            "order_code": "PO-001",
            "supplier_id": 5,
            "project_id": 3,
            "total_amount": 10000,
            "items": [],
        }

        with patch(
            "app.services.purchase.purchase_service.PurchaseOrder"
        ) as MockOrder:
            mock_order = MagicMock()
            mock_order.id = 1
            MockOrder.return_value = mock_order

            result = service.create_purchase_order(order_data)

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert result == mock_order

    def test_creates_order_items(self, service, mock_db):
        order_data = {
            "order_no": "PO-002",
            "supplier_id": 2,
            "items": [
                {"material_id": 10, "material_code": "M001", "quantity": 5, "unit_price": 100},
            ],
        }

        with patch("app.services.purchase.purchase_service.PurchaseOrder") as MockOrder, \
             patch("app.services.purchase.purchase_service.PurchaseOrderItem") as MockItem:
            mock_order = MagicMock()
            mock_order.id = 1
            MockOrder.return_value = mock_order
            mock_item = MagicMock()
            MockItem.return_value = mock_item

            service.create_purchase_order(order_data)

        MockItem.assert_called_once()
        assert mock_db.add.call_count == 2  # order + item


# ---------------------------------------------------------------------------
# submit_purchase_order / approve_purchase_order
# ---------------------------------------------------------------------------

class TestSubmitAndApprove:
    def test_submit_returns_false_when_not_found(self, service, mock_db):
        with patch.object(service, "get_purchase_order_by_id", return_value=None):
            result = service.submit_purchase_order(999)
        assert result is False

    def test_submit_sets_status_submitted(self, service, mock_db):
        order = MagicMock()
        with patch.object(service, "get_purchase_order_by_id", return_value=order):
            result = service.submit_purchase_order(1)
        assert result is True
        assert order.status == "SUBMITTED"

    def test_approve_returns_false_when_not_found(self, service, mock_db):
        with patch.object(service, "get_purchase_order_by_id", return_value=None):
            result = service.approve_purchase_order(999, approver_id=1)
        assert result is False

    def test_approve_sets_status_approved(self, service, mock_db):
        order = MagicMock()
        with patch.object(service, "get_purchase_order_by_id", return_value=order):
            result = service.approve_purchase_order(1, approver_id=7)
        assert result is True
        assert order.status == "APPROVED"
        assert order.approver_id == 7
