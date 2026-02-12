# -*- coding: utf-8 -*-
"""Tests for app/services/approval_engine/adapters/outsourcing.py"""
from unittest.mock import MagicMock

from app.services.approval_engine.adapters.outsourcing import OutsourcingOrderApprovalAdapter


class TestOutsourcingOrderApprovalAdapter:
    def setup_method(self):
        self.db = MagicMock()
        self.adapter = OutsourcingOrderApprovalAdapter(self.db)

    def test_entity_type(self):
        assert self.adapter.entity_type == "OUTSOURCING_ORDER"

    def test_get_entity_found(self):
        mock_order = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        result = self.adapter.get_entity(1)
        assert result == mock_order

    def test_get_entity_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.adapter.get_entity(999)
        assert result is None

    def test_get_entity_data_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.adapter.get_entity_data(999)
        assert result == {} or result is not None

    def test_on_submit(self):
        mock_order = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        instance = MagicMock()
        self.adapter.on_submit(1, instance)
        # Should update order status

    def test_on_approved(self):
        mock_order = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        instance = MagicMock()
        self.adapter.on_approved(1, instance)

    def test_on_rejected(self):
        mock_order = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        instance = MagicMock()
        self.adapter.on_rejected(1, instance)

    def test_on_withdrawn(self):
        mock_order = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        instance = MagicMock()
        self.adapter.on_withdrawn(1, instance)

    def test_generate_title(self):
        mock_order = MagicMock()
        mock_order.order_no = "OS-001"
        mock_order.vendor = MagicMock()
        mock_order.vendor.vendor_name = "TestVendor"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order
        result = self.adapter.generate_title(1)
        assert isinstance(result, str)
