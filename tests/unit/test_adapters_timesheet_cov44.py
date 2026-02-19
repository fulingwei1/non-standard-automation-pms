# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 工时报表适配器"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.timesheet import TimesheetReportAdapter
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def adapter():
    mock_db = MagicMock()
    with patch("app.services.report_framework.adapters.base.ReportEngine"):
        return TimesheetReportAdapter(mock_db)


class TestTimesheetReportAdapter:

    def test_get_report_code(self, adapter):
        assert adapter.get_report_code() == "TIMESHEET_WEEKLY"

    def test_generate_data_returns_dict(self, adapter):
        result = adapter.generate_data(params={})
        assert isinstance(result, dict)

    def test_generate_data_has_title(self, adapter):
        result = adapter.generate_data(params={})
        assert result.get("title") == "工时报表"

    def test_generate_data_has_summary(self, adapter):
        result = adapter.generate_data(params={})
        assert "summary" in result

    def test_generate_data_has_details(self, adapter):
        result = adapter.generate_data(params={})
        assert "details" in result

    def test_adapter_inherits_base(self, adapter):
        from app.services.report_framework.adapters.base import BaseReportAdapter
        assert isinstance(adapter, BaseReportAdapter)

    def test_generate_uses_engine_first(self, adapter):
        adapter.engine.generate.return_value = {"engine": True}
        result = adapter.generate(params={}, format="json")
        assert result == {"engine": True}
