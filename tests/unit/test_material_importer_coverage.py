# -*- coding: utf-8 -*-
"""material_importer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.unified_import.material_importer import MaterialImporter

class TestMaterialImporterInit:
    def test_init(self):
        service = MaterialImporter(Mock())
        assert service is not None
