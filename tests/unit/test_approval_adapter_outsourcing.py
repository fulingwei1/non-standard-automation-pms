# -*- coding: utf-8 -*-
"""
外协订单审批适配器单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.models.approval import ApprovalInstance
from app.models.outsourcing import OutsourcingOrder, OutsourcingOrderItem
from app.models.project import Project, Machine
from app.models.vendor import Vendor
from app.services.approval_engine.adapters.outsourcing import (
    OutsourcingOrderApprovalAdapter,
)


class TestOutsourcingOrderApprovalAdapter(unittest.TestCase):
    """测试外协订单审批适配器"""

    def setUp(self):
        """每个测试前的初始化"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        self.adapter = OutsourcingOrderApprovalAdapter(self.mock_db)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取外协订单实体"""
        # 准备mock数据
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.id = 1
        mock_order.order_no = "OS-2024-001"

        # 配置mock查询
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        # 执行测试
        result = self.adapter.get_entity(1)

        # 验证
        self.assertEqual(result, mock_order)
        self.mock_db.query.assert_called_once_with(OutsourcingOrder)

    def test_get_entity_not_found(self):
        """测试获取不存在的订单"""
        # 配置mock返回None
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # 执行测试
        result = self.adapter.get_entity(999)

        # 验证
        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_complete(self):
        """测试获取完整的订单数据"""
        # 准备mock订单
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.id = 1
        mock_order.order_no = "OS-2024-001"
        mock_order.order_title = "设备外协加工"
        mock_order.order_type = "MACHINING"
        mock_order.order_description = "精密加工"
        mock_order.status = "DRAFT"
        mock_order.total_amount = Decimal("10000.00")
        mock_order.tax_rate = Decimal("13.00")
        mock_order.tax_amount = Decimal("1300.00")
        mock_order.amount_with_tax = Decimal("11300.00")
        mock_order.required_date = date(2024, 12, 31)
        mock_order.estimated_date = date(2024, 12, 25)
        mock_order.actual_date = None
        mock_order.payment_status = "UNPAID"
        mock_order.paid_amount = Decimal("0.00")
        mock_order.contract_no = "CT-001"
        mock_order.project_id = 10
        mock_order.machine_id = 20
        mock_order.vendor_id = 30
        mock_order.created_by = 1

        # 准备关联对象
        mock_project = Mock(spec=Project)
        mock_project.project_code = "PRJ-001"
        mock_project.project_name = "测试项目"
        mock_project.status = "IN_PROGRESS"

        mock_machine = Mock(spec=Machine)
        mock_machine.machine_code = "MC-001"
        mock_machine.machine_name = "加工中心"

        mock_vendor = Mock(spec=Vendor)
        mock_vendor.vendor_name = "XX外协厂"
        mock_vendor.vendor_code = "VD-001"

        # 配置数据库查询mock
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 5
            elif model == Project:
                mock_filter.first.return_value = mock_project
            elif model == Machine:
                mock_filter.first.return_value = mock_machine
            elif model == Vendor:
                mock_filter.first.return_value = mock_vendor

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.adapter.get_entity_data(1)

        # 验证基本字段
        self.assertEqual(result["order_no"], "OS-2024-001")
        self.assertEqual(result["order_title"], "设备外协加工")
        self.assertEqual(result["order_type"], "MACHINING")
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["total_amount"], 10000.00)
        self.assertEqual(result["amount_with_tax"], 11300.00)
        self.assertEqual(result["item_count"], 5)

        # 验证关联数据
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["machine_code"], "MC-001")
        self.assertEqual(result["machine_name"], "加工中心")
        self.assertEqual(result["vendor_name"], "XX外协厂")

    def test_get_entity_data_minimal(self):
        """测试最小化订单数据（无关联对象）"""
        # 准备最小订单
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.id = 2
        mock_order.order_no = "OS-2024-002"
        mock_order.order_title = "简单订单"
        mock_order.order_type = "WELDING"
        mock_order.order_description = None
        mock_order.status = "DRAFT"
        mock_order.total_amount = None
        mock_order.tax_rate = None
        mock_order.tax_amount = None
        mock_order.amount_with_tax = None
        mock_order.required_date = None
        mock_order.estimated_date = None
        mock_order.actual_date = None
        mock_order.payment_status = "UNPAID"
        mock_order.paid_amount = None
        mock_order.contract_no = None
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.vendor_id = None
        mock_order.created_by = 1

        # 配置数据库查询
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 0
            else:
                mock_filter.first.return_value = None

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.adapter.get_entity_data(2)

        # 验证
        self.assertEqual(result["order_no"], "OS-2024-002")
        self.assertEqual(result["total_amount"], 0)
        self.assertEqual(result["item_count"], 0)
        self.assertIsNone(result["required_date"])
        # 不应包含项目/设备/供应商信息
        self.assertNotIn("project_code", result)
        self.assertNotIn("machine_code", result)
        self.assertNotIn("vendor_name", result)

    def test_get_entity_data_order_not_found(self):
        """测试订单不存在时返回空字典"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.adapter.get_entity_data(999)

        self.assertEqual(result, {})

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试提交审批时状态变更"""
        # 准备mock订单
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        mock_instance = Mock(spec=ApprovalInstance)

        # 执行测试
        self.adapter.on_submit(1, mock_instance)

        # 验证状态变更
        self.assertEqual(mock_order.status, "PENDING_APPROVAL")
        self.mock_db.flush.assert_called_once()

    def test_on_submit_order_not_found(self):
        """测试提交时订单不存在"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        mock_instance = Mock(spec=ApprovalInstance)

        # 不应抛出异常
        self.adapter.on_submit(999, mock_instance)
        self.mock_db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试审批通过时状态变更"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "PENDING_APPROVAL"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        mock_instance = Mock(spec=ApprovalInstance)

        # 执行测试
        self.adapter.on_approved(1, mock_instance)

        # 验证
        self.assertEqual(mock_order.status, "APPROVED")
        self.mock_db.flush.assert_called_once()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试审批驳回时状态变更"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "PENDING_APPROVAL"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        mock_instance = Mock(spec=ApprovalInstance)

        # 执行测试
        self.adapter.on_rejected(1, mock_instance)

        # 验证
        self.assertEqual(mock_order.status, "REJECTED")
        self.mock_db.flush.assert_called_once()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试审批撤回时状态变更"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "PENDING_APPROVAL"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        mock_instance = Mock(spec=ApprovalInstance)

        # 执行测试
        self.adapter.on_withdrawn(1, mock_instance)

        # 验证
        self.assertEqual(mock_order.status, "DRAFT")
        self.mock_db.flush.assert_called_once()

    # ========== generate_title() 测试 ==========

    def test_generate_title_with_order_title(self):
        """测试生成审批标题（带订单标题）"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.order_no = "OS-2024-001"
        mock_order.order_title = "设备外协加工"

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        # 执行测试
        result = self.adapter.generate_title(1)

        # 验证
        self.assertEqual(result, "外协订单审批 - OS-2024-001 - 设备外协加工")

    def test_generate_title_without_order_title(self):
        """测试生成审批标题（无订单标题）"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.order_no = "OS-2024-002"
        mock_order.order_title = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        # 执行测试
        result = self.adapter.generate_title(1)

        # 验证
        self.assertEqual(result, "外协订单审批 - OS-2024-002")

    def test_generate_title_order_not_found(self):
        """测试订单不存在时的标题"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # 执行测试
        result = self.adapter.generate_title(999)

        # 验证
        self.assertEqual(result, "外协订单审批 - 999")

    # ========== generate_summary() 测试 ==========

    def test_generate_summary_complete(self):
        """测试生成完整审批摘要"""
        # 准备mock订单
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.order_no = "OS-2024-001"
        mock_order.order_type = "MACHINING"
        mock_order.amount_with_tax = Decimal("11300.00")
        mock_order.required_date = date(2024, 12, 31)
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.machine_id = 20

        # 准备关联对象
        mock_vendor = Mock(spec=Vendor)
        mock_vendor.vendor_name = "XX外协厂"

        mock_project = Mock(spec=Project)
        mock_project.project_name = "测试项目"

        mock_machine = Mock(spec=Machine)
        mock_machine.machine_code = "MC-001"

        # 配置数据库查询
        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 3
            elif model == Vendor:
                mock_filter.first.return_value = mock_vendor
            elif model == Project:
                mock_filter.first.return_value = mock_project
            elif model == Machine:
                mock_filter.first.return_value = mock_machine

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.adapter.generate_summary(1)

        # 验证摘要包含关键信息
        self.assertIn("OS-2024-001", result)
        self.assertIn("XX外协厂", result)
        self.assertIn("MACHINING", result)
        self.assertIn("¥11,300.00", result)
        self.assertIn("明细行数: 3", result)
        self.assertIn("2024-12-31", result)
        self.assertIn("测试项目", result)
        self.assertIn("MC-001", result)

    def test_generate_summary_minimal(self):
        """测试生成最小化摘要"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.order_no = "OS-2024-002"
        mock_order.order_type = "WELDING"
        mock_order.amount_with_tax = None
        mock_order.required_date = None
        mock_order.vendor_id = None
        mock_order.project_id = None
        mock_order.machine_id = None

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 0
            else:
                mock_filter.first.return_value = None

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        result = self.adapter.generate_summary(1)

        # 验证
        self.assertIn("OS-2024-002", result)
        self.assertIn("未指定", result)  # 默认外协商
        self.assertIn("WELDING", result)
        self.assertIn("未填写", result)  # 金额未填写

    def test_generate_summary_order_not_found(self):
        """测试订单不存在时返回空摘要"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.adapter.generate_summary(999)

        self.assertEqual(result, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success(self):
        """测试验证成功的情况"""
        # 准备完整有效的订单
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = "测试订单"
        mock_order.order_type = "MACHINING"
        mock_order.amount_with_tax = Decimal("10000.00")
        mock_order.required_date = date(2024, 12, 31)

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 2

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # 执行测试
        is_valid, error = self.adapter.validate_submit(1)

        # 验证
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_submit_order_not_found(self):
        """测试订单不存在"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        is_valid, error = self.adapter.validate_submit(999)

        self.assertFalse(is_valid)
        self.assertEqual(error, "外协订单不存在")

    def test_validate_submit_invalid_status(self):
        """测试无效的订单状态"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "APPROVED"  # 已审批状态不能重新提交

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertIn("当前状态", error)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_missing_vendor(self):
        """测试缺少外协商"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "请选择外协商")

    def test_validate_submit_missing_project(self):
        """测试缺少关联项目"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "请关联项目")

    def test_validate_submit_missing_title(self):
        """测试缺少订单标题"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "请填写订单标题")

    def test_validate_submit_missing_order_type(self):
        """测试缺少订单类型"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = "测试"
        mock_order.order_type = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "请选择订单类型")

    def test_validate_submit_no_items(self):
        """测试订单无明细行"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = "测试"
        mock_order.order_type = "MACHINING"

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 0  # 无明细

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "外协订单至少需要一条明细")

    def test_validate_submit_invalid_amount(self):
        """测试无效的订单金额"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = "测试"
        mock_order.order_type = "MACHINING"
        mock_order.amount_with_tax = Decimal("0.00")  # 金额为0

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 1

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "订单总金额必须大于0")

    def test_validate_submit_missing_required_date(self):
        """测试缺少要求交期"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "DRAFT"
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = "测试"
        mock_order.order_type = "MACHINING"
        mock_order.amount_with_tax = Decimal("10000.00")
        mock_order.required_date = None  # 缺少交期

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 1

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        is_valid, error = self.adapter.validate_submit(1)

        self.assertFalse(is_valid)
        self.assertEqual(error, "请填写要求交期")

    # ========== get_cc_user_ids() 测试 ==========

    def test_get_cc_user_ids_with_project_manager(self):
        """测试获取抄送人（包含项目经理）"""
        # 准备mock订单
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.project_id = 10

        # 准备项目
        mock_project = Mock(spec=Project)
        mock_project.manager_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == Project:
                mock_filter.first.return_value = mock_project

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock部门负责人查询方法
        with patch.object(
            self.adapter,
            'get_department_manager_user_ids_by_codes',
            return_value=[200, 300]
        ):
            # 执行测试
            result = self.adapter.get_cc_user_ids(1)

            # 验证：应包含项目经理和生产部门负责人
            self.assertIn(100, result)
            self.assertIn(200, result)
            self.assertIn(300, result)
            # 验证去重
            self.assertEqual(len(result), len(set(result)))

    def test_get_cc_user_ids_no_project_manager(self):
        """测试项目无经理时的抄送人"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.project_id = 10

        mock_project = Mock(spec=Project)
        mock_project.manager_id = None  # 无项目经理

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == Project:
                mock_filter.first.return_value = mock_project

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        with patch.object(
            self.adapter,
            'get_department_manager_user_ids_by_codes',
            return_value=[200]
        ):
            result = self.adapter.get_cc_user_ids(1)

            # 验证：只包含部门负责人
            self.assertIn(200, result)
            self.assertEqual(len(result), 1)

    def test_get_cc_user_ids_order_not_found(self):
        """测试订单不存在时返回空列表"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.adapter.get_cc_user_ids(999)

        self.assertEqual(result, [])

    def test_get_cc_user_ids_no_project(self):
        """测试订单无关联项目"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.project_id = None

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_order

        with patch.object(
            self.adapter,
            'get_department_manager_user_ids_by_codes',
            return_value=[200]
        ):
            result = self.adapter.get_cc_user_ids(1)

            # 验证：只包含部门负责人
            self.assertIn(200, result)

    def test_get_cc_user_ids_deduplication(self):
        """测试抄送人去重"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.project_id = 10

        mock_project = Mock(spec=Project)
        mock_project.manager_id = 100

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == Project:
                mock_filter.first.return_value = mock_project

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        # Mock返回重复的用户ID
        with patch.object(
            self.adapter,
            'get_department_manager_user_ids_by_codes',
            return_value=[100, 200, 100]  # 包含重复ID
        ):
            result = self.adapter.get_cc_user_ids(1)

            # 验证去重
            self.assertEqual(len(result), len(set(result)))
            self.assertIn(100, result)
            self.assertIn(200, result)

    # ========== 边界情况和异常处理 ==========

    def test_entity_type_attribute(self):
        """测试entity_type属性"""
        self.assertEqual(self.adapter.entity_type, "OUTSOURCING_ORDER")

    def test_callbacks_with_none_order(self):
        """测试所有回调方法在订单不存在时不抛异常"""
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        mock_instance = Mock(spec=ApprovalInstance)

        # 不应抛出异常
        self.adapter.on_submit(999, mock_instance)
        self.adapter.on_approved(999, mock_instance)
        self.adapter.on_rejected(999, mock_instance)
        self.adapter.on_withdrawn(999, mock_instance)

        # flush不应被调用
        self.mock_db.flush.assert_not_called()

    def test_get_entity_data_with_none_amounts(self):
        """测试金额为None时的处理"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.id = 1
        mock_order.order_no = "TEST"
        mock_order.order_title = "Test"
        mock_order.order_type = "TEST"
        mock_order.order_description = None
        mock_order.status = "DRAFT"
        mock_order.total_amount = None
        mock_order.tax_rate = None
        mock_order.tax_amount = None
        mock_order.amount_with_tax = None
        mock_order.paid_amount = None
        mock_order.required_date = None
        mock_order.estimated_date = None
        mock_order.actual_date = None
        mock_order.payment_status = "UNPAID"
        mock_order.contract_no = None
        mock_order.project_id = None
        mock_order.machine_id = None
        mock_order.vendor_id = None
        mock_order.created_by = 1

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 0

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.adapter.get_entity_data(1)

        # 验证None金额被转换为0
        self.assertEqual(result["total_amount"], 0)
        self.assertEqual(result["tax_rate"], 0)
        self.assertEqual(result["tax_amount"], 0)
        self.assertEqual(result["amount_with_tax"], 0)
        self.assertEqual(result["paid_amount"], 0)

    def test_validate_submit_rejected_status_allowed(self):
        """测试REJECTED状态允许重新提交"""
        mock_order = Mock(spec=OutsourcingOrder)
        mock_order.status = "REJECTED"  # 被驳回后可重新提交
        mock_order.vendor_id = 30
        mock_order.project_id = 10
        mock_order.order_title = "测试"
        mock_order.order_type = "MACHINING"
        mock_order.amount_with_tax = Decimal("10000.00")
        mock_order.required_date = date(2024, 12, 31)

        def query_side_effect(model):
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_query.filter.return_value = mock_filter

            if model == OutsourcingOrder:
                mock_filter.first.return_value = mock_order
            elif model == OutsourcingOrderItem:
                mock_filter.count.return_value = 1

            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        is_valid, error = self.adapter.validate_submit(1)

        self.assertTrue(is_valid)
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
