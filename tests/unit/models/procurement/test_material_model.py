# -*- coding: utf-8 -*-
"""
Material Model 测试
"""

import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.models.material import Material


class TestMaterialModel:
    """Material 模型测试"""

    def test_create_material(self, db_session):
        """测试创建物料"""
        material = Material(
            material_code="MAT001",
            material_name="测试物料",
            material_type="原材料",
            unit="件",
            unit_price=Decimal("100.00")
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.id is not None
        assert material.material_code == "MAT001"
        assert material.material_name == "测试物料"

    def test_material_code_unique(self, db_session):
        """测试物料编码唯一性"""
        m1 = Material(
            material_code="MAT001",
            material_name="物料1"
        )
        db_session.add(m1)
        db_session.commit()
        
        m2 = Material(
            material_code="MAT001",
            material_name="物料2"
        )
        db_session.add(m2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_material_type(self, db_session):
        """测试物料类型"""
        types = ["原材料", "半成品", "成品", "辅料"]
        
        for i, mt in enumerate(types):
            material = Material(
                material_code=f"MAT_TYPE_{i}",
                material_name=f"{mt}测试",
                material_type=mt
            )
            db_session.add(material)
        db_session.commit()
        
        count = db_session.query(Material).filter(
            Material.material_type.in_(types)
        ).count()
        assert count == len(types)

    def test_material_unit(self, db_session):
        """测试物料单位"""
        material = Material(
            material_code="MAT002",
            material_name="单位测试",
            unit="千克"
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.unit == "千克"

    def test_material_price(self, db_session):
        """测试物料价格"""
        material = Material(
            material_code="MAT003",
            material_name="价格测试",
            unit_price=Decimal("256.50")
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.unit_price == Decimal("256.50")

    def test_material_specification(self, db_session):
        """测试物料规格"""
        spec = "100mm×200mm×50mm"
        material = Material(
            material_code="MAT004",
            material_name="规格测试",
            specification=spec
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.specification == spec

    def test_material_update(self, db_session, sample_material):
        """测试更新物料"""
        sample_material.material_name = "更新后的物料"
        sample_material.unit_price = Decimal("150.00")
        db_session.commit()
        
        db_session.refresh(sample_material)
        assert sample_material.material_name == "更新后的物料"

    def test_material_delete(self, db_session):
        """测试删除物料"""
        material = Material(
            material_code="MAT_DEL",
            material_name="待删除"
        )
        db_session.add(material)
        db_session.commit()
        mid = material.id
        
        db_session.delete(material)
        db_session.commit()
        
        deleted = db_session.query(Material).filter_by(id=mid).first()
        assert deleted is None

    def test_material_category(self, db_session):
        """测试物料分类"""
        material = Material(
            material_code="MAT005",
            material_name="分类测试",
            category="电子元器件"
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.category == "电子元器件"

    def test_material_stock(self, db_session):
        """测试物料库存"""
        material = Material(
            material_code="MAT006",
            material_name="库存测试",
            stock_quantity=Decimal("500.00"),
            min_stock=Decimal("100.00")
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.stock_quantity == Decimal("500.00")
        assert material.min_stock == Decimal("100.00")

    def test_multiple_materials(self, db_session):
        """测试多个物料"""
        materials = [
            Material(
                material_code=f"MAT{i:03d}",
                material_name=f"物料{i}",
                unit_price=Decimal(f"{i*10}.00")
            ) for i in range(1, 6)
        ]
        db_session.add_all(materials)
        db_session.commit()
        
        count = db_session.query(Material).count()
        assert count >= 5

    def test_material_description(self, db_session):
        """测试物料描述"""
        desc = "高品质进口原材料，通过ISO认证"
        material = Material(
            material_code="MAT007",
            material_name="描述测试",
            description=desc
        )
        db_session.add(material)
        db_session.commit()
        
        assert material.description == desc
