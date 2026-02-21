# -*- coding: utf-8 -*-
"""
库存盘点服务增强测试
覆盖所有核心方法和边界条件
"""
import unittest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.stock_count_service import StockCountService
from app.models.inventory_tracking import (
    StockCountTask,
    StockCountDetail,
    StockAdjustment,
    MaterialStock,
    MaterialTransaction,
)
from app.models.material import Material


class TestStockCountService(unittest.TestCase):
    """库存盘点服务测试"""

    def setUp(self):
        """测试前置"""
        self.db = MagicMock()
        self.tenant_id = 1
        self.service = StockCountService(self.db, self.tenant_id)

    def tearDown(self):
        """测试清理"""
        self.db.reset_mock()

    # ============ 盘点任务创建测试 ============

    def test_create_count_task_success(self):
        """测试创建盘点任务 - 成功"""
        # Mock数据库操作
        self.db.flush = MagicMock()
        self.db.commit = MagicMock()
        
        # Mock _create_count_details
        with patch.object(self.service, '_create_count_details', return_value=[]):
            task = self.service.create_count_task(
                count_type='FULL',
                count_date=date(2024, 1, 15),
                location='仓库A',
                created_by=1,
                assigned_to=2
            )
        
        # 验证
        self.assertIsInstance(task, StockCountTask)
        self.assertEqual(task.tenant_id, self.tenant_id)
        self.assertEqual(task.count_type, 'FULL')
        self.assertEqual(task.status, 'PENDING')
        self.assertTrue(task.task_no.startswith('CNT-'))
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_create_count_task_with_all_params(self):
        """测试创建盘点任务 - 包含所有参数"""
        with patch.object(self.service, '_create_count_details', return_value=[]):
            task = self.service.create_count_task(
                count_type='PARTIAL',
                count_date=date(2024, 1, 15),
                location='仓库B',
                category_id=10,
                material_ids=[1, 2, 3],
                created_by=1,
                assigned_to=2,
                remark='年度盘点'
            )
        
        self.assertEqual(task.location, '仓库B')
        self.assertEqual(task.category_id, 10)
        self.assertEqual(task.remark, '年度盘点')

    def test_create_count_task_initializes_counters(self):
        """测试创建盘点任务 - 初始化计数器"""
        with patch.object(self.service, '_create_count_details', return_value=[]):
            task = self.service.create_count_task(
                count_type='FULL',
                count_date=date(2024, 1, 15)
            )
        
        self.assertEqual(task.total_items, 0)
        self.assertEqual(task.counted_items, 0)
        self.assertEqual(task.matched_items, 0)
        self.assertEqual(task.diff_items, 0)
        self.assertEqual(task.total_diff_value, Decimal(0))

    # ============ 盘点明细创建测试 ============

    def test_create_count_details_basic(self):
        """测试创建盘点明细 - 基本功能"""
        # Mock库存查询
        mock_stock = MagicMock(spec=MaterialStock)
        mock_stock.id = 1
        mock_stock.material_id = 100
        mock_stock.material_code = 'MAT001'
        mock_stock.material_name = '物料A'
        mock_stock.location = '仓库A'
        mock_stock.batch_number = 'B001'
        mock_stock.quantity = Decimal('100')
        mock_stock.unit_price = Decimal('10.5')
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = [mock_stock]
        
        self.db.query.return_value = mock_query
        
        task = StockCountTask(id=1, tenant_id=self.tenant_id)
        
        details = self.service._create_count_details(
            task=task,
            location='仓库A',
            category_id=None,
            material_ids=None
        )
        
        self.assertEqual(len(details), 1)
        detail = details[0]
        self.assertEqual(detail.material_id, 100)
        self.assertEqual(detail.system_quantity, Decimal('100'))
        self.assertEqual(detail.status, 'PENDING')
        self.assertIsNone(detail.actual_quantity)

    def test_create_count_details_filter_by_location(self):
        """测试创建盘点明细 - 按位置过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query
        
        task = StockCountTask(id=1, tenant_id=self.tenant_id)
        
        self.service._create_count_details(
            task=task,
            location='仓库B',
            category_id=None,
            material_ids=None
        )
        
        # 验证location过滤被调用
        self.assertTrue(mock_query.filter.called)

    def test_create_count_details_filter_by_category(self):
        """测试创建盘点明细 - 按分类过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query
        
        task = StockCountTask(id=1, tenant_id=self.tenant_id)
        
        self.service._create_count_details(
            task=task,
            location=None,
            category_id=5,
            material_ids=None
        )
        
        # 验证join被调用（用于category过滤）
        self.assertTrue(mock_query.join.called)

    def test_create_count_details_filter_by_material_ids(self):
        """测试创建盘点明细 - 按物料ID过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query
        
        task = StockCountTask(id=1, tenant_id=self.tenant_id)
        
        self.service._create_count_details(
            task=task,
            location=None,
            category_id=None,
            material_ids=[1, 2, 3]
        )
        
        # 验证filter被多次调用
        self.assertTrue(mock_query.filter.called)

    def test_create_count_details_empty_stock(self):
        """测试创建盘点明细 - 空库存"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query
        
        task = StockCountTask(id=1, tenant_id=self.tenant_id)
        
        details = self.service._create_count_details(
            task=task,
            location=None,
            category_id=None,
            material_ids=None
        )
        
        self.assertEqual(len(details), 0)

    # ============ 盘点任务查询测试 ============

    def test_get_count_tasks_no_filter(self):
        """测试查询盘点任务 - 无过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        tasks = self.service.get_count_tasks()
        
        self.assertEqual(tasks, [])
        self.db.query.assert_called_once_with(StockCountTask)

    def test_get_count_tasks_filter_by_status(self):
        """测试查询盘点任务 - 按状态过滤"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_task]
        
        self.db.query.return_value = mock_query
        
        tasks = self.service.get_count_tasks(status='IN_PROGRESS')
        
        self.assertEqual(len(tasks), 1)

    def test_get_count_tasks_filter_by_date_range(self):
        """测试查询盘点任务 - 按日期范围过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        tasks = self.service.get_count_tasks(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证filter被调用（包括tenant_id + start_date + end_date）
        self.assertTrue(mock_query.filter.called)

    def test_get_count_tasks_custom_limit(self):
        """测试查询盘点任务 - 自定义限制"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        self.service.get_count_tasks(limit=100)
        
        mock_query.limit.assert_called_with(100)

    def test_get_count_task_success(self):
        """测试获取盘点任务详情 - 成功"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_task
        
        self.db.query.return_value = mock_query
        
        task = self.service.get_count_task(1)
        
        self.assertEqual(task.id, 1)

    def test_get_count_task_not_found(self):
        """测试获取盘点任务详情 - 不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        self.db.query.return_value = mock_query
        
        task = self.service.get_count_task(999)
        
        self.assertIsNone(task)

    # ============ 盘点任务状态管理测试 ============

    def test_start_count_task_success(self):
        """测试开始盘点 - 成功"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'PENDING'
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            task = self.service.start_count_task(1)
        
        self.assertEqual(task.status, 'IN_PROGRESS')
        self.assertIsNotNone(task.start_time)
        self.db.commit.assert_called_once()

    def test_start_count_task_not_found(self):
        """测试开始盘点 - 任务不存在"""
        with patch.object(self.service, 'get_count_task', return_value=None):
            with self.assertRaises(ValueError) as context:
                self.service.start_count_task(999)
        
        self.assertIn('盘点任务不存在', str(context.exception))

    def test_start_count_task_invalid_status(self):
        """测试开始盘点 - 状态不允许"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'COMPLETED'
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with self.assertRaises(ValueError) as context:
                self.service.start_count_task(1)
        
        self.assertIn('盘点任务状态不允许开始', str(context.exception))

    def test_cancel_count_task_success(self):
        """测试取消盘点 - 成功"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'PENDING'
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            task = self.service.cancel_count_task(1)
        
        self.assertEqual(task.status, 'CANCELLED')
        self.db.commit.assert_called_once()

    def test_cancel_count_task_completed(self):
        """测试取消盘点 - 已完成任务不能取消"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'COMPLETED'
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with self.assertRaises(ValueError) as context:
                self.service.cancel_count_task(1)
        
        self.assertIn('已完成的盘点任务不能取消', str(context.exception))

    # ============ 盘点明细管理测试 ============

    def test_get_count_details_success(self):
        """测试获取盘点明细 - 成功"""
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_detail]
        
        self.db.query.return_value = mock_query
        
        details = self.service.get_count_details(1)
        
        self.assertEqual(len(details), 1)

    def test_record_actual_quantity_success(self):
        """测试录入实盘数量 - 成功"""
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.id = 1
        mock_detail.system_quantity = Decimal('100')
        mock_detail.unit_price = Decimal('10')
        mock_detail.task_id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detail
        
        self.db.query.return_value = mock_query
        
        with patch.object(self.service, '_update_task_statistics'):
            detail = self.service.record_actual_quantity(
                detail_id=1,
                actual_quantity=Decimal('95'),
                counted_by=1,
                remark='盘点备注'
            )
        
        self.assertEqual(detail.actual_quantity, Decimal('95'))
        self.assertEqual(detail.difference, Decimal('-5'))
        self.assertEqual(detail.diff_value, Decimal('-50'))
        self.assertEqual(detail.status, 'COUNTED')
        self.assertIsNotNone(detail.counted_at)

    def test_record_actual_quantity_zero_system_quantity(self):
        """测试录入实盘数量 - 系统数量为0"""
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.system_quantity = Decimal('0')
        mock_detail.unit_price = Decimal('10')
        mock_detail.task_id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_detail
        
        self.db.query.return_value = mock_query
        
        with patch.object(self.service, '_update_task_statistics'):
            detail = self.service.record_actual_quantity(
                detail_id=1,
                actual_quantity=Decimal('10')
            )
        
        self.assertEqual(detail.difference_rate, Decimal('0'))

    def test_record_actual_quantity_not_found(self):
        """测试录入实盘数量 - 明细不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        self.db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.record_actual_quantity(
                detail_id=999,
                actual_quantity=Decimal('100')
            )
        
        self.assertIn('盘点明细不存在', str(context.exception))

    def test_batch_record_quantities_success(self):
        """测试批量录入实盘数量 - 成功"""
        records = [
            {'detail_id': 1, 'actual_quantity': '95', 'remark': '备注1'},
            {'detail_id': 2, 'actual_quantity': '105'}
        ]
        
        mock_detail = MagicMock(spec=StockCountDetail)
        
        with patch.object(self.service, 'record_actual_quantity', return_value=mock_detail):
            details = self.service.batch_record_quantities(
                records=records,
                counted_by=1
            )
        
        self.assertEqual(len(details), 2)

    def test_mark_for_recount_success(self):
        """测试标记需要复盘 - 成功"""
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.id = 1
        
        self.db.query.return_value.get.return_value = mock_detail
        
        detail = self.service.mark_for_recount(
            detail_id=1,
            recount_reason='数量异常'
        )
        
        self.assertTrue(detail.is_recounted)
        self.assertEqual(detail.recount_reason, '数量异常')
        self.assertEqual(detail.status, 'PENDING')
        self.assertIsNone(detail.actual_quantity)

    def test_mark_for_recount_not_found(self):
        """测试标记需要复盘 - 明细不存在"""
        self.db.query.return_value.get.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.mark_for_recount(
                detail_id=999,
                recount_reason='数量异常'
            )
        
        self.assertIn('盘点明细不存在', str(context.exception))

    # ============ 任务统计测试 ============

    def test_update_task_statistics_success(self):
        """测试更新任务统计 - 成功"""
        mock_task = MagicMock(spec=StockCountTask)
        
        mock_detail1 = MagicMock(spec=StockCountDetail)
        mock_detail1.status = 'COUNTED'
        mock_detail1.difference = Decimal('0')
        mock_detail1.diff_value = Decimal('0')
        
        mock_detail2 = MagicMock(spec=StockCountDetail)
        mock_detail2.status = 'COUNTED'
        mock_detail2.difference = Decimal('-5')
        mock_detail2.diff_value = Decimal('-50')
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with patch.object(self.service, 'get_count_details', return_value=[mock_detail1, mock_detail2]):
                self.service._update_task_statistics(1)
        
        self.assertEqual(mock_task.total_items, 2)
        self.assertEqual(mock_task.counted_items, 2)
        self.assertEqual(mock_task.matched_items, 1)
        self.assertEqual(mock_task.diff_items, 1)

    def test_update_task_statistics_task_not_found(self):
        """测试更新任务统计 - 任务不存在"""
        with patch.object(self.service, 'get_count_task', return_value=None):
            # 不应抛出异常
            self.service._update_task_statistics(999)

    # ============ 库存调整审批测试 ============

    def test_approve_adjustment_success(self):
        """测试批准库存调整 - 成功"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'IN_PROGRESS'
        mock_task.task_no = 'CNT-001'
        
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.status = 'COUNTED'
        mock_detail.difference = Decimal('-5')
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with patch.object(self.service, 'get_count_details', return_value=[mock_detail]):
                with patch.object(self.service, '_create_adjustment') as mock_create:
                    with patch.object(self.service, '_execute_adjustment'):
                        mock_adjustment = MagicMock()
                        mock_create.return_value = mock_adjustment
                        
                        result = self.service.approve_adjustment(
                            task_id=1,
                            approved_by=1,
                            auto_adjust=True
                        )
        
        self.assertEqual(mock_task.status, 'COMPLETED')
        self.assertIsNotNone(mock_task.end_time)
        self.assertEqual(result['total_adjustments'], 1)

    def test_approve_adjustment_task_not_found(self):
        """测试批准库存调整 - 任务不存在"""
        with patch.object(self.service, 'get_count_task', return_value=None):
            with self.assertRaises(ValueError) as context:
                self.service.approve_adjustment(task_id=999, approved_by=1)
        
        self.assertIn('盘点任务不存在', str(context.exception))

    def test_approve_adjustment_invalid_status(self):
        """测试批准库存调整 - 状态不允许"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'PENDING'
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with self.assertRaises(ValueError) as context:
                self.service.approve_adjustment(task_id=1, approved_by=1)
        
        self.assertIn('盘点任务状态不允许审批', str(context.exception))

    def test_approve_adjustment_has_uncounted(self):
        """测试批准库存调整 - 有未盘点明细"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'IN_PROGRESS'
        
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.status = 'PENDING'
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with patch.object(self.service, 'get_count_details', return_value=[mock_detail]):
                with self.assertRaises(ValueError) as context:
                    self.service.approve_adjustment(task_id=1, approved_by=1)
        
        self.assertIn('还有', str(context.exception))
        self.assertIn('条明细未盘点', str(context.exception))

    def test_approve_adjustment_no_auto_adjust(self):
        """测试批准库存调整 - 不自动调整"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.status = 'IN_PROGRESS'
        mock_task.task_no = 'CNT-001'
        
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.status = 'COUNTED'
        mock_detail.difference = Decimal('-5')
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with patch.object(self.service, 'get_count_details', return_value=[mock_detail]):
                with patch.object(self.service, '_create_adjustment') as mock_create:
                    with patch.object(self.service, '_execute_adjustment') as mock_execute:
                        mock_adjustment = MagicMock()
                        mock_create.return_value = mock_adjustment
                        
                        self.service.approve_adjustment(
                            task_id=1,
                            approved_by=1,
                            auto_adjust=False
                        )
                        
                        # 验证不执行调整
                        mock_execute.assert_not_called()

    # ============ 库存调整创建测试 ============

    def test_create_adjustment_success(self):
        """测试创建库存调整记录 - 成功"""
        mock_detail = MagicMock(spec=StockCountDetail)
        mock_detail.id = 1
        mock_detail.material_id = 100
        mock_detail.material_code = 'MAT001'
        mock_detail.material_name = '物料A'
        mock_detail.location = '仓库A'
        mock_detail.batch_number = 'B001'
        mock_detail.system_quantity = Decimal('100')
        mock_detail.actual_quantity = Decimal('95')
        mock_detail.difference = Decimal('-5')
        mock_detail.counted_by = 1
        mock_detail.unit_price = Decimal('10')
        mock_detail.diff_value = Decimal('-50')
        
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.id = 1
        mock_task.task_no = 'CNT-001'
        
        adjustment = self.service._create_adjustment(
            detail=mock_detail,
            task=mock_task,
            approved_by=1
        )
        
        self.assertIsInstance(adjustment, StockAdjustment)
        self.assertEqual(adjustment.material_id, 100)
        self.assertEqual(adjustment.difference, Decimal('-5'))
        self.assertEqual(adjustment.status, 'APPROVED')

    # ============ 库存调整执行测试 ============

    def test_execute_adjustment_success(self):
        """测试执行库存调整 - 成功"""
        mock_adjustment = MagicMock(spec=StockAdjustment)
        mock_adjustment.material_id = 100
        mock_adjustment.difference = Decimal('-5')
        mock_adjustment.unit_price = Decimal('10')
        mock_adjustment.location = '仓库A'
        mock_adjustment.batch_number = 'B001'
        
        with patch.object(self.service.inventory_service, 'create_transaction') as mock_create:
            with patch.object(self.service.inventory_service, 'update_stock') as mock_update:
                self.service._execute_adjustment(mock_adjustment)
        
        mock_create.assert_called_once()
        mock_update.assert_called_once()

    # ============ 盘点汇总和分析测试 ============

    def test_get_count_summary_success(self):
        """测试获取盘点汇总 - 成功"""
        mock_task = MagicMock(spec=StockCountTask)
        mock_task.task_no = 'CNT-001'
        mock_task.count_type = 'FULL'
        mock_task.location = '仓库A'
        mock_task.count_date = date(2024, 1, 15)
        mock_task.status = 'COMPLETED'
        mock_task.total_items = 3
        mock_task.counted_items = 3
        mock_task.diff_items = 2
        mock_task.total_diff_value = Decimal('-30')
        
        mock_detail1 = MagicMock(spec=StockCountDetail)
        mock_detail1.difference = Decimal('0')
        mock_detail1.diff_value = Decimal('0')
        
        mock_detail2 = MagicMock(spec=StockCountDetail)
        mock_detail2.difference = Decimal('5')
        mock_detail2.diff_value = Decimal('50')
        
        mock_detail3 = MagicMock(spec=StockCountDetail)
        mock_detail3.difference = Decimal('-8')
        mock_detail3.diff_value = Decimal('-80')
        
        with patch.object(self.service, 'get_count_task', return_value=mock_task):
            with patch.object(self.service, 'get_count_details', return_value=[mock_detail1, mock_detail2, mock_detail3]):
                with patch.object(self.service, '_get_top_differences', return_value=[]):
                    summary = self.service.get_count_summary(1)
        
        self.assertEqual(summary['task_info']['task_no'], 'CNT-001')
        self.assertEqual(summary['statistics']['total_items'], 3)
        self.assertEqual(summary['statistics']['matched_items'], 1)
        self.assertEqual(summary['statistics']['profit_items'], 1)
        self.assertEqual(summary['statistics']['loss_items'], 1)
        self.assertEqual(summary['value_analysis']['profit_value'], 50.0)
        self.assertEqual(summary['value_analysis']['loss_value'], -80.0)

    def test_get_count_summary_task_not_found(self):
        """测试获取盘点汇总 - 任务不存在"""
        with patch.object(self.service, 'get_count_task', return_value=None):
            with self.assertRaises(ValueError) as context:
                self.service.get_count_summary(999)
        
        self.assertIn('盘点任务不存在', str(context.exception))

    def test_get_top_differences_success(self):
        """测试获取差异最大的物料 - 成功"""
        mock_detail1 = MagicMock(spec=StockCountDetail)
        mock_detail1.material_code = 'MAT001'
        mock_detail1.material_name = '物料A'
        mock_detail1.location = '仓库A'
        mock_detail1.system_quantity = Decimal('100')
        mock_detail1.actual_quantity = Decimal('90')
        mock_detail1.difference = Decimal('-10')
        mock_detail1.difference_rate = Decimal('-10')
        mock_detail1.diff_value = Decimal('-100')
        
        mock_detail2 = MagicMock(spec=StockCountDetail)
        mock_detail2.material_code = 'MAT002'
        mock_detail2.material_name = '物料B'
        mock_detail2.location = '仓库A'
        mock_detail2.system_quantity = Decimal('50')
        mock_detail2.actual_quantity = Decimal('55')
        mock_detail2.difference = Decimal('5')
        mock_detail2.difference_rate = Decimal('10')
        mock_detail2.diff_value = Decimal('25')
        
        top_diffs = self.service._get_top_differences([mock_detail1, mock_detail2], limit=10)
        
        self.assertEqual(len(top_diffs), 2)
        # 应该按差异金额绝对值排序
        self.assertEqual(top_diffs[0]['material_code'], 'MAT001')

    def test_analyze_count_history_success(self):
        """测试分析历史盘点数据 - 成功"""
        mock_task1 = MagicMock(spec=StockCountTask)
        mock_task1.count_date = date(2024, 1, 15)
        mock_task1.total_items = 100
        mock_task1.matched_items = 90
        mock_task1.total_diff_value = Decimal('-50')
        
        mock_task2 = MagicMock(spec=StockCountTask)
        mock_task2.count_date = date(2024, 1, 20)
        mock_task2.total_items = 80
        mock_task2.matched_items = 75
        mock_task2.total_diff_value = Decimal('-30')
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_task1, mock_task2]
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_count_history(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertEqual(result['summary']['total_count_tasks'], 2)
        self.assertEqual(result['summary']['total_items_counted'], 180)
        self.assertEqual(result['summary']['total_matched_items'], 165)
        self.assertEqual(len(result['trend']), 2)

    def test_analyze_count_history_empty_result(self):
        """测试分析历史盘点数据 - 空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.analyze_count_history()
        
        self.assertEqual(result['summary']['total_count_tasks'], 0)
        self.assertEqual(result['summary']['avg_accuracy_rate'], 0)


if __name__ == '__main__':
    unittest.main()
