# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/renderers/pdf_renderer.py"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.report_framework.renderers.pdf_renderer import PdfRenderer


@pytest.mark.skip("TODO: hangs during collection")
class TestPdfRenderer:
    def test_format_name(self):
        renderer = PdfRenderer.__new__(PdfRenderer)
        assert renderer.format_name == "pdf"

    def test_content_type(self):
        renderer = PdfRenderer.__new__(PdfRenderer)
        assert renderer.content_type == "application/pdf"
