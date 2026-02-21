# -*- coding: utf-8 -*-
"""
集成测试配置和fixtures
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, PurchaseRequest
from app.models.vendor import Vendor
from app.models.project import Project
from app.models.user import User


@pytest.fixture
def test_materials(db: Session):
    """创建测试物料数据"""
    # 创建或获取物料分类
    category = db.query(MaterialCategory).filter_by(category_code="RAW_METAL").first()
    if not category:
        category = MaterialCategory(
            category_code="RAW_METAL",
            category_name="原材料-金属",
            level=1,
            is_active=True
        )
        db.add(category)
        db.flush()
    
    # 创建或获取测试物料
    material_codes = ["M001", "M002", "M003"]
    materials = []
    
    material_configs = [
        {
            "material_code": "M001",
            "material_name": "不锈钢板 304",
            "specification": "1.5mm*1220*2440",
            "unit": "张",
            "material_type": "RAW_MATERIAL",
            "standard_price": Decimal("350.00"),
            "safety_stock": Decimal("50"),
            "current_stock": Decimal("30"),
            "lead_time_days": 7,
            "min_order_qty": Decimal("10"),
            "is_active": True,
            "is_key_material": True
        },
        {
            "material_code": "M002",
            "material_name": "铝合金型材 6061",
            "specification": "50*50*3mm",
            "unit": "米",
            "material_type": "RAW_MATERIAL",
            "standard_price": Decimal("45.50"),
            "safety_stock": Decimal("200"),
            "current_stock": Decimal("180"),
            "lead_time_days": 5,
            "min_order_qty": Decimal("50"),
            "is_active": True,
            "is_key_material": False
        },
        {
            "material_code": "M003",
            "material_name": "电机 AC220V",
            "specification": "0.75KW 1400rpm",
            "unit": "台",
            "material_type": "PURCHASED_PART",
            "standard_price": Decimal("280.00"),
            "safety_stock": Decimal("10"),
            "current_stock": Decimal("15"),
            "lead_time_days": 10,
            "min_order_qty": Decimal("5"),
            "is_active": True,
            "is_key_material": True
        }
    ]
    
    for config in material_configs:
        existing = db.query(Material).filter_by(material_code=config["material_code"]).first()
        if existing:
            materials.append(existing)
        else:
            material = Material(category_id=category.id, **config)
            db.add(material)
            db.flush()
            materials.append(material)
    
    db.commit()
    return materials


@pytest.fixture
def test_suppliers(db: Session):
    """创建测试供应商数据"""
    supplier_configs = [
        {
            "supplier_code": "SUP001",
            "supplier_name": "上海金属材料有限公司",
            "vendor_type": "MATERIAL",
            "contact_person": "张经理",
            "contact_phone": "021-12345678",
            "contact_email": "zhang@metal.com",
            "address": "上海市浦东新区XX路123号",
            "status": "ACTIVE",
            "supplier_level": "A",
            "payment_terms": "月结30天"
        },
        {
            "supplier_code": "SUP002",
            "supplier_name": "广东铝材供应商",
            "vendor_type": "MATERIAL",
            "contact_person": "李总",
            "contact_phone": "0755-87654321",
            "contact_email": "li@aluminum.com",
            "address": "广东省深圳市XX区XX路456号",
            "status": "ACTIVE",
            "supplier_level": "B",
            "payment_terms": "货到付款"
        },
        {
            "supplier_code": "SUP003",
            "supplier_name": "江苏电机制造厂",
            "vendor_type": "MATERIAL",
            "contact_person": "王工",
            "contact_phone": "025-11112222",
            "contact_email": "wang@motor.com",
            "address": "江苏省南京市XX区XX路789号",
            "status": "ACTIVE",
            "supplier_level": "A",
            "payment_terms": "月结60天"
        }
    ]
    
    suppliers = []
    for config in supplier_configs:
        existing = db.query(Vendor).filter_by(supplier_code=config["supplier_code"]).first()
        if existing:
            suppliers.append(existing)
        else:
            supplier = Vendor(**config)
            db.add(supplier)
            db.flush()
            suppliers.append(supplier)
    
    db.commit()
    return suppliers


@pytest.fixture
def test_project(db: Session):
    """创建测试项目"""
    # 检查项目是否已存在
    existing_project = db.query(Project).filter_by(project_code="PRJ2026001").first()
    if existing_project:
        return existing_project
    
    project = Project(
        project_code="PRJ2026001",
        project_name="自动化生产线项目A",
        project_type="CUSTOM",
        status="ST01",
        stage="S1",
        planned_start_date=datetime.utcnow().date(),
        planned_end_date=(datetime.utcnow() + timedelta(days=90)).date(),
        is_active=True
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def test_user(db: Session):
    """创建测试用户"""
    from app.core.security import get_password_hash
    
    # 检查用户是否已存在
    existing_user = db.query(User).filter_by(username="test_purchaser").first()
    if existing_user:
        return existing_user
    
    user = User(
        username="test_purchaser",
        email="purchaser@test.com",
        real_name="测试采购员",
        password_hash=get_password_hash("test123456"),
        is_active=True
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def integration_test_data(db: Session, test_materials, test_suppliers, test_project, test_user):
    """集成测试完整数据集"""
    return {
        "materials": test_materials,
        "suppliers": test_suppliers,
        "project": test_project,
        "user": test_user,
        "db": db
    }
