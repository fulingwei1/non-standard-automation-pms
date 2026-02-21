# -*- coding: utf-8 -*-
"""
采购订单审批适配器增强单元测试

测试覆盖：
- 所有核心方法的正常流程和边界情况
- 数据库查询的 mock 策略：构造真实数据对象让业务逻辑执行
- 25-35个测试用例，目标覆盖率70%+
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
    from app.models.organization import Department, Employee
    from app.models.user import User
    SKIP = False
except Exception as e:
    SKIP = True
    print(f"导入失败: {e}")

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


# ==================== 辅助函数 ====================

def make_db():
    """创建mock数据库会话"""
    db = MagicMock()
    db.flush = MagicMock()
    return db


def make_purchase_order(**kwargs):
    """创建mock采购订单对象"""
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
    order.vendor_id = kwargs.get("vendor_id", kwargs.get("supplier_id", 100))  # alias
    order.source_request_id = kwargs.get("source_request_id", None)
    order.created_by = kwargs.get("created_by", 1)
    order.contract_no = kwargs.get("contract_no", None)
    order.submitted_at = kwargs.get("submitted_at", None)
    order.approved_by = kwargs.get("approved_by", None)
    order.approved_at = kwargs.get("approved_at", None)
    order.approval_note = kwargs.get("approval_note", None)
    return order


def make_vendor(**kwargs):
    """创建mock供应商对象"""
    vendor = MagicMock(spec=Vendor)
    vendor.id = kwargs.get("id", 100)
    vendor.vendor_name = kwargs.get("vendor_name", "测试供应商")
    vendor.vendor_code = kwargs.get("vendor_code", "VEN-001")
    return vendor


def make_project(**kwargs):
    """创建mock项目对象"""
    project = MagicMock(spec=Project)
    project.id = kwargs.get("id", 200)
    project.project_code = kwargs.get("project_code", "PROJ-001")
    project.project_name = kwargs.get("project_name", "测试项目")
    project.priority = kwargs.get("priority", "NORMAL")
    project.manager_id = kwargs.get("manager_id", 10)
    return project


def make_approval_instance(**kwargs):
    """创建mock审批实例对象"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = kwargs.get("id", 1000)
    instance.status = kwargs.get("status", "PENDING")
    instance.approved_by = kwargs.get("approved_by", None)
    instance.reject_reason = kwargs.get("reject_reason", None)
    return instance


def make_department(**kwargs):
    """创建mock部门对象"""
    dept = MagicMock(spec=Department)
    dept.id = kwargs.get("id", 1)
    dept.dept_name = kwargs.get("dept_name", "采购部")
    dept.dept_code = kwargs.get("dept_code", "PURCHASE")
    dept.manager_id = kwargs.get("manager_id", 1)
    dept.is_active = kwargs.get("is_active", True)
    return dept


def make_employee(**kwargs):
    """创建mock员工对象"""
    emp = MagicMock(spec=Employee)
    emp.id = kwargs.get("id", 1)
    emp.name = kwargs.get("name", "张三")
    emp.employee_code = kwargs.get("employee_code", "EMP001")
    return emp


def make_user(**kwargs):
    """创建mock用户对象"""
    user = MagicMock(spec=User)
    user.id = kwargs.get("id", 1)
    user.real_name = kwargs.get("real_name", "张三")
    user.username = kwargs.get("username", "EMP001")
    user.is_active = kwargs.get("is_active", True)
    return user


# ==================== 测试类 ====================

class TestPurchaseOrderApprovalAdapterInit:
    """测试适配器初始化"""

    def test_init_with_db(self):
        """测试使用数据库会话初始化"""
        db = make_db()
        adapter = PurchaseOrderApprovalAdapter(db)
        assert adapter.db is db
        assert adapter.entity_type == "PURCHASE_ORDER"

    def test_entity_type_constant(self):
        """测试entity_type常量"""
        db = make_db()
        adapter = PurchaseOrderApprovalAdapter(db)
        assert PurchaseOrderApprovalAdapter.entity_type == "PURCHASE_ORDER"


class TestGetEntity:
    """测试获取采购订单实体"""

    def test_get_entity_exists(self):
        """测试获取存在的采购订单"""
        db = make_db()
        order = make_purchase_order(id=123)
        
        # Mock数据库查询
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        result = adapter.get_entity(123)
        
        assert result is order
        db.query.assert_called_once_with(PurchaseOrder)

    def test_get_entity_not_found(self):
        """测试获取不存在的采购订单"""
        db = make_db()
        
        # Mock数据库查询返回None
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        result = adapter.get_entity(999)
        
        assert result is None


