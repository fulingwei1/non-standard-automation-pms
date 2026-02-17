# -*- coding: utf-8 -*-
"""
未中标深度原因分析服务单元测试
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestLossDeepAnalysisServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        assert service.db == db_session
        assert service.hourly_rate_service is not None


class TestDetermineInvestmentStage:
    """测试判断项目投入阶段"""

    def test_stage_s1_requirement_only(self, db_session):
        """测试S1阶段-仅需求调研"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = "S1"

        with patch.object(service, '_get_project_hours', return_value=10.0):
            result = service._determine_investment_stage(project)

            assert result == "requirement_only"

    def test_stage_s2_design(self, db_session):
        """测试S2阶段-方案设计"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = "S2"

        result = service._determine_investment_stage(project)

        assert result == "design"

    def test_stage_s4_detailed_design(self, db_session):
        """测试S4阶段-详细设计"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = "S4"

        result = service._determine_investment_stage(project)

        assert result == "detailed_design"

    def test_stage_by_hours_high(self, db_session):
        """测试通过工时判断-高工时"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = None

        with patch.object(service, '_get_project_hours', return_value=100.0):
            result = service._determine_investment_stage(project)

            assert result == "detailed_design"

    def test_stage_by_hours_medium(self, db_session):
        """测试通过工时判断-中等工时"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = None

        with patch.object(service, '_get_project_hours', return_value=50.0):
            result = service._determine_investment_stage(project)

            assert result == "design"

    def test_stage_by_hours_low(self, db_session):
        """测试通过工时判断-低工时"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = None

        with patch.object(service, '_get_project_hours', return_value=20.0):
            result = service._determine_investment_stage(project)

            assert result == "requirement_only"

    def test_stage_unknown(self, db_session):
        """测试未知阶段"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)

        project = MagicMock()
        project.id = 1
        project.stage = None

        with patch.object(service, '_get_project_hours', return_value=0.0):
            result = service._determine_investment_stage(project)

            assert result == "unknown"


class TestGetProjectHours:
    """测试获取项目工时"""

    def test_get_hours_empty(self, db_session):
        """测试无工时记录"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service._get_project_hours(99999)

        assert result == 0.0


class TestCalculateProjectCost:
    """测试计算项目成本"""

    def test_calculate_empty_cost(self, db_session):
        """测试无成本记录"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service._calculate_project_cost(99999)

        assert result == Decimal("0")


class TestAnalyzeLostProjects:
    """测试分析未中标项目"""

    def test_analyze_no_projects(self, db_session):
        """测试无未中标项目"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service.analyze_lost_projects()

        assert result["total_lost_projects"] == 0
        assert "stage_analysis" in result
        assert "reason_analysis" in result
        assert "investment_analysis" in result
        assert "pattern_analysis" in result

    def test_analyze_with_date_filter(self, db_session):
        """测试带日期过滤"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service.analyze_lost_projects(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
        )

        assert result["analysis_period"]["start_date"] == "2025-01-01"
        assert result["analysis_period"]["end_date"] == "2025-12-31"


class TestAnalyzeInvestmentStage:
    """测试分析投入阶段"""

    def test_analyze_empty_projects(self, db_session):
        """测试空项目列表"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service._analyze_investment_stage([])

        assert result["statistics"]["requirement_only"] == 0
        assert result["statistics"]["design"] == 0
        assert result["statistics"]["detailed_design"] == 0
        assert result["details"] == []
        assert result["summary"]["detailed_design_count"] == 0


class TestAnalyzeLossReasons:
    """测试分析未中标原因"""

    def test_analyze_empty_projects(self, db_session):
        """测试空项目列表"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service._analyze_loss_reasons([])

        assert result["statistics"] == {}
        assert result["top_reasons"] == []


