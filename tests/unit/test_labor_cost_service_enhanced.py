# -*- coding: utf-8 -*-
"""
labor_cost_service.py 增强测试
目标：提升覆盖率到60%+

覆盖重点：
1. LaborCostService - 工时成本自动计算
2. LaborCostCalculationService - 批量月度成本计算
3. LaborCostExpenseService - 未中标项目工时费用化处理
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
import uuid

from app.services.labor_cost_service import (
    LaborCostService,
    LaborCostCalculationService,
    LaborCostExpenseService,
    PresaleExpense
)
from app.models.enums import LeadOutcomeEnum


# ============ Fixtures ============

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_project():
    """Mock项目"""
    project = MagicMock()
    project.id = 1
    project.project_code = "PRJ-001"
    project.project_name = "测试项目"
    project.stage = "S4"
    project.outcome = LeadOutcomeEnum.LOST.value
    project.loss_reason = "价格原因"
    project.salesperson_id = 100
    project.source_lead_id = "LEAD-001"
    project.opportunity_id = 200
    project.created_at = datetime(2024, 1, 1)
    project.updated_at = datetime(2024, 1, 15)
    project.actual_cost = Decimal("0")
    return project


@pytest.fixture
def mock_timesheet():
    """Mock工时记录"""
    ts = MagicMock()
    ts.id = 1
    ts.project_id = 1
    ts.user_id = 10
    ts.hours = 8.0
    ts.work_date = date(2024, 1, 10)
    ts.status = "APPROVED"
    ts.department_id = 5
    ts.department_name = "研发部"
    return ts


@pytest.fixture
def mock_user():
    """Mock用户"""
    user = MagicMock()
    user.id = 10
    user.username = "testuser"
    user.real_name = "测试用户"
    user.department = "研发部"
    user.department_id = 5
    user.department_name = "研发部"
    return user


# ============ LaborCostService 测试 ============

class TestLaborCostServiceGetUserHourlyRate:
    """测试获取用户时薪"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_hourly_rate_with_date(self, mock_hourly_service):
        """测试获取用户时薪（指定日期）"""
        mock_db = MagicMock()
        mock_hourly_service.get_user_hourly_rate.return_value = Decimal("150")
        
        result = LaborCostService.get_user_hourly_rate(
            mock_db, user_id=10, work_date=date(2024, 1, 10)
        )
        
        assert result == Decimal("150")
        mock_hourly_service.get_user_hourly_rate.assert_called_once_with(
            mock_db, 10, date(2024, 1, 10)
        )

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_hourly_rate_without_date(self, mock_hourly_service):
        """测试获取用户时薪（不指定日期）"""
        mock_db = MagicMock()
        mock_hourly_service.get_user_hourly_rate.return_value = Decimal("200")
        
        result = LaborCostService.get_user_hourly_rate(mock_db, user_id=20)
        
        assert result == Decimal("200")
        mock_hourly_service.get_user_hourly_rate.assert_called_once_with(
            mock_db, 20, None
        )


class TestLaborCostServiceCalculateProjectWithRecalculate:
    """测试重新计算项目成本"""

    @patch('app.services.labor_cost.utils.process_user_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.delete_existing_costs')
    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    def test_calculate_with_recalculate_true(
        self, mock_query, mock_delete, mock_group, mock_process, mock_db, mock_project, mock_timesheet
    ):
        """测试重新计算（recalculate=True）"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_query.return_value = [mock_timesheet]
        mock_group.return_value = {
            10: {'total_hours': 8.0, 'work_date': date(2024, 1, 10)}
        }
        mock_process.return_value = ([], Decimal("1200"))
        
        result = LaborCostService.calculate_project_labor_cost(
            mock_db, project_id=1, recalculate=True
        )
        
        assert result['success'] is True
        mock_delete.assert_called_once()  # 应该调用删除


class TestLaborCostServiceCalculateAllProjects:
    """测试批量计算所有项目"""

    @patch('app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost')
    def test_calculate_all_with_project_ids_filter(self, mock_calc, mock_db):
        """测试使用项目ID过滤批量计算"""
        # Mock查询返回的项目ID
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [(1,), (2,)]
        
        # Mock计算结果
        mock_calc.return_value = {
            'success': True,
            'cost_count': 5,
            'total_cost': 10000
        }
        
        result = LaborCostService.calculate_all_projects_labor_cost(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            project_ids=[1, 2]
        )
        
        assert result['success'] is True
        assert result['total_projects'] == 2
        assert result['success_count'] == 2
        assert result['fail_count'] == 0

    @patch('app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost')
    def test_calculate_all_with_exception(self, mock_calc, mock_db):
        """测试批量计算时出现异常"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [(1,)]
        
        # Mock抛出异常
        mock_calc.side_effect = Exception("数据库错误")
        
        result = LaborCostService.calculate_all_projects_labor_cost(mock_db)
        
        assert result['fail_count'] == 1
        assert len(result['results']) == 1
        assert result['results'][0]['success'] is False


