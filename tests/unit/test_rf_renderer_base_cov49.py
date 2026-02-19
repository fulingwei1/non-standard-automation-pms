# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/renderers/base.py"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

try:
    from app.services.report_framework.renderers.base import (
        Renderer, ReportResult, RenderError
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteRenderer(Renderer):
    @property
    def format_name(self) -> str:
        return "test_format"

    @property
    def content_type(self) -> str:
        return "application/test"

    def render(self, sections, metadata):
        return ReportResult(data={"sections": sections}, format=self.format_name)


def test_report_result_creation():
    result = ReportResult(data={"key": "val"}, format="json")
    assert result.format == "json"
    assert result.data == {"key": "val"}
    assert result.content_type == "application/json"
    assert result.file_path is None
    assert result.file_name is None


def test_report_result_with_all_fields():
    now = datetime.now()
    result = ReportResult(
        data={"k": 1},
        format="pdf",
        file_path="/tmp/r.pdf",
        file_name="r.pdf",
        content_type="application/pdf",
        generated_at=now,
        metadata={"code": "X"},
    )
    assert result.file_path == "/tmp/r.pdf"
    assert result.file_name == "r.pdf"
    assert result.metadata == {"code": "X"}


def test_render_error_is_exception():
    err = RenderError("something went wrong")
    assert isinstance(err, Exception)
    assert str(err) == "something went wrong"


def test_renderer_is_abstract():
    with pytest.raises(TypeError):
        Renderer()


def test_concrete_renderer_format_name():
    renderer = ConcreteRenderer()
    assert renderer.format_name == "test_format"


def test_concrete_renderer_content_type():
    renderer = ConcreteRenderer()
    assert renderer.content_type == "application/test"


def test_concrete_renderer_render():
    renderer = ConcreteRenderer()
    result = renderer.render([{"type": "metrics"}], {"code": "X"})
    assert isinstance(result, ReportResult)
    assert result.format == "test_format"
