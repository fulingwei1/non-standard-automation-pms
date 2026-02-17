# -*- coding: utf-8 -*-
"""Tests for cost_overrun_analysis_service"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

class TestCostOverrunAnalysisService:
    """Test suite for CostOverrunAnalysisService"""
    
    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService
        return CostOverrunAnalysisService(db_session)
    
    def test_analyze_reasons(self, service):
        """Test analyzing cost overrun reasons"""
        result = service.analyze_reasons()
        assert result is not None
        assert isinstance(result, dict)
        assert 'analysis_period' in result
        assert 'total_overrun_projects' in result
        assert 'reasons' in result


# ──────────────────────────────────────────────────────────────────────────────
# G4 补充测试（MagicMock，不依赖真实数据库）
# ──────────────────────────────────────────────────────────────────────────────

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestCostOverrunAnalysisServiceG4:
    """G4 补充：CostOverrunAnalysisService 深度覆盖"""

    def _make_service(self):
        from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService
        db = MagicMock()
        service = CostOverrunAnalysisService(db)
        return service, db

    # ---- analyze_reasons: 无项目时返回结构正确 ----

    def test_analyze_reasons_no_projects(self):
        """无项目时返回空原因列表"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_reasons()

        assert result["total_overrun_projects"] == 0
        assert result["reasons"] == []
        assert isinstance(result, dict)

    # ---- analyze_reasons: 有超支项目 ----

    def test_analyze_reasons_with_overrun_project(self):
        """有超支项目时 total_overrun_projects >= 1"""
        service, db = self._make_service()

        project = MagicMock()
        project.id = 1
        project.project_code = "PJ-001"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("150000")

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [project]
        db.query.return_value = q

        # patch _analyze_project_overrun 返回确定的超支结果
        with patch.object(
            service, "_analyze_project_overrun",
            return_value={
                "has_overrun": True,
                "overrun_amount": 50000,
                "project_id": 1,
                "project_code": "PJ-001",
                "reasons": ["scope_change"]
            }
        ):
            result = service.analyze_reasons()

        assert result["total_overrun_projects"] == 1
        assert len(result["reasons"]) == 1
        assert result["reasons"][0]["reason"] == "scope_change"

    # ---- analyze_reasons: date 过滤参数传入 ----

    def test_analyze_reasons_with_date_filter(self):
        """传入 start_date/end_date 时 analysis_period 正确"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_reasons(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert result["analysis_period"]["start_date"] == "2024-01-01"
        assert result["analysis_period"]["end_date"] == "2024-12-31"

    # ---- analyze_reasons: project_id 过滤 ----

    def test_analyze_reasons_with_project_id(self):
        """传入 project_id 时，结果只包含该项目"""
        service, db = self._make_service()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.analyze_reasons(project_id=42)
        assert result["total_overrun_projects"] == 0

    # ---- analyze_accountability ----

    def test_analyze_accountability_no_data(self):
        """无超支项目时 accountability 返回空"""
        service, db = self._make_service()
        with patch.object(
            service, "analyze_reasons",
            return_value={"projects": [], "total_overrun_projects": 0, "reasons": []}
        ):
            result = service.analyze_accountability()
        assert isinstance(result, dict)

    # ---- _analyze_project_overrun: 无超支 ----

    def test_analyze_project_overrun_no_overrun(self):
        """预算 >= 实际成本时，has_overrun=False"""
        service, db = self._make_service()
        project = MagicMock()
        project.id = 1
        project.project_code = "PJ-002"
        project.budget_amount = Decimal("200000")
        project.actual_cost = Decimal("100000")
        project.project_name = "项目2"

        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = project
        db.query.return_value = q

        result = service._analyze_project_overrun(project)
        assert result["has_overrun"] is False
