# -*- coding: utf-8 -*-
"""import_export单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_template.import_export import ImportExportMixin

class TestImportExportMixinInit:
    def test_init(self):
        service = ImportExportMixin(Mock())
        assert service is not None
