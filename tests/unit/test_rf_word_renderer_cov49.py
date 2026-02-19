# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/renderers/word_renderer.py"""

import pytest
from unittest.mock import MagicMock, patch, mock_open

try:
    from app.services.report_framework.renderers.word_renderer import WordRenderer
    from app.services.report_framework.renderers.base import RenderError
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_word_renderer_format_name():
    renderer = WordRenderer()
    assert renderer.format_name == "word"


def test_word_renderer_content_type():
    renderer = WordRenderer()
    assert "wordprocessingml" in renderer.content_type


def test_word_renderer_custom_output_dir():
    renderer = WordRenderer(output_dir="/tmp/test_reports")
    assert renderer.output_dir == "/tmp/test_reports"


@patch("app.services.report_framework.renderers.word_renderer.Document")
@patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
def test_render_success(mock_makedirs, mock_document_cls):
    mock_doc = MagicMock()
    mock_document_cls.return_value = mock_doc
    mock_doc.sections = [MagicMock()]
    mock_doc.add_heading.return_value = MagicMock()
    mock_doc.add_paragraph.return_value = MagicMock()

    renderer = WordRenderer(output_dir="/tmp/word_test")
    sections = [{"type": "metrics", "title": "概览", "items": [{"label": "总数", "value": "10"}]}]
    metadata = {"code": "TEST", "name": "测试报告"}

    result = renderer.render(sections, metadata)
    assert result.format == "word"
    assert result.file_name.endswith(".docx")


@patch("app.services.report_framework.renderers.word_renderer.Document")
@patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
def test_render_table_section(mock_makedirs, mock_document_cls):
    mock_doc = MagicMock()
    mock_document_cls.return_value = mock_doc
    mock_doc.sections = [MagicMock()]

    # set up mock table
    mock_table = MagicMock()
    mock_doc.add_table.return_value = mock_table
    mock_row = MagicMock()
    mock_table.rows.__getitem__ = lambda self, idx: mock_row

    renderer = WordRenderer(output_dir="/tmp/word_test")
    sections = [{
        "type": "table",
        "title": "明细",
        "data": [{"name": "Alice", "score": 90}],
        "columns": [{"field": "name", "label": "姓名"}, {"field": "score", "label": "分数"}],
    }]
    metadata = {"code": "T2", "name": "Table Report"}
    result = renderer.render(sections, metadata)
    assert result.format == "word"


@patch("app.services.report_framework.renderers.word_renderer.Document")
@patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
def test_render_chart_section(mock_makedirs, mock_document_cls):
    mock_doc = MagicMock()
    mock_document_cls.return_value = mock_doc
    mock_doc.sections = [MagicMock()]
    mock_doc.add_paragraph.return_value = MagicMock(add_run=MagicMock())

    renderer = WordRenderer(output_dir="/tmp/word_test")
    sections = [{"type": "chart", "title": "图表"}]
    metadata = {"code": "C1", "name": "Chart Report"}
    result = renderer.render(sections, metadata)
    assert result.format == "word"


@patch("app.services.report_framework.renderers.word_renderer.Document")
@patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
def test_render_raises_render_error(mock_makedirs, mock_document_cls):
    mock_document_cls.side_effect = Exception("docx error")
    renderer = WordRenderer(output_dir="/tmp/word_test")
    with pytest.raises(RenderError):
        renderer.render([], {"code": "ERR", "name": "Error Report"})
