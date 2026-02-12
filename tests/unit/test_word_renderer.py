# -*- coding: utf-8 -*-
"""Tests for report_framework/renderers/word_renderer.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestWordRenderer:
    def test_init_default(self):
        from app.services.report_framework.renderers.word_renderer import WordRenderer
        renderer = WordRenderer()
        assert renderer.output_dir == "reports/word"

    def test_init_custom_dir(self):
        from app.services.report_framework.renderers.word_renderer import WordRenderer
        renderer = WordRenderer(output_dir="/tmp/test")
        assert renderer.output_dir == "/tmp/test"

    def test_format_name(self):
        from app.services.report_framework.renderers.word_renderer import WordRenderer
        renderer = WordRenderer()
        assert renderer.format_name == "word"

    def test_content_type(self):
        from app.services.report_framework.renderers.word_renderer import WordRenderer
        renderer = WordRenderer()
        assert "word" in renderer.content_type or "openxml" in renderer.content_type

    @patch("app.services.report_framework.renderers.word_renderer.Document")
    @patch("app.services.report_framework.renderers.word_renderer.os.makedirs")
    def test_render_creates_file(self, mock_makedirs, mock_doc_class):
        from app.services.report_framework.renderers.word_renderer import WordRenderer
        renderer = WordRenderer(output_dir="/tmp/test_reports")
        mock_doc = MagicMock()
        mock_doc.sections = [MagicMock()]
        mock_doc_class.return_value = mock_doc
        result = renderer.render(
            sections=[],
            metadata={"code": "test_report", "title": "Test"}
        )
        assert result is not None
        mock_doc.save.assert_called_once()
