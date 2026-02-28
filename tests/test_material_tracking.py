# -*- coding: utf-8 -*-
"""
物料跟踪系统测试
Team 5: 完整测试套件
"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory
from app.models.production.material_tracking import (
    MaterialBatch,
    MaterialConsumption,
    MaterialAlert,
    MaterialAlertRule,
)
from app.models.production.work_order import WorkOrder
from app.models.project import Project
from app.models.user import User


class TestMaterialBatch:
    """批次管理测试"""
    
    def test_create_batch(self, db: Session, test_material: Material):
        """测试创建物料批次"""
        batch = MaterialBatch(
            batch_no="BATCH-20260216-001",
            material_id=test_material.id,
            production_date=date.today(),
            expire_date=date.today() + timedelta(days=365),
            initial_qty=1000,
            current_qty=1000,
            consumed_qty=0,
            quality_status="QUALIFIED",
            warehouse_location="A-01-01",
            status="ACTIVE",
            barcode="BAR123456789",
        )
        
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        assert batch.id is not None
        assert batch.batch_no == "BATCH-20260216-001"
        assert batch.current_qty == 1000
        assert batch.status == "ACTIVE"
    
    def test_batch_barcode_unique(self, db: Session, test_material: Material):
        """测试条码唯一性"""
        batch1 = MaterialBatch(
            batch_no="BATCH-001",
            material_id=test_material.id,
            initial_qty=100,
            current_qty=100,
            barcode="UNIQUE123",
        )
        db.add(batch1)
        db.commit()
        
        # 尝试创建相同条码
        batch2 = MaterialBatch(
            batch_no="BATCH-002",
            material_id=test_material.id,
            initial_qty=100,
            current_qty=100,
            barcode="UNIQUE123",
        )
        db.add(batch2)
        
        with pytest.raises(Exception):  # IntegrityError
            db.commit()
    
    def test_batch_consumption_update(self, db: Session, test_material: Material):
        """测试批次消耗后库存更新"""
        batch = MaterialBatch(
            batch_no="BATCH-CONS-001",
            material_id=test_material.id,
            initial_qty=1000,
            current_qty=1000,
            consumed_qty=0,
            status="ACTIVE",
        )
        db.add(batch)
        db.commit()
        
        # 消耗100
        batch.current_qty = batch.current_qty - 100
        batch.consumed_qty = batch.consumed_qty + 100
        db.commit()
        
        assert batch.current_qty == 900
        assert batch.consumed_qty == 100
    
    def test_batch_depletion(self, db: Session, test_material: Material):
        """测试批次耗尽状态"""
        batch = MaterialBatch(
            batch_no="BATCH-DEP-001",
            material_id=test_material.id,
            initial_qty=100,
            current_qty=100,
            status="ACTIVE",
        )
        db.add(batch)
        db.commit()
        
        # 消耗全部
        batch.current_qty = 0
        batch.consumed_qty = 100
        batch.status = "DEPLETED"
        db.commit()
        
        assert batch.status == "DEPLETED"
        assert batch.current_qty == 0


class TestMaterialConsumption:
    """消耗记录测试"""
    
    def test_create_consumption(self, db: Session, test_material: Material, test_batch: MaterialBatch):
        """测试创建消耗记录"""
        consumption = MaterialConsumption(
            consumption_no="CONS-20260216-001",
            material_id=test_material.id,
            batch_id=test_batch.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=50,
            unit="件",
            consumption_type="PRODUCTION",
            standard_qty=45,
            unit_price=10.5,
            total_cost=525,
        )
        
        db.add(consumption)
        db.commit()
        db.refresh(consumption)
        
        assert consumption.id is not None
        assert consumption.consumption_qty == 50
        assert consumption.total_cost == 525
    
    def test_waste_identification(self, db: Session, test_material: Material):
        """测试浪费识别"""
        consumption = MaterialConsumption(
            consumption_no="CONS-WASTE-001",
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=110,  # 实际消耗
            standard_qty=100,     # 标准消耗
            unit="件",
            consumption_type="PRODUCTION",
        )
        
        # 计算差异
        consumption.variance_qty = float(consumption.consumption_qty) - float(consumption.standard_qty)
        consumption.variance_rate = (consumption.variance_qty / float(consumption.standard_qty)) * 100
        consumption.is_waste = abs(consumption.variance_rate) > 10
        
        db.add(consumption)
        db.commit()
        
        assert consumption.variance_qty == 10
        assert consumption.variance_rate == 10.0
        assert consumption.is_waste == False  # 刚好10%,不算浪费
        
        # 测试超过10%的浪费
        consumption2 = MaterialConsumption(
            consumption_no="CONS-WASTE-002",
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=120,
            standard_qty=100,
            unit="件",
            consumption_type="PRODUCTION",
        )
        consumption2.variance_qty = 20
        consumption2.variance_rate = 20.0
        consumption2.is_waste = True
        
        db.add(consumption2)
        db.commit()
        
        assert consumption2.is_waste == True
    
    def test_consumption_types(self, db: Session, test_material: Material):
        """测试不同消耗类型"""
        types = ["PRODUCTION", "TESTING", "WASTE", "REWORK", "OTHER"]
        
        for i, cons_type in enumerate(types, 1):
            consumption = MaterialConsumption(
                consumption_no=f"CONS-TYPE-{i:03d}",
                material_id=test_material.id,
                material_code=test_material.material_code,
                material_name=test_material.material_name,
                consumption_date=datetime.now(),
                consumption_qty=10,
                unit="件",
                consumption_type=cons_type,
            )
            db.add(consumption)
        
        db.commit()
        
        # 验证所有类型都已创建
        count = db.query(MaterialConsumption).filter(
            MaterialConsumption.material_id == test_material.id
        ).count()
        assert count == len(types)


class TestMaterialAlert:
    """物料预警测试"""
    
    def test_create_alert(self, db: Session, test_material: Material):
        """测试创建预警记录"""
        alert = MaterialAlert(
            alert_no="ALERT-20260216-001",
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            alert_date=datetime.now(),
            alert_type="LOW_STOCK",
            alert_level="WARNING",
            current_stock=50,
            safety_stock=100,
            shortage_qty=50,
            alert_message="库存低于安全库存",
            status="ACTIVE",
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        assert alert.id is not None
        assert alert.alert_type == "LOW_STOCK"
        assert alert.shortage_qty == 50
    
    def test_alert_levels(self, db: Session, test_material: Material):
        """测试不同预警级别"""
        levels = ["INFO", "WARNING", "CRITICAL", "URGENT"]
        
        for i, level in enumerate(levels, 1):
            alert = MaterialAlert(
                alert_no=f"ALERT-LEVEL-{i:03d}",
                material_id=test_material.id,
                material_code=test_material.material_code,
                material_name=test_material.material_name,
                alert_date=datetime.now(),
                alert_type="LOW_STOCK",
                alert_level=level,
                current_stock=50,
                safety_stock=100,
                alert_message=f"{level}级别预警",
                status="ACTIVE",
            )
            db.add(alert)
        
        db.commit()
        
        # 验证
        count = db.query(MaterialAlert).filter(
            MaterialAlert.material_id == test_material.id
        ).count()
        assert count == len(levels)
    
    def test_alert_types(self, db: Session, test_material: Material):
        """测试不同预警类型"""
        types = ["SHORTAGE", "LOW_STOCK", "EXPIRED", "SLOW_MOVING", "HIGH_WASTE"]
        
        for i, alert_type in enumerate(types, 1):
            alert = MaterialAlert(
                alert_no=f"ALERT-TYPE-{i:03d}",
                material_id=test_material.id,
                material_code=test_material.material_code,
                material_name=test_material.material_name,
                alert_date=datetime.now(),
                alert_type=alert_type,
                alert_level="WARNING",
                alert_message=f"{alert_type}类型预警",
                status="ACTIVE",
            )
            db.add(alert)
        
        db.commit()
        
        count = db.query(MaterialAlert).count()
        assert count == len(types)
    
    def test_alert_resolution(self, db: Session, test_material: Material, test_user: User):
        """测试预警解决"""
        alert = MaterialAlert(
            alert_no="ALERT-RES-001",
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            alert_date=datetime.now(),
            alert_type="LOW_STOCK",
            alert_level="WARNING",
            alert_message="库存不足",
            status="ACTIVE",
        )
        db.add(alert)
        db.commit()
        
        # 解决预警
        alert.status = "RESOLVED"
        alert.resolved_by_id = test_user.id
        alert.resolved_at = datetime.now()
        alert.resolution_note = "已安排采购"
        db.commit()
        
        assert alert.status == "RESOLVED"
        assert alert.resolved_by_id == test_user.id


class TestMaterialAlertRule:
    """预警规则测试"""
    
    def test_create_rule(self, db: Session, test_material: Material):
        """测试创建预警规则"""
        rule = MaterialAlertRule(
            rule_name="低库存预警规则",
            material_id=test_material.id,
            alert_type="LOW_STOCK",
            alert_level="WARNING",
            threshold_type="PERCENTAGE",
            threshold_value=20,
            safety_days=7,
            lead_time_days=3,
            buffer_ratio=1.2,
            is_active=True,
        target_type="PROJECT"
    )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        assert rule.id is not None
        assert rule.threshold_value == 20
        assert rule.is_active == True
    
    def test_global_rule(self, db: Session):
        """测试全局规则(material_id=NULL)"""
        rule = MaterialAlertRule(
            rule_name="全局低库存预警",
            material_id=None,  # 全局规则
            alert_type="LOW_STOCK",
            alert_level="WARNING",
            threshold_type="PERCENTAGE",
            threshold_value=30,
            is_active=True,
        target_type="PROJECT"
    )
        
        db.add(rule)
        db.commit()
        
        assert rule.material_id is None
    
    def test_rule_priority(self, db: Session, test_material: Material):
        """测试规则优先级"""
        rule1 = MaterialAlertRule(
            rule_name="规则1",
            material_id=test_material.id,
            alert_type="LOW_STOCK",
            threshold_type="PERCENTAGE",
            threshold_value=20,
            priority=1,
            is_active=True,
        target_type="PROJECT"
    )
        
        rule2 = MaterialAlertRule(
            rule_name="规则2",
            material_id=test_material.id,
            alert_type="LOW_STOCK",
            threshold_type="PERCENTAGE",
            threshold_value=30,
            priority=10,  # 高优先级
            is_active=True,
        target_type="PROJECT"
    )
        
        db.add_all([rule1, rule2])
        db.commit()
        
        # 查询最高优先级
        top_rule = db.query(MaterialAlertRule).filter(
            MaterialAlertRule.material_id == test_material.id,
            MaterialAlertRule.is_active == True
        ).order_by(MaterialAlertRule.priority.desc()).first()
        
        assert top_rule.rule_name == "规则2"
        assert top_rule.priority == 10


class TestBatchTracing:
    """批次追溯测试"""
    
    def test_forward_tracing(self, db: Session, test_material: Material, test_batch: MaterialBatch):
        """测试正向追溯: 批次 -> 消耗 -> 项目"""
        # 创建消耗记录
        consumption = MaterialConsumption(
            consumption_no="CONS-TRACE-001",
            material_id=test_material.id,
            batch_id=test_batch.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=50,
            unit="件",
            consumption_type="PRODUCTION",
        )
        db.add(consumption)
        db.commit()
        
        # 查询批次的所有消耗记录
        consumptions = db.query(MaterialConsumption).filter(
            MaterialConsumption.batch_id == test_batch.id
        ).all()
        
        assert len(consumptions) > 0
        assert consumptions[0].batch_id == test_batch.id
    
    def test_backward_tracing(self, db: Session, test_material: Material, test_batch: MaterialBatch, test_project: Project):
        """测试反向追溯: 项目 -> 消耗 -> 批次"""
        # 创建消耗记录关联项目
        consumption = MaterialConsumption(
            consumption_no="CONS-BACK-001",
            material_id=test_material.id,
            batch_id=test_batch.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=30,
            unit="件",
            consumption_type="PRODUCTION",
            project_id=test_project.id,
        )
        db.add(consumption)
        db.commit()
        
        # 从项目查找使用的批次
        consumptions = db.query(MaterialConsumption).filter(
            MaterialConsumption.project_id == test_project.id
        ).all()
        
        batch_ids = set([c.batch_id for c in consumptions if c.batch_id])
        
        assert test_batch.id in batch_ids


class TestSafetyStockCalculation:
    """安全库存计算测试"""
    
    def test_avg_daily_consumption(self, db: Session, test_material: Material):
        """测试平均日消耗计算"""
        # 创建30天的消耗记录
        for i in range(30):
            consumption = MaterialConsumption(
                consumption_no=f"CONS-AVG-{i:03d}",
                material_id=test_material.id,
                material_code=test_material.material_code,
                material_name=test_material.material_name,
                consumption_date=datetime.now() - timedelta(days=i),
                consumption_qty=10,  # 每天10件
                unit="件",
                consumption_type="PRODUCTION",
            )
            db.add(consumption)
        
        db.commit()
        
        # 计算平均日消耗
        total = db.query(MaterialConsumption).filter(
            MaterialConsumption.material_id == test_material.id
        ).count()
        
        assert total == 30
        avg_daily = (30 * 10) / 30
        assert avg_daily == 10
    
    def test_safety_stock_formula(self):
        """测试安全库存公式: 安全库存 = 平均日消耗 × (安全天数 + 采购周期) × 安全系数"""
        avg_daily_consumption = 10
        safety_days = 7
        lead_time_days = 3
        buffer_ratio = 1.2
        
        safety_stock = avg_daily_consumption * (safety_days + lead_time_days) * buffer_ratio
        
        assert safety_stock == 10 * 10 * 1.2
        assert safety_stock == 120


class TestInventoryTurnover:
    """库存周转率测试"""
    
    def test_turnover_calculation(self, db: Session, test_material: Material):
        """测试周转率计算: 周转率 = 消耗数量 / 平均库存"""
        # 设置库存
        test_material.current_stock = 200
        db.commit()
        
        # 创建消耗记录
        for i in range(10):
            consumption = MaterialConsumption(
                consumption_no=f"CONS-TURN-{i:03d}",
                material_id=test_material.id,
                material_code=test_material.material_code,
                material_name=test_material.material_name,
                consumption_date=datetime.now() - timedelta(days=i),
                consumption_qty=20,
                unit="件",
                consumption_type="PRODUCTION",
            )
            db.add(consumption)
        
        db.commit()
        
        # 计算周转率
        total_consumption = 10 * 20  # 200
        avg_stock = 200
        turnover_rate = total_consumption / avg_stock
        
        assert turnover_rate == 1.0
        
        # 周转天数
        period_days = 30
        turnover_days = period_days / turnover_rate
        assert turnover_days == 30


class TestWasteTracing:
    """浪费追溯测试"""
    
    def test_waste_identification_threshold(self, db: Session, test_material: Material):
        """测试浪费识别阈值"""
        # 正常消耗 (差异 < 10%)
        normal = MaterialConsumption(
            consumption_no="CONS-NORMAL-001",
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=105,
            standard_qty=100,
            unit="件",
            consumption_type="PRODUCTION",
        )
        normal.variance_qty = 5
        normal.variance_rate = 5.0
        normal.is_waste = False
        
        # 浪费消耗 (差异 > 10%)
        waste = MaterialConsumption(
            consumption_no="CONS-WASTE-001",
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            consumption_date=datetime.now(),
            consumption_qty=125,
            standard_qty=100,
            unit="件",
            consumption_type="PRODUCTION",
        )
        waste.variance_qty = 25
        waste.variance_rate = 25.0
        waste.is_waste = True
        
        db.add_all([normal, waste])
        db.commit()
        
        # 查询浪费记录
        waste_records = db.query(MaterialConsumption).filter(
            MaterialConsumption.is_waste == True
        ).all()
        
        assert len(waste_records) == 1
        assert waste_records[0].variance_rate > 10


# ================== Fixtures ==================
@pytest.fixture
def test_material(db: Session) -> Material:
    """测试物料"""
    category = MaterialCategory(
        category_code="TEST-CAT",
        category_name="测试分类",
        level=1,
    )
    db.add(category)
    db.commit()
    
    material = Material(
        material_code="MAT-TEST-001",
        material_name="测试物料",
        category_id=category.id,
        unit="件",
        standard_price=10.5,
        safety_stock=100,
        current_stock=500,
        is_active=True,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return material


@pytest.fixture
def test_batch(db: Session, test_material: Material) -> MaterialBatch:
    """测试批次"""
    batch = MaterialBatch(
        batch_no="BATCH-TEST-001",
        material_id=test_material.id,
        production_date=date.today(),
        initial_qty=1000,
        current_qty=1000,
        consumed_qty=0,
        quality_status="QUALIFIED",
        warehouse_location="A-01-01",
        status="ACTIVE",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    return batch


@pytest.fixture
def test_user(db: Session) -> User:
    """测试用户"""
    from app.core.security import get_password_hash
    
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash=get_password_hash("test123"),
        real_name="测试用户",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def test_project(db: Session) -> Project:
    """测试项目"""
    project = Project(
        project_no="PRJ-TEST-001",
        project_name="测试项目",
        project_type="标准项目",
        status="IN_PROGRESS",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project
