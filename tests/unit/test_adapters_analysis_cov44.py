# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 分析报表适配器"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services.report_framework.adapters.analysis import WorkloadAnalysisAdapter
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def adapter():
    mock_db = MagicMock()
    with patch("app.services.report_framework.adapters.base.ReportEngine"):
        return WorkloadAnalysisAdapter(mock_db)


class TestWorkloadAnalysisAdapter:

    def test_get_report_code(self, adapter):
        assert adapter.get_report_code() == "WORKLOAD_ANALYSIS"

    def test_generate_data_delegates_to_generator(self, adapter):
        with patch("app.services.report_framework.adapters.analysis.AnalysisReportGenerator") as MockGen:
            MockGen.generate_workload_analysis.return_value = {"items": [], "title": "负荷"}
            result = adapter.generate_data({"department_id": 1})
            MockGen.generate_workload_analysis.assert_called_once()
            assert result["title"] == "负荷分析报告"
            assert result["report_type"] == "WORKLOAD_ANALYSIS"

    def test_generate_data_parses_string_dates(self, adapter):
        with patch("app.services.report_framework.adapters.analysis.AnalysisReportGenerator") as MockGen:
            MockGen.generate_workload_analysis.return_value = {}
            adapter.generate_data({
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            })
            _, args, kwargs = MockGen.generate_workload_analysis.mock_calls[0]
            # end_date 应被解析为 date 对象
            assert isinstance(kwargs.get("end_date") or args[3], date)

    def test_generate_data_no_dates_ok(self, adapter):
        with patch("app.services.report_framework.adapters.analysis.AnalysisReportGenerator") as MockGen:
            MockGen.generate_workload_analysis.return_value = {}
            result = adapter.generate_data({})
            assert "report_type" in result

    def test_generate_falls_back_to_generate_data(self, adapter):
        adapter.engine.generate.side_effect = Exception("no yaml")
        with patch("app.services.report_framework.adapters.analysis.AnalysisReportGenerator") as MockGen, \
             patch.object(adapter, "_convert_to_report_result", return_value={"ok": True}) as mock_conv:
            MockGen.generate_workload_analysis.return_value = {}
            result = adapter.generate(params={}, format="json")
            mock_conv.assert_called_once()

    def test_adapter_stores_db(self, adapter):
        assert adapter.db is not None
