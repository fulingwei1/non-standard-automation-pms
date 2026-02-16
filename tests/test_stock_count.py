# -*- coding: utf-8 -*-
"""
库存盘点服务测试
Team 2: 物料全流程跟踪系统
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.inventory_tracking import (
    StockCountTask,
    StockCountDetail,
    StockAdjustment,
)
from app.models.material import Material, MaterialCategory
from app.services.inventory_management_service import InventoryManagementService
from app.services.stock_count_service import StockCountService


class TestStockCountService:
    """库存盘点服务测试"""

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
        
        # 创建多个测试物料
        materials = []
        for i in range(5):
            material = Material(
                material_code=f'TEST-MAT-{i+1:03d}',
                material_name=f'测试物料{chr(65+i)}',
                category_id=category.id,
                unit='件',
                is_active=True
            )
            db.add(material)
            materials.append(material)
        
        db.commit()
        
        # 初始化库存
        inv_service = InventoryManagementService(db, test_tenant.id)
        for material in materials:
            inv_service.purchase_in(
                material_id=material.id,
                quantity=Decimal(str((i+1) * 100)),
                unit_price=Decimal('50.00'),
                location='仓库A',
                batch_number=f'BATCH-{i+1:03d}'
            )
        
        return {
            'materials': materials,
            'category': category,
            'tenant_id': test_tenant.id
        }

    # ============ 盘点任务创建测试 ============

    def test_create_full_count_task(self, db: Session, setup_test_data):
        """测试创建全盘任务"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        assert task.id is not None
        assert task.task_no.startswith('CNT-')
        assert task.count_type == 'FULL'
        assert task.status == 'PENDING'
        assert task.total_items == 5  # 5个物料

    def test_create_partial_count_task(self, db: Session, setup_test_data):
        """测试创建抽盘任务"""
        materials = setup_test_data['materials']
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 只盘点前3个物料
        task = service.create_count_task(
            count_type='PARTIAL',
            count_date=date.today(),
            location='仓库A',
            material_ids=[m.id for m in materials[:3]],
            created_by=1
        )
        
        assert task.total_items == 3

    def test_create_category_count_task(self, db: Session, setup_test_data):
        """测试按分类盘点"""
        category = setup_test_data['category']
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        task = service.create_count_task(
            count_type='CYCLE',
            count_date=date.today(),
            category_id=category.id,
            created_by=1
        )
        
        assert task.total_items == 5  # 该分类下所有物料

    # ============ 盘点明细测试 ============

    def test_get_count_details(self, db: Session, setup_test_data):
        """测试获取盘点明细"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建盘点任务
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        # 获取明细
        details = service.get_count_details(task.id)
        
        assert len(details) == 5
        for detail in details:
            assert detail.system_quantity > 0
            assert detail.status == 'PENDING'

    def test_record_actual_quantity(self, db: Session, setup_test_data):
        """测试录入实盘数量"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建盘点任务
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        details = service.get_count_details(task.id)
        detail = details[0]
        
        # 录入实盘数量 (账实相符)
        updated = service.record_actual_quantity(
            detail_id=detail.id,
            actual_quantity=detail.system_quantity,
            counted_by=1
        )
        
        assert updated.actual_quantity == detail.system_quantity
        assert updated.difference == Decimal('0')
        assert updated.status == 'COUNTED'

    def test_record_actual_quantity_with_difference(self, db: Session, setup_test_data):
        """测试录入有差异的实盘数量"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建盘点任务
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        details = service.get_count_details(task.id)
        detail = details[0]
        
        # 录入实盘数量 (盘盈)
        actual_qty = detail.system_quantity + Decimal('10')
        updated = service.record_actual_quantity(
            detail_id=detail.id,
            actual_quantity=actual_qty,
            counted_by=1
        )
        
        assert updated.difference == Decimal('10')
        assert updated.difference_rate > 0

    def test_batch_record_quantities(self, db: Session, setup_test_data):
        """测试批量录入实盘数量"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建盘点任务
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        details = service.get_count_details(task.id)
        
        # 批量录入
        records = [
            {
                'detail_id': d.id,
                'actual_quantity': float(d.system_quantity),
                'remark': f'盘点物料{i+1}'
            }
            for i, d in enumerate(details)
        ]
        
        updated_details = service.batch_record_quantities(
            records=records,
            counted_by=1
        )
        
        assert len(updated_details) == 5
        for d in updated_details:
            assert d.status == 'COUNTED'

    def test_mark_for_recount(self, db: Session, setup_test_data):
        """测试标记复盘"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建盘点任务并录入数量
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        details = service.get_count_details(task.id)
        detail = details[0]
        
        service.record_actual_quantity(
            detail_id=detail.id,
            actual_quantity=detail.system_quantity,
            counted_by=1
        )
        
        # 标记复盘
        updated = service.mark_for_recount(
            detail_id=detail.id,
            recount_reason='差异较大,需要复盘'
        )
        
        assert updated.is_recounted is True
        assert updated.status == 'PENDING'
        assert updated.actual_quantity is None

    # ============ 盘点任务状态测试 ============

    def test_start_count_task(self, db: Session, setup_test_data):
        """测试开始盘点"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            created_by=1
        )
        
        # 开始盘点
        started = service.start_count_task(task.id)
        
        assert started.status == 'IN_PROGRESS'
        assert started.start_time is not None

    def test_cancel_count_task(self, db: Session, setup_test_data):
        """测试取消盘点"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            created_by=1
        )
        
        # 取消盘点
        cancelled = service.cancel_count_task(task.id)
        
        assert cancelled.status == 'CANCELLED'

    # ============ 库存调整测试 ============

    def test_approve_adjustment_no_difference(self, db: Session, setup_test_data):
        """测试审批无差异的盘点"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建盘点任务
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        service.start_count_task(task.id)
        
        # 录入实盘数量 (账实相符)
        details = service.get_count_details(task.id)
        for detail in details:
            service.record_actual_quantity(
                detail_id=detail.id,
                actual_quantity=detail.system_quantity,
                counted_by=1
            )
        
        # 审批
        result = service.approve_adjustment(
            task_id=task.id,
            approved_by=1
        )
        
        assert result['task'].status == 'COMPLETED'
        assert result['total_adjustments'] == 0  # 无差异,无调整记录

    def test_approve_adjustment_with_difference(self, db: Session, setup_test_data):
        """测试审批有差异的盘点"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        inv_service = InventoryManagementService(db, tenant_id)
        
        # 创建盘点任务
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        service.start_count_task(task.id)
        
        # 录入实盘数量 (有差异)
        details = service.get_count_details(task.id)
        for i, detail in enumerate(details):
            # 第一个物料盘盈10,第二个物料盘亏5,其他账实相符
            if i == 0:
                actual_qty = detail.system_quantity + Decimal('10')
            elif i == 1:
                actual_qty = detail.system_quantity - Decimal('5')
            else:
                actual_qty = detail.system_quantity
            
            service.record_actual_quantity(
                detail_id=detail.id,
                actual_quantity=actual_qty,
                counted_by=1
            )
        
        # 审批并自动调整
        result = service.approve_adjustment(
            task_id=task.id,
            approved_by=1,
            auto_adjust=True
        )
        
        assert result['task'].status == 'COMPLETED'
        assert result['total_adjustments'] == 2  # 2条有差异
        
        # 验证库存已调整
        materials = setup_test_data['materials']
        stock_0 = inv_service.get_total_quantity(materials[0].id)
        stock_1 = inv_service.get_total_quantity(materials[1].id)
        
        # 原库存分别是100和200,调整后应该是110和195
        assert stock_0 == Decimal('110')
        assert stock_1 == Decimal('195')

    # ============ 盘点报表测试 ============

    def test_get_count_summary(self, db: Session, setup_test_data):
        """测试获取盘点汇总"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建并完成盘点
        task = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            location='仓库A',
            created_by=1
        )
        
        service.start_count_task(task.id)
        
        details = service.get_count_details(task.id)
        for i, detail in enumerate(details):
            # 设置不同的差异情况
            if i == 0:
                actual_qty = detail.system_quantity + Decimal('10')  # 盘盈
            elif i == 1:
                actual_qty = detail.system_quantity - Decimal('5')   # 盘亏
            else:
                actual_qty = detail.system_quantity  # 相符
            
            service.record_actual_quantity(
                detail_id=detail.id,
                actual_quantity=actual_qty,
                counted_by=1
            )
        
        # 获取汇总
        summary = service.get_count_summary(task.id)
        
        assert summary['task_info']['task_no'] == task.task_no
        assert summary['statistics']['total_items'] == 5
        assert summary['statistics']['matched_items'] == 3
        assert summary['statistics']['profit_items'] == 1
        assert summary['statistics']['loss_items'] == 1
        assert 'top_differences' in summary

    def test_analyze_count_history(self, db: Session, setup_test_data):
        """测试分析历史盘点数据"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建多个盘点任务
        for i in range(3):
            task = service.create_count_task(
                count_type='FULL',
                count_date=date.today() - timedelta(days=i*10),
                location='仓库A',
                created_by=1
            )
            
            service.start_count_task(task.id)
            
            details = service.get_count_details(task.id)
            for detail in details:
                service.record_actual_quantity(
                    detail_id=detail.id,
                    actual_quantity=detail.system_quantity,
                    counted_by=1
                )
            
            service.approve_adjustment(task_id=task.id, approved_by=1)
        
        # 分析历史
        analysis = service.analyze_count_history()
        
        assert analysis['summary']['total_count_tasks'] == 3
        assert analysis['summary']['avg_accuracy_rate'] == 100.0
        assert len(analysis['trend']) == 3

    # ============ 盘点任务查询测试 ============

    def test_get_count_tasks(self, db: Session, setup_test_data):
        """测试查询盘点任务列表"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建多个任务
        for i in range(3):
            service.create_count_task(
                count_type='FULL',
                count_date=date.today(),
                created_by=1
            )
        
        # 查询任务列表
        tasks = service.get_count_tasks()
        
        assert len(tasks) >= 3

    def test_get_count_tasks_by_status(self, db: Session, setup_test_data):
        """测试按状态查询盘点任务"""
        tenant_id = setup_test_data['tenant_id']
        
        service = StockCountService(db, tenant_id)
        
        # 创建任务并设置不同状态
        task1 = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            created_by=1
        )
        
        task2 = service.create_count_task(
            count_type='FULL',
            count_date=date.today(),
            created_by=1
        )
        
        service.start_count_task(task2.id)
        
        # 查询待盘点
        pending_tasks = service.get_count_tasks(status='PENDING')
        assert len([t for t in pending_tasks if t.id == task1.id]) == 1
        
        # 查询盘点中
        in_progress_tasks = service.get_count_tasks(status='IN_PROGRESS')
        assert len([t for t in in_progress_tasks if t.id == task2.id]) == 1
