# -*- coding: utf-8 -*-
"""
Tests for delay_root_cause_service service
Covers: app/services/delay_root_cause_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 106 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.delay_root_cause_service import DelayRootCauseService
from app.models.project import Project
from app.models.progress import Task


@pytest.fixture
def delay_root_cause_service(db_session: Session):
    """创建 DelayRootCauseService 实例"""
    return DelayRootCauseService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        planned_end_date=date.today() + timedelta(days=30),
        actual_end_date=None
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_delayed_task(db_session: Session, test_project):
    """创建测试延期任务"""
    task = Task(
        project_id=test_project.id,
        task_name="测试任务",
        plan_start_date=date.today() - timedelta(days=10),
        plan_end_date=date.today() - timedelta(days=5),
        actual_start_date=date.today() - timedelta(days=8),
        actual_end_date=None,
        is_delayed=True,
        delay_reason="MATERIAL_SHORTAGE"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


class TestDelayRootCauseService:
    """Test suite for DelayRootCauseService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = DelayRootCauseService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_analyze_root_cause_no_tasks(self, delay_root_cause_service):
        """测试延期根因分析 - 无延期任务"""
        result = delay_root_cause_service.analyze_root_cause()
        
        assert result is not None
        assert 'analysis_period' in result
        assert 'total_delayed_tasks' in result
        assert 'root_causes' in result
        assert result['total_delayed_tasks'] == 0
        assert len(result['root_causes']) == 0

    def test_analyze_root_cause_with_date_range(self, delay_root_cause_service):
        """测试延期根因分析 - 带日期范围"""
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        result = delay_root_cause_service.analyze_root_cause(
        start_date=start_date,
        end_date=end_date
        )
        
        assert result is not None
        assert result['analysis_period']['start_date'] == start_date.isoformat()
        assert result['analysis_period']['end_date'] == end_date.isoformat()

    def test_analyze_root_cause_with_project_id(self, delay_root_cause_service, test_project, test_delayed_task):
        """测试延期根因分析 - 指定项目"""
        result = delay_root_cause_service.analyze_root_cause(
        project_id=test_project.id
        )
        
        assert result is not None
        assert 'root_causes' in result
        assert isinstance(result['root_causes'], list)
        assert 'summary' in result

    def test_analyze_root_cause_with_reasons(self, delay_root_cause_service, test_delayed_task):
        """测试延期根因分析 - 有延期原因"""
        result = delay_root_cause_service.analyze_root_cause()
        
        assert result is not None
        if result['total_delayed_tasks'] > 0:
            assert len(result['root_causes']) > 0
            assert result['root_causes'][0]['reason'] == "MATERIAL_SHORTAGE"

    def test_analyze_impact_no_tasks(self, delay_root_cause_service):
        """测试延期影响分析 - 无延期任务"""
        result = delay_root_cause_service.analyze_impact()
        
        assert result is not None
        assert 'impact_analysis' in result
        assert 'total_impact' in result

    def test_analyze_impact_with_date_range(self, delay_root_cause_service):
        """测试延期影响分析 - 带日期范围"""
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        result = delay_root_cause_service.analyze_impact(
        start_date=start_date,
        end_date=end_date
        )
        
        assert result is not None
        assert 'analysis_period' in result

    def test_analyze_trends_no_data(self, delay_root_cause_service):
        """测试延期趋势分析 - 无数据"""
        result = delay_root_cause_service.analyze_trends()
        
        assert result is not None
        assert 'trends' in result
        assert isinstance(result['trends'], list)

    def test_analyze_trends_with_date_range(self, delay_root_cause_service):
        """测试延期趋势分析 - 带日期范围"""
        start_date = date.today() - timedelta(days=180)
        end_date = date.today()
        
        result = delay_root_cause_service.analyze_trends(
        start_date=start_date,
        end_date=end_date
        )
        
        assert result is not None
        assert 'analysis_period' in result
        assert 'trends' in result
