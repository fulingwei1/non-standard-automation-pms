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
    from tests.conftest import _get_or_create_user
    user = _get_or_create_user(
        db_session,
        username="test_user",
        password="test123",
        real_name="测试用户",
        department="测试部门",
        employee_role="ENGINEER"
    )
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

    def test_sync_to_hr_success(self, timesheet_sync_service, db_session):
        """测试同步到HR - 成功场景"""
        from unittest.mock import patch
        from app.services.overtime_calculation_service import OvertimeCalculationService
        
        with patch.object(OvertimeCalculationService, 'get_overtime_statistics') as mock_stats:
            mock_stats.return_value = {
                'total_users': 10,
                'total_overtime_hours': 50.0
            }
            
            result = timesheet_sync_service.sync_to_hr(
                year=2026,
                month=1,
                department_id=None
            )
            
            assert result is not None
            assert result['success'] is True
            assert 'statistics' in result

    def test_sync_to_hr_with_department(self, timesheet_sync_service, db_session):
        """测试同步到HR - 指定部门"""
        from unittest.mock import patch
        from app.services.overtime_calculation_service import OvertimeCalculationService
        
        with patch.object(OvertimeCalculationService, 'get_overtime_statistics') as mock_stats:
            mock_stats.return_value = {
                'total_users': 5,
                'total_overtime_hours': 25.0
            }
            
            result = timesheet_sync_service.sync_to_hr(
                year=2026,
                month=1,
                department_id=1
            )
            
            assert result is not None
            assert result['success'] is True
            mock_stats.assert_called_once_with(2026, 1, 1)

    def test_sync_all_on_approval_timesheet_not_found(self, timesheet_sync_service):
        """测试自动同步 - 工时记录不存在"""
        result = timesheet_sync_service.sync_all_on_approval(timesheet_id=99999)
        
        assert result is not None
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_sync_all_on_approval_success(self, timesheet_sync_service, test_timesheet):
        """测试自动同步 - 成功场景（有项目）"""
        with patch.object(timesheet_sync_service, 'sync_to_finance') as mock_finance, \
             patch.object(timesheet_sync_service, 'sync_to_project') as mock_project:
            
            mock_finance.return_value = {'success': True, 'created': True}
            mock_project.return_value = {'success': True}
            
            result = timesheet_sync_service.sync_all_on_approval(timesheet_id=test_timesheet.id)
            
            assert result is not None
            assert result['success'] is True
            assert 'results' in result
            assert result['results']['finance'] is not None
            assert result['results']['project'] is not None

    def test_sync_all_on_approval_with_rd_project(self, timesheet_sync_service, db_session, test_user):
        """测试自动同步 - 有研发项目"""
        from app.models.rd_project import RdProject
        
        # 创建研发项目
        rd_project = RdProject(
            project_no="RD001",
            project_name="研发项目",
            category_type="SELF",
            initiation_date=date.today()
        )
        db_session.add(rd_project)
        db_session.commit()
        
        # 创建有研发项目的工时记录
        timesheet = Timesheet(
            user_id=test_user.id,
            rd_project_id=rd_project.id,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED"
        )
        db_session.add(timesheet)
        db_session.commit()
        db_session.refresh(timesheet)
        
        with patch.object(timesheet_sync_service, 'sync_to_rd') as mock_rd:
            mock_rd.return_value = {'success': True, 'created': True}
            
            result = timesheet_sync_service.sync_all_on_approval(timesheet_id=timesheet.id)
            
            assert result is not None
            assert result['success'] is True
            assert result['results']['rd'] is not None

    def test_sync_to_rd_not_approved(self, timesheet_sync_service, db_session, test_user):
        """测试同步到研发 - 工时记录未审批"""
        from app.models.rd_project import RdProject
        
        rd_project = RdProject(
            project_no="RD001",
            project_name="研发项目",
            category_type="SELF",
            initiation_date=date.today()
        )
        db_session.add(rd_project)
        db_session.commit()
        
        timesheet = Timesheet(
            user_id=test_user.id,
            rd_project_id=rd_project.id,
            work_date=date.today(),
            hours=8.0,
            status="DRAFT"
        )
        db_session.add(timesheet)
        db_session.commit()
        db_session.refresh(timesheet)
        
        result = timesheet_sync_service.sync_to_rd(timesheet_id=timesheet.id)
        
        assert result is not None
        assert result['success'] is False
        assert '已审批' in result['message']

    def test_sync_to_rd_no_rd_project(self, timesheet_sync_service, db_session, test_user):
        """测试同步到研发 - 工时记录未关联研发项目"""
        timesheet = Timesheet(
            user_id=test_user.id,
            rd_project_id=None,
            work_date=date.today(),
            hours=8.0,
            status="APPROVED"
        )
        db_session.add(timesheet)
        db_session.commit()
        db_session.refresh(timesheet)
        
        result = timesheet_sync_service.sync_to_rd(timesheet_id=timesheet.id)
        
        assert result is not None
        assert result['success'] is False
        assert '未关联研发项目' in result['message']

    def test_sync_to_rd_batch(self, timesheet_sync_service, db_session, test_user):
        """测试批量同步到研发"""
        from app.models.rd_project import RdProject
        
        rd_project = RdProject(
            project_no="RD001",
            project_name="研发项目",
            category_type="SELF",
            initiation_date=date.today()
        )
        db_session.add(rd_project)
        db_session.commit()
        
        # 创建多个已审批的工时记录
        timesheets = []
        for i in range(3):
            ts = Timesheet(
                user_id=test_user.id,
                rd_project_id=rd_project.id,
                work_date=date.today() - timedelta(days=i),
                hours=8.0,
                status="APPROVED"
            )
            db_session.add(ts)
            timesheets.append(ts)
        db_session.commit()
        
        with patch.object(timesheet_sync_service, '_create_rd_cost_from_timesheet') as mock_create:
            mock_create.return_value = {
                'success': True,
                'created': True
            }
            
            result = timesheet_sync_service.sync_to_rd(
                rd_project_id=rd_project.id,
                year=date.today().year,
                month=date.today().month
            )
            
            assert result is not None
            assert result['success'] is True
            assert 'created_count' in result
            assert 'updated_count' in result

    def test_sync_to_project_not_approved(self, timesheet_sync_service, db_session, test_project, test_user):
        """测试同步到项目 - 工时记录未审批"""
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
        
        result = timesheet_sync_service.sync_to_project(timesheet_id=timesheet.id)
        
        assert result is not None
        assert result['success'] is False
        assert '已审批' in result['message']

    def test_sync_to_project_no_project(self, timesheet_sync_service, db_session, test_user):
        """测试同步到项目 - 工时记录未关联项目"""
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
        
        result = timesheet_sync_service.sync_to_project(timesheet_id=timesheet.id)
        
        assert result is not None
        assert result['success'] is False
        assert '未关联项目' in result['message']

    def test_sync_to_project_batch(self, timesheet_sync_service, db_session, test_project, test_user):
        """测试批量同步到项目"""
        from app.services.labor_cost_service import LaborCostService
        
        with patch.object(LaborCostService, 'calculate_project_labor_cost') as mock_calc:
            mock_calc.return_value = {
                'success': True,
                'total_cost': 1000.0
            }
            
            result = timesheet_sync_service.sync_to_project(project_id=test_project.id)
            
            assert result is not None
            assert result['success'] is True

    def test_sync_to_project_incomplete_params(self, timesheet_sync_service):
        """测试同步到项目 - 参数不完整"""
        result = timesheet_sync_service.sync_to_project()
        
        assert result is not None
        assert result['success'] is False
        assert '参数不完整' in result['message']

    def test_create_financial_cost_from_timesheet_new(self, timesheet_sync_service, test_timesheet):
        """测试创建财务成本记录 - 新建"""
        from unittest.mock import patch
        from app.services.hourly_rate_service import HourlyRateService
        
        with patch.object(HourlyRateService, 'get_user_hourly_rate') as mock_rate:
            mock_rate.return_value = Decimal('50.0')
            
            # 确保不存在现有记录
            timesheet_sync_service.db.query(FinancialProjectCost).filter(
                FinancialProjectCost.source_type == 'TIMESHEET',
                FinancialProjectCost.source_no == str(test_timesheet.id)
            ).delete()
            timesheet_sync_service.db.commit()
            
            result = timesheet_sync_service._create_financial_cost_from_timesheet(test_timesheet)
            
            assert result is not None
            assert result['success'] is True
            assert result['created'] is True
            assert 'cost_id' in result

    def test_create_financial_cost_from_timesheet_update(self, timesheet_sync_service, test_timesheet, db_session):
        """测试创建财务成本记录 - 更新现有"""
        from unittest.mock import patch
        from app.services.hourly_rate_service import HourlyRateService
        
        # 创建现有记录
        existing_cost = FinancialProjectCost(
            project_id=test_timesheet.project_id,
            cost_type='LABOR',
            cost_category='人工费',
            cost_item='工时成本',
            amount=Decimal('100.0'),
            cost_date=test_timesheet.work_date,
            uploaded_by=test_timesheet.user_id,
            source_type='TIMESHEET',
            source_no=str(test_timesheet.id)
        )
        db_session.add(existing_cost)
        db_session.commit()
        db_session.refresh(existing_cost)
        
        with patch.object(HourlyRateService, 'get_user_hourly_rate') as mock_rate:
            mock_rate.return_value = Decimal('60.0')
            
            result = timesheet_sync_service._create_financial_cost_from_timesheet(test_timesheet)
            
            assert result is not None
            assert result['success'] is True
            assert result['updated'] is True
            assert result['cost_id'] == existing_cost.id
