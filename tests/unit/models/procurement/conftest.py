# -*- coding: utf-8 -*-
"""
Procurement Models 测试的 Fixtures
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def sample_supplier(db_session):
    """创建示例供应商"""
    from app.models.vendor import Supplier
    
    supplier = Supplier(
        supplier_code="SUP001",
        supplier_name="测试供应商",
        contact_person="供应商联系人",
        contact_phone="13800000001"
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def sample_material(db_session):
    """创建示例物料"""
    from app.models.material import Material
    
    material = Material(
        material_code="MAT001",
        material_name="测试物料",
        material_type="原材料",
        unit="件"
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material
