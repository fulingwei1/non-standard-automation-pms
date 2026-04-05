# -*- coding: utf-8 -*-
"""
BOM导入器测试
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from app.services.unified_import.bom_importer import BomImporter
from app.models.material import BomHeader, BomItem
from app.models.project import Project


class TestBomImporter:
    """BOM导入器测试"""

    def test_import_bom_data_success(self, db_session, test_user, test_project, test_material):
        """测试成功导入BOM数据"""
        # 准备测试数据
        df = pd.DataFrame({
            "BOM编码*": ["BOM001", "BOM001"],
            "项目编码*": [test_project.project_code, test_project.project_code],
            "物料编码*": [test_material.material_code, test_material.material_code],
            "用量*": [10, 20],
            "单位": ["件", "件"],
            "备注": ["备注1", "备注2"],
        })

        # 执行导入
        imported_count, updated_count, failed_rows = BomImporter.import_bom_data(
            db_session, df, test_user.id, update_existing=False
        )

        # 验证结果
        assert imported_count == 2
        assert updated_count == 0
        assert len(failed_rows) == 0

    def test_import_bom_data_missing_columns(self, db_session, test_user):
        """测试缺少必需列"""
        df = pd.DataFrame({
            "BOM编码*": ["BOM001"],
            "项目编码*": ["PJ001"],
            # 缺少 "物料编码*" 和 "用量*"
        })

        with pytest.raises(Exception) as exc_info:
            BomImporter.import_bom_data(db_session, df, test_user.id)

        assert "缺少必需的列" in str(exc_info.value)

    def test_import_bom_data_project_not_found(self, db_session, test_user, test_material):
        """测试项目不存在"""
        df = pd.DataFrame({
            "BOM编码*": ["BOM001"],
            "项目编码*": ["NONEXISTENT"],
            "物料编码*": [test_material.material_code],
            "用量*": [10],
        })

        imported_count, updated_count, failed_rows = BomImporter.import_bom_data(
            db_session, df, test_user.id
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "未找到项目" in failed_rows[0]["error"]

    def test_import_bom_data_material_not_found(self, db_session, test_user, test_project):
        """测试物料不存在"""
        df = pd.DataFrame({
            "BOM编码*": ["BOM001"],
            "项目编码*": [test_project.project_code],
            "物料编码*": ["NONEXISTENT"],
            "用量*": [10],
        })

        imported_count, updated_count, failed_rows = BomImporter.import_bom_data(
            db_session, df, test_user.id
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "未找到物料" in failed_rows[0]["error"]

    def test_import_bom_data_invalid_quantity(self, db_session, test_user, test_project, test_material):
        """测试无效的用量"""
        df = pd.DataFrame({
            "BOM编码*": ["BOM001"],
            "项目编码*": [test_project.project_code],
            "物料编码*": [test_material.material_code],
            "用量*": ["invalid"],
        })

        imported_count, updated_count, failed_rows = BomImporter.import_bom_data(
            db_session, df, test_user.id
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "用量" in failed_rows[0]["error"]

    def test_import_bom_data_update_existing(self, db_session, test_user, test_project, test_material):
        """测试更新已存在的BOM明细"""
        # 先创建BOM头
        bom_header = BomHeader(
            bom_no="BOM001",
            bom_name="测试BOM",
            project_id=test_project.id,
            version="1.0",
            status="DRAFT",
            created_by=test_user.id,
        )
        db_session.add(bom_header)
        db_session.flush()

        # 创建已存在的BOM明细
        bom_item = BomItem(
            bom_id=bom_header.id,
            item_no=1,
            material_id=test_material.id,
            material_code=test_material.material_code,
            material_name=test_material.material_name,
            specification=test_material.specification,
            unit="件",
            quantity=Decimal("10"),
            source_type="PURCHASE",
        )
        db_session.add(bom_item)
        db_session.commit()

        # 导入相同数据（更新模式）
        df = pd.DataFrame({
            "BOM编码*": ["BOM001"],
            "项目编码*": [test_project.project_code],
            "物料编码*": [test_material.material_code],
            "用量*": [20],
        })

        imported_count, updated_count, failed_rows = BomImporter.import_bom_data(
            db_session, df, test_user.id, update_existing=True
        )

        assert imported_count == 0
        assert updated_count == 1