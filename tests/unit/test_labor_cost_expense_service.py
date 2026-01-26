# -*- coding: utf-8 -*-
"""
LaborCostExpenseService 单元测试
测试工时费用化处理服务的各项功能
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.labor_cost_expense_service import LaborCostExpenseService


class TestLaborCostExpenseServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock(spec=Session)
        service = LaborCostExpenseService(mock_db)
        assert service.db == mock_db
        assert service.hourly_rate_service is not None


class TestIdentifyLostProjects:
    """测试识别未中标项目"""

    @patch.object(LaborCostExpenseService, '_has_detailed_design')
    @patch.object(LaborCostExpenseService, '_get_project_hours')
    @patch.object(LaborCostExpenseService, '_calculate_project_cost')
    def test_identify_no_projects(self, mock_cost, mock_hours, mock_design):
        """测试无未中标项目"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = LaborCostExpenseService(mock_db)
        result = service.identify_lost_projects()

        assert result == []

    @patch.object(LaborCostExpenseService, '_has_detailed_design')
    @patch.object(LaborCostExpenseService, '_get_project_hours')
    @patch.object(LaborCostExpenseService, '_calculate_project_cost')
    def test_identify_lost_projects(self, mock_cost, mock_hours, mock_design):
        """测试识别未中标项目"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.outcome = LeadOutcomeEnum.LOST.value
        mock_project.loss_reason = "PRICE"
        mock_project.salesperson_id = 10
        mock_project.source_lead_id = "LD001"
        mock_project.opportunity_id = 5

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        mock_design.return_value = True
        mock_hours.return_value = 100.0
        mock_cost.return_value = Decimal('10000')

        service = LaborCostExpenseService(mock_db)
        result = service.identify_lost_projects()

        assert len(result) == 1
        assert result[0]['project_id'] == 1
        assert result[0]['has_detailed_design'] is True
        assert result[0]['total_hours'] == 100.0
        assert result[0]['total_cost'] == 10000.0

    @patch.object(LaborCostExpenseService, '_has_detailed_design')
    @patch.object(LaborCostExpenseService, '_get_project_hours')
    @patch.object(LaborCostExpenseService, '_calculate_project_cost')
    def test_identify_with_date_range(self, mock_cost, mock_hours, mock_design):
        """测试带日期范围的识别"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.outcome = LeadOutcomeEnum.LOST.value
        mock_project.loss_reason = None
        mock_project.salesperson_id = None
        mock_project.source_lead_id = None
        mock_project.opportunity_id = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [mock_project]
        mock_db.query.return_value = query_mock

        mock_design.return_value = False
        mock_hours.return_value = 20.0
        mock_cost.return_value = Decimal('2000')

        service = LaborCostExpenseService(mock_db)
        result = service.identify_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        assert len(result) == 1

    @patch.object(LaborCostExpenseService, '_has_detailed_design')
    @patch.object(LaborCostExpenseService, '_get_project_hours')
    @patch.object(LaborCostExpenseService, '_calculate_project_cost')
    def test_identify_exclude_abandoned(self, mock_cost, mock_hours, mock_design):
        """测试排除放弃的项目"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = LaborCostExpenseService(mock_db)
        result = service.identify_lost_projects(include_abandoned=False)

        # 验证只查询LOST状态
        assert result == []


class TestExpenseLostProjects:
    """测试费用化处理"""

    @patch('app.services.labor_cost_expense_service.HourlyRateService.get_user_hourly_rate')
    def test_expense_no_projects(self, mock_hourly_rate):
        """测试无项目时的费用化"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = LaborCostExpenseService(mock_db)
        result = service.expense_lost_projects()

        assert result['total_projects'] == 0
        assert result['total_expenses'] == 0
        assert result['total_amount'] == 0.0

    @patch('app.services.labor_cost_expense_service.HourlyRateService.get_user_hourly_rate')
    @patch.object(LaborCostExpenseService, '_get_lead_id_from_project')
    @patch.object(LaborCostExpenseService, '_get_user_name')
    def test_expense_with_timesheets(self, mock_user_name, mock_lead_id, mock_hourly_rate):
        """测试有工时记录的费用化"""
        mock_db = MagicMock(spec=Session)
        mock_hourly_rate.return_value = Decimal('200')
        mock_lead_id.return_value = None
        mock_user_name.return_value = "测试销售"

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.outcome = LeadOutcomeEnum.LOST.value
        mock_project.opportunity_id = None
        mock_project.salesperson_id = 10
        mock_project.loss_reason = "PRICE"
        mock_project.updated_at = None

        mock_ts = Mock(spec=Timesheet)
        mock_ts.user_id = 1
        mock_ts.hours = 40
        mock_ts.work_date = date(2024, 6, 15)
        mock_ts.department_id = 5
        mock_ts.department_name = "技术部"

        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.department = "技术部"

        # 第一次查询返回项目
        query_project = MagicMock()
        query_project.filter.return_value = query_project
        query_project.all.return_value = [mock_project]

        # 第二次查询返回工时记录
        query_ts = MagicMock()
        query_ts.filter.return_value.all.return_value = [mock_ts]

        # 第三次查询返回用户
        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        mock_db.query.side_effect = [query_project, query_ts, query_user, query_user]

        service = LaborCostExpenseService(mock_db)
        result = service.expense_lost_projects()

        assert result['total_projects'] == 1
        assert result['total_expenses'] == 1
        assert result['total_amount'] == 8000.0  # 40 * 200


