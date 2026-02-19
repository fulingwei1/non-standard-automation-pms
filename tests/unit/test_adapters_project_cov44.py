# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 项目报表适配器"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.report_framework.adapters.project import ProjectReportAdapter
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def make_adapter():
    def _make(report_type="weekly"):
        mock_db = MagicMock()
        with patch("app.services.report_framework.adapters.base.ReportEngine"):
            return ProjectReportAdapter(mock_db, report_type=report_type)
    return _make


class TestProjectReportAdapter:

    def test_get_report_code_weekly(self, make_adapter):
        adapter = make_adapter("weekly")
        assert adapter.get_report_code() == "PROJECT_WEEKLY"

    def test_get_report_code_monthly(self, make_adapter):
        adapter = make_adapter("monthly")
        assert adapter.get_report_code() == "PROJECT_MONTHLY"

    def test_generate_data_raises_without_project_id(self, make_adapter):
        adapter = make_adapter()
        with pytest.raises(ValueError, match="project_id"):
            adapter.generate_data(params={})

    def test_generate_data_calls_generator(self, make_adapter):
        adapter = make_adapter("weekly")
        with patch("app.services.report_framework.adapters.project.ProjectReportGenerator") as MockGen:
            MockGen.generate_weekly.return_value = {"items": []}
            result = adapter.generate_data({"project_id": 1})
            MockGen.generate_weekly.assert_called_once()

    def test_generate_data_monthly_calls_monthly_generator(self, make_adapter):
        adapter = make_adapter("monthly")
        with patch("app.services.report_framework.adapters.project.ProjectReportGenerator") as MockGen:
            MockGen.generate_monthly.return_value = {"items": []}
            result = adapter.generate_data({"project_id": 2})
            MockGen.generate_monthly.assert_called_once()

    def test_init_stores_report_type(self, make_adapter):
        adapter = make_adapter("monthly")
        assert adapter.report_type == "monthly"

    def test_adapter_is_base_report_adapter(self, make_adapter):
        from app.services.report_framework.adapters.base import BaseReportAdapter
        adapter = make_adapter()
        assert isinstance(adapter, BaseReportAdapter)
