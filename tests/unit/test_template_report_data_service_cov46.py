# -*- coding: utf-8 -*-
"""第四十六批 - 模板报表数据服务单元测试"""
import pytest
from datetime import date

pytest.importorskip("app.services.template_report_data_service",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.template_report_data_service import TemplateReportDataService


def _make_template(tid=1, is_active=True):
    t = MagicMock()
    t.id = tid
    t.template_code = "RPT001"
    t.template_name = "测试报表"
    t.report_type = "PROJECT_WEEKLY"
    t.is_active = is_active
    t.sections = {}
    t.metrics_config = {}
    return t


def _make_service(template=None, is_active=True):
    db = MagicMock()
    t = template or _make_template(is_active=is_active)
    db.query.return_value.filter.return_value.first.return_value = t
    return TemplateReportDataService(db), db, t


class TestGetTemplate:
    def test_raises_when_template_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = TemplateReportDataService(db)
        with pytest.raises(ValueError, match="不存在"):
            svc._get_template(99)

    def test_raises_when_template_inactive(self):
        db = MagicMock()
        t = _make_template(is_active=False)
        db.query.return_value.filter.return_value.first.return_value = t
        svc = TemplateReportDataService(db)
        with pytest.raises(ValueError, match="停用"):
            svc._get_template(1)

    def test_returns_template_when_active(self):
        db = MagicMock()
        t = _make_template(is_active=True)
        db.query.return_value.filter.return_value.first.return_value = t
        svc = TemplateReportDataService(db)
        result = svc._get_template(1)
        assert result is t


class TestParseFilters:
    def test_none_returns_empty_dict(self):
        svc = TemplateReportDataService(MagicMock())
        assert svc._parse_filters(None) == {}

    def test_dict_returned_as_is(self):
        svc = TemplateReportDataService(MagicMock())
        f = {"key": "val"}
        assert svc._parse_filters(f) == f

    def test_json_string_parsed(self):
        svc = TemplateReportDataService(MagicMock())
        result = svc._parse_filters('{"a": 1}')
        assert result == {"a": 1}

    def test_invalid_json_returns_empty(self):
        svc = TemplateReportDataService(MagicMock())
        result = svc._parse_filters("not json {{")
        assert result == {}


class TestNormalizeDates:
    def test_swaps_when_start_after_end(self):
        svc = TemplateReportDataService(MagicMock())
        start, end = svc._normalize_dates(date(2024, 2, 1), date(2024, 1, 1))
        assert start <= end

    def test_defaults_end_to_today(self):
        svc = TemplateReportDataService(MagicMock())
        start, end = svc._normalize_dates(None, None)
        assert end == date.today()


class TestBuildContext:
    def test_returns_all_context_keys(self):
        svc, db, t = _make_service()
        report_data = {
            "template_id": 1,
            "template_code": "RPT001",
            "template_name": "测试报表",
            "report_type": "PROJECT_WEEKLY",
            "period": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "sections": {},
            "metrics": {},
            "charts": []
        }

        with patch("app.services.template_report_data_service.TemplateReportCore.generate_from_template",
                   return_value=report_data):
            result = svc.build_context(1)

        assert "template_info" in result
        assert "metrics_list" in result
        assert "sections_overview" in result
        assert "section_rows" in result
        assert "charts_overview" in result
