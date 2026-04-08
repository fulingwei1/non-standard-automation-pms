# -*- coding: utf-8 -*-
"""unified_importer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.unified_import.unified_importer import UnifiedImporter

class TestUnifiedImporterInit:
    def test_init(self):
        service = UnifiedImporter(Mock())
        assert service is not None
