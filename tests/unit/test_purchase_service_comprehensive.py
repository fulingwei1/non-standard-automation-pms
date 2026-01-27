# -*- coding: utf-8 -*-
"""
Tests for PurchaseService
Covers: app/services/purchase/purchase_service.py
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.purchase.purchase_service import PurchaseService
from app.models.purchase import PurchaseOrder, PurchaseRequest, GoodsReceipt


@pytest.fixture
def db_mock():
    """Create a MagicMock db session that supports chained query calls."""
    return MagicMock()


@pytest.fixture
def service(db_mock):
    """Create PurchaseService with mock db."""
    return PurchaseService(db_mock)


class TestPurchaseServiceComprehensive:
    """Test suite for PurchaseService."""

    def test_init(self):
        """测试服务初始化"""
        mock_db = MagicMock()
        svc = PurchaseService(mock_db)
        assert svc.db == mock_db

    # ---- get_purchase_orders ----

    def test_get_purchase_orders_success(self, service, db_mock):
        """测试获取采购订单列表 - 成功"""
        mock_order = MagicMock()
        mock_order.id = 1
        db_mock.query.return_value.options.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_order]

        result = service.get_purchase_orders()
        assert len(result) == 1
        assert result[0].id == 1

    def test_get_purchase_orders_with_filters(self, service, db_mock):
        """测试获取采购订单列表 - 带过滤条件"""
        chain = db_mock.query.return_value.options.return_value
        chain.filter.return_value = chain
        chain.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = service.get_purchase_orders(project_id=1, supplier_id=2, status="DRAFT")
        assert result == []

    # ---- get_purchase_order_by_id ----

    def test_get_purchase_order_by_id_found(self, service, db_mock):
        """测试根据ID获取采购订单 - 找到"""
        mock_order = MagicMock()
        mock_order.id = 1
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = mock_order

        result = service.get_purchase_order_by_id(1)
        assert result is not None
        assert result.id == 1

    def test_get_purchase_order_by_id_not_found(self, service, db_mock):
        """测试根据ID获取采购订单 - 未找到"""
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = None

        result = service.get_purchase_order_by_id(999)
        assert result is None

    # ---- create_purchase_order ----

    def test_create_purchase_order_success(self, service, db_mock):
        """测试创建采购订单 - 成功"""
        order_data = {
            'order_code': 'PO-001',
            'supplier_id': 1,
            'project_id': 1,
            'total_amount': 10000,
            'items': [
                {'material_id': 1, 'quantity': 10, 'unit_price': 100, 'total_amount': 1000}
            ]
        }

        result = service.create_purchase_order(order_data)
        assert result is not None
        db_mock.add.assert_called()
        db_mock.flush.assert_called()

    def test_create_purchase_order_no_items(self, service, db_mock):
        """测试创建采购订单 - 无订单项"""
        order_data = {
            'order_code': 'PO-002',
            'supplier_id': 1,
            'project_id': 1,
            'total_amount': 0,
        }

        result = service.create_purchase_order(order_data)
        assert result is not None
        db_mock.flush.assert_called()

    # ---- update_purchase_order ----

    def test_update_purchase_order_success(self, service, db_mock):
        """测试更新采购订单 - 成功"""
        mock_order = MagicMock()
        mock_order.id = 1
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = mock_order

        result = service.update_purchase_order(1, {'total_amount': 20000})
        assert result is not None

    def test_update_purchase_order_not_found(self, service, db_mock):
        """测试更新采购订单 - 未找到"""
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = None

        result = service.update_purchase_order(999, {'total_amount': 20000})
        assert result is None

    # ---- submit_purchase_order ----

    def test_submit_purchase_order_success(self, service, db_mock):
        """测试提交采购订单 - 成功"""
        mock_order = MagicMock()
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = mock_order

        result = service.submit_purchase_order(1)
        assert result is True
        assert mock_order.status == 'SUBMITTED'

    def test_submit_purchase_order_not_found(self, service, db_mock):
        """测试提交采购订单 - 未找到"""
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = None

        result = service.submit_purchase_order(999)
        assert result is False

    # ---- approve_purchase_order ----

    def test_approve_purchase_order_success(self, service, db_mock):
        """测试审批采购订单 - 成功"""
        mock_order = MagicMock()
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = mock_order

        result = service.approve_purchase_order(1, approver_id=10)
        assert result is True
        assert mock_order.status == 'APPROVED'
        assert mock_order.approver_id == 10

    def test_approve_purchase_order_not_found(self, service, db_mock):
        """测试审批采购订单 - 未找到"""
        db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = None

        result = service.approve_purchase_order(999, approver_id=10)
        assert result is False

    # ---- get_goods_receipts ----

    def test_get_goods_receipts_success(self, service, db_mock):
        """测试获取收货记录列表 - 成功"""
        mock_receipt = MagicMock()
        db_mock.query.return_value.options.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_receipt]

        result = service.get_goods_receipts()
        assert len(result) == 1

    # ---- create_goods_receipt ----

    def test_create_goods_receipt_success(self, service, db_mock):
        """测试创建收货记录 - 成功"""
        receipt_data = {
            'order_id': 1,
            'receipt_date': '2025-01-01',
            'receiver_name': '张三',
            'items': []
        }

        result = service.create_goods_receipt(receipt_data)
        assert result is not None
        db_mock.add.assert_called()

    # ---- get_purchase_requests ----

    def test_get_purchase_requests_success(self, service, db_mock):
        """测试获取采购申请列表 - 成功"""
        mock_request = MagicMock()
        db_mock.query.return_value.options.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_request]

        result = service.get_purchase_requests()
        assert len(result) == 1

    # ---- create_purchase_request ----

    def test_create_purchase_request_success(self, service, db_mock):
        """测试创建采购申请 - 成功"""
        request_data = {
            'request_code': 'PR-001',
            'project_id': 1,
            'requester_id': 10,
            'title': '测试采购申请',
            'total_amount': 5000,
            'items': []
        }

        result = service.create_purchase_request(request_data)
        assert result is not None
        db_mock.add.assert_called()
