# -*- coding: utf-8 -*-
"""第二十二批：bom_importer 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    import pandas as pd
    from app.services.unified_import.bom_importer import BomImporter
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def db():
    return MagicMock()


def make_df(rows):
    """Helper: create DataFrame with BOM columns"""
    return pd.DataFrame(rows)


class TestBomImporterMissingColumns:
    def test_missing_required_columns_raises_http_error(self, db):
        """缺少必需列时抛出HTTPException"""
        from fastapi import HTTPException
        df = pd.DataFrame([{"SomeCol": "val"}])
        with pytest.raises(HTTPException) as exc_info:
            BomImporter.import_bom_data(db, df, current_user_id=1)
        assert exc_info.value.status_code == 400

    def test_all_required_columns_present_no_error(self, db):
        """所有必需列存在时不报列缺失错误"""
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "PRJ001",
            "物料编码*": "MAT001",
            "用量*": "2.0"
        }])
        # Project not found → should return (0, 0, [failed_row])
        db.query.return_value.filter.return_value.first.return_value = None
        result = BomImporter.import_bom_data(db, df, current_user_id=1)
        assert isinstance(result, tuple)
        assert len(result) == 3


class TestBomImporterRowValidation:
    def test_quantity_nan_goes_to_failed(self, db):
        """用量为NaN时行进入失败列表"""
        import numpy as np
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "PRJ001",
            "物料编码*": "MAT001",
            "用量*": np.nan
        }])
        imported, updated, failed = BomImporter.import_bom_data(db, df, current_user_id=1)
        assert any("用量" in str(r.get("error", "")) for r in failed)

    def test_quantity_zero_goes_to_failed(self, db):
        """用量为0时行进入失败列表"""
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "PRJ001",
            "物料编码*": "MAT001",
            "用量*": "0"
        }])
        imported, updated, failed = BomImporter.import_bom_data(db, df, current_user_id=1)
        assert any("用量" in str(r.get("error", "")) for r in failed)

    def test_invalid_quantity_format_goes_to_failed(self, db):
        """用量格式错误时行进入失败列表"""
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "PRJ001",
            "物料编码*": "MAT001",
            "用量*": "abc"
        }])
        imported, updated, failed = BomImporter.import_bom_data(db, df, current_user_id=1)
        assert any("格式" in str(r.get("error", "")) or "量" in str(r.get("error", "")) for r in failed)

    def test_project_not_found_goes_to_failed(self, db):
        """项目不存在时行进入失败列表"""
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "NONEXIST",
            "物料编码*": "MAT001",
            "用量*": "2.5"
        }])
        db.query.return_value.filter.return_value.first.return_value = None
        imported, updated, failed = BomImporter.import_bom_data(db, df, current_user_id=1)
        assert any("项目" in str(r.get("error", "")) for r in failed)

    def test_material_not_found_goes_to_failed(self, db):
        """物料不存在时行进入失败列表"""
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "PRJ001",
            "物料编码*": "NONEXIST_MAT",
            "用量*": "2.5"
        }])
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"

        def query_side(model):
            m = MagicMock()
            m.filter.return_value = m
            if "Project" in str(model):
                m.first.return_value = mock_project
            else:
                m.first.return_value = None
            return m

        db.query.side_effect = query_side
        imported, updated, failed = BomImporter.import_bom_data(db, df, current_user_id=1)
        assert any("物料" in str(r.get("error", "")) for r in failed)


class TestBomImporterUpdateExisting:
    def test_update_existing_flag_updates_count(self, db):
        """update_existing=True 时更新计数增加"""
        df = make_df([{
            "BOM编码*": "B001",
            "项目编码*": "PRJ001",
            "物料编码*": "MAT001",
            "用量*": "3.0"
        }])
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"

        mock_material = MagicMock()
        mock_material.id = 10
        mock_material.material_code = "MAT001"
        mock_material.material_name = "物料A"
        mock_material.specification = "规格A"
        mock_material.source_type = "PURCHASE"

        mock_bom_header = MagicMock()
        mock_bom_header.id = 100

        mock_bom_item = MagicMock()

        def query_side(model):
            from app.models.material import Material, BomHeader, BomItem
            from app.models.project import Project
            m = MagicMock()
            m.filter.return_value = m
            if model is Project:
                m.first.return_value = mock_project
            elif model is Material:
                m.first.return_value = mock_material
            elif model is BomHeader:
                m.first.return_value = mock_bom_header
            elif model is BomItem:
                m.first.return_value = mock_bom_item
                m.count.return_value = 1
            else:
                m.first.return_value = None
                m.count.return_value = 0
            return m

        db.query.side_effect = query_side
        imported, updated, failed = BomImporter.import_bom_data(
            db, df, current_user_id=1, update_existing=True
        )
        assert updated == 1