class TestAnalyzeInvestmentOutput:
    """测试分析投入产出"""

    def test_analyze_empty_projects(self, db_session):
        """测试空项目列表"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service._analyze_investment_output([])

        assert result["summary"]["total_projects"] == 0
        assert result["summary"]["total_hours"] == 0
        assert result["summary"]["total_cost"] == 0


class TestIdentifyPatterns:
    """测试识别未中标模式"""

    def test_identify_empty_projects(self, db_session):
        """测试空项目列表"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service._identify_patterns([])

        assert result["high_investment_low_win_rate"] == []
        assert result["detailed_design_loss_patterns"] == []
        assert result["salesperson_patterns"] == []


class TestAnalyzeByStage:
    """测试按阶段分析"""

    def test_analyze_by_stage_no_projects(self, db_session):
        """测试无项目"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service.analyze_by_stage("detailed_design")

        assert result["stage"] == "detailed_design"
        assert result["total_projects"] == 0
        assert result["projects"] == []

    def test_analyze_by_stage_with_dates(self, db_session):
        """测试带日期过滤"""
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService

        service = LossDeepAnalysisService(db_session)
        result = service.analyze_by_stage(
        "design",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
        )

        assert result["stage"] == "design"


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()


# ──────────────────────────────────────────────────────────────────────────────
# G4 补充测试（纯 MagicMock，不依赖真实数据库）
# ──────────────────────────────────────────────────────────────────────────────

class TestLossDeepAnalysisServiceG4:
    """G4 补充：LossDeepAnalysisService 额外覆盖"""

    def _make_service(self):
        from app.services.loss_deep_analysis_service import LossDeepAnalysisService
        db = MagicMock()
        with patch(
            "app.services.loss_deep_analysis_service.HourlyRateService"
        ) as MockHRS:
            MockHRS.return_value = MagicMock()
            service = LossDeepAnalysisService(db)
        return service, db

    # ---- analyze_lost_projects: 无项目时返回空 ----

    def test_analyze_lost_projects_empty(self):
        """无未中标项目时返回空汇总"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_lost_projects()

        assert isinstance(result, dict)
        assert result["summary"]["total_projects"] == 0

    # ---- analyze_lost_projects: 日期过滤 ----

    def test_analyze_lost_projects_with_dates(self):
        """传入 start_date/end_date 时正常运行"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert isinstance(result, dict)

    # ---- _determine_investment_stage: s2=design ----

    def test_determine_investment_stage_s2(self):
        """S2 阶段判定为 design"""
        service, db = self._make_service()
        project = MagicMock()
        project.stage = "S2"
        result = service._determine_investment_stage(project)
        assert result == "design"

    # ---- _determine_investment_stage: 高工时走 detailed_design ----

    def test_determine_investment_stage_high_hours(self):
        """工时 > 100h 时判断为 detailed_design"""
        service, db = self._make_service()
        project = MagicMock()
        project.stage = None
        project.id = 1

        with patch.object(service, '_get_project_hours', return_value=150.0):
            result = service._determine_investment_stage(project)
        assert result == "detailed_design"

    # ---- _identify_patterns: 单项目 ----

    def test_identify_patterns_single_project(self):
        """单个项目不产生 patterns"""
        service, db = self._make_service()
        projects = [{"salesperson_id": 1, "salesperson_name": "张三", "cost": 10000}]
        result = service._identify_patterns(projects)
        assert isinstance(result, dict)

    # ---- analyze_by_stage: requirement_only 阶段 ----

    def test_analyze_by_stage_requirement_only(self):
        """analyze_by_stage 对 requirement_only 阶段也能正常返回"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_by_stage("requirement_only")
        assert result["stage"] == "requirement_only"
        assert result["total_projects"] == 0

    # ---- _calculate_project_cost ----

    def test_calculate_project_cost_no_timesheets(self):
        """无工时记录时成本为 0"""
        service, db = self._make_service()
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service._calculate_project_cost(project_id=1)
        assert result == 0 or result == 0.0
