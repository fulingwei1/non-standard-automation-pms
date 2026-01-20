# -*- coding: utf-8 -*-
"""
Tests for timesheet_sync_service service
Covers: app/services/timesheet_sync_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 171 lines
Batch: 1
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.timesheet_sync_service import TimesheetSyncService
from app.models.timesheet import Timesheet
from app.models.project import Project, FinancialProjectCost


@pytest.fixture
def timesheet_sync_service(db_session: Session):
    """创建 TimesheetSyncService 实例"""
    return TimesheetSyncService(db_session)


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
def test_user(db_session: Session):
    """创建测试用户"""
    from app.models.user import User
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


@pytest.fixture
def test_timesheet(db_session: Session, test_project, test_user):
    """创建测试工时记录"""
    timesheet = Timesheet(
        user_id=test_user.id,
        project_id=test_project.id,
        work_date=date.today(),
        hours=8.0,
        status="APPROVED"
    )
    db_session.add(timesheet)
    db_session.commit()
    db_session.refresh(timesheet)
    return timesheet


class TestTimesheetSyncService:
    """Test suite for TimesheetSyncService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = TimesheetSyncService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_sync_to_finance_timesheet_not_found(self, timesheet_sync_service):
        """测试同步到财务 - 工时记录不存在"""
        result = timesheet_sync_service.sync_to_finance(timesheet_id=99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_to_finance_not_approved(self, timesheet_sync_service, db_session, test_project, test_user):
        """测试同步到财务 - 工时记录未审批"""
        timesheet = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today(),
            hours=8.0,
            status="DRAFT"
        )
        db_session.add(timesheet)
        db_session.commit()
        db_session.refresh(timesheet)
        
        result = timesheet_sync_service.sync_to_finance(timesheet_id=timesheet.id)
        
        assert result is not None
        assert result['success'] is False
        assert '已审批' in result['message']

    def test_sync_to_finance_no_project(self, timesheet_sync_service, db_session, test_user):
        """测试同步到财务 - 工时记录未关联项目"""
        timesheet = Timesheet(
            user_id=test_user.id,
            project_id=None,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED"
        )
        db_session.add(timesheet)
        db_session.commit()
        db_session.refresh(timesheet)
        
        result = timesheet_sync_service.sync_to_finance(timesheet_id=timesheet.id)
        
        assert result is not None
        assert result['success'] is False
        assert '未关联项目' in result['message']

    def test_sync_to_finance_success(self, timesheet_sync_service, test_timesheet):
        """测试同步到财务 - 成功场景"""
        with patch.object(timesheet_sync_service, '_create_financial_cost_from_timesheet') as mock_create:
            mock_create.return_value = {
                'success': True,
                'created': True,
                'message': '同步成功'
            }
            
            result = timesheet_sync_service.sync_to_finance(timesheet_id=test_timesheet.id)
            
            assert result is not None
            assert result['success'] is True
            mock_create.assert_called_once()

    def test_sync_to_finance_batch(self, timesheet_sync_service, db_session, test_project, test_user):
        """测试批量同步到财务"""
        # 创建多个已审批的工时记录
        timesheets = []
        for i in range(3):
            ts = Timesheet(
                user_id=test_user.id,
                project_id=test_project.id,
                work_date=date.today() - timedelta(days=i),
                hours=8.0,
                status="APPROVED"
            )
            db_session.add(ts)
            timesheets.append(ts)
        db_session.commit()
        
        with patch.object(timesheet_sync_service, '_create_financial_cost_from_timesheet') as mock_create:
            mock_create.return_value = {
                'success': True,
                'created': True
            }
            
            result = timesheet_sync_service.sync_to_finance(
                project_id=test_project.id,
                year=date.today().year,
                month=date.today().month
            )
            
            assert result is not None
            assert result['success'] is True
            assert 'created_count' in result
            assert 'updated_count' in result

    def test_sync_to_finance_incomplete_params(self, timesheet_sync_service):
        """测试同步到财务 - 参数不完整"""
        result = timesheet_sync_service.sync_to_finance()
        
        assert result is not None
        assert result['success'] is False
        assert '参数不完整' in result['message']

    def test_sync_to_rd_timesheet_not_found(self, timesheet_sync_service):
        """测试同步到研发 - 工时记录不存在"""
        result = timesheet_sync_service.sync_to_rd(timesheet_id=99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_to_project_timesheet_not_found(self, timesheet_sync_service):
        """测试同步到项目 - 工时记录不存在"""
        result = timesheet_sync_service.sync_to_project(timesheet_id=99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_to_hr_timesheet_not_found(self, timesheet_sync_service):
        """测试同步到HR - 工时记录不存在"""
        result = timesheet_sync_service.sync_to_hr(timesheet_id=99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']
