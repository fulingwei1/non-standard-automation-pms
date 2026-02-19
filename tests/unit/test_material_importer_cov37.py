# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 物料数据导入器
tests/unit/test_material_importer_cov37.py
"""
import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.unified_import.material_importer")

from app.services.unified_import.material_importer import MaterialImporter


def _make_db():
    db = MagicMock()
    # query(...).filter(...).first() → None by default (no existing material / vendor)
    db.query.return_value.filter.return_value.first.return_value = None
    return db


class TestMaterialImporterMissingColumns:
    def test_raises_http_exception_on_missing_required_columns(self):
        from fastapi import HTTPException
        db = _make_db()
        df = pd.DataFrame({"规格型号": ["A"]})  # missing 物料编码* and 物料名称*
        with pytest.raises(HTTPException) as exc_info:
            MaterialImporter.import_material_data(db, df, current_user_id=1)
        assert exc_info.value.status_code == 400


class TestMaterialImporterImport:
    def _make_df(self, rows):
        return pd.DataFrame(rows)

    def test_imports_new_material(self):
        db = _make_db()
        df = self._make_df([{"物料编码*": "M001", "物料名称*": "螺丝"}])
        imported, updated, failed = MaterialImporter.import_material_data(db, df, 1)
        assert imported == 1
        assert updated == 0
        assert failed == []

    def test_skips_row_with_empty_code(self):
        db = _make_db()
        df = self._make_df([{"物料编码*": "", "物料名称*": "螺丝"}])
        imported, updated, failed = MaterialImporter.import_material_data(db, df, 1)
        assert imported == 0
        assert len(failed) == 1
        assert "必填" in failed[0]["error"]

    def test_fails_duplicate_without_update_flag(self):
        db = _make_db()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        df = self._make_df([{"物料编码*": "M001", "物料名称*": "螺丝"}])
        imported, updated, failed = MaterialImporter.import_material_data(
            db, df, 1, update_existing=False
        )
        assert imported == 0
        assert len(failed) == 1

    def test_updates_existing_when_flag_set(self):
        db = _make_db()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        df = self._make_df([{"物料编码*": "M001", "物料名称*": "螺丝-新"}])
        imported, updated, failed = MaterialImporter.import_material_data(
            db, df, 1, update_existing=True
        )
        assert updated == 1
        assert imported == 0

    def test_parses_price_field(self):
        db = _make_db()
        df = self._make_df([{"物料编码*": "M002", "物料名称*": "垫片", "参考价格": "12.5"}])
        imported, updated, failed = MaterialImporter.import_material_data(db, df, 1)
        assert imported == 1
        # check db.add was called with a Material-like object
        db.add.assert_called()

    def test_handles_invalid_price_gracefully(self):
        db = _make_db()
        df = self._make_df([
            {"物料编码*": "M003", "物料名称*": "弹簧", "参考价格": "not_a_number"}
        ])
        imported, updated, failed = MaterialImporter.import_material_data(db, df, 1)
        # Should still import, just with default price 0
        assert imported == 1

    def test_creates_supplier_if_not_exists(self):
        db = _make_db()
        # first query returns None for Vendor, then None for Material
        call_results = [None, None]
        db.query.return_value.filter.return_value.first.side_effect = call_results

        df = self._make_df([
            {"物料编码*": "M004", "物料名称*": "齿轮", "默认供应商": "新供应商"}
        ])
        MaterialImporter.import_material_data(db, df, 1)
        # Supplier should have been added (flush called)
        db.flush.assert_called()
