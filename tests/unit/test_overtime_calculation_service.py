# -*- coding: utf-8 -*-
"""
Tests for overtime_calculation_service service
Covers: app/services/overtime_calculation_service.py
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

from app.services.overtime_calculation_service import OvertimeCalculationService
from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.organization import Department


@pytest.fixture
def overtime_calculation_service(db_session: Session):
    """创建 OvertimeCalculationService 实例"""
    return OvertimeCalculationService(db_session)


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


@pytest.fixture
def test_timesheets(db_session: Session, test_user):
    """创建测试工时记录"""
    timesheets = []
    # 正常工时
    timesheet1 = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        project_id=1,
        work_date=date.today(),
        hours=8.0,
        status="APPROVED",
        overtime_type="NORMAL"
    )
    db_session.add(timesheet1)
    timesheets.append(timesheet1)
    
    # 加班工时
    timesheet2 = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        project_id=1,
        work_date=date.today() - timedelta(days=1),
        hours=2.0,
        status="APPROVED",
        overtime_type="OVERTIME"
    )
    db_session.add(timesheet2)
    timesheets.append(timesheet2)
    
    db_session.commit()
    return timesheets


class TestOvertimeCalculationService:
    """Test suite for OvertimeCalculationService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = OvertimeCalculationService(db_session)
        assert service is not None
        assert service.db == db_session
        assert service.OVERTIME_MULTIPLIER == Decimal("1.5")
        assert service.WEEKEND_MULTIPLIER == Decimal("2.0")
        assert service.HOLIDAY_MULTIPLIER == Decimal("3.0")

    def test_calculate_overtime_pay_normal(self, overtime_calculation_service, test_user):
        """测试计算加班工资 - 正常工时"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_overtime_pay(
                user_id=test_user.id,
                work_date=date.today(),
                hours=Decimal("8.0"),
                overtime_type="NORMAL"
            )
            
            assert result == Decimal("0")  # 正常工时不计算加班工资

    def test_calculate_overtime_pay_overtime(self, overtime_calculation_service, test_user):
        """测试计算加班工资 - 工作日加班"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_overtime_pay(
                user_id=test_user.id,
                work_date=date.today(),
                hours=Decimal("2.0"),
                overtime_type="OVERTIME"
            )
            
            # 2小时 * 100元/小时 * (1.5 - 1) = 100元
            assert result == Decimal("100.00")

    def test_calculate_overtime_pay_weekend(self, overtime_calculation_service, test_user):
        """测试计算加班工资 - 周末加班"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_overtime_pay(
                user_id=test_user.id,
                work_date=date.today(),
                hours=Decimal("4.0"),
                overtime_type="WEEKEND"
            )
            
            # 4小时 * 100元/小时 * (2.0 - 1) = 400元
            assert result == Decimal("400.00")

    def test_calculate_overtime_pay_holiday(self, overtime_calculation_service, test_user):
        """测试计算加班工资 - 节假日加班"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_overtime_pay(
                user_id=test_user.id,
                work_date=date.today(),
                hours=Decimal("3.0"),
                overtime_type="HOLIDAY"
            )
            
            # 3小时 * 100元/小时 * (3.0 - 1) = 600元
            assert result == Decimal("600.00")

    def test_calculate_overtime_pay_invalid_type(self, overtime_calculation_service, test_user):
        """测试计算加班工资 - 无效类型"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_overtime_pay(
                user_id=test_user.id,
                work_date=date.today(),
                hours=Decimal("2.0"),
                overtime_type="INVALID"
            )
            
            assert result == Decimal("0")

    def test_calculate_user_monthly_overtime_pay_user_not_found(self, overtime_calculation_service):
        """测试计算用户月度加班工资 - 用户不存在"""
        result = overtime_calculation_service.calculate_user_monthly_overtime_pay(
            user_id=99999,
            year=2024,
            month=1
        )
        
        assert 'error' in result
        assert '不存在' in result['error']

    def test_calculate_user_monthly_overtime_pay_success(self, overtime_calculation_service, test_user, test_timesheets):
        """测试计算用户月度加班工资 - 成功场景"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_user_monthly_overtime_pay(
                user_id=test_user.id,
                year=date.today().year,
                month=date.today().month
            )
            
            assert result is not None
            assert result['user_id'] == test_user.id
            assert 'total_hours' in result
            assert 'normal_hours' in result
            assert 'overtime_hours' in result
            assert 'total_overtime_pay' in result
            assert 'daily_records' in result

    def test_calculate_user_monthly_overtime_pay_no_timesheets(self, overtime_calculation_service, test_user):
        """测试计算用户月度加班工资 - 无工时记录"""
        with patch('app.services.overtime_calculation_service.HourlyRateService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            result = overtime_calculation_service.calculate_user_monthly_overtime_pay(
                user_id=test_user.id,
                year=2024,
                month=1
            )
            
            assert result is not None
            assert result['total_hours'] == 0.0
            assert result['total_overtime_pay'] == 0.0

    def test_get_overtime_statistics_no_department(self, overtime_calculation_service):
        """测试获取加班统计 - 无部门筛选"""
        result = overtime_calculation_service.get_overtime_statistics(
            year=date.today().year,
            month=date.today().month
        )
        
        assert result is not None
        assert result['year'] == date.today().year
        assert result['month'] == date.today().month
        assert 'total_users' in result
        assert 'total_overtime_hours' in result
        assert 'total_overtime_pay' in result
        assert 'user_statistics' in result

    def test_get_overtime_statistics_with_department(self, overtime_calculation_service, db_session):
        """测试获取加班统计 - 指定部门"""
        # 创建部门
        department = Department(
            department_name="测试部门",
            department_code="DEPT001"
        )
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)
        
        result = overtime_calculation_service.get_overtime_statistics(
            year=date.today().year,
            month=date.today().month,
            department_id=department.id
        )
        
        assert result is not None
        assert result['department_id'] == department.id

    def test_get_overtime_statistics_december(self, overtime_calculation_service):
        """测试获取加班统计 - 12月（跨年边界）"""
        result = overtime_calculation_service.get_overtime_statistics(
            year=2024,
            month=12
        )
        
        assert result is not None
        assert result['year'] == 2024
        assert result['month'] == 12
