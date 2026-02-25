# -*- coding: utf-8 -*-
"""
Supplier Model 测试
"""

import pytest
from sqlalchemy.exc import IntegrityError
from app.models.vendor import Supplier


class TestSupplierModel:
    """Supplier 模型测试"""

    def test_create_supplier(self, db_session):
        """测试创建供应商"""
        supplier = Supplier(
            supplier_code="SUP001",
            supplier_name="测试供应商",
            contact_person="张三",
            contact_phone="13800138000"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.id is not None
        assert supplier.supplier_code == "SUP001"
        assert supplier.supplier_name == "测试供应商"

    def test_supplier_code_unique(self, db_session):
        """测试供应商编码唯一性"""
        s1 = Supplier(
            supplier_code="SUP001",
            supplier_name="供应商1"
        )
        db_session.add(s1)
        db_session.commit()
        
        s2 = Supplier(
            supplier_code="SUP001",
            supplier_name="供应商2"
        )
        db_session.add(s2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_supplier_contact_info(self, db_session):
        """测试供应商联系信息"""
        supplier = Supplier(
            supplier_code="SUP002",
            supplier_name="联系测试",
            contact_person="李四",
            contact_phone="13900139000",
            contact_email="lisi@supplier.com",
            address="上海市浦东新区XXX路"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.contact_person == "李四"
        assert supplier.contact_phone == "13900139000"
        assert supplier.contact_email == "lisi@supplier.com"

    def test_supplier_level(self, db_session):
        """测试供应商等级"""
        supplier = Supplier(
            supplier_code="SUP003",
            supplier_name="等级测试",
            supplier_level="A级"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.supplier_level == "A级"

    def test_supplier_status(self, db_session, sample_supplier):
        """测试供应商状态"""
        sample_supplier.status = "ACTIVE"
        db_session.commit()
        
        db_session.refresh(sample_supplier)
        assert sample_supplier.status == "ACTIVE"

    def test_supplier_update(self, db_session, sample_supplier):
        """测试更新供应商"""
        sample_supplier.supplier_name = "更新后的供应商"
        sample_supplier.contact_phone = "13900000000"
        db_session.commit()
        
        db_session.refresh(sample_supplier)
        assert sample_supplier.supplier_name == "更新后的供应商"

    def test_supplier_delete(self, db_session):
        """测试删除供应商"""
        supplier = Supplier(
            supplier_code="SUP_DEL",
            supplier_name="待删除"
        )
        db_session.add(supplier)
        db_session.commit()
        sid = supplier.id
        
        db_session.delete(supplier)
        db_session.commit()
        
        deleted = db_session.query(Supplier).filter_by(id=sid).first()
        assert deleted is None

    def test_supplier_type(self, db_session):
        """测试供应商类型"""
        supplier = Supplier(
            supplier_code="SUP004",
            supplier_name="类型测试",
            supplier_type="原材料供应商"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.supplier_type == "原材料供应商"

    def test_supplier_description(self, db_session):
        """测试供应商描述"""
        desc = "专业的电子元器件供应商，合作5年"
        supplier = Supplier(
            supplier_code="SUP005",
            supplier_name="描述测试",
            description=desc
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.description == desc

    def test_multiple_suppliers(self, db_session):
        """测试多个供应商"""
        suppliers = [
            Supplier(
                supplier_code=f"SUP{i:03d}",
                supplier_name=f"供应商{i}"
            ) for i in range(1, 6)
        ]
        db_session.add_all(suppliers)
        db_session.commit()
        
        count = db_session.query(Supplier).count()
        assert count >= 5

    def test_supplier_credit_level(self, db_session):
        """测试供应商信用等级"""
        supplier = Supplier(
            supplier_code="SUP006",
            supplier_name="信用测试",
            credit_level="AAA"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.credit_level == "AAA"

    def test_supplier_payment_terms(self, db_session):
        """测试供应商付款条款"""
        supplier = Supplier(
            supplier_code="SUP007",
            supplier_name="付款测试",
            payment_terms="货到付款"
        )
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.payment_terms == "货到付款"
