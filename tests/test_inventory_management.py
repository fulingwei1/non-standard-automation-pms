# -*- coding: utf-8 -*-
"""
库存管理服务测试
Team 2: 物料全流程跟踪系统
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.inventory_tracking import (
    MaterialTransaction,
    MaterialStock,
    MaterialReservation,
    StockAdjustment,
)
from app.models.material import Material, MaterialCategory
from app.services.inventory_management_service import (
    InventoryManagementService,
    InsufficientStockError
)


class TestInventoryManagementService:
    """库存管理服务测试"""

    @pytest.fixture
    def setup_test_data(self, db: Session, test_tenant):
        """准备测试数据"""
        # 创建物料分类
        category = MaterialCategory(
            category_code='TEST-CAT',
            category_name='测试分类',
            level=1
        )
        db.add(category)
        db.flush()
        
        # 创建测试物料
        material = Material(
            material_code='TEST-MAT-001',
            material_name='测试物料A',
            category_id=category.id,
            unit='件',
            safety_stock=Decimal('100'),
            is_active=True
        )
        db.add(material)
        db.commit()
        
        return {
            'material': material,
            'category': category,
            'tenant_id': test_tenant.id
        }

    # ============ 交易记录测试 ============

    def test_create_transaction(self, db: Session, setup_test_data):
        """测试创建交易记录"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        transaction = service.create_transaction(
            material_id=material.id,
            transaction_type='PURCHASE_IN',
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            target_location='仓库A',
            batch_number='BATCH-001'
        )
        
        assert transaction.id is not None
        assert transaction.material_code == 'TEST-MAT-001'
        assert transaction.quantity == Decimal('100')
        assert transaction.total_amount == Decimal('5000.00')

    def test_get_transactions(self, db: Session, setup_test_data):
        """测试查询交易记录"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 创建多个交易记录
        for i in range(5):
            service.create_transaction(
                material_id=material.id,
                transaction_type='PURCHASE_IN',
                quantity=Decimal(str(10 * (i + 1))),
                target_location='仓库A'
            )
        
        db.commit()
        
        # 查询交易记录
        transactions = service.get_transactions(material_id=material.id)
        assert len(transactions) == 5

    # ============ 库存更新测试 ============

    def test_purchase_in(self, db: Session, setup_test_data):
        """测试采购入库"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        result = service.purchase_in(
            material_id=material.id,
            quantity=Decimal('200'),
            unit_price=Decimal('60.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        assert result['message'] == '入库成功: 200 件'
        
        # 验证库存
        stock = result['stock']
        assert stock.quantity == Decimal('200')
        assert stock.available_quantity == Decimal('200')
        assert stock.unit_price == Decimal('60.00')

    def test_weighted_avg_cost(self, db: Session, setup_test_data):
        """测试加权平均成本计算"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 第一次入库: 100件 @ 50元
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        # 第二次入库: 200件 @ 60元
        result = service.purchase_in(
            material_id=material.id,
            quantity=Decimal('200'),
            unit_price=Decimal('60.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        # 加权平均单价 = (100*50 + 200*60) / 300 = 56.67
        stock = result['stock']
        expected_price = (Decimal('100') * Decimal('50') + Decimal('200') * Decimal('60')) / Decimal('300')
        assert abs(stock.unit_price - expected_price) < Decimal('0.01')

    def test_insufficient_stock_error(self, db: Session, setup_test_data):
        """测试库存不足异常"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库少量物料
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('50'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        # 尝试出库超过库存的数量
        with pytest.raises(InsufficientStockError):
            service.issue_material(
                material_id=material.id,
                quantity=Decimal('100'),
                location='仓库A'
            )

    # ============ 出库测试 ============

    def test_issue_material_fifo(self, db: Session, setup_test_data):
        """测试先进先出出库"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 分批入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('60.00'),
            location='仓库A',
            batch_number='BATCH-002'
        )
        
        # FIFO出库
        result = service.issue_material(
            material_id=material.id,
            quantity=Decimal('150'),
            location='仓库A',
            cost_method='FIFO'
        )
        
        # 应该先从BATCH-001出100,再从BATCH-002出50
        assert result['total_quantity'] == Decimal('150')
        # 成本 = 100*50 + 50*60 = 8000
        assert result['total_cost'] == Decimal('8000.00')

    def test_issue_material_lifo(self, db: Session, setup_test_data):
        """测试后进先出出库"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 分批入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('60.00'),
            location='仓库A',
            batch_number='BATCH-002'
        )
        
        # LIFO出库
        result = service.issue_material(
            material_id=material.id,
            quantity=Decimal('150'),
            location='仓库A',
            cost_method='LIFO'
        )
        
        # 应该先从BATCH-002出100,再从BATCH-001出50
        assert result['total_quantity'] == Decimal('150')
        # 成本 = 100*60 + 50*50 = 8500
        assert result['total_cost'] == Decimal('8500.00')

    # ============ 退料测试 ============

    def test_return_material(self, db: Session, setup_test_data):
        """测试退料入库"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 先入库再出库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        service.issue_material(
            material_id=material.id,
            quantity=Decimal('50'),
            location='仓库A'
        )
        
        # 退料
        result = service.return_material(
            material_id=material.id,
            quantity=Decimal('20'),
            location='仓库A'
        )
        
        assert '退料成功' in result['message']
        
        # 验证库存
        total = service.get_total_quantity(material.id)
        assert total == Decimal('70')  # 100 - 50 + 20

    # ============ 库存转移测试 ============

    def test_transfer_stock(self, db: Session, setup_test_data):
        """测试库存转移"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 仓库A入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        # 转移到仓库B
        result = service.transfer_stock(
            material_id=material.id,
            quantity=Decimal('30'),
            from_location='仓库A',
            to_location='仓库B',
            batch_number='BATCH-001'
        )
        
        assert '转移成功' in result['message']
        
        # 验证库存
        stock_a = service.get_available_quantity(material.id, '仓库A')
        stock_b = service.get_available_quantity(material.id, '仓库B')
        assert stock_a == Decimal('70')
        assert stock_b == Decimal('30')

    # ============ 物料预留测试 ============

    def test_reserve_material(self, db: Session, setup_test_data):
        """测试物料预留"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        # 预留
        reservation = service.reserve_material(
            material_id=material.id,
            quantity=Decimal('30'),
            project_id=1
        )
        
        assert reservation.reserved_quantity == Decimal('30')
        assert reservation.status == 'ACTIVE'
        
        # 验证可用库存减少
        available = service.get_available_quantity(material.id)
        assert available == Decimal('70')  # 100 - 30

    def test_cancel_reservation(self, db: Session, setup_test_data):
        """测试取消预留"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库并预留
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        reservation = service.reserve_material(
            material_id=material.id,
            quantity=Decimal('30')
        )
        
        # 取消预留
        service.cancel_reservation(
            reservation_id=reservation.id,
            cancel_reason='测试取消'
        )
        
        # 验证可用库存恢复
        available = service.get_available_quantity(material.id)
        assert available == Decimal('100')

    def test_reserve_insufficient_stock(self, db: Session, setup_test_data):
        """测试预留库存不足"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库少量物料
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('50'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        # 尝试预留超过可用库存的数量
        with pytest.raises(InsufficientStockError):
            service.reserve_material(
                material_id=material.id,
                quantity=Decimal('100')
            )

    # ============ 库存分析测试 ============

    def test_calculate_turnover_rate(self, db: Session, setup_test_data):
        """测试库存周转率计算"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('1000'),
            unit_price=Decimal('100.00'),
            location='仓库A'
        )
        
        # 出库
        service.issue_material(
            material_id=material.id,
            quantity=Decimal('600'),
            location='仓库A'
        )
        
        # 计算周转率
        result = service.calculate_turnover_rate(material_id=material.id)
        
        assert 'turnover_rate' in result
        assert 'turnover_days' in result
        assert result['total_issue_value'] == 60000.0  # 600 * 100

    def test_analyze_aging(self, db: Session, setup_test_data):
        """测试库龄分析"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A',
            batch_number='BATCH-001'
        )
        
        # 分析库龄
        result = service.analyze_aging()
        
        assert len(result) > 0
        assert 'aging_category' in result[0]
        assert 'days_in_stock' in result[0]

    # ============ 库存查询测试 ============

    def test_get_stock(self, db: Session, setup_test_data):
        """测试查询库存"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库到不同位置
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('50'),
            unit_price=Decimal('50.00'),
            location='仓库B'
        )
        
        # 查询所有库存
        stocks = service.get_stock(material.id)
        assert len(stocks) == 2
        
        # 查询指定位置
        stocks_a = service.get_stock(material.id, location='仓库A')
        assert len(stocks_a) == 1
        assert stocks_a[0].quantity == Decimal('100')

    def test_get_available_quantity(self, db: Session, setup_test_data):
        """测试获取可用库存数量"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        # 预留部分
        service.reserve_material(
            material_id=material.id,
            quantity=Decimal('30')
        )
        
        # 获取可用数量
        available = service.get_available_quantity(material.id)
        assert available == Decimal('70')

    def test_get_total_quantity(self, db: Session, setup_test_data):
        """测试获取总库存数量"""
        material = setup_test_data['material']
        tenant_id = setup_test_data['tenant_id']
        
        service = InventoryManagementService(db, tenant_id)
        
        # 多处入库
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('100'),
            unit_price=Decimal('50.00'),
            location='仓库A'
        )
        
        service.purchase_in(
            material_id=material.id,
            quantity=Decimal('50'),
            unit_price=Decimal('50.00'),
            location='仓库B'
        )
        
        # 获取总数量
        total = service.get_total_quantity(material.id)
        assert total == Decimal('150')
