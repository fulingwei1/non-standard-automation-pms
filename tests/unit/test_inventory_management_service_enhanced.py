# -*- coding: utf-8 -*-
"""
库存管理服务增强测试
覆盖所有核心方法和边界条件
"""
import unittest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.inventory_management_service import (
    InventoryManagementService,
    InsufficientStockError
)
from app.models.inventory_tracking import (
    MaterialTransaction,
    MaterialStock,
    MaterialReservation,
)
from app.models.material import Material


class TestInventoryManagementServiceEnhanced(unittest.TestCase):
    """库存管理服务增强测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.tenant_id = 1
        self.service = InventoryManagementService(self.db, self.tenant_id)
        
        # 创建mock物料
        self.material = Material(
            id=100,
            material_code='M001',
            material_name='测试物料',
            unit='个',
            safety_stock=Decimal('10')
        )
        
        # 创建mock库存
        self.stock = MaterialStock(
            id=1,
            tenant_id=self.tenant_id,
            material_id=100,
            material_code='M001',
            material_name='测试物料',
            location='仓库A',
            batch_number='BATCH001',
            quantity=Decimal('100'),
            available_quantity=Decimal('80'),
            reserved_quantity=Decimal('20'),
            unit='个',
            unit_price=Decimal('10.5'),
            total_value=Decimal('1050'),
            last_in_date=datetime.now(),
            status='NORMAL'
        )

    # ============ 库存查询测试 ============

    def test_get_stock_basic(self):
        """测试基本库存查询"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.get_stock(material_id=100)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].material_id, 100)

    def test_get_stock_with_location_filter(self):
        """测试按仓位查询库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.get_stock(material_id=100, location='仓库A')
        
        self.assertEqual(result[0].location, '仓库A')

    def test_get_stock_with_batch_filter(self):
        """测试按批次查询库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.get_stock(
            material_id=100,
            batch_number='BATCH001'
        )
        
        self.assertEqual(result[0].batch_number, 'BATCH001')

    def test_get_stock_with_all_filters(self):
        """测试组合条件查询库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.get_stock(
            material_id=100,
            location='仓库A',
            batch_number='BATCH001'
        )
        
        self.assertEqual(len(result), 1)

    def test_get_available_quantity_success(self):
        """测试获取可用库存数量"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = Decimal('80')
        
        result = self.service.get_available_quantity(material_id=100)
        
        self.assertEqual(result, Decimal('80'))

    def test_get_available_quantity_zero(self):
        """测试获取可用库存为零"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = self.service.get_available_quantity(material_id=100)
        
        self.assertEqual(result, Decimal('0'))

    def test_get_available_quantity_with_location(self):
        """测试按仓位获取可用数量"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = Decimal('50')
        
        result = self.service.get_available_quantity(
            material_id=100,
            location='仓库A'
        )
        
        self.assertEqual(result, Decimal('50'))

    def test_get_total_quantity_success(self):
        """测试获取总库存数量"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = Decimal('100')
        
        result = self.service.get_total_quantity(material_id=100)
        
        self.assertEqual(result, Decimal('100'))

    def test_get_total_quantity_zero(self):
        """测试总库存为零"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None
        
        result = self.service.get_total_quantity(material_id=100)
        
        self.assertEqual(result, Decimal('0'))

    def test_get_all_stocks_basic(self):
        """测试查询所有库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.get_all_stocks()
        
        self.assertEqual(len(result), 1)

    def test_get_all_stocks_with_filters(self):
        """测试带过滤条件查询所有库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.get_all_stocks(
            location='仓库A',
            status='NORMAL',
            limit=50
        )
        
        self.assertEqual(len(result), 1)

    # ============ 交易记录测试 ============

    def test_create_transaction_success(self):
        """测试创建交易记录"""
        self.db.query.return_value.get.return_value = self.material
        
        result = self.service.create_transaction(
            material_id=100,
            transaction_type='PURCHASE_IN',
            quantity=Decimal('50'),
            unit_price=Decimal('10'),
            target_location='仓库A'
        )
        
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()

    def test_create_transaction_material_not_found(self):
        """测试创建交易记录-物料不存在"""
        self.db.query.return_value.get.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.create_transaction(
                material_id=999,
                transaction_type='PURCHASE_IN',
                quantity=Decimal('50'),
                unit_price=Decimal('10')
            )
        
        self.assertIn('物料不存在', str(context.exception))

    def test_create_transaction_with_all_params(self):
        """测试创建交易记录-所有参数"""
        self.db.query.return_value.get.return_value = self.material
        
        result = self.service.create_transaction(
            material_id=100,
            transaction_type='ISSUE',
            quantity=Decimal('30'),
            unit_price=Decimal('10.5'),
            source_location='仓库A',
            target_location='生产线',
            batch_number='BATCH001',
            related_order_id=1001,
            related_order_type='WORK_ORDER',
            related_order_no='WO-2024-001',
            operator_id=5,
            remark='正常领料',
            cost_method='FIFO'
        )
        
        self.db.add.assert_called_once()

    def test_get_transactions_basic(self):
        """测试查询交易记录"""
        mock_transaction = MaterialTransaction(
            id=1,
            tenant_id=self.tenant_id,
            material_id=100,
            transaction_type='PURCHASE_IN',
            quantity=Decimal('50')
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_transaction]
        
        result = self.service.get_transactions()
        
        self.assertEqual(len(result), 1)

    def test_get_transactions_with_filters(self):
        """测试带过滤条件查询交易记录"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_transactions(
            material_id=100,
            transaction_type='ISSUE',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            limit=50
        )
        
        self.assertEqual(len(result), 0)

    # ============ 库存更新测试 ============

    def test_update_stock_purchase_in_new_stock(self):
        """测试更新库存-采购入库(新库存)"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        self.db.query.return_value.get.return_value = self.material
        
        result = self.service.update_stock(
            material_id=100,
            quantity=Decimal('50'),
            transaction_type='PURCHASE_IN',
            location='仓库A',
            unit_price=Decimal('10')
        )
        
        self.db.add.assert_called()
        self.db.flush.assert_called_once()

    def test_update_stock_purchase_in_existing_stock(self):
        """测试更新库存-采购入库(已有库存)"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.stock
        self.db.query.return_value.get.return_value = self.material
        
        original_qty = self.stock.quantity
        
        result = self.service.update_stock(
            material_id=100,
            quantity=Decimal('50'),
            transaction_type='PURCHASE_IN',
            location='仓库A',
            batch_number='BATCH001',
            unit_price=Decimal('12')
        )
        
        self.assertEqual(self.stock.quantity, original_qty + Decimal('50'))

    def test_update_stock_issue_success(self):
        """测试更新库存-出库成功"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.stock
        self.db.query.return_value.get.return_value = self.material
        
        original_qty = self.stock.quantity
        
        result = self.service.update_stock(
            material_id=100,
            quantity=Decimal('30'),
            transaction_type='ISSUE',
            location='仓库A',
            batch_number='BATCH001'
        )
        
        self.assertEqual(self.stock.quantity, original_qty - Decimal('30'))

    def test_update_stock_issue_insufficient(self):
        """测试更新库存-库存不足"""
        self.stock.available_quantity = Decimal('10')
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.stock
        self.db.query.return_value.get.return_value = self.material
        
        with self.assertRaises(InsufficientStockError):
            self.service.update_stock(
                material_id=100,
                quantity=Decimal('50'),
                transaction_type='ISSUE',
                location='仓库A'
            )

    def test_update_stock_adjust_positive(self):
        """测试更新库存-正向调整"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.stock
        self.db.query.return_value.get.return_value = self.material
        
        original_qty = self.stock.quantity
        
        result = self.service.update_stock(
            material_id=100,
            quantity=Decimal('20'),
            transaction_type='ADJUST',
            location='仓库A'
        )
        
        self.assertEqual(self.stock.quantity, original_qty + Decimal('20'))

    def test_update_stock_adjust_negative(self):
        """测试更新库存-负向调整"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.stock
        self.db.query.return_value.get.return_value = self.material
        
        original_qty = self.stock.quantity
        
        result = self.service.update_stock(
            material_id=100,
            quantity=Decimal('-15'),
            transaction_type='ADJUST',
            location='仓库A'
        )
        
        self.assertEqual(self.stock.quantity, original_qty - Decimal('15'))

    def test_calculate_stock_status_normal(self):
        """测试计算库存状态-正常"""
        self.stock.quantity = Decimal('50')
        self.stock.expire_date = None
        
        # Mock material with safety_stock
        mock_material = MagicMock()
        mock_material.safety_stock = Decimal('10')
        self.db.query.return_value.get.return_value = mock_material
        
        status = self.service._calculate_stock_status(self.stock)
        
        self.assertEqual(status, 'NORMAL')

    def test_calculate_stock_status_low(self):
        """测试计算库存状态-低库存"""
        self.stock.quantity = Decimal('5')
        self.stock.expire_date = None
        
        # Mock material with safety_stock
        mock_material = MagicMock()
        mock_material.safety_stock = Decimal('10')
        self.db.query.return_value.get.return_value = mock_material
        
        status = self.service._calculate_stock_status(self.stock)
        
        self.assertEqual(status, 'LOW')

    def test_calculate_stock_status_empty(self):
        """测试计算库存状态-空库存"""
        self.stock.quantity = Decimal('0')
        
        status = self.service._calculate_stock_status(self.stock)
        
        self.assertEqual(status, 'EMPTY')

    def test_calculate_stock_status_expired(self):
        """测试计算库存状态-已过期"""
        self.stock.expire_date = date.today() - timedelta(days=1)
        
        status = self.service._calculate_stock_status(self.stock)
        
        self.assertEqual(status, 'EXPIRED')

    # ============ 入库操作测试 ============

    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_purchase_in_success(self, mock_update, mock_create):
        """测试采购入库成功"""
        mock_transaction = MagicMock()
        mock_create.return_value = mock_transaction
        mock_update.return_value = self.stock
        
        result = self.service.purchase_in(
            material_id=100,
            quantity=Decimal('50'),
            unit_price=Decimal('10'),
            location='仓库A',
            batch_number='BATCH002',
            purchase_order_id=1001,
            purchase_order_no='PO-2024-001',
            operator_id=5
        )
        
        self.assertIn('transaction', result)
        self.assertIn('stock', result)
        self.assertIn('message', result)
        self.db.commit.assert_called_once()

    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_purchase_in_with_dates(self, mock_update, mock_create):
        """测试采购入库-带日期信息"""
        mock_transaction = MagicMock()
        mock_create.return_value = mock_transaction
        
        stock_copy = MaterialStock(
            id=1,
            tenant_id=self.tenant_id,
            material_id=100,
            location='仓库A',
            quantity=Decimal('50')
        )
        mock_update.return_value = stock_copy
        
        prod_date = date(2024, 1, 1)
        exp_date = date(2025, 1, 1)
        
        result = self.service.purchase_in(
            material_id=100,
            quantity=Decimal('50'),
            unit_price=Decimal('10'),
            location='仓库A',
            production_date=prod_date,
            expire_date=exp_date
        )
        
        self.assertEqual(stock_copy.production_date, prod_date)
        self.assertEqual(stock_copy.expire_date, exp_date)

    # ============ 出库操作测试 ============

    @patch.object(InventoryManagementService, '_release_reservation')
    @patch.object(InventoryManagementService, '_select_stock_for_issue')
    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_issue_material_success(self, mock_update, mock_create, mock_select, mock_release):
        """测试领料出库成功"""
        mock_transaction = MaterialTransaction(
            id=1,
            total_amount=Decimal('315')
        )
        mock_create.return_value = mock_transaction
        mock_select.return_value = [(self.stock, Decimal('30'))]
        
        result = self.service.issue_material(
            material_id=100,
            quantity=Decimal('30'),
            location='仓库A',
            work_order_id=2001,
            work_order_no='WO-2024-001',
            operator_id=5
        )
        
        self.assertIn('transactions', result)
        self.assertIn('total_quantity', result)
        self.assertEqual(result['total_quantity'], Decimal('30'))
        self.db.commit.assert_called_once()

    @patch.object(InventoryManagementService, '_release_reservation')
    @patch.object(InventoryManagementService, '_select_stock_for_issue')
    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_issue_material_with_reservation(self, mock_update, mock_create, mock_select, mock_release):
        """测试领料出库-带预留"""
        mock_transaction = MagicMock(total_amount=Decimal('315'))
        mock_create.return_value = mock_transaction
        mock_select.return_value = [(self.stock, Decimal('30'))]
        
        result = self.service.issue_material(
            material_id=100,
            quantity=Decimal('30'),
            location='仓库A',
            reservation_id=3001
        )
        
        mock_release.assert_called_once_with(3001, Decimal('30'))

    def test_select_stock_for_issue_fifo(self):
        """测试选择库存-先进先出"""
        stock1 = MaterialStock(
            id=1,
            material_id=100,
            location='仓库A',
            available_quantity=Decimal('50'),
            last_in_date=datetime(2024, 1, 1)
        )
        stock2 = MaterialStock(
            id=2,
            material_id=100,
            location='仓库A',
            available_quantity=Decimal('50'),
            last_in_date=datetime(2024, 2, 1)
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [stock1, stock2]
        
        result = self.service._select_stock_for_issue(
            material_id=100,
            location='仓库A',
            quantity=Decimal('60'),
            cost_method='FIFO'
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], Decimal('50'))
        self.assertEqual(result[1][1], Decimal('10'))

    def test_select_stock_for_issue_lifo(self):
        """测试选择库存-后进先出"""
        stock1 = MaterialStock(
            id=1,
            material_id=100,
            location='仓库A',
            available_quantity=Decimal('50'),
            last_in_date=datetime(2024, 1, 1)
        )
        stock2 = MaterialStock(
            id=2,
            material_id=100,
            location='仓库A',
            available_quantity=Decimal('50'),
            last_in_date=datetime(2024, 2, 1)
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [stock2, stock1]
        
        result = self.service._select_stock_for_issue(
            material_id=100,
            location='仓库A',
            quantity=Decimal('60'),
            cost_method='LIFO'
        )
        
        self.assertEqual(len(result), 2)

    def test_select_stock_for_issue_no_stock(self):
        """测试选择库存-无库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        with self.assertRaises(InsufficientStockError):
            self.service._select_stock_for_issue(
                material_id=100,
                location='仓库A',
                quantity=Decimal('50'),
                cost_method='FIFO'
            )

    def test_select_stock_for_issue_insufficient(self):
        """测试选择库存-库存不足"""
        stock = MaterialStock(
            id=1,
            material_id=100,
            location='仓库A',
            available_quantity=Decimal('20')
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [stock]
        
        with self.assertRaises(InsufficientStockError):
            self.service._select_stock_for_issue(
                material_id=100,
                location='仓库A',
                quantity=Decimal('50'),
                cost_method='FIFO'
            )

    # ============ 退料操作测试 ============

    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_return_material_success(self, mock_update, mock_create):
        """测试退料入库成功"""
        mock_transaction = MagicMock()
        mock_create.return_value = mock_transaction
        mock_update.return_value = self.stock
        
        result = self.service.return_material(
            material_id=100,
            quantity=Decimal('15'),
            location='仓库A',
            batch_number='BATCH001',
            work_order_id=2001,
            operator_id=5
        )
        
        self.assertIn('transaction', result)
        self.assertIn('stock', result)
        self.db.commit.assert_called_once()

    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_return_material_auto_batch(self, mock_update, mock_create):
        """测试退料入库-自动生成批次"""
        mock_transaction = MagicMock()
        mock_create.return_value = mock_transaction
        mock_update.return_value = self.stock
        
        result = self.service.return_material(
            material_id=100,
            quantity=Decimal('15'),
            location='仓库A'
        )
        
        # 验证调用时生成了批次号
        call_args = mock_create.call_args
        self.assertIsNotNone(call_args[1]['batch_number'])
        self.assertIn('RETURN', call_args[1]['batch_number'])

    # ============ 库存转移测试 ============

    @patch.object(InventoryManagementService, 'create_transaction')
    @patch.object(InventoryManagementService, 'update_stock')
    def test_transfer_stock_success(self, mock_update, mock_create):
        """测试库存转移成功"""
        from_stock = MaterialStock(
            id=1,
            material_id=100,
            location='仓库A',
            unit_price=Decimal('10.5')
        )
        to_stock = MaterialStock(
            id=2,
            material_id=100,
            location='仓库B',
            unit_price=Decimal('10.5')
        )
        
        mock_transaction = MagicMock()
        mock_create.return_value = mock_transaction
        mock_update.side_effect = [from_stock, to_stock]
        
        result = self.service.transfer_stock(
            material_id=100,
            quantity=Decimal('20'),
            from_location='仓库A',
            to_location='仓库B',
            batch_number='BATCH001',
            operator_id=5
        )
        
        self.assertIn('out_transaction', result)
        self.assertIn('in_transaction', result)
        self.assertIn('from_stock', result)
        self.assertIn('to_stock', result)
        self.assertEqual(mock_create.call_count, 2)
        self.db.commit.assert_called_once()

    # ============ 物料预留测试 ============

    @patch.object(InventoryManagementService, 'get_available_quantity')
    def test_reserve_material_success(self, mock_available):
        """测试预留物料成功"""
        mock_available.return_value = Decimal('100')
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [self.stock]
        
        result = self.service.reserve_material(
            material_id=100,
            quantity=Decimal('30'),
            project_id=101,
            work_order_id=2001,
            expected_use_date=date.today() + timedelta(days=7),
            created_by=5
        )
        
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    @patch.object(InventoryManagementService, 'get_available_quantity')
    def test_reserve_material_insufficient(self, mock_available):
        """测试预留物料-库存不足"""
        mock_available.return_value = Decimal('10')
        
        with self.assertRaises(InsufficientStockError):
            self.service.reserve_material(
                material_id=100,
                quantity=Decimal('50')
            )

    @patch.object(InventoryManagementService, 'get_available_quantity')
    def test_reserve_material_multiple_stocks(self, mock_available):
        """测试预留物料-跨多个库存"""
        mock_available.return_value = Decimal('100')
        
        stock1 = MaterialStock(
            id=1,
            material_id=100,
            available_quantity=Decimal('30'),
            reserved_quantity=Decimal('0')
        )
        stock2 = MaterialStock(
            id=2,
            material_id=100,
            available_quantity=Decimal('50'),
            reserved_quantity=Decimal('0')
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [stock1, stock2]
        
        result = self.service.reserve_material(
            material_id=100,
            quantity=Decimal('60')
        )
        
        self.assertEqual(stock1.reserved_quantity, Decimal('30'))
        self.assertEqual(stock2.reserved_quantity, Decimal('30'))

    def test_cancel_reservation_success(self):
        """测试取消预留成功"""
        reservation = MaterialReservation(
            id=3001,
            tenant_id=self.tenant_id,
            material_id=100,
            reserved_quantity=Decimal('30'),
            remaining_quantity=Decimal('30'),
            status='ACTIVE'
        )
        
        stock = MaterialStock(
            id=1,
            material_id=100,
            reserved_quantity=Decimal('30'),
            available_quantity=Decimal('50')
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = reservation
        
        mock_query_stock = MagicMock()
        mock_query_stock.filter.return_value = mock_query_stock
        mock_query_stock.all.return_value = [stock]
        
        self.db.query.side_effect = [mock_query, mock_query_stock]
        
        result = self.service.cancel_reservation(
            reservation_id=3001,
            cancelled_by=5,
            cancel_reason='项目取消'
        )
        
        self.assertEqual(reservation.status, 'CANCELLED')
        self.db.commit.assert_called_once()

    def test_cancel_reservation_not_found(self):
        """测试取消预留-记录不存在"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.cancel_reservation(reservation_id=9999)
        
        self.assertIn('预留记录不存在', str(context.exception))

    def test_cancel_reservation_invalid_status(self):
        """测试取消预留-状态不允许"""
        reservation = MaterialReservation(
            id=3001,
            tenant_id=self.tenant_id,
            status='USED'
        )
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = reservation
        
        with self.assertRaises(ValueError) as context:
            self.service.cancel_reservation(reservation_id=3001)
        
        self.assertIn('预留状态不允许取消', str(context.exception))

    def test_release_reservation_full(self):
        """测试释放预留-完全使用"""
        reservation = MaterialReservation(
            id=3001,
            used_quantity=Decimal('0'),
            remaining_quantity=Decimal('30'),
            status='ACTIVE'
        )
        
        self.db.query.return_value.get.return_value = reservation
        
        self.service._release_reservation(3001, Decimal('30'))
        
        self.assertEqual(reservation.used_quantity, Decimal('30'))
        self.assertEqual(reservation.remaining_quantity, Decimal('0'))
        self.assertEqual(reservation.status, 'USED')

    def test_release_reservation_partial(self):
        """测试释放预留-部分使用"""
        reservation = MaterialReservation(
            id=3001,
            used_quantity=Decimal('0'),
            remaining_quantity=Decimal('30'),
            status='ACTIVE'
        )
        
        self.db.query.return_value.get.return_value = reservation
        
        self.service._release_reservation(3001, Decimal('15'))
        
        self.assertEqual(reservation.used_quantity, Decimal('15'))
        self.assertEqual(reservation.remaining_quantity, Decimal('15'))
        self.assertEqual(reservation.status, 'PARTIAL_USED')

    # ============ 库存分析测试 ============

    def test_calculate_turnover_rate_success(self):
        """测试计算周转率成功"""
        transactions = [
            MaterialTransaction(
                id=1,
                transaction_type='ISSUE',
                total_amount=Decimal('1000')
            ),
            MaterialTransaction(
                id=2,
                transaction_type='ISSUE',
                total_amount=Decimal('1500')
            )
        ]
        
        stocks = [
            MaterialStock(id=1, total_value=Decimal('5000')),
            MaterialStock(id=2, total_value=Decimal('3000'))
        ]
        
        mock_query_trans = MagicMock()
        mock_query_trans.filter.return_value = mock_query_trans
        mock_query_trans.all.return_value = transactions
        
        mock_query_stock = MagicMock()
        mock_query_stock.filter.return_value = mock_query_stock
        mock_query_stock.all.return_value = stocks
        
        self.db.query.side_effect = [mock_query_trans, mock_query_stock]
        
        result = self.service.calculate_turnover_rate(material_id=100)
        
        self.assertIn('total_issue_value', result)
        self.assertIn('avg_stock_value', result)
        self.assertIn('turnover_rate', result)
        self.assertIn('turnover_days', result)

    def test_calculate_turnover_rate_zero_stock(self):
        """测试计算周转率-零库存"""
        mock_query_trans = MagicMock()
        mock_query_trans.filter.return_value = mock_query_trans
        mock_query_trans.all.return_value = []
        
        mock_query_stock = MagicMock()
        mock_query_stock.filter.return_value = mock_query_stock
        mock_query_stock.all.return_value = []
        
        self.db.query.side_effect = [mock_query_trans, mock_query_stock]
        
        result = self.service.calculate_turnover_rate()
        
        self.assertEqual(result['turnover_rate'], 0)
        self.assertEqual(result['turnover_days'], 0)

    def test_analyze_aging_success(self):
        """测试库龄分析成功"""
        stocks = [
            MaterialStock(
                id=1,
                material_id=100,
                material_code='M001',
                material_name='物料1',
                location='仓库A',
                batch_number='B001',
                quantity=Decimal('50'),
                unit_price=Decimal('10'),
                total_value=Decimal('500'),
                last_in_date=datetime.now() - timedelta(days=15)
            ),
            MaterialStock(
                id=2,
                material_id=101,
                material_code='M002',
                material_name='物料2',
                location='仓库B',
                batch_number='B002',
                quantity=Decimal('100'),
                unit_price=Decimal('20'),
                total_value=Decimal('2000'),
                last_in_date=datetime.now() - timedelta(days=120)
            )
        ]
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = stocks
        
        result = self.service.analyze_aging()
        
        self.assertIn('aging_summary', result)
        self.assertIn('details', result)
        self.assertIn('0-30天', result['aging_summary'])
        self.assertIn('91-180天', result['aging_summary'])
        self.assertEqual(len(result['details']), 2)

    def test_analyze_aging_with_location(self):
        """测试库龄分析-指定仓位"""
        stocks = [
            MaterialStock(
                id=1,
                material_id=100,
                material_code='M001',
                material_name='物料1',
                location='仓库A',
                quantity=Decimal('50'),
                unit_price=Decimal('10'),
                total_value=Decimal('500'),
                last_in_date=datetime.now() - timedelta(days=200)
            )
        ]
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = stocks
        
        result = self.service.analyze_aging(location='仓库A')
        
        self.assertEqual(len(result['details']), 1)
        self.assertEqual(result['details'][0]['aging_category'], '181-365天')

    def test_analyze_aging_empty_stock(self):
        """测试库龄分析-空库存"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.analyze_aging()
        
        self.assertEqual(len(result['details']), 0)
        self.assertEqual(result['aging_summary']['0-30天']['count'], 0)


if __name__ == '__main__':
    unittest.main()
