# -*- coding: utf-8 -*-
"""unified_importer单元测试"""
from app.services.unified_import.unified_importer import UnifiedImporter


class TestUnifiedImporterInit:
    def test_init(self):
        assert hasattr(UnifiedImporter, "import_data")