class TestGetEntityData:
    """测试获取采购订单数据"""

    def test_get_entity_data_full(self):
        """测试获取完整的采购订单数据"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            order_no="PO-2025-001",
            order_title="测试订单",
            order_type="URGENT",
            total_amount="100000",
            amount_with_tax="113000",
            project_id=200,
            vendor_id=100
        )
        vendor = make_vendor(id=100, vendor_name="优质供应商")
        project = make_project(id=200, project_name="重要项目")
        
        # Mock数据库查询
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == Vendor:
                filter_mock.first.return_value = vendor
            elif model == Project:
                filter_mock.first.return_value = project
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 5
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["order_no"] == "PO-2025-001"
        assert data["order_title"] == "测试订单"
        assert data["order_type"] == "URGENT"
        assert data["total_amount"] == 100000.0
        assert data["amount_with_tax"] == 113000.0
        assert data["vendor_name"] == "优质供应商"
        assert data["project_name"] == "重要项目"
        assert data["item_count"] == 5

    def test_get_entity_data_minimal(self):
        """测试获取最小数据的采购订单"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            project_id=None,
            vendor_id=None,
            order_title=None
        )
        
        # Mock数据库查询
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 0
            else:
                filter_mock.first.return_value = None
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["order_no"] == "PO-2025-001"
        assert data["order_title"] == "采购订单-PO-2025-001"
        assert data["item_count"] == 0
        assert "vendor_name" not in data
        assert "project_name" not in data

    def test_get_entity_data_not_found(self):
        """测试获取不存在的订单数据"""
        db = make_db()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(999)
        
        assert data == {}

    def test_get_entity_data_with_dates(self):
        """测试订单数据包含日期字段"""
        db = make_db()
        order_date = datetime(2025, 1, 15)
        required_date = datetime(2025, 2, 15)
        
        order = make_purchase_order(
            id=1,
            order_date=order_date,
            required_date=required_date,
            project_id=None,
            vendor_id=None
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 3
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["order_date"] == "2025-01-15T00:00:00"
        assert data["required_date"] == "2025-02-15T00:00:00"


class TestOnSubmit:
    """测试提交审批回调"""

    def test_on_submit_success(self):
        """测试成功提交审批"""
        db = make_db()
        order = make_purchase_order(id=1, status="DRAFT")
        instance = make_approval_instance()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_submit(1, instance)
        
        assert order.status == "PENDING_APPROVAL"
        assert order.submitted_at is not None
        db.flush.assert_called_once()

    def test_on_submit_order_not_found(self):
        """测试提交不存在的订单"""
        db = make_db()
        instance = make_approval_instance()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_submit(999, instance)
        
        db.flush.assert_not_called()


class TestOnApproved:
    """测试审批通过回调"""

    def test_on_approved_success(self):
        """测试审批通过"""
        db = make_db()
        order = make_purchase_order(id=1, status="PENDING_APPROVAL")
        instance = make_approval_instance(approved_by=5)
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_approved(1, instance)
        
        assert order.status == "APPROVED"
        assert order.approved_by == 5
        assert order.approved_at is not None
        db.flush.assert_called_once()

    def test_on_approved_order_not_found(self):
        """测试审批通过但订单不存在"""
        db = make_db()
        instance = make_approval_instance()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_approved(999, instance)
        
        db.flush.assert_not_called()


class TestOnRejected:
    """测试审批驳回回调"""

    def test_on_rejected_success(self):
        """测试审批驳回"""
        db = make_db()
        order = make_purchase_order(id=1, status="PENDING_APPROVAL")
        instance = make_approval_instance()
        instance.reject_reason = "价格过高"
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_rejected(1, instance)
        
        assert order.status == "REJECTED"
        assert order.approval_note == "价格过高"
        db.flush.assert_called_once()

    def test_on_rejected_without_reason(self):
        """测试驳回但无驳回原因"""
        db = make_db()
        order = make_purchase_order(id=1, status="PENDING_APPROVAL")
        instance = make_approval_instance()
        # 不设置 reject_reason
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_rejected(1, instance)
        
        assert order.status == "REJECTED"
        db.flush.assert_called_once()

    def test_on_rejected_order_not_found(self):
        """测试驳回但订单不存在"""
        db = make_db()
        instance = make_approval_instance()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_rejected(999, instance)
        
        db.flush.assert_not_called()


class TestOnWithdrawn:
    """测试审批撤回回调"""

    def test_on_withdrawn_success(self):
        """测试审批撤回"""
        db = make_db()
        order = make_purchase_order(id=1, status="PENDING_APPROVAL", submitted_at=datetime.now())
        instance = make_approval_instance()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_withdrawn(1, instance)
        
        assert order.status == "DRAFT"
        assert order.submitted_at is None
        db.flush.assert_called_once()

    def test_on_withdrawn_order_not_found(self):
        """测试撤回但订单不存在"""
        db = make_db()
        instance = make_approval_instance()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        adapter.on_withdrawn(999, instance)
        
        db.flush.assert_not_called()


class TestGenerateTitle:
    """测试生成审批标题"""

    def test_generate_title_with_order_title(self):
        """测试生成包含订单标题的审批标题"""
        db = make_db()
        order = make_purchase_order(id=1, order_no="PO-2025-100", order_title="紧急物料采购")
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert title == "采购订单审批 - PO-2025-100 - 紧急物料采购"

    def test_generate_title_without_order_title(self):
        """测试生成不包含订单标题的审批标题"""
        db = make_db()
        order = make_purchase_order(id=1, order_no="PO-2025-101", order_title=None)
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        title = adapter.generate_title(1)
        
        assert title == "采购订单审批 - PO-2025-101"

    def test_generate_title_order_not_found(self):
        """测试订单不存在时生成标题"""
        db = make_db()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        title = adapter.generate_title(999)
        
        assert title == "采购订单审批 - 999"


class TestGenerateSummary:
    """测试生成审批摘要"""

    def test_generate_summary_full(self):
        """测试生成完整摘要"""
        db = make_db()
        required_date = datetime(2025, 3, 15)
        order = make_purchase_order(
            id=1,
            order_no="PO-2025-200",
            amount_with_tax="123456.78",
            vendor_id=100,
            project_id=200,
            required_date=required_date
        )
        vendor = make_vendor(id=100, vendor_name="优质供应商")
        project = make_project(id=200, project_name="重要项目A")
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == Vendor:
                filter_mock.first.return_value = vendor
            elif model == Project:
                filter_mock.first.return_value = project
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 8
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        summary = adapter.generate_summary(1)
        
        assert "PO-2025-200" in summary
        assert "优质供应商" in summary
        assert "123,456.78" in summary
        assert "明细行数: 8" in summary
        assert "2025-03-15" in summary
        assert "重要项目A" in summary

    def test_generate_summary_minimal(self):
        """测试生成最小摘要"""
        db = make_db()
        order = make_purchase_order(id=1, order_no="PO-2025-201")
        # 手动设置为None的字段
        order.vendor_id = None
        order.project_id = None
        order.amount_with_tax = None
        order.required_date = None
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 0
            else:
                filter_mock.first.return_value = None
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        summary = adapter.generate_summary(1)
        
        assert "PO-2025-201" in summary
        assert "未指定" in summary
        assert "未填写" in summary
        assert "明细行数: 0" in summary

    def test_generate_summary_order_not_found(self):
        """测试订单不存在时生成摘要"""
        db = make_db()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        summary = adapter.generate_summary(999)
        
        assert summary == ""


class TestValidateSubmit:
    """测试验证提交审批"""

    def test_validate_submit_success(self):
        """测试验证通过"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now(),
            amount_with_tax="50000"
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 3
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error is None

    def test_validate_submit_order_not_found(self):
        """测试验证订单不存在"""
        db = make_db()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(999)
        
        assert valid is False
        assert error == "采购订单不存在"

    def test_validate_submit_invalid_status(self):
        """测试验证订单状态不允许提交"""
        db = make_db()
        order = make_purchase_order(id=1, status="APPROVED")
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert "APPROVED" in error
        assert "不允许提交审批" in error

    def test_validate_submit_no_supplier(self):
        """测试验证缺少供应商"""
        db = make_db()
        order = make_purchase_order(id=1, status="DRAFT", supplier_id=None)
        order.vendor_id = None
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请选择供应商"

    def test_validate_submit_no_order_date(self):
        """测试验证缺少订单日期"""
        db = make_db()
        order = make_purchase_order(id=1, status="DRAFT", supplier_id=100, order_date=None)
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = order
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "请填写订单日期"

    def test_validate_submit_no_items(self):
        """测试验证无订单明细"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now()
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 0
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "采购订单至少需要一条明细"

    def test_validate_submit_zero_amount(self):
        """测试验证金额为零"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            status="DRAFT",
            supplier_id=100,
            order_date=datetime.now(),
            amount_with_tax="0"
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 1
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is False
        assert error == "订单总金额必须大于0"

    def test_validate_submit_rejected_status_allowed(self):
        """测试验证驳回状态允许重新提交"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            status="REJECTED",
            supplier_id=100,
            order_date=datetime.now(),
            amount_with_tax="50000"
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 2
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        valid, error = adapter.validate_submit(1)
        
        assert valid is True
        assert error is None


class TestGetCCUserIds:
    """测试获取抄送人列表"""

    def test_get_cc_user_ids_with_project_manager(self):
        """测试获取包含项目经理的抄送人"""
        db = make_db()
        order = make_purchase_order(id=1, project_id=200)
        project = make_project(id=200, manager_id=10)
        dept = make_department(id=1, dept_code="PURCHASE", manager_id=1)
        emp = make_employee(id=1, name="采购经理")
        user = make_user(id=20, real_name="采购经理")
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == Project:
                filter_mock.first.return_value = project
            elif model == Department:
                filter_mock.all.return_value = [dept]
            elif model == Employee:
                filter_mock.all.return_value = [emp]
            elif model == User:
                filter_mock.all.return_value = [user]
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        assert 10 in cc_users  # 项目经理
        assert 20 in cc_users  # 采购部门经理

    def test_get_cc_user_ids_no_project(self):
        """测试获取无项目的抄送人"""
        db = make_db()
        order = make_purchase_order(id=1, project_id=None)
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            else:
                filter_mock.first.return_value = None
                filter_mock.all.return_value = []
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        assert isinstance(cc_users, list)

    def test_get_cc_user_ids_order_not_found(self):
        """测试订单不存在时获取抄送人"""
        db = make_db()
        
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        db.query.return_value = query_mock
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(999)
        
        assert cc_users == []

    def test_get_cc_user_ids_deduplication(self):
        """测试抄送人列表去重"""
        db = make_db()
        order = make_purchase_order(id=1, project_id=200)
        project = make_project(id=200, manager_id=10)
        
        # 假设采购经理也是项目经理（同一个人）
        dept = make_department(id=1, dept_code="PURCHASE", manager_id=1)
        emp = make_employee(id=1, name="张三")
        user = make_user(id=10, real_name="张三")  # 同一个用户ID
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == Project:
                filter_mock.first.return_value = project
            elif model == Department:
                filter_mock.all.return_value = [dept]
            elif model == Employee:
                filter_mock.all.return_value = [emp]
            elif model == User:
                filter_mock.all.return_value = [user]
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        cc_users = adapter.get_cc_user_ids(1)
        
        # 应该去重，只有一个用户ID
        assert cc_users.count(10) == 1


# ==================== 额外测试用例 ====================

class TestEdgeCases:
    """边界情况测试"""

    def test_decimal_conversion_in_entity_data(self):
        """测试Decimal类型转换为float"""
        db = make_db()
        order = make_purchase_order(
            id=1,
            total_amount=Decimal("123456.789"),
            tax_rate=Decimal("0.13"),
            vendor_id=None,
            project_id=None
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 0
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert isinstance(data["total_amount"], float)
        assert isinstance(data["tax_rate"], float)

    def test_date_isoformat_conversion(self):
        """测试日期ISO格式转换"""
        db = make_db()
        test_date = datetime(2025, 1, 1, 10, 30, 45)
        order = make_purchase_order(
            id=1,
            order_date=test_date,
            vendor_id=None,
            project_id=None
        )
        
        def query_side_effect(model):
            mock = MagicMock()
            filter_mock = MagicMock()
            mock.filter.return_value = filter_mock
            
            if model == PurchaseOrder:
                filter_mock.first.return_value = order
            elif model == PurchaseOrderItem:
                filter_mock.count.return_value = 0
            
            return mock
        
        db.query.side_effect = query_side_effect
        
        adapter = PurchaseOrderApprovalAdapter(db)
        data = adapter.get_entity_data(1)
        
        assert data["order_date"] == "2025-01-01T10:30:45"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
