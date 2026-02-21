# -*- coding: utf-8 -*-
"""
外协订单审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真实执行
3. 达到70%+覆盖率

策略：
- Mock db.query() 返回值，让适配器逻辑真正运行
- 测试所有核心方法的主要分支
- 覆盖边界情况和异常处理
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date
from decimal import Decimal

from app.services.approval_engine.adapters.outsourcing import OutsourcingOrderApprovalAdapter
from app.models.outsourcing import OutsourcingOrder, OutsourcingOrderItem
from app.models.project import Project, Machine
from app.models.vendor import Vendor


class TestOutsourcingAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.adapter = OutsourcingOrderApprovalAdapter(self.db)

    def _create_sample_order(self, **kwargs):
        """创建示例订单"""
        order = MagicMock(spec=OutsourcingOrder)
        order.id = kwargs.get('id', 1)
        order.order_no = kwargs.get('order_no', 'OUT-2024-001')
        order.order_title = kwargs.get('order_title', '机架焊接加工')
        order.order_type = kwargs.get('order_type', 'WELDING')
        order.order_description = kwargs.get('order_description', '机架主体焊接')
        order.status = kwargs.get('status', 'DRAFT')
        order.total_amount = Decimal(kwargs.get('total_amount', '50000.00'))
        order.tax_rate = Decimal(kwargs.get('tax_rate', '0.13'))
        order.tax_amount = Decimal(kwargs.get('tax_amount', '6500.00'))
        order.amount_with_tax = Decimal(kwargs.get('amount_with_tax', '56500.00'))
        order.required_date = kwargs.get('required_date', date(2024, 3, 15))
        order.estimated_date = kwargs.get('estimated_date', date(2024, 3, 10))
        order.actual_date = kwargs.get('actual_date', None)
        order.payment_status = kwargs.get('payment_status', 'UNPAID')
        order.paid_amount = Decimal(kwargs.get('paid_amount', '0.00'))
        order.contract_no = kwargs.get('contract_no', 'CON-2024-001')
        order.project_id = kwargs.get('project_id', 10)
        order.machine_id = kwargs.get('machine_id', 20)
        order.vendor_id = kwargs.get('vendor_id', 5)
        order.created_by = kwargs.get('created_by', 100)
        return order

    # ========== 测试 get_entity ==========

    def test_get_entity_found(self):
        """测试成功获取订单"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.adapter.get_entity(1)

        self.assertEqual(result, order)
        self.db.query.assert_called_once()

    def test_get_entity_not_found(self):
        """测试订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(999)

        self.assertIsNone(result)

    # ========== 测试 get_entity_data ==========

    def test_get_entity_data_not_found(self):
        """测试订单不存在返回空字典"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(999)

        self.assertEqual(result, {})

    def test_get_entity_data_basic_info(self):
        """测试基础订单信息"""
        order = self._create_sample_order()
        
        # Mock 查询序列：订单 -> 项目 -> 设备 -> 外协商（都不存在）
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,  # 获取订单
            None,   # 项目不存在
            None,   # 设备不存在
            None,   # 外协商不存在
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 3

        result = self.adapter.get_entity_data(1)

        self.assertEqual(result['order_no'], 'OUT-2024-001')
        self.assertEqual(result['order_title'], '机架焊接加工')
        self.assertEqual(result['order_type'], 'WELDING')
        self.assertEqual(result['status'], 'DRAFT')
        self.assertEqual(result['total_amount'], 50000.0)
        self.assertEqual(result['tax_rate'], 0.13)
        self.assertEqual(result['amount_with_tax'], 56500.0)
        self.assertEqual(result['item_count'], 3)
        self.assertEqual(result['vendor_id'], 5)
        self.assertEqual(result['project_id'], 10)
        self.assertEqual(result['machine_id'], 20)

    def test_get_entity_data_with_project_info(self):
        """测试包含项目信息"""
        order = self._create_sample_order()
        
        project = MagicMock(spec=Project)
        project.project_code = 'PRJ-001'
        project.project_name = '测试项目'
        project.status = 'IN_PROGRESS'
        
        # Mock 查询序列：订单 -> 项目 -> 设备 -> 外协商
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,    # 获取订单
            project,  # 获取项目
            None,     # 获取设备（无）
            None,     # 获取外协商（无）
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 2

        result = self.adapter.get_entity_data(1)

        self.assertEqual(result['project_code'], 'PRJ-001')
        self.assertEqual(result['project_name'], '测试项目')
        self.assertEqual(result['project_status'], 'IN_PROGRESS')

    def test_get_entity_data_with_machine_info(self):
        """测试包含设备信息"""
        order = self._create_sample_order()
        
        machine = MagicMock(spec=Machine)
        machine.machine_code = 'MC-001'
        machine.machine_name = '焊接机1号'
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,    # 订单
            None,     # 项目（无）
            machine,  # 设备
            None,     # 外协商（无）
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 1

        result = self.adapter.get_entity_data(1)

        self.assertEqual(result['machine_code'], 'MC-001')
        self.assertEqual(result['machine_name'], '焊接机1号')

    def test_get_entity_data_with_vendor_info(self):
        """测试包含外协商信息"""
        order = self._create_sample_order()
        
        vendor = MagicMock(spec=Vendor)
        vendor.vendor_name = 'XX焊接厂'
        vendor.vendor_code = 'VEN-001'
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,   # 订单
            None,    # 项目
            None,    # 设备
            vendor,  # 外协商
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 4

        result = self.adapter.get_entity_data(1)

        self.assertEqual(result['vendor_name'], 'XX焊接厂')
        self.assertEqual(result['vendor_code'], 'VEN-001')

    def test_get_entity_data_with_null_amounts(self):
        """测试金额为None的情况"""
        # 创建订单时直接设置属性为None，不通过Decimal转换
        order = MagicMock(spec=OutsourcingOrder)
        order.id = 1
        order.order_no = 'OUT-2024-001'
        order.order_title = '测试订单'
        order.order_type = 'WELDING'
        order.order_description = '测试'
        order.status = 'DRAFT'
        order.total_amount = None
        order.tax_rate = None
        order.tax_amount = None
        order.amount_with_tax = None
        order.required_date = None
        order.estimated_date = None
        order.actual_date = None
        order.payment_status = 'UNPAID'
        order.paid_amount = None
        order.contract_no = 'CON-001'
        order.project_id = None
        order.machine_id = None
        order.vendor_id = None
        order.created_by = 100
        
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 0

        result = self.adapter.get_entity_data(1)

        self.assertEqual(result['total_amount'], 0)
        self.assertEqual(result['tax_rate'], 0)
        self.assertEqual(result['amount_with_tax'], 0)

    def test_get_entity_data_with_null_dates(self):
        """测试日期为None的情况"""
        order = self._create_sample_order(
            required_date=None,
            estimated_date=None,
            actual_date=None
        )
        
        # Mock 查询序列：订单 -> 项目 -> 设备 -> 外协商（都不存在）
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,  # 订单
            None,   # 项目
            None,   # 设备
            None,   # 外协商
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 1

        result = self.adapter.get_entity_data(1)

        self.assertIsNone(result['required_date'])
        self.assertIsNone(result['estimated_date'])
        self.assertIsNone(result['actual_date'])

    def test_get_entity_data_date_formatting(self):
        """测试日期格式化"""
        order = self._create_sample_order(
            required_date=date(2024, 3, 15),
            estimated_date=date(2024, 3, 10),
            actual_date=date(2024, 3, 20)
        )
        
        # Mock 查询序列
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,  # 订单
            None,   # 项目
            None,   # 设备
            None,   # 外协商
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 1

        result = self.adapter.get_entity_data(1)

        self.assertEqual(result['required_date'], '2024-03-15')
        self.assertEqual(result['estimated_date'], '2024-03-10')
        self.assertEqual(result['actual_date'], '2024-03-20')

    # ========== 测试状态回调方法 ==========

    def test_on_submit_success(self):
        """测试提交审批回调"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        instance = MagicMock()
        self.adapter.on_submit(1, instance)

        self.assertEqual(order.status, 'PENDING_APPROVAL')
        self.db.flush.assert_called_once()

    def test_on_submit_order_not_found(self):
        """测试提交时订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        instance = MagicMock()
        self.adapter.on_submit(999, instance)

        self.db.flush.assert_not_called()

    def test_on_approved_success(self):
        """测试审批通过回调"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        instance = MagicMock()
        self.adapter.on_approved(1, instance)

        self.assertEqual(order.status, 'APPROVED')
        self.db.flush.assert_called_once()

    def test_on_approved_order_not_found(self):
        """测试审批通过时订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        instance = MagicMock()
        self.adapter.on_approved(999, instance)

        self.db.flush.assert_not_called()

    def test_on_rejected_success(self):
        """测试审批驳回回调"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        instance = MagicMock()
        self.adapter.on_rejected(1, instance)

        self.assertEqual(order.status, 'REJECTED')
        self.db.flush.assert_called_once()

    def test_on_rejected_order_not_found(self):
        """测试驳回时订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        instance = MagicMock()
        self.adapter.on_rejected(999, instance)

        self.db.flush.assert_not_called()

    def test_on_withdrawn_success(self):
        """测试撤回审批回调"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        instance = MagicMock()
        self.adapter.on_withdrawn(1, instance)

        self.assertEqual(order.status, 'DRAFT')
        self.db.flush.assert_called_once()

    def test_on_withdrawn_order_not_found(self):
        """测试撤回时订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        instance = MagicMock()
        self.adapter.on_withdrawn(999, instance)

        self.db.flush.assert_not_called()

    # ========== 测试 generate_title ==========

    def test_generate_title_with_order_title(self):
        """测试包含订单标题"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.adapter.generate_title(1)

        self.assertEqual(result, '外协订单审批 - OUT-2024-001 - 机架焊接加工')

    def test_generate_title_without_order_title(self):
        """测试没有订单标题"""
        order = self._create_sample_order(order_title=None)
        self.db.query.return_value.filter.return_value.first.return_value = order

        result = self.adapter.generate_title(1)

        self.assertEqual(result, '外协订单审批 - OUT-2024-001')

    def test_generate_title_order_not_found(self):
        """测试订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.generate_title(999)

        self.assertEqual(result, '外协订单审批 - 999')

    # ========== 测试 generate_summary ==========

    def test_generate_summary_complete_info(self):
        """测试完整信息的摘要"""
        order = self._create_sample_order()
        
        vendor = MagicMock(spec=Vendor)
        vendor.vendor_name = 'XX焊接厂'
        
        project = MagicMock(spec=Project)
        project.project_name = '测试项目'
        
        machine = MagicMock(spec=Machine)
        machine.machine_code = 'MC-001'
        
        # Mock 查询序列
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,   # 获取订单
            vendor,  # 获取外协商
            project, # 获取项目
            machine, # 获取设备
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 3

        result = self.adapter.generate_summary(1)

        self.assertIn('OUT-2024-001', result)
        self.assertIn('XX焊接厂', result)
        self.assertIn('WELDING', result)
        self.assertIn('¥56,500.00', result)
        self.assertIn('明细行数: 3', result)
        self.assertIn('2024-03-15', result)
        self.assertIn('测试项目', result)
        self.assertIn('MC-001', result)

    def test_generate_summary_order_not_found(self):
        """测试订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.generate_summary(999)

        self.assertEqual(result, '')

    def test_generate_summary_without_vendor(self):
        """测试没有外协商"""
        order = self._create_sample_order(vendor_id=None, project_id=None, machine_id=None)
        
        # Mock 查询序列：只返回订单（vendor_id=None不会查询外协商）
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 2

        result = self.adapter.generate_summary(1)

        self.assertIn('未指定', result)

    def test_generate_summary_without_amount(self):
        """测试没有金额"""
        # 创建金额为None的订单
        order = MagicMock(spec=OutsourcingOrder)
        order.id = 1
        order.order_no = 'OUT-2024-001'
        order.order_title = '测试订单'
        order.order_type = 'WELDING'
        order.status = 'DRAFT'
        order.amount_with_tax = None  # 金额为None
        order.required_date = date(2024, 3, 15)
        order.project_id = None
        order.machine_id = None
        order.vendor_id = 5
        
        vendor = MagicMock(spec=Vendor)
        vendor.vendor_name = '测试外协商'
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,
            vendor,
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 1

        result = self.adapter.generate_summary(1)

        self.assertIn('未填写', result)

    def test_generate_summary_minimal_info(self):
        """测试最小信息（无可选字段）"""
        order = self._create_sample_order(
            required_date=None,
            project_id=None,
            machine_id=None
        )
        
        vendor = MagicMock(spec=Vendor)
        vendor.vendor_name = '外协商A'
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,
            vendor,
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 5

        result = self.adapter.generate_summary(1)

        # 应该只有基本字段
        parts = result.split(' | ')
        self.assertGreaterEqual(len(parts), 5)
        # 不应包含日期、项目、设备
        self.assertNotIn('关联项目', result)
        self.assertNotIn('关联设备', result)

    # ========== 测试 validate_submit ==========

    def test_validate_submit_success(self):
        """测试所有条件满足"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 2

        can_submit, error = self.adapter.validate_submit(1)

        self.assertTrue(can_submit)
        self.assertIsNone(error)

    def test_validate_submit_order_not_found(self):
        """测试订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        can_submit, error = self.adapter.validate_submit(999)

        self.assertFalse(can_submit)
        self.assertEqual(error, '外协订单不存在')

    def test_validate_submit_invalid_status(self):
        """测试无效状态"""
        order = self._create_sample_order(status='APPROVED')
        self.db.query.return_value.filter.return_value.first.return_value = order

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertIn('不允许提交审批', error)

    def test_validate_submit_rejected_status_allowed(self):
        """测试驳回状态允许提交"""
        order = self._create_sample_order(status='REJECTED')
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = self.adapter.validate_submit(1)

        self.assertTrue(can_submit)
        self.assertIsNone(error)

    def test_validate_submit_missing_vendor(self):
        """测试缺少外协商"""
        order = self._create_sample_order(vendor_id=None)
        self.db.query.return_value.filter.return_value.first.return_value = order

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '请选择外协商')

    def test_validate_submit_missing_project(self):
        """测试缺少项目"""
        order = self._create_sample_order(project_id=None)
        self.db.query.return_value.filter.return_value.first.return_value = order

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '请关联项目')

    def test_validate_submit_missing_title(self):
        """测试缺少订单标题"""
        order = self._create_sample_order(order_title=None)
        self.db.query.return_value.filter.return_value.first.return_value = order

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '请填写订单标题')

    def test_validate_submit_missing_order_type(self):
        """测试缺少订单类型"""
        order = self._create_sample_order(order_type=None)
        self.db.query.return_value.filter.return_value.first.return_value = order

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '请选择订单类型')

    def test_validate_submit_no_items(self):
        """测试没有订单明细"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 0

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '外协订单至少需要一条明细')

    def test_validate_submit_zero_amount(self):
        """测试金额为0"""
        order = self._create_sample_order(amount_with_tax=Decimal('0'))
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '订单总金额必须大于0')

    def test_validate_submit_negative_amount(self):
        """测试负金额"""
        order = self._create_sample_order(amount_with_tax=Decimal('-100'))
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '订单总金额必须大于0')

    def test_validate_submit_null_amount(self):
        """测试金额为None"""
        # 创建金额为None的订单
        order = MagicMock(spec=OutsourcingOrder)
        order.id = 1
        order.order_no = 'OUT-2024-001'
        order.order_title = '测试订单'
        order.order_type = 'WELDING'
        order.status = 'DRAFT'
        order.vendor_id = 5
        order.project_id = 10
        order.amount_with_tax = None  # 金额为None
        order.required_date = date(2024, 3, 15)
        
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 1

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '订单总金额必须大于0')

    def test_validate_submit_missing_required_date(self):
        """测试缺少要求交期"""
        order = self._create_sample_order(required_date=None)
        self.db.query.return_value.filter.return_value.first.return_value = order
        self.db.query.return_value.filter.return_value.count.return_value = 3

        can_submit, error = self.adapter.validate_submit(1)

        self.assertFalse(can_submit)
        self.assertEqual(error, '请填写要求交期')

    # ========== 测试 get_cc_user_ids ==========

    def test_get_cc_user_ids_order_not_found(self):
        """测试订单不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_cc_user_ids(999)

        self.assertEqual(result, [])

    def test_get_cc_user_ids_with_project_manager(self):
        """测试项目经理抄送"""
        order = self._create_sample_order()
        
        project = MagicMock(spec=Project)
        project.manager_id = 200
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,
            project,
        ]
        
        with patch.object(self.adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(self.adapter, 'get_department_manager_user_id', return_value=None):
                result = self.adapter.get_cc_user_ids(1)

        self.assertIn(200, result)

    def test_get_cc_user_ids_without_project(self):
        """测试没有关联项目"""
        order = self._create_sample_order(project_id=None)
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        with patch.object(self.adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(self.adapter, 'get_department_manager_user_id', return_value=None):
                result = self.adapter.get_cc_user_ids(1)

        self.assertEqual(result, [])

    def test_get_cc_user_ids_with_prod_dept_managers(self):
        """测试生产部门负责人抄送"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        with patch.object(self.adapter, 'get_department_manager_user_ids_by_codes', return_value=[300, 301]):
            result = self.adapter.get_cc_user_ids(1)

        self.assertIn(300, result)
        self.assertIn(301, result)

    def test_get_cc_user_ids_with_fallback_dept_name(self):
        """测试备用部门名称查找"""
        order = self._create_sample_order()
        self.db.query.return_value.filter.return_value.first.return_value = order
        
        with patch.object(self.adapter, 'get_department_manager_user_ids_by_codes', return_value=[]):
            with patch.object(self.adapter, 'get_department_manager_user_id', return_value=400):
                result = self.adapter.get_cc_user_ids(1)

        self.assertIn(400, result)

    def test_get_cc_user_ids_deduplication(self):
        """测试去重"""
        order = self._create_sample_order()
        
        project = MagicMock(spec=Project)
        project.manager_id = 500
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,
            project,
        ]
        
        # 生产部门负责人也是500，应该去重
        with patch.object(self.adapter, 'get_department_manager_user_ids_by_codes', return_value=[500, 501]):
            result = self.adapter.get_cc_user_ids(1)

        self.assertEqual(result.count(500), 1)  # 只出现一次
        self.assertIn(501, result)

    def test_get_cc_user_ids_project_without_manager(self):
        """测试项目没有经理"""
        order = self._create_sample_order()
        
        project = MagicMock(spec=Project)
        project.manager_id = None
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            order,
            project,
        ]
        
        with patch.object(self.adapter, 'get_department_manager_user_ids_by_codes', return_value=[600]):
            result = self.adapter.get_cc_user_ids(1)

        # 只应该有部门负责人
        self.assertEqual(result, [600])


class TestAdapterProperties(unittest.TestCase):
    """测试适配器属性"""

    def setUp(self):
        self.db = MagicMock()
        self.adapter = OutsourcingOrderApprovalAdapter(self.db)

    def test_entity_type(self):
        """测试实体类型"""
        self.assertEqual(self.adapter.entity_type, 'OUTSOURCING_ORDER')

    def test_db_attribute(self):
        """测试数据库session"""
        self.assertEqual(self.adapter.db, self.db)


if __name__ == '__main__':
    unittest.main()
