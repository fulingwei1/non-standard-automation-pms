# -*- coding: utf-8 -*-
"""
采购订单审批适配器 单元测试
目标覆盖率: 60%+
覆盖: 数据转换、验证、审批回调、抄送人逻辑
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.approval_engine.adapters.purchase import PurchaseOrderApprovalAdapter
    from app.models.approval import ApprovalInstance
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem
    from app.models.project import Project
    from app.models.vendor import Vendor
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    """创建mock数据库会话"""
    db = MagicMock()
    db.flush = MagicMock()
    return db


def make_purchase_order(**kwargs):
    """创建mock采购订单"""
    order = MagicMock(spec=PurchaseOrder)
    order.id = kwargs.get("id", 1)
    order.order_no = kwargs.get("order_no", "PO-2025-001")
    order.order_title = kwargs.get("order_title", "测试采购订单")
    order.order_type = kwargs.get("order_type", "NORMAL")
    order.status = kwargs.get("status", "DRAFT")
    order.total_amount = Decimal(kwargs.get("total_amount", "50000"))
    order.tax_rate = Decimal(kwargs.get("tax_rate", "0.13"))
    order.tax_amount = Decimal(kwargs.get("tax_amount", "6500"))
    order.amount_with_tax = Decimal(kwargs.get("amount_with_tax", "56500"))
    order.currency = kwargs.get("currency", "CNY")
    order.order_date = kwargs.get("order_date", datetime.now())
    order.required_date = kwargs.get("required_date", datetime.now() + timedelta(days=30))
    order.promised_date = kwargs.get("promised_date", None)
    order.payment_terms = kwargs.get("payment_terms", "货到付款")
    order.project_id = kwargs.get("project_id", None)
    order.supplier_id = kwargs.get("supplier_id", 100)
    order.source_request_id = kwargs.get("source_request_id", None)
    order.created_by = kwargs.get("created_by", 1)
    order.contract_no = kwargs.get("contract_no", None)
    order.submitted_at = kwargs.get("submitted_at", None)
    order.approved_by = kwargs.get("approved_by", None)
    order.approved_at = kwargs.get("approved_at", None)
    order.approval_note = kwargs.get("approval_note", None)
    return order


def make_purchase_order_item(**kwargs):
    """创建mock采购订单明细"""
    item = MagicMock(spec=PurchaseOrderItem)
    item.id = kwargs.get("id", 1)
    item.order_id = kwargs.get("order_id", 1)
    item.line_no = kwargs.get("line_no", 1)
    item.material_name = kwargs.get("material_name", "测试物料")
    item.quantity = Decimal(kwargs.get("quantity", "10"))
    item.unit_price = Decimal(kwargs.get("unit_price", "5000"))
    return item


def make_project(**kwargs):
    """创建mock项目"""
    project = MagicMock(spec=Project)
    project.id = kwargs.get("id", 200)
    project.project_code = kwargs.get("project_code", "PROJ-001")
    project.project_name = kwargs.get("project_name", "测试项目")
    project.priority = kwargs.get("priority", "NORMAL")
    project.manager_id = kwargs.get("manager_id", 10)
    return project


def make_vendor(**kwargs):
    """创建mock供应商"""
    vendor = MagicMock(spec=Vendor)
    vendor.id = kwargs.get("id", 100)
    vendor.vendor_name = kwargs.get("vendor_name", "测试供应商")
    vendor.vendor_code = kwargs.get("vendor_code", "VEN-001")
    return vendor


def make_approval_instance(**kwargs):
    """创建mock审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = kwargs.get("id", 1000)
    instance.status = kwargs.get("status", "PENDING")
    instance.approved_by = kwargs.get("approved_by", None)
    instance.reject_reason = kwargs.get("reject_reason", None)
    return instance


