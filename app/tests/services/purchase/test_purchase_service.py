# -*- coding: utf-8 -*-
"""
采购服务测试

目标覆盖率: 70%+
测试用例数: 4个
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.purchase.purchase_service import PurchaseService
from app.models.purchase import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    GoodsReceipt,
)


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    return db


@pytest.fixture
def purchase_service(mock_db):
    """创建采购服务实例"""
    return PurchaseService(mock_db)


@pytest.fixture
def sample_purchase_order():
    """创建示例采购订单"""
    order = Mock(spec=PurchaseOrder)
    order.id = 1
    order.order_no = "PO-20240301-0001"
    order.supplier_id = 10
    order.project_id = 100
    order.total_amount = Decimal("5000.00")
    order.status = "DRAFT"
    order.order_date = datetime(2024, 3, 1)
    order.required_date = datetime(2024, 3, 15)
    order.created_at = datetime.now()
    order.vendor = Mock()
    order.vendor.vendor_name = "测试供应商"
    order.project = Mock()
    order.project.name = "测试项目"
    return order


@pytest.fixture
def sample_purchase_request():
    """创建示例采购申请"""
    request = Mock(spec=PurchaseRequest)
    request.id = 1
    request.request_no = "PR-20240301-0001"
    request.project_id = 100
    request.requested_by = 1
    request.total_amount = Decimal("3000.00")
    request.status = "DRAFT"
    request.created_at = datetime.now()
    request.project = Mock()
    request.project.name = "测试项目"
    request.requester = Mock()
    request.requester.username = "测试用户"
    return request


# 用于临时存储测试数据的全局字典
_test_data_store = {}


@pytest.fixture(autouse=True)
def mock_apply_pagination():
    """自动mock apply_pagination函数"""
    def fake_pagination(query, skip, limit):
        # 创建一个模拟的查询结果
        mock_result = Mock()
        # 返回存储的测试数据
        mock_result.all = lambda: _test_data_store.get('results', [])
        return mock_result
    
    with patch('app.services.purchase.purchase_service.apply_pagination', side_effect=fake_pagination):
        yield


def set_test_results(results):
    """设置测试结果数据"""
    _test_data_store['results'] = results


class TestPurchaseService:
    """采购服务测试类"""

    def test_get_purchase_orders_success(self, purchase_service, mock_db, sample_purchase_order):
        """测试获取采购订单列表成功"""
        set_test_results([sample_purchase_order])
        
        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        
        mock_query.options = Mock(return_value=mock_options)
        mock_options.filter = Mock(return_value=mock_filter)
        mock_filter.filter = Mock(return_value=mock_filter)
        mock_filter.order_by = Mock(return_value=mock_filter)
        
        mock_db.query.return_value = mock_query

        result = purchase_service.get_purchase_orders()

        assert len(result) == 1
        assert result[0].order_no == "PO-20240301-0001"

    def test_get_purchase_orders_with_filters(self, purchase_service, mock_db, sample_purchase_order):
        """测试带过滤条件获取采购订单"""
        set_test_results([sample_purchase_order])
        
        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        
        mock_query.options = Mock(return_value=mock_options)
        mock_options.filter = Mock(return_value=mock_filter)
        mock_filter.filter = Mock(return_value=mock_filter)
        mock_filter.order_by = Mock(return_value=mock_filter)
        
        mock_db.query.return_value = mock_query

        result = purchase_service.get_purchase_orders(
            project_id=100, supplier_id=10, status="DRAFT"
        )

        assert len(result) == 1

    def test_get_purchase_order_by_id_success(self, purchase_service, mock_db, sample_purchase_order):
        """测试根据ID获取采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_purchase_order)
        mock_db.query.return_value = mock_query

        result = purchase_service.get_purchase_order_by_id(1)

        assert result is not None
        assert result.id == 1

    def test_get_purchase_order_by_id_not_found(self, purchase_service, mock_db):
        """测试根据ID获取不存在的采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query.return_value = mock_query

        result = purchase_service.get_purchase_order_by_id(999)

        assert result is None

    def test_create_purchase_order_success(self, purchase_service, mock_db):
        """测试创建采购订单成功"""
        order_data = {
            "order_no": "PO-20240301-0002",
            "supplier_id": 10,
            "project_id": 100,
            "total_amount": Decimal("8000.00"),
            "order_date": datetime(2024, 3, 1),
            "expected_date": datetime(2024, 3, 15),
            "items": [
                {
                    "material_id": 1,
                    "material_code": "M001",
                    "material_name": "测试物料",
                    "quantity": 10,
                    "unit_price": Decimal("800.00"),
                    "amount": Decimal("8000.00"),
                }
            ],
        }

        mock_db.flush = Mock()
        
        result = purchase_service.create_purchase_order(order_data)

        assert result.supplier_id == 10
        assert result.project_id == 100
        assert result.status == "DRAFT"
        mock_db.add.assert_called()
        mock_db.flush.assert_called_once()

    def test_update_purchase_order_success(self, purchase_service, mock_db, sample_purchase_order):
        """测试更新采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_purchase_order)
        mock_db.query.return_value = mock_query

        update_data = {"status": "SUBMITTED", "total_amount": Decimal("6000.00")}
        result = purchase_service.update_purchase_order(1, update_data)

        assert result is not None
        assert result.status == "SUBMITTED"
        assert result.total_amount == Decimal("6000.00")

    def test_update_purchase_order_not_found(self, purchase_service, mock_db):
        """测试更新不存在的采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query.return_value = mock_query

        result = purchase_service.update_purchase_order(999, {"status": "SUBMITTED"})

        assert result is None

    def test_submit_purchase_order_success(self, purchase_service, mock_db, sample_purchase_order):
        """测试提交采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_purchase_order)
        mock_db.query.return_value = mock_query

        result = purchase_service.submit_purchase_order(1)

        assert result is True
        assert sample_purchase_order.status == "SUBMITTED"
        assert sample_purchase_order.submitted_at is not None

    def test_submit_purchase_order_not_found(self, purchase_service, mock_db):
        """测试提交不存在的采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query.return_value = mock_query

        result = purchase_service.submit_purchase_order(999)

        assert result is False

    def test_approve_purchase_order_success(self, purchase_service, mock_db, sample_purchase_order):
        """测试审批采购订单"""
        mock_query = Mock()
        mock_query.options = Mock(return_value=mock_query)
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=sample_purchase_order)
        mock_db.query.return_value = mock_query

        result = purchase_service.approve_purchase_order(1, approver_id=5)

        assert result is True
        assert sample_purchase_order.status == "APPROVED"
        assert sample_purchase_order.approver_id == 5
        assert sample_purchase_order.approved_at is not None

    def test_get_purchase_requests_success(self, purchase_service, mock_db, sample_purchase_request):
        """测试获取采购申请列表"""
        set_test_results([sample_purchase_request])
        
        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        
        mock_query.options = Mock(return_value=mock_options)
        mock_options.filter = Mock(return_value=mock_filter)
        mock_filter.filter = Mock(return_value=mock_filter)
        mock_filter.order_by = Mock(return_value=mock_filter)
        
        mock_db.query.return_value = mock_query

        result = purchase_service.get_purchase_requests()

        assert len(result) == 1
        assert result[0].request_no == "PR-20240301-0001"

    def test_create_purchase_request_success(self, purchase_service, mock_db):
        """测试创建采购申请"""
        request_data = {
            "request_no": "PR-20240301-0002",
            "project_id": 100,
            "requester_id": 1,
            "description": "测试采购申请",
            "total_amount": Decimal("5000.00"),
            "expected_date": datetime(2024, 3, 20),
            "items": [
                {
                    "material_id": 1,
                    "quantity": 5,
                    "unit_price": Decimal("1000.00"),
                    "amount": Decimal("5000.00"),
                }
            ],
        }

        mock_db.flush = Mock()

        result = purchase_service.create_purchase_request(request_data)

        assert result.project_id == 100
        assert result.requested_by == 1
        assert result.status == "DRAFT"
        assert mock_db.add.call_count >= 1
        mock_db.flush.assert_called_once()

    def test_generate_orders_from_request_success(self, purchase_service, mock_db, sample_purchase_request):
        """测试从采购申请生成订单"""
        mock_item = Mock()
        mock_item.id = 1
        mock_item.material_id = 1
        mock_item.quantity = 10
        mock_item.unit_price = Decimal("100.00")
        mock_item.amount = Decimal("1000.00")
        sample_purchase_request.items = [mock_item]

        mock_query = Mock()
        mock_filtered = Mock()
        mock_query.filter = Mock(return_value=mock_filtered)
        mock_filtered.first = Mock(return_value=sample_purchase_request)
        mock_db.query.return_value = mock_query
        mock_db.flush = Mock()

        result = purchase_service.generate_orders_from_request(request_id=1, supplier_id=10)

        assert result is True
        assert sample_purchase_request.status == "ORDER_GENERATED"
        assert mock_db.add.call_count >= 1

    def test_generate_orders_from_request_not_found(self, purchase_service, mock_db):
        """测试从不存在采购申请生成订单"""
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)
        mock_db.query.return_value = mock_query

        result = purchase_service.generate_orders_from_request(request_id=999, supplier_id=10)

        assert result is False


class TestGoodsReceiptService:
    """收货记录服务测试类"""

    def test_get_goods_receipts_success(self, purchase_service, mock_db):
        """测试获取收货记录列表"""
        mock_receipt = Mock(spec=GoodsReceipt)
        mock_receipt.id = 1
        mock_receipt.receipt_no = "GR-20240301-0001"
        
        set_test_results([mock_receipt])
        
        mock_query = Mock()
        mock_options = Mock()
        mock_filter = Mock()
        
        mock_query.options = Mock(return_value=mock_options)
        mock_options.filter = Mock(return_value=mock_filter)
        mock_filter.filter = Mock(return_value=mock_filter)
        mock_filter.order_by = Mock(return_value=mock_filter)
        
        mock_db.query.return_value = mock_query

        result = purchase_service.get_goods_receipts()

        assert len(result) == 1
        assert result[0].receipt_no == "GR-20240301-0001"

    def test_create_goods_receipt_success(self, purchase_service, mock_db):
        """测试创建收货记录"""
        receipt_data = {
            "receipt_no": "GR-20240301-0002",
            "order_id": 1,
            "supplier_id": 10,
            "receipt_date": datetime(2024, 3, 10),
            "items": [
                {
                    "order_item_id": 1,
                    "received_quantity": 10,
                    "qualified_quantity": 9,
                    "remark": "略有问题",
                }
            ],
        }

        mock_db.flush = Mock()

        result = purchase_service.create_goods_receipt(receipt_data)

        assert result.order_id == 1
        assert result.supplier_id == 10
        assert result.status == "COMPLETED"
        mock_db.add.assert_called()
        mock_db.flush.assert_called_once()