# -*- coding: utf-8 -*-
"""analysis_reports单元测试"""

from app.services.report_data_generation.analysis_reports import AnalysisReportMixin


class TestAnalysisReportMixinInit:
    def test_methods_available(self):
        assert AnalysisReportMixin is not None
        assert hasattr(AnalysisReportMixin, "generate_workload_analysis")
        assert hasattr(AnalysisReportMixin, "generate_cost_analysis")
