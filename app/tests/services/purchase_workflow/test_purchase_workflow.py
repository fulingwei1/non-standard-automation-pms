# -*- coding: utf-8 -*-
"""
采购工作流服务测试

目标覆盖率: 70%+
测试用例数: 4个
"""
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.services.purchase_workflow.service import PurchaseWorkflowService
from app.models.purchase import PurchaseOrder


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def workflow_service(mock_db):
    """创建采购工作流服务实例"""
    return PurchaseWorkflowService(mock_db)


@pytest.fixture
def sample_purchase_order():
    """创建示例采购订单"""
    order = Mock(spec=PurchaseOrder)
    order.id = 1
    order.order_no = "PO-20240301-0001"
    order.order_title = "测试采购订单"
    order.supplier_id = 10
    order.project_id = 100
    order.amount_with_tax = Decimal("5500.00")
    order.supplier = Mock()
    order.supplier.vendor_name = "测试供应商"
    return order


class TestPurchaseWorkflowService:
    """采购工作流服务测试类"""

    def test_entity_type_definition(self, workflow_service):
        """测试实体类型定义"""
        assert workflow_service.entity_type == "PURCHASE_ORDER"
        assert workflow_service.template_code == "PURCHASE_ORDER_APPROVAL"
        assert workflow_service.entity_label == "采购订单"

    def test_get_submittable_statuses(self, workflow_service):
        """测试可提交状态列表"""
        result = workflow_service._get_submittable_statuses()
        assert isinstance(result, list)
        assert "DRAFT" in result
        assert "REJECTED" in result

    def test_build_form_data_success(self, workflow_service, sample_purchase_order):
        """测试构建表单数据"""
        result = workflow_service._build_form_data(sample_purchase_order)

        assert result["order_no"] == "PO-20240301-0001"
        assert result["order_title"] == "测试采购订单"
        assert result["amount_with_tax"] == 5500.00
        assert result["supplier_id"] == 10
        assert result["project_id"] == 100

    def test_build_form_data_with_null_amount(self, workflow_service):
        """测试构建表单数据（金额为空）"""
        order = Mock(spec=PurchaseOrder)
        order.order_no = "PO-20240301-0002"
        order.order_title = "测试订单"
        order.supplier_id = 10
        order.project_id = 100
        order.amount_with_tax = None

        result = workflow_service._build_form_data(order)

        assert result["amount_with_tax"] == 0

    def test_build_pending_item_with_entity(self, workflow_service, sample_purchase_order):
        """测试构建待审批项（实体存在）"""
        mock_task = Mock()
        mock_task.id = 1

        result = workflow_service._build_pending_item(mock_task, sample_purchase_order)

        assert result["order_no"] == "PO-20240301-0001"
        assert result["order_title"] == "测试采购订单"
        assert result["amount_with_tax"] == 5500.00
        assert result["supplier_name"] == "测试供应商"

    def test_build_pending_item_without_entity(self, workflow_service):
        """测试构建待审批项（实体为空）"""
        mock_task = Mock()

        result = workflow_service._build_pending_item(mock_task, None)

        assert result["order_no"] is None
        assert result["order_title"] is None
        assert result["amount_with_tax"] == 0
        assert result["supplier_name"] is None

    def test_build_pending_item_with_null_amount(self, workflow_service):
        """测试构建待审批项（金额为空）"""
        mock_task = Mock()
        order = Mock()
        order.order_no = "PO-20240301-0003"
        order.order_title = "测试"
        order.amount_with_tax = None
        order.supplier = None

        result = workflow_service._build_pending_item(mock_task, order)

        assert result["amount_with_tax"] == 0
        assert result["supplier_name"] is None

    def test_build_history_item_success(self, workflow_service, sample_purchase_order):
        """测试构建审批历史项"""
        mock_task = Mock()

        result = workflow_service._build_history_item(mock_task, sample_purchase_order)

        assert result["order_no"] == "PO-20240301-0001"
        assert result["order_title"] == "测试采购订单"
        assert result["amount_with_tax"] == 5500.00

    def test_build_history_item_without_entity(self, workflow_service):
        """测试构建审批历史项（实体为空）"""
        mock_task = Mock()

        result = workflow_service._build_history_item(mock_task, None)

        assert result["order_no"] is None
        assert result["order_title"] is None
        assert result["amount_with_tax"] == 0

    def test_build_history_item_with_null_amount(self, workflow_service):
        """测试构建审批历史项（金额为空）"""
        mock_task = Mock()
        order = Mock()
        order.order_no = "PO-20240301-0004"
        order.order_title = "测试"
        order.amount_with_tax = None

        result = workflow_service._build_history_item(mock_task, order)

        assert result["amount_with_tax"] == 0