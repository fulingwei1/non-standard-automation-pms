# -*- coding: utf-8 -*-
import json
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from app.services.report_framework.renderers.json_renderer import CustomJSONEncoder, JsonRenderer


class TestCustomJSONEncoder:
    def test_datetime(self):
        result = json.dumps({"dt": datetime(2024, 1, 15, 10, 30)}, cls=CustomJSONEncoder)
        assert "2024-01-15" in result

    def test_date(self):
        result = json.dumps({"d": date(2024, 1, 15)}, cls=CustomJSONEncoder)
        assert "2024-01-15" in result

    def test_decimal(self):
        result = json.dumps({"v": Decimal("3.14")}, cls=CustomJSONEncoder)
        assert "3.14" in result


class TestJsonRenderer:
    def setup_method(self):
        self.renderer = JsonRenderer()

    def test_format_name(self):
        assert self.renderer.format_name == "json"

    def test_content_type(self):
        assert self.renderer.content_type == "application/json"

    def test_render(self):
        sections = [{"title": "Test", "data": [1, 2]}]
        metadata = {"code": "RPT001", "name": "Test Report"}
        result = self.renderer.render(sections, metadata)
        assert result.data["meta"]["report_code"] == "RPT001"
        assert result.data["sections"] == sections

    def test_to_json_string(self):
        sections = [{"title": "Test"}]
        metadata = {"code": "RPT001", "name": "Test"}
        result = self.renderer.render(sections, metadata)
        json_str = self.renderer.to_json_string(result)
        parsed = json.loads(json_str)
        assert parsed["meta"]["report_code"] == "RPT001"
