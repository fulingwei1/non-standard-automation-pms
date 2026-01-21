# -*- coding: utf-8 -*-
"""
Tests for cost_analysis_service service
Covers: app/services/cost_analysis_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 102 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_analysis_service import CostAnalysisService
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


@pytest.fixture
def cost_analysis_service(db_session: Session):
    """创建 CostAnalysisService 实例"""
    return CostAnalysisService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        budget_amount=Decimal("100000.00"),
        actual_cost=Decimal("50000.00"),
        is_active=True
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="test_user",
        real_name="测试用户",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCostAnalysisService:
    """Test suite for CostAnalysisService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = CostAnalysisService(db_session)
        assert service is not None
        assert service.db == db_session
        assert service.WARNING_THRESHOLD == 80
        assert service.CRITICAL_THRESHOLD == 100

    def test_predict_project_cost_not_found(self, cost_analysis_service):
        """测试预测项目成本 - 项目不存在"""
        result = cost_analysis_service.predict_project_cost(99999)
        
        assert result is not None
        assert 'error' in result
        assert '不存在' in result['error']

    def test_predict_project_cost_success(self, cost_analysis_service, test_project, test_user):
        """测试预测项目成本 - 成功场景"""
        # 创建工时记录
        timesheet = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED"
        )
        cost_analysis_service.db.add(timesheet)
        cost_analysis_service.db.commit()
        
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = cost_analysis_service.predict_project_cost(test_project.id)
            
            assert result is not None
            assert result['project_id'] == test_project.id
            assert 'budget' in result
            assert 'actual_cost' in result
            assert 'predicted_total_cost' in result
            assert 'cost_variance' in result

    def test_predict_project_cost_no_history(self, cost_analysis_service, test_project):
        """测试预测项目成本 - 无历史数据"""
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = cost_analysis_service.predict_project_cost(test_project.id, based_on_history=False)
            
            assert result is not None
            assert result['recorded_hours'] == 0

    def test_check_cost_overrun_alerts_no_projects(self, cost_analysis_service):
        """测试检查成本超支预警 - 无项目"""
        result = cost_analysis_service.check_cost_overrun_alerts()
        
        assert isinstance(result, list)

    def test_check_cost_overrun_alerts_with_project(self, cost_analysis_service, test_project):
        """测试检查成本超支预警 - 有项目"""
        # 设置项目超支
        test_project.actual_cost = Decimal("90000.00")  # 90%执行率
        cost_analysis_service.db.add(test_project)
        cost_analysis_service.db.commit()
        
        with patch.object(cost_analysis_service, 'predict_project_cost') as mock_predict:
            mock_predict.return_value = {'predicted_total_cost': 90000.0}
            
            result = cost_analysis_service.check_cost_overrun_alerts()
            
            assert isinstance(result, list)
            if len(result) > 0:
                assert result[0]['alert_level'] in ['WARNING', 'CRITICAL']

    def test_check_cost_overrun_alerts_specific_project(self, cost_analysis_service, test_project):
        """测试检查成本超支预警 - 指定项目"""
        test_project.actual_cost = Decimal("85000.00")
        cost_analysis_service.db.add(test_project)
        cost_analysis_service.db.commit()
        
        with patch.object(cost_analysis_service, 'predict_project_cost') as mock_predict:
            mock_predict.return_value = {'predicted_total_cost': 85000.0}
            
            result = cost_analysis_service.check_cost_overrun_alerts(project_id=test_project.id)
            
            assert isinstance(result, list)

    def test_compare_project_costs_not_found(self, cost_analysis_service):
        """测试对比项目成本 - 项目不存在"""
        result = cost_analysis_service.compare_project_costs([99999])
        
        assert result is not None
        assert 'error' in result
        assert '不存在' in result['error']

    def test_compare_project_costs_success(self, cost_analysis_service, test_project, test_user):
        """测试对比项目成本 - 成功场景"""
        # 创建工时记录
        timesheet = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED"
        )
        cost_analysis_service.db.add(timesheet)
        cost_analysis_service.db.commit()
        
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = cost_analysis_service.compare_project_costs([test_project.id])
            
            assert result is not None
            assert 'projects' in result
            assert 'summary' in result
            assert len(result['projects']) == 1

    def test_compare_project_costs_multiple(self, cost_analysis_service, db_session, test_user):
        """测试对比项目成本 - 多个项目"""
        projects = []
        for i in range(2):
            project = Project(
                project_code=f"PJ00{i+1}",
                project_name=f"测试项目{i+1}",
                budget_amount=Decimal("100000.00")
            )
            db_session.add(project)
            projects.append(project)
        db_session.commit()
        
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = cost_analysis_service.compare_project_costs([p.id for p in projects])
            
            assert result is not None
            assert len(result['projects']) == 2
            assert result['summary']['project_count'] == 2

    def test_analyze_cost_trend_not_found(self, cost_analysis_service):
        """测试分析成本趋势 - 项目不存在"""
        result = cost_analysis_service.analyze_cost_trend(99999)
        
        assert result is not None
        assert 'error' in result
        assert '不存在' in result['error']

    def test_analyze_cost_trend_success(self, cost_analysis_service, test_project, test_user):
        """测试分析成本趋势 - 成功场景"""
        # 创建工时记录
        timesheet = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED"
        )
        cost_analysis_service.db.add(timesheet)
        cost_analysis_service.db.commit()
        
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = cost_analysis_service.analyze_cost_trend(test_project.id, months=3)
            
            assert result is not None
            assert result['project_id'] == test_project.id
            assert 'monthly_trend' in result
            assert 'total_cost' in result
            assert 'total_hours' in result

    def test_analyze_cost_trend_custom_months(self, cost_analysis_service, test_project):
        """测试分析成本趋势 - 自定义月数"""
        with patch('app.services.cost_analysis_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = cost_analysis_service.analyze_cost_trend(test_project.id, months=6)
            
            assert result is not None
            assert 'start_date' in result
            assert 'end_date' in result
