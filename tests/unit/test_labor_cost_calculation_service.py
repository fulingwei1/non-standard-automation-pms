# -*- coding: utf-8 -*-
"""
Tests for labor_cost_calculation_service service
Covers: app/services/labor_cost_calculation_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 71 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.labor_cost_calculation_service import (
    query_approved_timesheets,
    delete_existing_costs,
    group_timesheets_by_user,
    find_existing_cost,
    update_existing_cost,
    create_new_cost,
    check_budget_alert,
    process_user_costs
)
from app.models.project import Project, ProjectCost
from app.models.timesheet import Timesheet
from app.models.user import User


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        actual_cost=Decimal("0.00")
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


@pytest.fixture
def test_timesheets(db_session: Session, test_project, test_user):
    """创建测试工时记录"""
    timesheets = []
    for i in range(3):
        timesheet = Timesheet(
        user_id=test_user.id,
        user_name=test_user.real_name,
        project_id=test_project.id,
        work_date=date.today() - timedelta(days=i),
        hours=8.0,
        status="APPROVED"
        )
        db_session.add(timesheet)
        timesheets.append(timesheet)
    db_session.commit()
    return timesheets


class TestLaborCostCalculationService:
    """Test suite for labor_cost_calculation_service."""

    def test_query_approved_timesheets_no_date_range(self, db_session, test_project, test_timesheets):
        """测试查询已审批工时 - 无日期范围"""
        result = query_approved_timesheets(
        db_session,
        project_id=test_project.id,
        start_date=None,
        end_date=None
        )
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(ts.status == "APPROVED" for ts in result)

    def test_query_approved_timesheets_with_date_range(self, db_session, test_project, test_timesheets):
        """测试查询已审批工时 - 带日期范围"""
        start_date = date.today() - timedelta(days=2)
        end_date = date.today()
        
        result = query_approved_timesheets(
        db_session,
        project_id=test_project.id,
        start_date=start_date,
        end_date=end_date
        )
        
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_query_approved_timesheets_no_results(self, db_session, test_project):
        """测试查询已审批工时 - 无结果"""
        result = query_approved_timesheets(
        db_session,
        project_id=test_project.id,
        start_date=None,
        end_date=None
        )
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_delete_existing_costs_success(self, db_session, test_project):
        """测试删除现有成本 - 成功场景"""
        # 创建测试成本记录
        cost = ProjectCost(
        project_id=test_project.id,
        source_module="TIMESHEET",
        source_type="LABOR_COST",
        amount=Decimal("1000.00")
        )
        db_session.add(cost)
        test_project.actual_cost = Decimal("1000.00")
        db_session.add(test_project)
        db_session.commit()
        
        delete_existing_costs(db_session, test_project, test_project.id)
        db_session.commit()
        
        # 验证成本已删除
        remaining_costs = db_session.query(ProjectCost).filter(
        ProjectCost.project_id == test_project.id,
        ProjectCost.source_module == "TIMESHEET"
        ).all()
        
        assert len(remaining_costs) == 0
        assert test_project.actual_cost == 0

    def test_group_timesheets_by_user_success(self, test_timesheets):
        """测试按用户分组工时 - 成功场景"""
        result = group_timesheets_by_user(test_timesheets)
        
        assert isinstance(result, dict)
        assert len(result) == 1  # 只有一个用户
        assert test_timesheets[0].user_id in result
        
        user_data = result[test_timesheets[0].user_id]
        assert user_data['total_hours'] == Decimal("24.0")  # 3条 * 8小时
        assert len(user_data['timesheet_ids']) == 3

    def test_group_timesheets_by_user_empty(self):
        """测试按用户分组工时 - 空列表"""
        result = group_timesheets_by_user([])
        
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_find_existing_cost_found(self, db_session, test_project, test_user):
        """测试查找现有成本 - 找到"""
        cost = ProjectCost(
        project_id=test_project.id,
        source_module="TIMESHEET",
        source_type="LABOR_COST",
        source_id=test_user.id,
        amount=Decimal("500.00")
        )
        db_session.add(cost)
        db_session.commit()
        
        result = find_existing_cost(db_session, test_project.id, test_user.id)
        
        assert result is not None
        assert result.amount == Decimal("500.00")

    def test_find_existing_cost_not_found(self, db_session, test_project, test_user):
        """测试查找现有成本 - 未找到"""
        result = find_existing_cost(db_session, test_project.id, test_user.id)
        
        assert result is None

    def test_update_existing_cost_success(self, db_session, test_project, test_user):
        """测试更新现有成本 - 成功场景"""
        existing_cost = ProjectCost(
        project_id=test_project.id,
        source_module="TIMESHEET",
        source_type="LABOR_COST",
        source_id=test_user.id,
        amount=Decimal("500.00")
        )
        db_session.add(existing_cost)
        test_project.actual_cost = Decimal("500.00")
        db_session.add(test_project)
        db_session.commit()
        
        user_data = {
        'user_name': '测试用户',
        'total_hours': Decimal("10.0")
        }
        new_amount = Decimal("1000.00")
        
        update_existing_cost(
        db_session,
        test_project,
        existing_cost,
        new_amount,
        user_data,
        date.today()
        )
        db_session.commit()
        
        assert existing_cost.amount == new_amount
        assert test_project.actual_cost == Decimal("1000.00")

    def test_create_new_cost_success(self, db_session, test_project, test_user):
        """测试创建新成本 - 成功场景"""
        user_data = {
        'user_name': '测试用户',
        'total_hours': Decimal("8.0")
        }
        cost_amount = Decimal("800.00")
        
        result = create_new_cost(
        db_session,
        test_project,
        test_project.id,
        test_user.id,
        cost_amount,
        user_data,
        date.today()
        )
        db_session.commit()
        
        assert result is not None
        assert result.amount == cost_amount
        assert result.source_id == test_user.id
        assert test_project.actual_cost == Decimal("800.00")

    def test_check_budget_alert_success(self, db_session, test_project, test_user):
        """测试检查预算预警 - 成功场景"""
        with patch('app.services.labor_cost_calculation_service.CostAlertService') as mock_service:
            check_budget_alert(db_session, test_project.id, test_user.id)
            
            # 验证调用了预警服务
        mock_service.check_budget_execution.assert_called_once()

    def test_check_budget_alert_exception(self, db_session, test_project, test_user):
        """测试检查预算预警 - 异常处理"""
        with patch('app.services.labor_cost_calculation_service.CostAlertService') as mock_service:
            mock_service.check_budget_execution.side_effect = Exception("Test error")
            
            # 应该不抛出异常
        check_budget_alert(db_session, test_project.id, test_user.id)

    def test_process_user_costs_new_cost(self, db_session, test_project, test_user):
        """测试处理用户成本 - 创建新成本"""
        with patch('app.services.labor_cost_calculation_service.LaborCostService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            user_costs = {
            test_user.id: {
            'user_id': test_user.id,
            'user_name': '测试用户',
            'total_hours': Decimal("8.0"),
            'timesheet_ids': [1, 2],
            'work_date': date.today()
            }
            }
            
            created_costs, total_cost = process_user_costs(
            db_session,
            test_project,
            test_project.id,
            user_costs,
            date.today(),
            recalculate=False
            )
            
            assert len(created_costs) == 1
            assert total_cost == Decimal("800.00")  # 8小时 * 100元/小时

    def test_process_user_costs_update_existing(self, db_session, test_project, test_user):
        """测试处理用户成本 - 更新现有成本"""
        # 创建现有成本
        existing_cost = ProjectCost(
        project_id=test_project.id,
        source_module="TIMESHEET",
        source_type="LABOR_COST",
        source_id=test_user.id,
        amount=Decimal("500.00")
        )
        db_session.add(existing_cost)
        db_session.commit()
        
        with patch('app.services.labor_cost_calculation_service.LaborCostService') as mock_service:
            mock_service.get_user_hourly_rate.return_value = Decimal("100.00")
            
            user_costs = {
            test_user.id: {
            'user_id': test_user.id,
            'user_name': '测试用户',
            'total_hours': Decimal("8.0"),
            'timesheet_ids': [1, 2],
            'work_date': date.today()
            }
            }
            
            created_costs, total_cost = process_user_costs(
            db_session,
            test_project,
            test_project.id,
            user_costs,
            date.today(),
            recalculate=False
            )
            
            assert len(created_costs) == 1
            assert created_costs[0].id == existing_cost.id
