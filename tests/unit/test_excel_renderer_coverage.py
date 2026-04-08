# -*- coding: utf-8 -*-
"""excel_renderer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.renderers.excel_renderer import ExcelRenderer

class TestExcelRendererInit:
    def test_init(self):
        service = ExcelRenderer(Mock())
        assert service is not None
