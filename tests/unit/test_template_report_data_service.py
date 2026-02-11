# -*- coding: utf-8 -*-
"""Tests for template_report_data_service.py"""
from unittest.mock import MagicMock, patch
from datetime import date
import json

from app.services.template_report_data_service import TemplateReportDataService


class TestTemplateReportDataService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = TemplateReportDataService(self.db)

    def test_parse_filters_none(self):
        assert self.service._parse_filters(None) == {}

    def test_parse_filters_dict(self):
        assert self.service._parse_filters({"a": 1}) == {"a": 1}

    def test_parse_filters_json_string(self):
        assert self.service._parse_filters('{"a": 1}') == {"a": 1}

    def test_parse_filters_invalid_string(self):
        assert self.service._parse_filters("not json") == {}

    def test_parse_filters_other_type(self):
        assert self.service._parse_filters(123) == {}

    def test_normalize_dates_defaults(self):
        start, end = self.service._normalize_dates(None, None)
        assert start < end

    def test_normalize_dates_swapped(self):
        start, end = self.service._normalize_dates(date(2025, 6, 1), date(2025, 1, 1))
        assert start <= end

    def test_humanize_label(self):
        assert TemplateReportDataService._humanize_label("total_hours") == "Total Hours"

    def test_to_json(self):
        assert TemplateReportDataService._to_json({"a": 1}) == '{"a": 1}'
        assert TemplateReportDataService._to_json(object()) != ""

    def test_build_metrics_list(self):
        result = self.service._build_metrics_list({"total": 100, "avg": 50})
        assert len(result) == 2
        assert result[0]['value'] == 100

    def test_build_sections_overview(self):
        sections = {
            "sec1": {"title": "Section 1", "type": "table", "data": [1, 2, 3]},
            "sec2": {"title": "Section 2", "data": {"key": "val"}, "summary": "ok"},
        }
        result = self.service._build_sections_overview(sections)
        assert len(result) == 2
        assert result[0]['item_count'] == 3
        assert result[1]['has_summary'] is True

    def test_build_section_rows_list_data(self):
        sections = {"sec1": {"title": "S1", "data": [{"a": 1}, {"a": 2}]}}
        result = self.service._build_section_rows(sections)
        assert len(result) == 2

    def test_build_section_rows_dict_data(self):
        sections = {"sec1": {"title": "S1", "data": {"key": "val"}}}
        result = self.service._build_section_rows(sections)
        assert len(result) == 1

    def test_build_section_rows_scalar_data(self):
        sections = {"sec1": {"title": "S1", "data": 42}}
        result = self.service._build_section_rows(sections)
        assert len(result) == 1
        assert result[0]['data_preview'] == "42"

    def test_build_charts_overview(self):
        charts = [{"title": "Chart 1", "type": "bar", "data": [1, 2, 3]}]
        result = self.service._build_charts_overview(charts)
        assert result[0]['data_points'] == 3

    def test_get_template_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        import pytest
        with pytest.raises(ValueError, match="不存在"):
            self.service._get_template(999)

    def test_get_template_inactive(self):
        template = MagicMock(is_active=False)
        self.db.query.return_value.filter.return_value.first.return_value = template
        import pytest
        with pytest.raises(ValueError, match="已停用"):
            self.service._get_template(1)

    @patch("app.services.template_report_data_service.TemplateReportCore.generate_from_template")
    def test_build_context(self, mock_gen):
        template = MagicMock(id=1, template_code="T001", template_name="测试",
                             report_type="MONTHLY", is_active=True)
        self.db.query.return_value.filter.return_value.first.return_value = template
        mock_gen.return_value = {
            "sections": {"s1": {"title": "S", "data": []}},
            "metrics": {"total": 10},
            "charts": [],
            "report_type": "MONTHLY",
            "period": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
        }
        result = self.service.build_context(1)
        assert 'template_info' in result
        assert 'metrics_list' in result
