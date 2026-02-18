# -*- coding: utf-8 -*-
"""第二十批 - pipeline_accountability_service 单元测试"""
import pytest
pytest.importorskip("app.services.pipeline_accountability_service")

from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch
from app.services.pipeline_accountability_service import PipelineAccountabilityService


def make_db():
    return MagicMock()


def make_service(db=None):
    if db is None:
        db = make_db()
    with patch("app.services.pipeline_accountability_service.HourlyRateService"):
        svc = PipelineAccountabilityService(db)
    return svc, db


def make_empty_breaks_analysis():
    return {
        "breaks": {},
        "summary": {"total_breaks": 0}
    }


class TestPipelineAccountabilityServiceInit:
    def test_init_sets_db(self):
        db = make_db()
        svc, _ = make_service(db)
        assert svc.db is db

    def test_init_creates_hourly_rate_service(self):
        svc, _ = make_service()
        assert svc.hourly_rate_service is not None


BREAK_SVC_PATH = "app.services.pipeline_break_analysis_service.PipelineBreakAnalysisService"


class TestAnalyzeByStage:
    def test_analyze_by_stage_empty_breaks(self):
        svc, db = make_service()
        with patch(BREAK_SVC_PATH) as MockBreak:
            mock_break_svc = MagicMock()
            mock_break_svc.analyze_pipeline_breaks.return_value = make_empty_breaks_analysis()
            MockBreak.return_value = mock_break_svc
            result = svc.analyze_by_stage()
            assert "analysis_period" in result

    def test_analyze_by_stage_with_dates(self):
        svc, db = make_service()
        start = date(2025, 1, 1)
        end = date(2025, 3, 31)
        with patch(BREAK_SVC_PATH) as MockBreak:
            mock_break_svc = MagicMock()
            mock_break_svc.analyze_pipeline_breaks.return_value = make_empty_breaks_analysis()
            MockBreak.return_value = mock_break_svc
            result = svc.analyze_by_stage(start_date=start, end_date=end)
            period = result.get("analysis_period", {})
            assert period.get("start_date") == "2025-01-01"
            assert period.get("end_date") == "2025-03-31"

    def test_analyze_by_stage_with_break_records(self):
        svc, db = make_service()
        breaks_data = {
            "breaks": {
                "LEAD_TO_OPP": {
                    "break_count": 1,
                    "break_records": [
                        {"responsible_person_id": 1, "pipeline_id": 10},
                    ]
                }
            }
        }
        user1 = MagicMock()
        user1.real_name = "张三"
        user1.department = "销售部"

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = user1  # always return user1
        db.query.return_value = q

        with patch(BREAK_SVC_PATH) as MockBreak:
            mock_break_svc = MagicMock()
            mock_break_svc.analyze_pipeline_breaks.return_value = breaks_data
            MockBreak.return_value = mock_break_svc
            result = svc.analyze_by_stage()
            assert "analysis_period" in result


class TestAnalyzeCostImpact:
    def test_analyze_cost_impact_empty(self):
        svc, db = make_service()
        with patch(BREAK_SVC_PATH) as MockBreak:
            mock_break_svc = MagicMock()
            mock_break_svc.analyze_pipeline_breaks.return_value = make_empty_breaks_analysis()
            MockBreak.return_value = mock_break_svc
            result = svc.analyze_cost_impact()
            assert "summary" in result
            assert result["summary"]["total_cost_impact"] == 0.0

    def test_analyze_cost_impact_with_dates(self):
        svc, db = make_service()
        start = date(2025, 1, 1)
        with patch(BREAK_SVC_PATH) as MockBreak:
            mock_break_svc = MagicMock()
            mock_break_svc.analyze_pipeline_breaks.return_value = make_empty_breaks_analysis()
            MockBreak.return_value = mock_break_svc
            result = svc.analyze_cost_impact(start_date=start)
            assert result["analysis_period"]["start_date"] == "2025-01-01"


class TestCalculateBreakCostImpact:
    def test_cost_impact_unknown_stage_returns_zero(self):
        svc, db = make_service()
        cost = svc._calculate_break_cost_impact("UNKNOWN_STAGE", {})
        assert cost == Decimal("0")

    def test_cost_impact_quote_to_contract_no_pipeline(self):
        svc, db = make_service()
        cost = svc._calculate_break_cost_impact("QUOTE_TO_CONTRACT", {})
        assert cost == Decimal("0")
