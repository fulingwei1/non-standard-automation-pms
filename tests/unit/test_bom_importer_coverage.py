# -*- coding: utf-8 -*-
"""bom_importer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.unified_import.bom_importer import BomImporter

class TestBomImporterInit:
    def test_init(self):
        service = BomImporter(Mock())
        assert service is not None
