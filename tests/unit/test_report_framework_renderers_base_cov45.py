# -*- coding: utf-8 -*-
"""
第四十五批覆盖：report_framework/renderers/base.py
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from typing import Any, Dict, List

pytest.importorskip("app.services.report_framework.renderers.base")

from app.services.report_framework.renderers.base import (
    ReportResult,
    RenderError,
    Renderer,
)


class ConcreteRenderer(Renderer):
    """测试用具体渲染器"""

    @property
    def format_name(self) -> str:
        return "test"

    @property
    def content_type(self) -> str:
        return "application/test"

    def render(self, sections: List[Dict[str, Any]], metadata: Dict[str, Any]) -> ReportResult:
        return ReportResult(
            data={"sections": sections},
            format=self.format_name,
            content_type=self.content_type,
        )


class TestReportResult:
    def test_basic_creation(self):
        result = ReportResult(data={"key": "val"}, format="json")
        assert result.data == {"key": "val"}
        assert result.format == "json"
        assert result.content_type == "application/json"
        assert isinstance(result.generated_at, datetime)
        assert result.metadata == {}
        assert result.file_path is None
        assert result.file_name is None

    def test_full_creation(self):
        result = ReportResult(
            data={"x": 1},
            format="pdf",
            file_path="/tmp/report.pdf",
            file_name="report.pdf",
            content_type="application/pdf",
            metadata={"version": "1.0"},
        )
        assert result.file_path == "/tmp/report.pdf"
        assert result.file_name == "report.pdf"
        assert result.metadata["version"] == "1.0"


class TestRenderError:
    def test_is_exception(self):
        err = RenderError("something went wrong")
        assert isinstance(err, Exception)
        assert str(err) == "something went wrong"

    def test_raise_and_catch(self):
        with pytest.raises(RenderError, match="render failed"):
            raise RenderError("render failed")


class TestRenderer:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            Renderer()

    def test_concrete_format_name(self):
        renderer = ConcreteRenderer()
        assert renderer.format_name == "test"

    def test_concrete_content_type(self):
        renderer = ConcreteRenderer()
        assert renderer.content_type == "application/test"

    def test_concrete_render(self):
        renderer = ConcreteRenderer()
        sections = [{"type": "metrics", "items": []}]
        metadata = {"name": "Test Report"}
        result = renderer.render(sections, metadata)
        assert isinstance(result, ReportResult)
        assert result.format == "test"
        assert "sections" in result.data

    def test_render_result_has_timestamp(self):
        renderer = ConcreteRenderer()
        result = renderer.render([], {})
        assert result.generated_at <= datetime.now()

    def test_render_empty_sections(self):
        renderer = ConcreteRenderer()
        result = renderer.render([], {"code": "empty"})
        assert result.data["sections"] == []