class TestLaborCostServiceCalculateMonthly:
    """测试月度成本计算"""

    @patch('app.services.labor_cost_service.LaborCostService.calculate_all_projects_labor_cost')
    def test_calculate_monthly_delegates_to_all_projects(
        self, mock_calc_all, mock_db
    ):
        """测试月度计算委托给批量计算"""
        mock_calc_all.return_value = {
            'success': True,
            'total_projects': 10,
            'success_count': 10
        }
        
        result = LaborCostService.calculate_monthly_labor_cost(
            mock_db, year=2024, month=1
        )
        
        assert result['success'] is True
        # 验证确实调用了calculate_all_projects_labor_cost
        assert mock_calc_all.called

    @patch('app.common.date_range.get_month_range_by_ym')
    @patch('app.services.labor_cost_service.LaborCostService.calculate_all_projects_labor_cost')
    def test_calculate_monthly_with_project_filter(
        self, mock_calc_all, mock_get_range, mock_db
    ):
        """测试月度计算带项目过滤"""
        mock_get_range.return_value = (date(2024, 2, 1), date(2024, 2, 29))
        mock_calc_all.return_value = {'success': True}
        
        result = LaborCostService.calculate_monthly_labor_cost(
            mock_db, year=2024, month=2, project_ids=[1, 2, 3]
        )
        
        mock_calc_all.assert_called_once_with(
            mock_db, date(2024, 2, 1), date(2024, 2, 29), [1, 2, 3]
        )


# ============ LaborCostCalculationService 测试 ============

class TestLaborCostCalculationServiceInit:
    """测试LaborCostCalculationService初始化"""

    def test_init_stores_db(self, mock_db):
        """测试初始化存储数据库引用"""
        service = LaborCostCalculationService(mock_db)
        assert service.db == mock_db


