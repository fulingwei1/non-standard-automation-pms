# -*- coding: utf-8 -*-
"""export单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_integrity.export import ExportMixin

class TestExportMixinInit:
    def test_init(self):
        service = ExportMixin(Mock())
        assert service is not None
