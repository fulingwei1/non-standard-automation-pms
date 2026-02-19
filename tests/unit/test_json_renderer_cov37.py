# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - JSON渲染器
tests/unit/test_json_renderer_cov37.py
"""
import json
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.report_framework.renderers.json_renderer")

from app.services.report_framework.renderers.json_renderer import (
    CustomJSONEncoder,
    JsonRenderer,
)
from app.services.report_framework.renderers.base import ReportResult


# ── CustomJSONEncoder ─────────────────────────────────────────────────────────

class TestCustomJSONEncoder:
    def test_encodes_datetime(self):
        dt = datetime(2025, 6, 1, 12, 0, 0)
        result = json.dumps(dt, cls=CustomJSONEncoder)
        assert "2025-06-01" in result

    def test_encodes_date(self):
        d = date(2025, 6, 1)
        result = json.dumps(d, cls=CustomJSONEncoder)
        assert "2025-06-01" in result

    def test_encodes_decimal(self):
        result = json.dumps(Decimal("3.14"), cls=CustomJSONEncoder)
        assert "3.14" in result

    def test_encodes_object_with_dict(self):
        obj = MagicMock()
        obj.__dict__ = {"key": "value"}
        result = json.dumps(obj, cls=CustomJSONEncoder)
        assert "value" in result


# ── JsonRenderer ──────────────────────────────────────────────────────────────

class TestJsonRenderer:
    def setup_method(self):
        self.renderer = JsonRenderer()

    def test_format_name_is_json(self):
        assert self.renderer.format_name == "json"

    def test_content_type_is_application_json(self):
        assert self.renderer.content_type == "application/json"

    def test_render_returns_report_result(self):
        sections = [{"title": "Section 1", "data": []}]
        metadata = {"code": "RPT001", "name": "测试报告", "parameters": {}}
        result = self.renderer.render(sections, metadata)
        assert isinstance(result, ReportResult)
        assert result.format == "json"
        assert "sections" in result.data
        assert "meta" in result.data

    def test_render_meta_contains_report_code(self):
        sections = []
        metadata = {"code": "RPT999", "name": "代码测试"}
        result = self.renderer.render(sections, metadata)
        assert result.data["meta"]["report_code"] == "RPT999"

    def test_to_json_string_produces_valid_json(self):
        result = ReportResult(
            data={"key": "value"},
            format="json",
            content_type="application/json",
        )
        json_str = self.renderer.to_json_string(result)
        parsed = json.loads(json_str)
        assert parsed["key"] == "value"

    def test_to_json_string_with_indent(self):
        result = ReportResult(
            data={"a": 1},
            format="json",
            content_type="application/json",
        )
        json_str = self.renderer.to_json_string(result, indent=4)
        # Indented JSON contains newlines
        assert "\n" in json_str
