# -*- coding: utf-8 -*-
"""pdf_renderer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.report_framework.renderers.pdf_renderer import PdfRenderer

class TestPdfRendererInit:
    def test_init(self):
        service = PdfRenderer(Mock())
        assert service is not None