class TestGetLostProjectExpenses:
    """测试获取未中标项目费用"""

    @patch.object(LaborCostExpenseService, '_get_project_hours')
    @patch.object(LaborCostExpenseService, '_calculate_project_cost')
    @patch.object(LaborCostExpenseService, '_get_user_name')
    def test_get_expenses_empty(self, mock_user_name, mock_cost, mock_hours):
        """测试无费用"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = LaborCostExpenseService(mock_db)
        result = service.get_lost_project_expenses()

        assert result['total_expenses'] == 0
        assert result['total_amount'] == 0

    @patch.object(LaborCostExpenseService, '_get_project_hours')
    @patch.object(LaborCostExpenseService, '_calculate_project_cost')
    @patch.object(LaborCostExpenseService, '_get_user_name')
    def test_get_expenses_with_data(self, mock_user_name, mock_cost, mock_hours):
        """测试获取费用数据"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 50.0
        mock_cost.return_value = Decimal('5000')
        mock_user_name.return_value = "测试销售"

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.outcome = LeadOutcomeEnum.LOST.value
        mock_project.salesperson_id = 10
        mock_project.loss_reason = "PRICE"
        mock_project.updated_at = None
        # 使用datetime而不是date，以便.date()调用正常工作
        from datetime import datetime
        mock_project.created_at = datetime(2024, 6, 1, 10, 0, 0)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        service = LaborCostExpenseService(mock_db)
        result = service.get_lost_project_expenses()

        assert result['total_expenses'] == 1
        assert result['total_amount'] == 5000.0
        assert result['expenses'][0]['expense_category'] == 'LOST_BID'


class TestGetExpenseStatistics:
    """测试获取费用统计"""

    @patch.object(LaborCostExpenseService, 'get_lost_project_expenses')
    def test_statistics_by_person(self, mock_get_expenses):
        """测试按人员统计"""
        mock_db = MagicMock(spec=Session)
        mock_get_expenses.return_value = {
            'total_amount': 10000,
            'total_hours': 100,
            'total_expenses': 2,
            'expenses': [
                {'salesperson_id': 1, 'amount': 5000, 'labor_hours': 50},
                {'salesperson_id': 1, 'amount': 5000, 'labor_hours': 50}
            ]
        }

        mock_user = Mock(spec=User)
        mock_user.name = "张三"
        mock_user.department_name = "销售部"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = LaborCostExpenseService(mock_db)
        result = service.get_expense_statistics(group_by='person')

        assert result['group_by'] == 'person'
        assert result['summary']['total_amount'] == 10000

    @patch.object(LaborCostExpenseService, 'get_lost_project_expenses')
    def test_statistics_by_time(self, mock_get_expenses):
        """测试按时间统计"""
        mock_db = MagicMock(spec=Session)
        mock_get_expenses.return_value = {
            'total_amount': 15000,
            'total_hours': 150,
            'total_expenses': 3,
            'expenses': [
                {'expense_date': date(2024, 1, 15), 'amount': 5000, 'labor_hours': 50, 'project_id': 1},
                {'expense_date': date(2024, 1, 20), 'amount': 5000, 'labor_hours': 50, 'project_id': 2},
                {'expense_date': date(2024, 2, 10), 'amount': 5000, 'labor_hours': 50, 'project_id': 3}
            ]
        }

        service = LaborCostExpenseService(mock_db)
        result = service.get_expense_statistics(group_by='time')

        assert result['group_by'] == 'time'
        assert len(result['statistics']) == 2  # 两个月


