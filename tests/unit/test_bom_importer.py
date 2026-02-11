# -*- coding: utf-8 -*-
"""Tests for app.services.unified_import.bom_importer"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi import HTTPException

from app.services.unified_import.bom_importer import BomImporter


class TestBomImporter(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

    def test_missing_required_columns(self):
        df = pd.DataFrame([{"col1": "a"}])
        with self.assertRaises(HTTPException):
            BomImporter.import_bom_data(self.db, df, 1)

    def test_nan_quantity_fails(self):
        df = pd.DataFrame([{
            "BOM编码*": "BOM001",
            "项目编码*": "P001",
            "物料编码*": "M001",
            "用量*": float("nan"),
        }])
        imported, updated, failed = BomImporter.import_bom_data(self.db, df, 1)
        self.assertEqual(imported, 0)
        self.assertEqual(len(failed), 1)
        self.assertIn("必填项", failed[0]["error"])

    def test_zero_quantity_fails(self):
        df = pd.DataFrame([{
            "BOM编码*": "BOM001",
            "项目编码*": "P001",
            "物料编码*": "M001",
            "用量*": 0,
        }])
        imported, updated, failed = BomImporter.import_bom_data(self.db, df, 1)
        self.assertEqual(imported, 0)
        self.assertTrue(len(failed) > 0)

    def test_project_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        df = pd.DataFrame([{
            "BOM编码*": "BOM001",
            "项目编码*": "P999",
            "物料编码*": "M001",
            "用量*": 5,
        }])
        imported, updated, failed = BomImporter.import_bom_data(self.db, df, 1)
        self.assertEqual(imported, 0)
        self.assertIn("未找到项目", failed[0]["error"])

    def test_material_not_found(self):
        project = MagicMock()
        project.id = 1
        # first call: project found, second: material not found
        self.db.query.return_value.filter.return_value.first.side_effect = [project, None]
        df = pd.DataFrame([{
            "BOM编码*": "BOM001",
            "项目编码*": "P001",
            "物料编码*": "M999",
            "用量*": 5,
        }])
        imported, updated, failed = BomImporter.import_bom_data(self.db, df, 1)
        self.assertEqual(imported, 0)
        self.assertIn("未找到物料", failed[0]["error"])

    def test_happy_path_new_bom_item(self):
        project = MagicMock()
        project.id = 1
        project.project_name = "项目A"

        material = MagicMock()
        material.id = 10
        material.material_name = "物料A"
        material.specification = "spec"
        material.source_type = "PURCHASE"

        bom_header = MagicMock()
        bom_header.id = 100

        # project, material, bom_header, existing bom_item (None)
        self.db.query.return_value.filter.return_value.first.side_effect = [
            project, material, bom_header, None
        ]
        self.db.query.return_value.filter.return_value.count.return_value = 0

        df = pd.DataFrame([{
            "BOM编码*": "BOM001",
            "项目编码*": "P001",
            "物料编码*": "M001",
            "用量*": 5,
        }])
        imported, updated, failed = BomImporter.import_bom_data(self.db, df, 1)
        self.assertEqual(imported, 1)
        self.assertEqual(len(failed), 0)


if __name__ == "__main__":
    unittest.main()
