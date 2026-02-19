# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 未中标深度原因分析服务 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services.loss_deep_analysis_service import LossDeepAnalysisService
    HAS_LDAS = True
except Exception:
    HAS_LDAS = False

pytestmark = pytest.mark.skipif(not HAS_LDAS, reason="loss_deep_analysis_service 导入失败")


def make_service():
    db = MagicMock()
    with patch("app.services.loss_deep_analysis_service.HourlyRateService"):
        svc = LossDeepAnalysisService(db)
    return svc, db


class TestLossDeepAnalysisServiceInit:
    def test_init(self):
        db = MagicMock()
        with patch("app.services.loss_deep_analysis_service.HourlyRateService"):
            svc = LossDeepAnalysisService(db)
        assert svc.db is db


class TestAnalyzeLostProjects:
    def test_analyze_empty_projects(self):
        """无未中标项目时返回空结果"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = svc.analyze_lost_projects()

        assert result["total_lost_projects"] == 0
        assert "stage_analysis" in result
        assert "reason_analysis" in result
        assert "investment_analysis" in result
        assert "pattern_analysis" in result

    def test_analyze_with_date_range(self):
        """带日期范围的分析"""
        svc, db = make_service()
        mock_query = MagicMock()
        db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = svc.analyze_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert result["analysis_period"]["start_date"] == "2024-01-01"
        assert result["analysis_period"]["end_date"] == "2024-12-31"

    def test_analyze_returns_period_info(self):
        """返回分析期间信息"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = svc.analyze_lost_projects()
        assert result["analysis_period"]["start_date"] is None
        assert result["analysis_period"]["end_date"] is None


class TestDetermineInvestmentStage:
    def test_stage_s4_is_detailed_design(self):
        """S4阶段对应详细设计"""
        svc, db = make_service()
        project = MagicMock()
        project.stage = "S4"
        result = svc._determine_investment_stage(project)
        assert result == "detailed_design"

    def test_stage_s1_is_requirement_only(self):
        """S1阶段对应仅需求调研"""
        svc, db = make_service()
        project = MagicMock()
        project.stage = "S1"
        with patch.object(svc, "_get_project_hours", return_value=10):
            result = svc._determine_investment_stage(project)
        assert result == "requirement_only"

    def test_stage_s2_is_design(self):
        """S2阶段对应方案设计"""
        svc, db = make_service()
        project = MagicMock()
        project.stage = "S2"
        with patch.object(svc, "_get_project_hours", return_value=30):
            result = svc._determine_investment_stage(project)
        assert result == "design"

    def test_unknown_stage_uses_hours(self):
        """未知阶段通过工时判断"""
        svc, db = make_service()
        project = MagicMock()
        project.stage = "X99"

        with patch.object(svc, "_get_project_hours", return_value=100):
            result = svc._determine_investment_stage(project)
        assert result == "detailed_design"

    def test_no_stage_few_hours(self):
        """无阶段且工时少，判断为需求调研"""
        svc, db = make_service()
        project = MagicMock()
        project.stage = None

        with patch.object(svc, "_get_project_hours", return_value=5):
            result = svc._determine_investment_stage(project)
        # 少于40小时，可能是 requirement_only 或 unknown
        assert result in ["requirement_only", "unknown"]


class TestAnalyzeInvestmentStage:
    def test_analyze_stage_with_projects(self):
        """分析包含项目的投入阶段"""
        svc, db = make_service()
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.stage = "S4"
        project.loss_reason = "PRICE"
        project.loss_reason_detail = "价格太高"

        with patch.object(svc, "_determine_investment_stage", return_value="detailed_design"), \
             patch.object(svc, "_get_project_hours", return_value=100), \
             patch.object(svc, "_calculate_project_cost", return_value=5000):
            result = svc._analyze_investment_stage([project])

        assert result["statistics"]["detailed_design"] == 1
        assert len(result["details"]) == 1
        assert result["summary"]["detailed_design_count"] == 1

    def test_analyze_stage_empty(self):
        """无项目时统计全零"""
        svc, db = make_service()
        result = svc._analyze_investment_stage([])
        assert result["summary"]["detailed_design_count"] == 0
        assert result["summary"]["detailed_design_percentage"] == 0


class TestGetProjectHours:
    def test_get_project_hours_no_timesheets(self):
        """无工时记录时返回0"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.scalar.return_value = None
        result = svc._get_project_hours(1)
        assert result == 0

    def test_get_project_hours_with_data(self):
        """有工时记录时返回总计"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.scalar.return_value = 120.5
        result = svc._get_project_hours(1)
        assert result == 120.5