class TestHasDetailedDesign:
    """测试判断是否投入详细设计"""

    @patch.object(LaborCostExpenseService, '_get_project_hours')
    def test_stage_s4_returns_true(self, mock_hours):
        """测试S4阶段返回True"""
        mock_db = MagicMock(spec=Session)
        service = LaborCostExpenseService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = 'S4'
        mock_project.id = 1

        result = service._has_detailed_design(mock_project)
        assert result is True

    @patch.object(LaborCostExpenseService, '_get_project_hours')
    def test_stage_s2_returns_false(self, mock_hours):
        """测试S2阶段返回False"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 20.0  # 低于80小时

        service = LaborCostExpenseService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = 'S2'
        mock_project.id = 1

        result = service._has_detailed_design(mock_project)
        assert result is False

    @patch.object(LaborCostExpenseService, '_get_project_hours')
    def test_high_hours_returns_true(self, mock_hours):
        """测试工时超过80小时返回True"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 100.0

        service = LaborCostExpenseService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = None
        mock_project.id = 1

        result = service._has_detailed_design(mock_project)
        assert result is True


class TestGetProjectHours:
    """测试获取项目工时"""

    def test_get_hours_returns_sum(self):
        """测试返回工时总和"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 80.5

        service = LaborCostExpenseService(mock_db)
        result = service._get_project_hours(project_id=1)

        assert result == 80.5

    def test_get_hours_returns_zero_when_none(self):
        """测试无工时返回0"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        service = LaborCostExpenseService(mock_db)
        result = service._get_project_hours(project_id=1)

        assert result == 0.0


class TestCalculateProjectCost:
    """测试计算项目成本"""

    @patch('app.services.labor_cost_expense_service.HourlyRateService.get_user_hourly_rate')
    def test_calculate_cost_no_timesheets(self, mock_hourly_rate):
        """测试无工时记录的成本"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = LaborCostExpenseService(mock_db)
        result = service._calculate_project_cost(project_id=1)

        assert result == Decimal('0')

    @patch('app.services.labor_cost_expense_service.HourlyRateService.get_user_hourly_rate')
    def test_calculate_cost_with_user(self, mock_hourly_rate):
        """测试有用户的成本计算"""
        mock_db = MagicMock(spec=Session)
        mock_hourly_rate.return_value = Decimal('200')

        mock_ts = Mock(spec=Timesheet)
        mock_ts.hours = 40
        mock_ts.user_id = 1
        mock_ts.work_date = date(2024, 1, 15)

        mock_user = Mock(spec=User)
        mock_user.id = 1

        query_ts = MagicMock()
        query_ts.filter.return_value.all.return_value = [mock_ts]

        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        mock_db.query.side_effect = [query_ts, query_user]

        service = LaborCostExpenseService(mock_db)
        result = service._calculate_project_cost(project_id=1)

        assert result == Decimal('8000')

    def test_calculate_cost_without_user(self):
        """测试无用户时使用默认单价"""
        mock_db = MagicMock(spec=Session)

        mock_ts = Mock(spec=Timesheet)
        mock_ts.hours = 40
        mock_ts.user_id = 999

        query_ts = MagicMock()
        query_ts.filter.return_value.all.return_value = [mock_ts]

        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [query_ts, query_user]

        service = LaborCostExpenseService(mock_db)
        result = service._calculate_project_cost(project_id=1)

        # 40 * 300 = 12000
        assert result == Decimal('12000')


class TestGetUserName:
    """测试获取用户名称"""

    def test_get_name_none_id(self):
        """测试用户ID为None"""
        mock_db = MagicMock(spec=Session)
        service = LaborCostExpenseService(mock_db)

        result = service._get_user_name(None)
        assert result is None

    def test_get_name_with_real_name(self):
        """测试有真实姓名"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(1)

        assert result == "张三"

    def test_get_name_without_real_name(self):
        """测试无真实姓名用用户名"""
        mock_db = MagicMock(spec=Session)

        mock_user = Mock(spec=User)
        mock_user.real_name = None
        mock_user.username = "zhangsan"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(1)

        assert result == "zhangsan"

    def test_get_name_user_not_found(self):
        """测试用户不存在"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(999)

        assert result is None