class TestPurchaseOrderApprovalAdapter:
    """采购订单审批适配器测试"""

    def test_adapter_entity_type(self):
        """测试适配器实体类型"""
        db = make_db()
        adapter = PurchaseOrderApprovalAdapter(db)
        assert adapter.entity_type == "PURCHASE_ORDER"

    def test_get_entity_found(self):
        """测试获取采购订单实体 - 找到"""
        db = make_db()
        order = make_purchase_order(id=1)
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        result = adapter.get_entity(1)
        
        assert result == order

    def test_get_entity_not_found(self):
        """测试获取采购订单实体 - 未找到"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = PurchaseOrderApprovalAdapter(db)
        result = adapter.get_entity(999)
        
        assert result is None

    def test_get_entity_data_complete(self):
        """测试获取实体数据 - 完整数据"""
        db = make_db()
        order = make_purchase_order(
            order_no="PO-001",
            order_type="URGENT",
            total_amount="80000",
            amount_with_tax="90400",
            project_id=200,
            supplier_id=100
        )
        project = make_project(project_name="紧急项目", priority="HIGH")
        vendor = make_vendor(vendor_name="优质供应商")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 3
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            elif model == Vendor:
                query_mock.filter.return_value.first.return_value = vendor
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["order_no"] == "PO-001"
        assert data["order_type"] == "URGENT"
        assert data["total_amount"] == 80000.0
        assert data["amount_with_tax"] == 90400.0
        assert data["item_count"] == 3
        assert data["project_name"] == "紧急项目"
        assert data["project_priority"] == "HIGH"
        assert data["vendor_name"] == "优质供应商"

    def test_get_entity_data_minimal(self):
        """测试获取实体数据 - 最小化数据"""
        db = make_db()
        order = make_purchase_order(
            project_id=None,
            supplier_id=None
        )
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 0
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["project_id"] is None
        assert data["supplier_id"] is None
        assert data["item_count"] == 0
        assert "project_name" not in data
        assert "vendor_name" not in data

    def test_get_entity_data_not_found(self):
        """测试获取实体数据 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(999)
        
        assert data == {}

    def test_on_submit(self):
        """测试提交审批回调"""
        db = make_db()
        order = make_purchase_order(status="DRAFT", submitted_at=None)
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert order.status == "PENDING_APPROVAL"
        assert order.submitted_at is not None
        db.flush.assert_called_once()

    def test_on_approved(self):
        """测试审批通过回调"""
        db = make_db()
        order = make_purchase_order(
            status="PENDING_APPROVAL",
            approved_by=None,
            approved_at=None
        )
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance(approved_by=10)
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert order.status == "APPROVED"
        assert order.approved_by == 10
        assert order.approved_at is not None
        db.flush.assert_called_once()

    def test_on_rejected(self):
        """测试审批驳回回调"""
        db = make_db()
        order = make_purchase_order(status="PENDING_APPROVAL")
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        instance.reject_reason = "价格过高"
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_rejected(1, instance)
        
        assert order.status == "REJECTED"
        assert order.approval_note == "价格过高"
        db.flush.assert_called_once()

    def test_on_withdrawn(self):
        """测试审批撤回回调"""
        db = make_db()
        order = make_purchase_order(
            status="PENDING_APPROVAL",
            submitted_at=datetime.now()
        )
        db.query.return_value.filter.return_value.first.return_value = order
        instance = make_approval_instance()
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_withdrawn(1, instance)
        
        assert order.status == "DRAFT"
        assert order.submitted_at is None
        db.flush.assert_called_once()

    def test_generate_title_with_order_title(self):
        """测试生成标题 - 有订单标题"""
        db = make_db()
        order = make_purchase_order(
            order_no="PO-123",
            order_title="办公用品采购"
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert "采购订单审批" in title
        assert "PO-123" in title
        assert "办公用品采购" in title

    def test_generate_title_without_order_title(self):
        """测试生成标题 - 无订单标题"""
        db = make_db()
        order = make_purchase_order(
            order_no="PO-456",
            order_title=None
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert "采购订单审批" in title
        assert "PO-456" in title

    def test_generate_summary_complete(self):
        """测试生成摘要 - 完整信息"""
        db = make_db()
        order = make_purchase_order(
            order_no="PO-789",
            amount_with_tax="120000",
            required_date=datetime(2025, 3, 15),
            supplier_id=100,
            project_id=200
        )
        vendor = make_vendor(vendor_name="供应商A")
        project = make_project(project_name="项目X")
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 5
            elif model == Vendor:
                query_mock.filter.return_value.first.return_value = vendor
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        summary = adapter.generate_summary(1)
        
        assert "PO-789" in summary
        assert "供应商A" in summary
        assert "120,000.00" in summary
        assert "5" in summary
        assert "2025-03-15" in summary
        assert "项目X" in summary

    def test_validate_submit_success(self):
        """测试提交验证 - 成功"""
        db = make_db()
        order = make_purchase_order(
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now(),
            amount_with_tax="60000"
        )
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 2
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error is None

    def test_validate_submit_not_found(self):
        """测试提交验证 - 实体不存在"""
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert "不存在" in error

    def test_validate_submit_wrong_status(self):
        """测试提交验证 - 状态错误"""
        db = make_db()
        order = make_purchase_order(status="APPROVED")
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "不允许提交审批" in error

    def test_validate_submit_no_supplier(self):
        """测试提交验证 - 缺少供应商"""
        db = make_db()
        order = make_purchase_order(status="DRAFT", supplier_id=None)
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "选择供应商" in error

    def test_validate_submit_no_order_date(self):
        """测试提交验证 - 缺少订单日期"""
        db = make_db()
        order = make_purchase_order(
            status="DRAFT",
            supplier_id=100,
            order_date=None
        )
        db.query.return_value.filter.return_value.first.return_value = order
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "订单日期" in error

    def test_validate_submit_no_items(self):
        """测试提交验证 - 无订单明细"""
        db = make_db()
        order = make_purchase_order(
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now()
        )
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 0
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "至少需要一条明细" in error

    def test_validate_submit_zero_amount(self):
        """测试提交验证 - 金额为0"""
        db = make_db()
        order = make_purchase_order(
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now(),
            amount_with_tax="0"
        )
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 1
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须大于0" in error

    def test_validate_submit_negative_amount(self):
        """测试提交验证 - 金额为负"""
        db = make_db()
        order = make_purchase_order(
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now(),
            amount_with_tax="-1000"
        )
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == PurchaseOrderItem:
                query_mock.filter.return_value.count.return_value = 1
            return query_mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "必须大于0" in error

    @patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes')
    def test_get_cc_user_ids_with_project(self, mock_get_dept_managers):
        """测试获取抄送人 - 有项目关联"""
        db = make_db()
        order = make_purchase_order(project_id=200)
        project = make_project(manager_id=10)
        
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == PurchaseOrder:
                query_mock.filter.return_value.first.return_value = order
            elif model == Project:
                query_mock.filter.return_value.first.return_value = project
            return query_mock
        
        db.query.side_effect = query_side_effect
        mock_get_dept_managers.return_value = [20, 21]
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        assert 10 in cc_users  # 项目经理
        assert 20 in cc_users  # 采购部门负责人
        assert 21 in cc_users
        assert len(set(cc_users)) == len(cc_users)  # 验证去重

    @patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_id')
    @patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes')
    def test_get_cc_user_ids_fallback_to_name(self, mock_get_by_codes, mock_get_by_name):
        """测试获取抄送人 - 按编码查找失败，回退到按名称查找"""
        db = make_db()
        order = make_purchase_order(project_id=None)
        db.query.return_value.filter.return_value.first.return_value = order
        
        mock_get_by_codes.return_value = []  # 按编码查找失败
        mock_get_by_name.return_value = 30  # 按名称查找成功
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        assert 30 in cc_users
        mock_get_by_name.assert_called_with('采购部')