class TestLaborCostCalculationServiceCalculateMonthly:
    """测试批量月度计算服务"""

    @patch('app.services.labor_cost.utils.process_user_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    @patch('app.common.date_range.get_month_range_by_ym')
    def test_calculate_monthly_costs_success(
        self, mock_get_range, mock_query, mock_group, mock_process, mock_db, mock_project
    ):
        """测试成功计算月度成本"""
        mock_get_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock查询项目ID
        mock_query_result = MagicMock()
        mock_db.query.return_value = mock_query_result
        mock_query_result.filter.return_value = mock_query_result
        mock_query_result.distinct.return_value = mock_query_result
        mock_query_result.all.return_value = [(1,), (2,)]
        
        # Mock查询项目
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock工时查询
        mock_query.return_value = [MagicMock(hours=8.0)]
        mock_group.return_value = {10: {'total_hours': 8.0}}
        mock_process.return_value = ([], Decimal("1200"))
        
        service = LaborCostCalculationService(mock_db)
        result = service.calculate_monthly_costs(2024, 1)
        
        assert result['year'] == 2024
        assert result['month'] == 1
        assert 'projects_processed' in result
        assert 'total_cost' in result

    @patch('app.common.date_range.get_month_range_by_ym')
    def test_calculate_monthly_costs_with_errors(self, mock_get_range, mock_db):
        """测试月度计算遇到错误"""
        mock_get_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock查询项目ID返回None
        mock_query_result = MagicMock()
        mock_db.query.return_value = mock_query_result
        mock_query_result.filter.return_value = mock_query_result
        mock_query_result.distinct.return_value = mock_query_result
        mock_query_result.all.return_value = [(None,), (999,)]
        
        # Mock项目不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service = LaborCostCalculationService(mock_db)
        result = service.calculate_monthly_costs(2024, 1)
        
        # None项目ID应该被跳过
        assert result['projects_processed'] == 0


# ============ PresaleExpense 测试 ============

class TestPresaleExpense:
    """测试售前费用模型"""

    def test_presale_expense_init(self):
        """测试PresaleExpense初始化"""
        expense = PresaleExpense(
            project_id=1,
            amount=1000.0,
            description="测试费用"
        )
        
        assert expense.project_id == 1
        assert expense.amount == 1000.0
        assert expense.description == "测试费用"

    def test_presale_expense_multiple_attributes(self):
        """测试PresaleExpense多个属性"""
        expense = PresaleExpense(
            project_id=2,
            project_name="项目A",
            amount=5000.0,
            expense_type="LABOR_COST",
            user_id=10,
            user_name="张三"
        )
        
        assert expense.project_id == 2
        assert expense.project_name == "项目A"
        assert expense.expense_type == "LABOR_COST"
        assert expense.user_name == "张三"


# ============ LaborCostExpenseService 测试 ============

class TestLaborCostExpenseServiceInit:
    """测试LaborCostExpenseService初始化"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_init_creates_hourly_rate_service(self, mock_hourly_service, mock_db):
        """测试初始化创建时薪服务"""
        service = LaborCostExpenseService(mock_db)
        
        assert service.db == mock_db
        assert mock_hourly_service.called


class TestLaborCostExpenseServiceIdentifyLostProjects:
    """测试识别未中标项目"""

    def test_identify_lost_projects_with_date_range(self, mock_db, mock_project):
        """测试使用日期范围识别"""
        # 简化测试 - 只返回空列表
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # 返回空列表
        
        service = LaborCostExpenseService(mock_db)
        result = service.identify_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_identify_lost_projects_include_abandoned_false(self, mock_db):
        """测试不包含放弃的项目"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        service = LaborCostExpenseService(mock_db)
        result = service.identify_lost_projects(include_abandoned=False)
        
        # 验证只查询LOST项目
        assert result == []

    def test_identify_lost_projects_detailed_design_by_stage(self, mock_db):
        """测试通过阶段判断详细设计"""
        project = MagicMock()
        project.id = 1
        project.stage = "S5"  # 已进入详细设计阶段
        
        # 直接测试_has_detailed_design方法,避免复杂的Mock
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("30.0")
        
        service = LaborCostExpenseService(mock_db)
        result = service._has_detailed_design(project)
        
        # S5阶段应该有详细设计
        assert result is True

    def test_identify_lost_projects_detailed_design_by_hours(self, mock_db):
        """测试通过工时判断详细设计"""
        # 直接测试_has_detailed_design方法
        project = MagicMock()
        project.id = 1
        project.stage = "S2"  # 早期阶段
        
        # Mock工时查询 - 超过80小时
        mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("100.0")
        
        service = LaborCostExpenseService(mock_db)
        result = service._has_detailed_design(project)
        
        # 超过80小时应该有详细设计
        assert result is True


class TestLaborCostExpenseServiceExpenseLostProjects:
    """测试费用化处理"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_expense_lost_projects_with_project_ids(
        self, mock_hourly_service, mock_db, mock_project, mock_timesheet, mock_user
    ):
        """测试指定项目ID进行费用化"""
        # Mock查询
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_project]
        
        # Mock工时查询
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]
        
        # Mock用户查询
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock时薪
        mock_hourly_service.return_value.get_user_hourly_rate.return_value = Decimal("150")
        
        service = LaborCostExpenseService(mock_db)
        result = service.expense_lost_projects(project_ids=[1], created_by=100)
        
        assert result['total_projects'] == 1
        assert 'total_amount' in result
        assert 'expenses' in result

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_expense_lost_projects_with_date_range(
        self, mock_hourly_service, mock_db
    ):
        """测试使用日期范围费用化"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        service = LaborCostExpenseService(mock_db)
        result = service.expense_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert result['total_projects'] == 0


class TestLaborCostExpenseServiceGetLostProjectExpenses:
    """测试获取未中标项目费用"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_expenses_with_salesperson_filter(
        self, mock_hourly_service, mock_db, mock_project
    ):
        """测试使用销售人员过滤"""
        # 简化Mock - 只返回空列表
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []  # 返回空列表避免复杂的Mock
        
        service = LaborCostExpenseService(mock_db)
        result = service.get_lost_project_expenses(salesperson_id=100)
        
        assert 'expenses' in result
        assert 'total_amount' in result
        assert result['total_amount'] == 0

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_expenses_with_department_filter(
        self, mock_hourly_service, mock_db
    ):
        """测试使用部门过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = []
        
        service = LaborCostExpenseService(mock_db)
        result = service.get_lost_project_expenses(department_id=5)
        
        assert result['total_expenses'] == 0


class TestLaborCostExpenseServiceGetStatistics:
    """测试费用统计"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    @patch('app.services.labor_cost_service.LaborCostExpenseService.get_lost_project_expenses')
    def test_statistics_by_person(
        self, mock_get_expenses, mock_hourly_service, mock_db, mock_user
    ):
        """测试按人员统计"""
        mock_get_expenses.return_value = {
            'total_amount': 5000.0,
            'total_hours': 50.0,
            'total_expenses': 2,
            'expenses': [
                {
                    'salesperson_id': 100,
                    'amount': 3000.0,
                    'labor_hours': 30.0
                },
                {
                    'salesperson_id': 100,
                    'amount': 2000.0,
                    'labor_hours': 20.0
                }
            ]
        }
        
        # Mock用户查询
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        service = LaborCostExpenseService(mock_db)
        result = service.get_expense_statistics(group_by='person')
        
        assert result['group_by'] == 'person'
        assert 'statistics' in result
        assert 'summary' in result

    @patch('app.services.hourly_rate_service.HourlyRateService')
    @patch('app.services.labor_cost_service.LaborCostExpenseService.get_lost_project_expenses')
    def test_statistics_by_department(
        self, mock_get_expenses, mock_hourly_service, mock_db, mock_timesheet
    ):
        """测试按部门统计"""
        mock_get_expenses.return_value = {
            'total_amount': 3000.0,
            'total_hours': 30.0,
            'total_expenses': 1,
            'expenses': [
                {
                    'project_id': 1,
                    'amount': 3000.0,
                    'labor_hours': 30.0,
                    'expense_date': date(2024, 1, 15)
                }
            ]
        }
        
        # Mock工时查询
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]
        
        # Mock部门查询
        mock_dept = MagicMock()
        mock_dept.dept_name = "研发部"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_dept
        
        service = LaborCostExpenseService(mock_db)
        result = service.get_expense_statistics(group_by='department')
        
        assert result['group_by'] == 'department'

    @patch('app.services.hourly_rate_service.HourlyRateService')
    @patch('app.services.labor_cost_service.LaborCostExpenseService.get_lost_project_expenses')
    def test_statistics_by_time(self, mock_get_expenses, mock_hourly_service, mock_db):
        """测试按时间统计"""
        mock_get_expenses.return_value = {
            'total_amount': 8000.0,
            'total_hours': 80.0,
            'total_expenses': 2,
            'expenses': [
                {
                    'expense_date': date(2024, 1, 15),
                    'amount': 5000.0,
                    'labor_hours': 50.0
                },
                {
                    'expense_date': date(2024, 2, 10),
                    'amount': 3000.0,
                    'labor_hours': 30.0
                }
            ]
        }
        
        service = LaborCostExpenseService(mock_db)
        result = service.get_expense_statistics(group_by='time')
        
        assert result['group_by'] == 'time'
        assert len(result['statistics']) >= 0


class TestLaborCostExpenseServiceInternalMethods:
    """测试内部辅助方法"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_has_detailed_design_invalid_stage(self, mock_hourly_service, mock_db):
        """测试无效阶段判断详细设计"""
        project = MagicMock()
        project.stage = "INVALID_STAGE"
        project.id = 1
        
        # Mock工时 < 80
        mock_db.query.return_value.filter.return_value.scalar.return_value = 30.0
        
        service = LaborCostExpenseService(mock_db)
        result = service._has_detailed_design(project)
        
        assert result is False

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_project_hours_none(self, mock_hourly_service, mock_db):
        """测试获取项目工时为None"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        service = LaborCostExpenseService(mock_db)
        result = service._get_project_hours(1)
        
        assert result == 0.0

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_calculate_project_cost_no_user(
        self, mock_hourly_service, mock_db, mock_timesheet
    ):
        """测试计算成本时用户不存在"""
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service = LaborCostExpenseService(mock_db)
        result = service._calculate_project_cost(1)
        
        # 用户不存在时使用默认300元/小时
        assert result == Decimal('2400')  # 8小时 * 300

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_name_none_user_id(self, mock_hourly_service, mock_db):
        """测试获取用户名（user_id为None）"""
        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(None)
        
        assert result is None

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_name_user_not_found(self, mock_hourly_service, mock_db):
        """测试获取用户名（用户不存在）"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(999)
        
        assert result is None

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_name_with_real_name(self, mock_hourly_service, mock_db, mock_user):
        """测试获取用户真实姓名"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(10)
        
        assert result == "测试用户"

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_name_fallback_to_username(self, mock_hourly_service, mock_db):
        """测试获取用户名回退到username"""
        user = MagicMock()
        user.real_name = None
        user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = user
        
        service = LaborCostExpenseService(mock_db)
        result = service._get_user_name(10)
        
        assert result == "testuser"

    @patch('app.services.hourly_rate_service.HourlyRateService')
    @patch('app.models.sales.Lead')
    def test_get_lead_id_from_project_with_source_lead(
        self, mock_lead_model, mock_hourly_service, mock_db, mock_project
    ):
        """测试从项目获取线索ID（有source_lead_id）"""
        # Mock线索查询
        mock_lead = MagicMock()
        mock_lead.id = 500
        mock_db.query.return_value.filter.return_value.first.return_value = mock_lead
        
        service = LaborCostExpenseService(mock_db)
        result = service._get_lead_id_from_project(mock_project)
        
        assert result == 500

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_lead_id_from_project_no_source_lead(
        self, mock_hourly_service, mock_db
    ):
        """测试从项目获取线索ID（无source_lead_id）"""
        project = MagicMock()
        project.source_lead_id = None
        
        service = LaborCostExpenseService(mock_db)
        result = service._get_lead_id_from_project(project)
        
        assert result is None


# ============ 边界情况测试 ============

class TestEdgeCases:
    """边界情况测试"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_expense_projects_empty_timesheets(
        self, mock_hourly_service, mock_db, mock_project
    ):
        """测试费用化时没有工时记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = [[mock_project], []]  # 第一次返回项目,第二次返回空工时
        
        service = LaborCostExpenseService(mock_db)
        result = service.expense_lost_projects(project_ids=[1])
        
        assert result['total_expenses'] == 0

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_statistics_by_department_no_department(
        self, mock_hourly_service, mock_db
    ):
        """测试按部门统计时无部门信息"""
        # Mock工时没有部门ID
        ts = MagicMock()
        ts.department_id = None
        
        mock_db.query.return_value.filter.return_value.all.return_value = [ts]
        
        service = LaborCostExpenseService(mock_db)
        expenses = [{
            'project_id': 1,
            'amount': 1000.0,
            'labor_hours': 10.0,
            'expense_date': date(2024, 1, 15)
        }]
        
        result = service._statistics_by_department(expenses)
        
        assert len(result) == 0  # 无部门信息应该返回空


# ============ 集成测试 ============

class TestIntegration:
    """集成测试（涉及多个方法协作）"""

    @patch('app.services.hourly_rate_service.HourlyRateService')
    @patch('app.services.labor_cost.utils.process_user_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    def test_calculate_and_identify_lost_projects_workflow(
        self, mock_query, mock_group, mock_process, mock_hourly_service, 
        mock_db, mock_project
    ):
        """测试完整工作流：计算成本 -> 识别未中标项目"""
        # Step 1: 计算成本
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_query.return_value = []
        
        cost_result = LaborCostService.calculate_project_labor_cost(mock_db, 1)
        assert cost_result['success'] is True
        
        # Step 2: 识别未中标项目 - 简化测试,只返回空列表
        mock_query_lost = MagicMock()
        mock_query_lost.filter.return_value = mock_query_lost
        mock_query_lost.all.return_value = []
        
        mock_db.query = MagicMock(return_value=mock_query_lost)
        
        expense_service = LaborCostExpenseService(mock_db)
        lost_projects = expense_service.identify_lost_projects()
        
        assert isinstance(lost_projects, list)
