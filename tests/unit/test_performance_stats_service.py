# -*- coding: utf-8 -*-
"""
Tests for performance_stats_service service
Covers: app/services/performance_stats_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 100 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.performance_stats_service import PerformanceStatsService
from app.models.user import User
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.organization import Department


@pytest.fixture
def performance_stats_service(db_session: Session):
    """创建 PerformanceStatsService 实例"""
    return PerformanceStatsService(db_session)


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="test_user",
        real_name="测试用户",
        email="test@example.com",
        password_hash="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_timesheets(db_session: Session, test_user, test_project):
    """创建测试工时记录"""
    timesheets = []
    for i in range(5):
        timesheet = Timesheet(
        user_id=test_user.id,
        project_id=test_project.id,
        work_date=date.today() - timedelta(days=i),
        hours=8.0,
        status="APPROVED"
        )
        db_session.add(timesheet)
        timesheets.append(timesheet)
    db_session.commit()
    return timesheets


class TestPerformanceStatsService:
    """Test suite for PerformanceStatsService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = PerformanceStatsService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_get_user_performance_stats_user_not_found(self, performance_stats_service):
        """测试获取用户绩效统计 - 用户不存在"""
        result = performance_stats_service.get_user_performance_stats(99999)
        
        assert result is not None
        assert 'error' in result
        assert '不存在' in result['error']

    def test_get_user_performance_stats_success(self, performance_stats_service, test_user, test_timesheets):
        """测试获取用户绩效统计 - 成功场景"""
        result = performance_stats_service.get_user_performance_stats(test_user.id)
        
        assert result is not None
        assert 'error' not in result
        assert 'total_hours' in result
        assert 'project_contributions' in result
        assert 'monthly_stats' in result
        assert result['total_hours'] == 40.0  # 5条记录 * 8小时

    def test_get_user_performance_stats_with_date_range(self, performance_stats_service, test_user, test_timesheets):
        """测试获取用户绩效统计 - 带日期范围"""
        start_date = date.today() - timedelta(days=3)
        end_date = date.today()
        
        result = performance_stats_service.get_user_performance_stats(
        test_user.id,
        start_date=start_date,
        end_date=end_date
        )
        
        assert result is not None
        assert result['total_hours'] > 0

    def test_get_user_performance_stats_no_timesheets(self, performance_stats_service, test_user):
        """测试获取用户绩效统计 - 无工时记录"""
        result = performance_stats_service.get_user_performance_stats(test_user.id)
        
        assert result is not None
        assert result['total_hours'] == 0.0
        assert len(result['project_contributions']) == 0

    def test_get_user_performance_stats_project_contribution(self, performance_stats_service, test_user, test_project, test_timesheets):
        """测试项目贡献度统计"""
        result = performance_stats_service.get_user_performance_stats(test_user.id)
        
        assert result is not None
        assert len(result['project_contributions']) > 0
        contribution = result['project_contributions'][0]
        assert 'project_id' in contribution
        assert 'total_hours' in contribution
        assert 'contribution_rate' in contribution

    def test_get_department_performance_stats_not_found(self, performance_stats_service):
        """测试获取部门绩效统计 - 部门不存在"""
        result = performance_stats_service.get_department_performance_stats(99999)
        
        assert result is not None
        assert 'error' in result

    def test_get_department_performance_stats_success(self, performance_stats_service, db_session, test_user):
        """测试获取部门绩效统计 - 成功场景"""
        # 创建部门
        department = Department(
        department_name="测试部门",
        department_code="DEPT001"
        )
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)
        
        # 更新用户部门
        test_user.department_id = department.id
        db_session.add(test_user)
        db_session.commit()
        
        result = performance_stats_service.get_department_performance_stats(department.id)
        
        assert result is not None
        assert 'error' not in result
        assert 'department_id' in result
        assert 'total_hours' in result
        assert 'user_stats' in result

    def test_get_department_performance_stats_no_users(self, performance_stats_service, db_session):
        """测试获取部门绩效统计 - 无用户"""
        department = Department(
        department_name="空部门",
        department_code="DEPT002"
        )
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)
        
        result = performance_stats_service.get_department_performance_stats(department.id)
        
        assert result is not None
        assert result['total_hours'] == 0.0
        assert len(result['user_stats']) == 0

    def test_analyze_skill_expertise_user_not_found(self, performance_stats_service):
        """测试分析技能专长 - 用户不存在"""
        result = performance_stats_service.analyze_skill_expertise(99999)
        
        assert result is not None
        assert 'error' in result

    def test_analyze_skill_expertise_success(self, performance_stats_service, test_user, test_timesheets):
        """测试分析技能专长 - 成功场景"""
        result = performance_stats_service.analyze_skill_expertise(test_user.id)
        
        assert result is not None
        assert 'error' not in result
        assert 'user_id' in result
        assert 'skill_areas' in result
        assert 'expertise_level' in result

    def test_analyze_skill_expertise_no_data(self, performance_stats_service, test_user):
        """测试分析技能专长 - 无数据"""
        result = performance_stats_service.analyze_skill_expertise(test_user.id)
        
        assert result is not None
        assert len(result.get('skill_areas', [])) == 0
