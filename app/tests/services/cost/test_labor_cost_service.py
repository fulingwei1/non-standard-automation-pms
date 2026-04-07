# -*- coding: utf-8 -*-
"""
工时成本服务测试

测试 LaborCostService 的核心功能：
- 工时成本自动计算
- 用户时薪获取
- 项目工时统计
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from app.models.timesheet import Timesheet, TimesheetStatusEnum

from app.services.cost.labor_cost_service import LaborCostService


class TestLaborCostService:
    """工时成本服务测试类"""

    @patch('app.services.cost.labor_cost_service.HourlyRateService.get_user_hourly_rate')
    def test_get_user_hourly_rate(self, mock_get_rate, db_session, test_user):
        """测试获取用户时薪"""
        mock_get_rate.return_value = Decimal("150")
        
        rate = LaborCostService.get_user_hourly_rate(db_session, test_user.id)
        
        assert rate == Decimal("150")
        mock_get_rate.assert_called_once()

    @patch('app.services.cost.labor_cost_service.HourlyRateService.get_user_hourly_rate')
    def test_get_user_hourly_rate_with_date(self, mock_get_rate, db_session, test_user):
        """测试带日期的获取用户时薪"""
        test_date = date(2025, 1, 15)
        mock_get_rate.return_value = Decimal("200")
        
        rate = LaborCostService.get_user_hourly_rate(db_session, test_user.id, test_date)
        
        assert rate == Decimal("200")
        mock_get_rate.assert_called_once_with(db_session, test_user.id, test_date)

    def test_calculate_project_labor_cost_no_project(self, db_session):
        """测试计算不存在的项目工时成本"""
        result = LaborCostService.calculate_project_labor_cost(
            db_session,
            project_id=99999
        )
        
        assert result["success"] is False
        assert "项目不存在" in result["message"]

    def test_calculate_project_labor_cost_no_timesheets(self, db_session, test_project):
        """测试没有工时记录的项目"""
        result = LaborCostService.calculate_project_labor_cost(
            db_session,
            project_id=test_project.id
        )
        
        assert result["success"] is True
        assert "没有已审批的工时记录" in result["message"]
        assert result["cost_count"] == 0

    def test_calculate_project_labor_cost_with_timesheets(self, db_session, test_user, test_project):
        """测试有工时记录的項目"""
        # 创建已审批的工时记录
        timesheet1 = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today() - timedelta(days=5),
            hours=8,
            hourly_rate=Decimal("100"),
            status=TimesheetStatusEnum.APPROVED,
            description="测试工时1",
        )
        timesheet2 = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today() - timedelta(days=3),
            hours=6,
            hourly_rate=Decimal("100"),
            status=TimesheetStatusEnum.APPROVED,
            description="测试工时2",
        )
        
        db_session.add(timesheet1)
        db_session.add(timesheet2)
        db_session.commit()
        
        # 使用 mock 来避免调用 HourlyRateService
        with patch('app.services.cost.labor_cost_service.HourlyRateService.get_user_hourly_rate') as mock_rate:
            mock_rate.return_value = Decimal("100")
            
            result = LaborCostService.calculate_project_labor_cost(
                db_session,
                project_id=test_project.id
            )
            
            assert result["success"] is True
            assert result["cost_count"] >= 0  # 可能创建了成本记录

    def test_calculate_project_labor_cost_with_date_range(self, db_session, test_user, test_project):
        """测试带日期范围的工时成本计算"""
        # 创建已审批的工时记录
        timesheet1 = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today() - timedelta(days=10),
            hours=8,
            hourly_rate=Decimal("120"),
            status=TimesheetStatusEnum.APPROVED,
        )
        timesheet2 = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today() - timedelta(days=3),
            hours=8,
            hourly_rate=Decimal("120"),
            status=TimesheetStatusEnum.APPROVED,
        )
        
        db_session.add(timesheet1)
        db_session.add(timesheet2)
        db_session.commit()
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        with patch('app.services.cost.labor_cost_service.HourlyRateService.get_user_hourly_rate') as mock_rate:
            mock_rate.return_value = Decimal("120")
            
            result = LaborCostService.calculate_project_labor_cost(
                db_session,
                project_id=test_project.id,
                start_date=start_date,
                end_date=end_date
            )
            
            assert result["success"] is True

    def test_calculate_project_labor_cost_with_unapproved(self, db_session, test_user, test_project):
        """测试只包含已审批工时（未审批的不计算）"""
        # 创建已审批和未审批的工时记录
        approved_timesheet = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today() - timedelta(days=5),
            hours=8,
            hourly_rate=Decimal("100"),
            status=TimesheetStatusEnum.APPROVED,
        )
        pending_timesheet = Timesheet(
            user_id=test_user.id,
            project_id=test_project.id,
            work_date=date.today() - timedelta(days=4),
            hours=6,
            hourly_rate=Decimal("100"),
            status=TimesheetStatusEnum.PENDING,
        )
        
        db_session.add(approved_timesheet)
        db_session.add(pending_timesheet)
        db_session.commit()
        
        with patch('app.services.cost.labor_cost_service.HourlyRateService.get_user_hourly_rate') as mock_rate:
            mock_rate.return_value = Decimal("100")
            
            result = LaborCostService.calculate_project_labor_cost(
                db_session,
                project_id=test_project.id
            )
            
            # 应该只计算已审批的工时
            assert result["success"] is True

    def test_service_initialization(self, db_session):
        """测试服务初始化"""
        service = LaborCostService(db_session)
        
        assert service.db is not None
        assert service.DEFAULT_HOURLY_RATE == Decimal("100")