# -*- coding: utf-8 -*-
"""通用报表生成单元测试"""
import pytest
from unittest.mock import MagicMock
from datetime import date
from app.services.template_report.generic_report import GenericReportMixin


class TestGenericReportMixin:
    def test_generate_generic_report(self):
        db = MagicMock()
        result = GenericReportMixin._generate_generic_report(
            db, "summary", None, None, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert result['report_type'] == "summary"
        assert 'period' in result
        assert result['message'] == "该报表类型待扩展"
