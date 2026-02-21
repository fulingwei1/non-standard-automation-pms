# -*- coding: utf-8 -*-
"""
采购订单审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.approval_engine.adapters.purchase import PurchaseOrderApprovalAdapter
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.approval import ApprovalInstance
from app.models.project import Project
from app.models.vendor import Vendor


class TestPurchaseAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = PurchaseOrderApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取采购订单实体"""
        mock_order = MagicMock(spec=PurchaseOrder)
        mock_order.id = self.entity_id
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_order)
        self.db.query.assert_called_once_with(PurchaseOrder)

    def test_get_entity_not_found(self):
        """测试获取不存在的采购订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_basic(self):
        """测试获取基础采购订单数据"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-001",
            order_title="办公用品采购",
            order_type="NORMAL",
            total_amount=Decimal("10000.00"),
            tax_rate=Decimal("0.13"),
            tax_amount=Decimal("1300.00"),
            amount_with_tax=Decimal("11300.00"),
            currency="CNY"
        )

        self._setup_query_returns(mock_order, item_count=5)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证基础字段
        self.assertEqual(result["order_no"], "PO-2024-001")
        self.assertEqual(result["order_title"], "办公用品采购")
        self.assertEqual(result["order_type"], "NORMAL")
        self.assertEqual(result["status"], "DRAFT")
        
        # 验证金额字段
        self.assertEqual(result["total_amount"], 10000.00)
        self.assertEqual(result["tax_rate"], 0.13)
        self.assertEqual(result["tax_amount"], 1300.00)
        self.assertEqual(result["amount_with_tax"], 11300.00)
        self.assertEqual(result["currency"], "CNY")
        
        # 验证明细数量
        self.assertEqual(result["item_count"], 5)

    def test_get_entity_data_with_project(self):
        """测试获取包含项目信息的采购订单数据"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-002",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "测试项目"
        mock_project.priority = "HIGH"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 3
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证项目信息被正确包含
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["project_priority"], "HIGH")

    def test_get_entity_data_with_vendor(self):
        """测试获取包含供应商信息的采购订单数据"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-003",
            supplier_id=20
        )

        mock_vendor = MagicMock(spec=Vendor)
        mock_vendor.vendor_name = "优质供应商"
        mock_vendor.vendor_code = "VND-001"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Vendor:
                mock_query.filter.return_value.first.return_value = mock_vendor
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 2
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证供应商信息
        self.assertEqual(result["vendor_name"], "优质供应商")
        self.assertEqual(result["vendor_code"], "VND-001")

    def test_get_entity_data_with_dates(self):
        """测试包含日期字段的数据"""
        order_date = datetime(2024, 1, 10, 10, 0, 0)
        required_date = datetime(2024, 1, 20, 10, 0, 0)
        promised_date = datetime(2024, 1, 18, 10, 0, 0)

        mock_order = self._create_mock_order(
            order_no="PO-2024-004",
            order_date=order_date,
            required_date=required_date,
            promised_date=promised_date
        )

        self._setup_query_returns(mock_order, item_count=1)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证日期被转换为ISO格式
        self.assertEqual(result["order_date"], order_date.isoformat())
        self.assertEqual(result["required_date"], required_date.isoformat())
        self.assertEqual(result["promised_date"], promised_date.isoformat())

    def test_get_entity_data_with_none_amounts(self):
        """测试金额为None的情况"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-005",
            total_amount=None,
            tax_rate=None,
            tax_amount=None,
            amount_with_tax=None
        )

        self._setup_query_returns(mock_order, item_count=1)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证None金额被转换为0
        self.assertEqual(result["total_amount"], 0)
        self.assertEqual(result["tax_rate"], 0)
        self.assertEqual(result["tax_amount"], 0)
        self.assertEqual(result["amount_with_tax"], 0)

    def test_get_entity_data_default_title(self):
        """测试默认标题生成"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-006",
            order_title=None
        )

        self._setup_query_returns(mock_order, item_count=1)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证默认标题
        self.assertEqual(result["order_title"], "采购订单-PO-2024-006")

    def test_get_entity_data_default_values(self):
        """测试默认值设置"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-007",
            order_type=None,
            currency=None
        )

        self._setup_query_returns(mock_order, item_count=1)

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证默认值
        self.assertEqual(result["order_type"], "NORMAL")
        self.assertEqual(result["currency"], "CNY")

    def test_get_entity_data_project_without_priority(self):
        """测试项目没有priority属性"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-008",
            project_id=10
        )

        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ-002"
        mock_project.project_name = "项目B"
        # 删除priority属性
        del mock_project.priority

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证priority为None（hasattr检查失败）
        self.assertIsNone(result["project_priority"])

    def test_get_entity_data_not_found(self):
        """测试获取不存在采购订单的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        # 应返回空字典
        self.assertEqual(result, {})

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_order = self._create_mock_order(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('app.services.approval_engine.adapters.purchase.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            self.adapter.on_submit(self.entity_id, self.instance)

            # 验证状态更改
            self.assertEqual(mock_order.status, "PENDING_APPROVAL")
            self.assertEqual(mock_order.submitted_at, mock_now)
            self.db.flush.assert_called_once()

    def test_on_submit_order_not_found(self):
        """测试提交不存在的采购订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试成功审批通过"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.instance.approved_by = 100
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        with patch('app.services.approval_engine.adapters.purchase.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            self.adapter.on_approved(self.entity_id, self.instance)

            # 验证状态和审批信息
            self.assertEqual(mock_order.status, "APPROVED")
            self.assertEqual(mock_order.approved_by, 100)
            self.assertEqual(mock_order.approved_at, mock_now)
            self.db.flush.assert_called_once()

    def test_on_approved_order_not_found(self):
        """测试审批通过不存在的采购订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试成功驳回审批"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证状态更改为REJECTED
        self.assertEqual(mock_order.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_with_reason(self):
        """测试驳回时记录驳回原因"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.instance.reject_reason = "价格太高"
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证驳回原因被记录
        self.assertEqual(mock_order.status, "REJECTED")
        self.assertEqual(mock_order.approval_note, "价格太高")
        self.db.flush.assert_called_once()

    def test_on_rejected_order_not_found(self):
        """测试驳回不存在的采购订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试成功撤回审批"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        mock_order.submitted_at = datetime(2024, 1, 10, 10, 0, 0)
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 验证状态恢复为DRAFT，submitted_at清除
        self.assertEqual(mock_order.status, "DRAFT")
        self.assertIsNone(mock_order.submitted_at)
        self.db.flush.assert_called_once()

    def test_on_withdrawn_order_not_found(self):
        """测试撤回不存在的采购订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== generate_title() 测试 ==========

    def test_generate_title_with_order_title(self):
        """测试生成包含订单标题的审批标题"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-001",
            order_title="办公用品采购"
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "采购订单审批 - PO-2024-001 - 办公用品采购")

    def test_generate_title_without_order_title(self):
        """测试生成不包含订单标题的审批标题"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-002",
            order_title=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, "采购订单审批 - PO-2024-002")

    def test_generate_title_order_not_found(self):
        """测试生成不存在采购订单的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.generate_title(self.entity_id)

        self.assertEqual(title, f"采购订单审批 - {self.entity_id}")

    # ========== generate_summary() 测试 ==========

    def test_generate_summary_basic(self):
        """测试生成基础摘要"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-001",
            supplier_id=10,
            amount_with_tax=Decimal("11300.00")
        )

        mock_vendor = MagicMock(spec=Vendor)
        mock_vendor.vendor_name = "优质供应商"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Vendor:
                mock_query.filter.return_value.first.return_value = mock_vendor
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 5
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证摘要包含关键信息
        self.assertIn("PO-2024-001", summary)
        self.assertIn("优质供应商", summary)
        self.assertIn("¥11,300.00", summary)
        self.assertIn("5", summary)

    def test_generate_summary_no_vendor(self):
        """测试生成没有供应商的摘要"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-002",
            supplier_id=None,
            amount_with_tax=Decimal("5000.00")
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 3
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证使用默认供应商名称
        self.assertIn("未指定", summary)

    def test_generate_summary_with_required_date(self):
        """测试生成包含交期的摘要"""
        required_date = datetime(2024, 1, 20, 10, 0, 0)
        mock_order = self._create_mock_order(
            order_no="PO-2024-003",
            supplier_id=10,
            required_date=required_date
        )

        mock_vendor = MagicMock(spec=Vendor)
        mock_vendor.vendor_name = "快速供应商"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Vendor:
                mock_query.filter.return_value.first.return_value = mock_vendor
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 2
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证包含交期
        self.assertIn("2024-01-20", summary)

    def test_generate_summary_with_project(self):
        """测试生成包含项目的摘要"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-004",
            supplier_id=10,
            project_id=20
        )

        mock_vendor = MagicMock(spec=Vendor)
        mock_vendor.vendor_name = "项目供应商"

        mock_project = MagicMock(spec=Project)
        mock_project.project_name = "重要项目"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Vendor:
                mock_query.filter.return_value.first.return_value = mock_vendor
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 8
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证包含项目名称
        self.assertIn("重要项目", summary)

    def test_generate_summary_no_amount(self):
        """测试生成没有金额的摘要"""
        mock_order = self._create_mock_order(
            order_no="PO-2024-005",
            supplier_id=10,
            amount_with_tax=None
        )

        mock_vendor = MagicMock(spec=Vendor)
        mock_vendor.vendor_name = "测试供应商"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Vendor:
                mock_query.filter.return_value.first.return_value = mock_vendor
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        summary = self.adapter.generate_summary(self.entity_id)

        # 验证使用默认金额提示
        self.assertIn("未填写", summary)

    def test_generate_summary_order_not_found(self):
        """测试生成不存在采购订单的摘要"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        summary = self.adapter.generate_summary(self.entity_id)

        # 应返回空字符串
        self.assertEqual(summary, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success_from_draft(self):
        """测试从草稿状态成功验证提交"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=10,
            order_date=datetime(2024, 1, 10),
            amount_with_tax=Decimal("10000.00")
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 3
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_submit_success_from_rejected(self):
        """测试从驳回状态成功验证提交"""
        mock_order = self._create_mock_order(
            status="REJECTED",
            supplier_id=10,
            order_date=datetime(2024, 1, 10),
            amount_with_tax=Decimal("5000.00")
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_submit_order_not_found(self):
        """测试验证不存在的采购订单"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "采购订单不存在")

    def test_validate_submit_invalid_status(self):
        """测试无效状态下提交"""
        mock_order = self._create_mock_order(status="PENDING_APPROVAL")
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_missing_supplier(self):
        """测试缺少供应商"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请选择供应商")

    def test_validate_submit_missing_order_date(self):
        """测试缺少订单日期"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=10,
            order_date=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请填写订单日期")

    def test_validate_submit_no_items(self):
        """测试没有订单明细"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=10,
            order_date=datetime(2024, 1, 10)
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 0
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "采购订单至少需要一条明细")

    def test_validate_submit_zero_amount(self):
        """测试金额为0"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=10,
            order_date=datetime(2024, 1, 10),
            amount_with_tax=Decimal("0.00")
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "订单总金额必须大于0")

    def test_validate_submit_negative_amount(self):
        """测试金额为负数"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=10,
            order_date=datetime(2024, 1, 10),
            amount_with_tax=Decimal("-1000.00")
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "订单总金额必须大于0")

    def test_validate_submit_none_amount(self):
        """测试金额为None"""
        mock_order = self._create_mock_order(
            status="DRAFT",
            supplier_id=10,
            order_date=datetime(2024, 1, 10),
            amount_with_tax=None
        )

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = 1
            return mock_query

        self.db.query.side_effect = query_side_effect

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "订单总金额必须大于0")

    # ========== get_cc_user_ids() 测试 ==========

    def test_get_cc_user_ids_order_not_found(self):
        """测试获取不存在采购订单的抄送人"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        cc_users = self.adapter.get_cc_user_ids(self.entity_id)

        # 应返回空列表
        self.assertEqual(cc_users, [])

    def test_get_cc_user_ids_with_project_manager(self):
        """测试获取包含项目经理的抄送人"""
        mock_order = self._create_mock_order(project_id=10)

        mock_project = MagicMock(spec=Project)
        mock_project.manager_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        self.db.query.side_effect = query_side_effect

        # Mock基类方法
        with patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[200]):
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 应包含项目经理和采购部负责人
            self.assertIn(100, cc_users)
            self.assertIn(200, cc_users)

    def test_get_cc_user_ids_without_project(self):
        """测试没有项目时获取抄送人"""
        mock_order = self._create_mock_order(project_id=None)

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock基类方法
        with patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[200]):
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 应只包含采购部负责人
            self.assertNotIn(100, cc_users)
            self.assertIn(200, cc_users)

    def test_get_cc_user_ids_project_without_manager(self):
        """测试项目没有项目经理"""
        mock_order = self._create_mock_order(project_id=10)

        mock_project = MagicMock(spec=Project)
        mock_project.manager_id = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        self.db.query.side_effect = query_side_effect

        with patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[200]):
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 不应包含项目经理
            self.assertNotIn(100, cc_users)
            self.assertIn(200, cc_users)

    def test_get_cc_user_ids_fallback_to_department_manager(self):
        """测试通过部门编码查找失败时，回退到部门名称查找"""
        mock_order = self._create_mock_order(project_id=None)

        self.db.query.return_value.filter.return_value.first.return_value = mock_order

        # Mock基类方法：第一次返回空，第二次返回300
        with patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[]), \
             patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_id', return_value=300):
            
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 应包含通过部门名称找到的负责人
            self.assertIn(300, cc_users)

    def test_get_cc_user_ids_deduplication(self):
        """测试抄送人去重"""
        mock_order = self._create_mock_order(project_id=10)

        mock_project = MagicMock(spec=Project)
        mock_project.manager_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == Project:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        self.db.query.side_effect = query_side_effect

        # 模拟重复的用户ID
        with patch.object(PurchaseOrderApprovalAdapter, 'get_department_manager_user_ids_by_codes', return_value=[100, 200]):
            cc_users = self.adapter.get_cc_user_ids(self.entity_id)

            # 验证去重
            self.assertEqual(len(cc_users), len(set(cc_users)))
            self.assertEqual(cc_users.count(100), 1)

    # ========== 辅助方法 ==========

    def _create_mock_order(self, **kwargs):
        """创建模拟采购订单对象"""
        mock_order = MagicMock(spec=PurchaseOrder)
        
        # 设置默认值
        defaults = {
            'id': self.entity_id,
            'order_no': 'PO-TEST-001',
            'order_title': None,
            'order_type': None,
            'status': 'DRAFT',
            'total_amount': Decimal("10000.00"),
            'tax_rate': Decimal("0.13"),
            'tax_amount': Decimal("1300.00"),
            'amount_with_tax': Decimal("11300.00"),
            'currency': None,
            'order_date': None,
            'required_date': None,
            'promised_date': None,
            'payment_terms': None,
            'project_id': None,
            'supplier_id': None,
            'source_request_id': None,
            'created_by': 1,
            'contract_no': None,
            'submitted_at': None,
            'approved_by': None,
            'approved_at': None,
            'approval_note': None,
        }
        
        # 合并自定义值
        defaults.update(kwargs)
        
        # 设置属性
        for key, value in defaults.items():
            setattr(mock_order, key, value)
        
        return mock_order

    def _setup_query_returns(self, mock_order, item_count=0):
        """设置基础查询返回"""
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == PurchaseOrder:
                mock_query.filter.return_value.first.return_value = mock_order
            elif model == PurchaseOrderItem:
                mock_query.filter.return_value.count.return_value = item_count
            return mock_query

        self.db.query.side_effect = query_side_effect


class TestAdapterEntityType(unittest.TestCase):
    """测试适配器类属性"""

    def test_entity_type(self):
        """测试entity_type类属性"""
        self.assertEqual(PurchaseOrderApprovalAdapter.entity_type, "PURCHASE_ORDER")


if __name__ == '__main__':
    unittest.main()
