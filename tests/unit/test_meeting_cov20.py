# -*- coding: utf-8 -*-
"""第二十批 - meeting (report_framework/adapters/meeting) 单元测试"""
import pytest
pytest.importorskip("app.services.report_framework.adapters.meeting")

from unittest.mock import MagicMock
from app.services.report_framework.adapters.meeting import MeetingReportAdapter


def make_adapter():
    db = MagicMock()
    return MeetingReportAdapter(db=db)


class TestMeetingReportAdapterInit:
    def test_instantiates(self):
        adapter = make_adapter()
        assert adapter is not None


class TestGetReportCode:
    def test_returns_correct_code(self):
        adapter = make_adapter()
        assert adapter.get_report_code() == "MEETING_MONTHLY"

    def test_returns_string(self):
        adapter = make_adapter()
        code = adapter.get_report_code()
        assert isinstance(code, str)


class TestGenerateData:
    def test_generate_data_returns_dict(self):
        adapter = make_adapter()
        params = {"year": 2025, "month": 1}
        result = adapter.generate_data(params)
        assert isinstance(result, dict)

    def test_generate_data_with_user(self):
        adapter = make_adapter()
        params = {"year": 2025, "month": 1}
        user = MagicMock()
        result = adapter.generate_data(params, user=user)
        assert isinstance(result, dict)

    def test_generate_data_with_none_user(self):
        adapter = make_adapter()
        params = {}
        result = adapter.generate_data(params, user=None)
        assert isinstance(result, dict)

    def test_generate_data_empty_params(self):
        adapter = make_adapter()
        result = adapter.generate_data({})
        assert result is not None
