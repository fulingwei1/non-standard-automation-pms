# -*- coding: utf-8 -*-
"""Tests for app.services.report_framework.renderers.pdf_renderer"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_framework.renderers.pdf_renderer import PdfRenderer
from app.services.report_framework.renderers.base import RenderError


class TestPdfRendererInit:
    def test_default_output_dir(self):
        renderer = PdfRenderer()
        assert renderer.output_dir == "reports/pdf"

    def test_custom_output_dir(self):
        renderer = PdfRenderer(output_dir="/tmp/test_pdf")
        assert renderer.output_dir == "/tmp/test_pdf"

    def test_format_name(self):
        renderer = PdfRenderer()
        assert renderer.format_name == "pdf"

    def test_content_type(self):
        renderer = PdfRenderer()
        assert renderer.content_type == "application/pdf"


class TestRegisterFonts:
    @patch("os.path.exists", return_value=False)
    def test_no_fonts_available(self, mock_exists):
        renderer = PdfRenderer.__new__(PdfRenderer)
        renderer._font_registered = False
        renderer._font_name = "Helvetica"
        renderer.FONT_PATHS = ["/nonexistent"]
        renderer._register_fonts()
        assert renderer._font_name == "Helvetica"
        assert renderer._font_registered is True


class TestRender:
    def test_render_empty_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = []
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert result.format == "pdf"
            assert result.file_path is not None
            assert os.path.exists(result.file_path)

    def test_render_with_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s1",
                    "title": "关键指标",
                    "type": "metrics",
                    "items": [
                        {"label": "总数", "value": "42"},
                        {"label": "完成率", "value": "85%"},
                    ],
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_with_table(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s2",
                    "title": "数据表",
                    "type": "table",
                    "columns": [
                        {"field": "name", "label": "名称"},
                        {"field": "value", "label": "数值"},
                    ],
                    "data": [
                        {"name": "A", "value": "100"},
                        {"name": "B", "value": "200"},
                    ],
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_with_chart(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s3",
                    "title": "图表",
                    "type": "chart",
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_empty_table(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s2",
                    "title": "空表",
                    "type": "table",
                    "columns": [],
                    "data": [],
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_landscape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = []
            metadata = {"code": "test", "name": "测试报告", "orientation": "landscape"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_metrics_more_than_4(self):
        """Test metric cards wrapping to multiple rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s1",
                    "title": "多指标",
                    "type": "metrics",
                    "items": [{"label": f"指标{i}", "value": str(i)} for i in range(6)],
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_table_truncation(self):
        """Test table with >50 rows gets truncated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s2",
                    "title": "大表",
                    "type": "table",
                    "columns": [{"field": "x", "label": "X"}],
                    "data": [{"x": str(i)} for i in range(60)],
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)

    def test_render_no_title_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = PdfRenderer(output_dir=tmpdir)
            sections = [
                {
                    "id": "s1",
                    "title": None,
                    "type": "metrics",
                    "items": [],
                }
            ]
            metadata = {"code": "test", "name": "测试报告"}

            result = renderer.render(sections, metadata)
            assert os.path.exists(result.file_path)


class TestRenderError:
    def test_bad_path(self):
        renderer = PdfRenderer(output_dir="/nonexistent/deeply/nested/path/that/should/fail")
        # SimpleDocTemplate might still succeed with makedirs, so let's mock it to fail
        with patch("app.services.report_framework.renderers.pdf_renderer.SimpleDocTemplate") as mock_doc:
            mock_doc.side_effect = Exception("cannot create")
            with pytest.raises(RenderError, match="PDF rendering failed"):
                renderer.render([], {"code": "test", "name": "test"})
