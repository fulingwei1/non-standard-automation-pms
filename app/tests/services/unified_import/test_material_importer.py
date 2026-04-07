# -*- coding: utf-8 -*-
"""
物料导入器测试
"""

import pytest
import pandas as pd
from decimal import Decimal

from app.services.unified_import.material_importer import MaterialImporter
from app.models.material import Material


class TestMaterialImporter:
    """物料导入器测试"""

    def test_import_material_data_success(self, db_session, test_user):
        """测试成功导入物料数据"""
        df = pd.DataFrame({
            "物料编码*": ["MAT001", "MAT002"],
            "物料名称*": ["物料A", "物料B"],
            "规格型号": ["规格A", "规格B"],
            "单位": ["件", "个"],
            "物料类型": ["原材料", "辅料"],
            "参考价格": [100.0, 200.0],
            "安全库存": [10, 20],
        })

        imported_count, updated_count, failed_rows = MaterialImporter.import_material_data(
            db_session, df, test_user.id, update_existing=False
        )

        assert imported_count == 2
        assert updated_count == 0
        assert len(failed_rows) == 0

    def test_import_material_data_missing_columns(self, db_session, test_user):
        """测试缺少必需列"""
        df = pd.DataFrame({
            "物料编码*": ["MAT001"],
            # 缺少 "物料名称*"
        })

        with pytest.raises(Exception) as exc_info:
            MaterialImporter.import_material_data(db_session, df, test_user.id)

        assert "缺少必需的列" in str(exc_info.value)

    def test_import_material_data_missing_required_fields(self, db_session, test_user):
        """测试缺少必填字段"""
        df = pd.DataFrame({
            "物料编码*": ["MAT001"],
            "物料名称*": [""],  # 空名称
        })

        imported_count, updated_count, failed_rows = MaterialImporter.import_material_data(
            db_session, df, test_user.id
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "必填项" in failed_rows[0]["error"]

    def test_import_material_data_duplicate(self, db_session, test_user):
        """测试重复物料编码"""
        # 先创建一个物料
        material = Material(
            material_code="MAT001",
            material_name="已存在物料",
            unit="件",
            is_active=True,
            created_by=test_user.id,
        )
        db_session.add(material)
        db_session.commit()

        # 尝试导入相同编码
        df = pd.DataFrame({
            "物料编码*": ["MAT001"],
            "物料名称*": ["新物料"],
        })

        imported_count, updated_count, failed_rows = MaterialImporter.import_material_data(
            db_session, df, test_user.id, update_existing=False
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "已存在" in failed_rows[0]["error"]

    def test_import_material_data_update_existing(self, db_session, test_user):
        """测试更新已存在的物料"""
        # 先创建一个物料
        material = Material(
            material_code="MAT001",
            material_name="原物料",
            unit="件",
            standard_price=Decimal("100"),
            is_active=True,
            created_by=test_user.id,
        )
        db_session.add(material)
        db_session.commit()

        # 更新导入
        df = pd.DataFrame({
            "物料编码*": ["MAT001"],
            "物料名称*": ["更新后的物料"],
            "参考价格": [200.0],
        })

        imported_count, updated_count, failed_rows = MaterialImporter.import_material_data(
            db_session, df, test_user.id, update_existing=True
        )

        assert imported_count == 0
        assert updated_count == 1

    def test_import_material_data_with_vendor(self, db_session, test_user, test_vendor):
        """测试带供应商的物料导入"""
        # 先确保供应商存在
        db_session.commit()
        
        df = pd.DataFrame({
            "物料编码*": ["MAT001"],
            "物料名称*": ["测试物料"],
            "默认供应商": [test_vendor.supplier_name],
        })

        imported_count, updated_count, failed_rows = MaterialImporter.import_material_data(
            db_session, df, test_user.id
        )

        # 确保提交更改
        db_session.commit()
        
        assert imported_count == 1
        # 验证物料的默认供应商已设置
        material = db_session.query(Material).filter(Material.material_code == "MAT001").first()
        assert material is not None
        assert material.default_supplier_id is not None