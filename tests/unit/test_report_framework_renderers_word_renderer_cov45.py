# -*- coding: utf-8 -*-
"""
第四十五批覆盖：report_framework/renderers/word_renderer.py
"""

import pytest
import os
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.report_framework.renderers.word_renderer")

from app.services.report_framework.renderers.word_renderer import WordRenderer
from app.services.report_framework.renderers.base import ReportResult, RenderError


@pytest.fixture
def renderer():
    return WordRenderer(output_dir="/tmp/test_word_reports")


class TestWordRendererProperties:
    def test_format_name(self, renderer):
        assert renderer.format_name == "word"

    def test_content_type(self, renderer):
        assert "wordprocessingml" in renderer.content_type

    def test_output_dir_default(self):
        r = WordRenderer()
        assert r.output_dir == "reports/word"

    def test_output_dir_custom(self, renderer):
        assert renderer.output_dir == "/tmp/test_word_reports"


class TestWordRendererRender:
    @patch("app.services.report_framework.renderers.word_renderer.Document")
    @patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
    def test_render_success(self, mock_makedirs, mock_doc_cls, renderer):
        mock_doc = MagicMock()
        mock_doc.sections = [MagicMock()]
        mock_doc_cls.return_value = mock_doc

        result = renderer.render(
            sections=[],
            metadata={"code": "TEST", "name": "测试报告"},
        )
        assert isinstance(result, ReportResult)
        assert result.format == "word"
        assert result.file_name.endswith(".docx")
        mock_doc.save.assert_called_once()

    @patch("app.services.report_framework.renderers.word_renderer.Document")
    @patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
    def test_render_raises_render_error_on_exception(self, mock_makedirs, mock_doc_cls, renderer):
        mock_doc_cls.side_effect = RuntimeError("docx error")
        with pytest.raises(RenderError, match="Word rendering failed"):
            renderer.render(sections=[], metadata={})

    @patch("app.services.report_framework.renderers.word_renderer.Document")
    @patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
    def test_render_metrics_section(self, mock_makedirs, mock_doc_cls, renderer):
        mock_doc = MagicMock()
        mock_doc.sections = [MagicMock()]
        table_mock = MagicMock()
        mock_doc.add_table.return_value = table_mock
        table_mock.rows = [MagicMock() for _ in range(3)]
        mock_doc_cls.return_value = mock_doc

        sections = [
            {
                "type": "metrics",
                "title": "指标",
                "items": [
                    {"label": "总数", "value": "100"},
                    {"label": "成功率", "value": "75%"},
                ],
            }
        ]
        result = renderer.render(sections=sections, metadata={"code": "M"})
        assert isinstance(result, ReportResult)

    @patch("app.services.report_framework.renderers.word_renderer.Document")
    @patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
    def test_render_table_section_empty_data(self, mock_makedirs, mock_doc_cls, renderer):
        mock_doc = MagicMock()
        mock_doc.sections = [MagicMock()]
        mock_doc_cls.return_value = mock_doc

        sections = [{"type": "table", "title": "表格", "data": [], "columns": []}]
        result = renderer.render(sections=sections, metadata={"code": "T"})
        assert isinstance(result, ReportResult)

    @patch("app.services.report_framework.renderers.word_renderer.Document")
    @patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
    def test_render_chart_section(self, mock_makedirs, mock_doc_cls, renderer):
        mock_doc = MagicMock()
        mock_doc.sections = [MagicMock()]
        mock_doc_cls.return_value = mock_doc

        sections = [{"type": "chart", "title": "图表"}]
        result = renderer.render(sections=sections, metadata={"code": "C"})
        assert isinstance(result, ReportResult)
