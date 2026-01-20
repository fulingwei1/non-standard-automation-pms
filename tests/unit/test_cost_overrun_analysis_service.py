# -*- coding: utf-8 -*-
"""
Tests for cost_overrun_analysis_service service
Covers: app/services/cost_overrun_analysis_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 158 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_overrun_analysis_service import CostOverrunAnalysisService
from app.models.project import Project, ProjectCost


@pytest.fixture
def cost_overrun_analysis_service(db_session: Session):
    """创建 CostOverrunAnalysisService 实例"""
    return CostOverrunAnalysisService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目（成本超支）"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        contract_amount=Decimal("100000.00"),
        budget_amount=Decimal("100000.00"),
        actual_cost=Decimal("120000.00"),  # 超支
        status="ST10"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestCostOverrunAnalysisService:
    """Test suite for CostOverrunAnalysisService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = CostOverrunAnalysisService(db_session)
        assert service is not None
        assert service.db == db_session
        assert service.hourly_rate_service is not None

    def test_analyze_reasons_no_projects(self, cost_overrun_analysis_service):
        """测试成本超支原因分析 - 无项目"""
        result = cost_overrun_analysis_service.analyze_reasons()
        
        assert result is not None
        assert 'analysis_period' in result
        assert 'total_overrun_projects' in result
        assert 'reasons' in result
        assert result['total_overrun_projects'] == 0

    def test_analyze_reasons_with_date_range(self, cost_overrun_analysis_service):
        """测试成本超支原因分析 - 带日期范围"""
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        result = cost_overrun_analysis_service.analyze_reasons(
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result['analysis_period']['start_date'] == start_date.isoformat()
        assert result['analysis_period']['end_date'] == end_date.isoformat()

    def test_analyze_reasons_with_project_id(self, cost_overrun_analysis_service, test_project):
        """测试成本超支原因分析 - 指定项目"""
        result = cost_overrun_analysis_service.analyze_reasons(
            project_id=test_project.id
        )
        
        assert result is not None
        assert 'reasons' in result
        assert isinstance(result['reasons'], list)

    def test_analyze_accountability_no_projects(self, cost_overrun_analysis_service):
        """测试成本超支归责分析 - 无项目"""
        result = cost_overrun_analysis_service.analyze_accountability()
        
        assert result is not None
        assert 'accountability_stats' in result
        assert isinstance(result['accountability_stats'], list)

    def test_analyze_accountability_with_date_range(self, cost_overrun_analysis_service):
        """测试成本超支归责分析 - 带日期范围"""
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        result = cost_overrun_analysis_service.analyze_accountability(
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert 'analysis_period' in result

    def test_analyze_impact_no_projects(self, cost_overrun_analysis_service):
        """测试成本超支影响分析 - 无项目"""
        result = cost_overrun_analysis_service.analyze_impact()
        
        assert result is not None
        assert 'impact_analysis' in result
        assert 'total_impact' in result

    def test_analyze_impact_with_date_range(self, cost_overrun_analysis_service):
        """测试成本超支影响分析 - 带日期范围"""
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        result = cost_overrun_analysis_service.analyze_impact(
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert 'analysis_period' in result
