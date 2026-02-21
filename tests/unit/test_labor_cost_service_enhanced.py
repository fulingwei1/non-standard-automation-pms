# -*- coding: utf-8 -*-
"""
工时成本服务增强测试

覆盖所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.labor_cost_service import (
    LaborCostCalculationService,
    LaborCostExpenseService,
    LaborCostService,
)


class TestLaborCostService(unittest.TestCase):
    """LaborCostService 测试类"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = LaborCostService(self.mock_db)

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_hourly_rate_success(self, mock_hourly_rate_service):
        """测试获取用户时薪 - 成功"""
        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal("150")
        
        result = LaborCostService.get_user_hourly_rate(
            self.mock_db, 
            user_id=1, 
            work_date=date(2024, 1, 15)
        )
        
        self.assertEqual(result, Decimal("150"))
        mock_hourly_rate_service.get_user_hourly_rate.assert_called_once_with(
            self.mock_db, 1, date(2024, 1, 15)
        )

    @patch('app.services.hourly_rate_service.HourlyRateService')
    def test_get_user_hourly_rate_no_date(self, mock_hourly_rate_service):
        """测试获取用户时薪 - 无日期参数"""
        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal("100")
        
        result = LaborCostService.get_user_hourly_rate(self.mock_db, user_id=1)
        
        self.assertEqual(result, Decimal("100"))
        mock_hourly_rate_service.get_user_hourly_rate.assert_called_once_with(
            self.mock_db, 1, None
        )

    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    @patch('app.services.labor_cost.utils.delete_existing_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.process_user_costs')
    def test_calculate_project_labor_cost_project_not_found(
        self, mock_process, mock_group, mock_delete, mock_query
    ):
        """测试计算项目成本 - 项目不存在"""
        self.mock_db.query().filter().first.return_value = None
        
        result = LaborCostService.calculate_project_labor_cost(
            self.mock_db, 
            project_id=999
        )
        
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "项目不存在")

    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    @patch('app.services.labor_cost.utils.delete_existing_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.process_user_costs')
    def test_calculate_project_labor_cost_no_timesheets(
        self, mock_process, mock_group, mock_delete, mock_query
    ):
        """测试计算项目成本 - 无工时记录"""
        mock_project = Mock(spec=Project, id=1, project_name="Test")
        self.mock_db.query().filter().first.return_value = mock_project
        mock_query.return_value = []
        
        result = LaborCostService.calculate_project_labor_cost(
            self.mock_db, 
            project_id=1
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "没有已审批的工时记录")
        self.assertEqual(result["cost_count"], 0)
        self.assertEqual(result["total_cost"], 0)

    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    @patch('app.services.labor_cost.utils.delete_existing_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.process_user_costs')
    def test_calculate_project_labor_cost_success(
        self, mock_process, mock_group, mock_delete, mock_query
    ):
        """测试计算项目成本 - 成功"""
        mock_project = Mock(spec=Project, id=1, project_name="Test")
        self.mock_db.query().filter().first.return_value = mock_project
        
        mock_timesheets = [
            Mock(user_id=1, hours=Decimal("8")),
            Mock(user_id=1, hours=Decimal("4")),
        ]
        mock_query.return_value = mock_timesheets
        
        mock_group.return_value = {
            1: {"total_hours": Decimal("12"), "timesheets": mock_timesheets}
        }
        
        mock_process.return_value = ([Mock(), Mock()], Decimal("1800"))
        
        result = LaborCostService.calculate_project_labor_cost(
            self.mock_db, 
            project_id=1
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["cost_count"], 2)
        self.assertEqual(result["total_cost"], 1800.0)
        self.assertEqual(result["user_count"], 1)

    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    @patch('app.services.labor_cost.utils.delete_existing_costs')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.process_user_costs')
    def test_calculate_project_labor_cost_with_recalculate(
        self, mock_process, mock_group, mock_delete, mock_query
    ):
        """测试计算项目成本 - 重新计算模式"""
        mock_project = Mock(spec=Project, id=1, project_name="Test")
        self.mock_db.query().filter().first.return_value = mock_project
        
        mock_timesheets = [Mock(user_id=1, hours=Decimal("8"))]
        mock_query.return_value = mock_timesheets
        mock_group.return_value = {1: {"total_hours": Decimal("8"), "timesheets": mock_timesheets}}
        mock_process.return_value = ([Mock()], Decimal("1200"))
        
        result = LaborCostService.calculate_project_labor_cost(
            self.mock_db, 
            project_id=1,
            recalculate=True
        )
        
        mock_delete.assert_called_once_with(self.mock_db, mock_project, 1)
        self.assertTrue(result["success"])

    @patch('app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost')
    def test_calculate_all_projects_labor_cost_success(self, mock_calc):
        """测试批量计算所有项目成本 - 成功"""
        self.mock_db.query().filter().distinct().all.return_value = [(1,), (2,), (3,)]
        
        mock_calc.side_effect = [
            {"success": True, "cost_count": 2, "total_cost": 1000},
            {"success": True, "cost_count": 3, "total_cost": 1500},
            {"success": False, "message": "Error"},
        ]
        
        result = LaborCostService.calculate_all_projects_labor_cost(self.mock_db)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["total_projects"], 3)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["fail_count"], 1)
        self.assertEqual(len(result["results"]), 3)

    @patch('app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost')
    def test_calculate_all_projects_labor_cost_with_date_range(self, mock_calc):
        """测试批量计算 - 带日期范围"""
        # 正确设置链式 mock
        mock_query = MagicMock()
        mock_query.filter.return_value.distinct.return_value.all.return_value = [(1,)]
        self.mock_db.query.return_value = mock_query
        
        mock_calc.return_value = {"success": True, "cost_count": 2, "total_cost": 1000}
        
        result = LaborCostService.calculate_all_projects_labor_cost(
            self.mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["total_projects"], 1)

    @patch('app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost')
    def test_calculate_all_projects_labor_cost_exception(self, mock_calc):
        """测试批量计算 - 异常处理"""
        self.mock_db.query().filter().distinct().all.return_value = [(1,), (2,)]
        
        mock_calc.side_effect = [
            {"success": True, "cost_count": 2},
            Exception("Database error")
        ]
        
        result = LaborCostService.calculate_all_projects_labor_cost(self.mock_db)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fail_count"], 1)
        self.assertIn("Database error", result["results"][1]["message"])

    @patch('app.services.labor_cost_service.get_month_range_by_ym')
    @patch('app.services.labor_cost_service.LaborCostService.calculate_all_projects_labor_cost')
    def test_calculate_monthly_labor_cost(self, mock_calc_all, mock_get_range):
        """测试月度成本计算"""
        mock_get_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock_calc_all.return_value = {"success": True, "total_projects": 5}
        
        result = LaborCostService.calculate_monthly_labor_cost(
            self.mock_db, 
            year=2024, 
            month=1
        )
        
        mock_get_range.assert_called_once_with(2024, 1)
        mock_calc_all.assert_called_once_with(
            self.mock_db, 
            date(2024, 1, 1), 
            date(2024, 1, 31), 
            None
        )
        self.assertTrue(result["success"])


class TestLaborCostCalculationService(unittest.TestCase):
    """LaborCostCalculationService 测试类"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = LaborCostCalculationService(self.mock_db)

    @patch('app.services.labor_cost_service.get_month_range_by_ym')
    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    @patch('app.services.labor_cost.utils.group_timesheets_by_user')
    @patch('app.services.labor_cost.utils.process_user_costs')
    def test_calculate_monthly_costs_success(
        self, mock_process, mock_group, mock_query, mock_get_range
    ):
        """测试月度成本计算 - 成功"""
        mock_get_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock project IDs query
        self.mock_db.query().filter().distinct().all.return_value = [(1,), (2,)]
        
        # Mock project queries
        mock_project1 = Mock(spec=Project, id=1)
        mock_project2 = Mock(spec=Project, id=2)
        self.mock_db.query().filter().first.side_effect = [mock_project1, mock_project2]
        
        # Mock timesheets
        mock_query.side_effect = [
            [Mock(user_id=1, hours=Decimal("8"))],
            [Mock(user_id=2, hours=Decimal("6"))],
        ]
        
        mock_group.side_effect = [
            {1: {"total_hours": Decimal("8")}},
            {2: {"total_hours": Decimal("6")}},
        ]
        
        mock_process.side_effect = [
            ([Mock()], Decimal("1200")),
            ([Mock()], Decimal("900")),
        ]
        
        result = self.service.calculate_monthly_costs(2024, 1)
        
        self.assertEqual(result["year"], 2024)
        self.assertEqual(result["month"], 1)
        self.assertEqual(result["projects_processed"], 2)
        self.assertEqual(result["total_cost"], 2100.0)
        self.assertEqual(len(result["errors"]), 0)

    @patch('app.services.labor_cost_service.get_month_range_by_ym')
    def test_calculate_monthly_costs_no_projects(self, mock_get_range):
        """测试月度成本计算 - 无项目"""
        mock_get_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        self.mock_db.query().filter().distinct().all.return_value = []
        
        result = self.service.calculate_monthly_costs(2024, 1)
        
        self.assertEqual(result["projects_processed"], 0)
        self.assertEqual(result["total_cost"], 0.0)

    @patch('app.services.labor_cost_service.get_month_range_by_ym')
    @patch('app.services.labor_cost.utils.query_approved_timesheets')
    def test_calculate_monthly_costs_exception(self, mock_query, mock_get_range):
        """测试月度成本计算 - 异常处理"""
        mock_get_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        self.mock_db.query().filter().distinct().all.return_value = [(1,)]
        
        mock_project = Mock(spec=Project, id=1)
        self.mock_db.query().filter().first.return_value = mock_project
        
        mock_query.side_effect = Exception("Database error")
        
        result = self.service.calculate_monthly_costs(2024, 1)
        
        self.assertEqual(result["projects_processed"], 0)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Database error", result["errors"][0]["error"])


class TestLaborCostExpenseService(unittest.TestCase):
    """LaborCostExpenseService 测试类"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        with patch('app.services.hourly_rate_service.HourlyRateService'):
            self.service = LaborCostExpenseService(self.mock_db)

    def test_identify_lost_projects_basic(self):
        """测试识别未中标项目 - 基本场景"""
        mock_project = Mock(
            spec=Project,
            id=1,
            project_code="P001",
            project_name="Lost Project",
            outcome=LeadOutcomeEnum.LOST.value,
            loss_reason="Price too high",
            salesperson_id=1,
            source_lead_id="L001",
            opportunity_id=10,
            stage="S2"
        )
        
        self.mock_db.query().filter().all.return_value = [mock_project]
        
        with patch.object(self.service, '_has_detailed_design', return_value=False):
            with patch.object(self.service, '_get_project_hours', return_value=40.0):
                with patch.object(self.service, '_calculate_project_cost', return_value=Decimal("6000")):
                    result = self.service.identify_lost_projects()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["project_id"], 1)
        self.assertEqual(result[0]["outcome"], LeadOutcomeEnum.LOST.value)
        self.assertEqual(result[0]["total_hours"], 40.0)
        self.assertEqual(result[0]["total_cost"], 6000.0)

    def test_identify_lost_projects_with_date_range(self):
        """测试识别未中标项目 - 带日期范围"""
        mock_project = Mock(
            spec=Project,
            id=1,
            project_code="P001",
            project_name="Lost Project",
            outcome=LeadOutcomeEnum.LOST.value,
            loss_reason="",
            salesperson_id=1,
            source_lead_id=None,
            opportunity_id=None,
            stage="S1"
        )
        
        self.mock_db.query().filter().all.return_value = [mock_project]
        
        with patch.object(self.service, '_has_detailed_design', return_value=False):
            with patch.object(self.service, '_get_project_hours', return_value=20.0):
                with patch.object(self.service, '_calculate_project_cost', return_value=Decimal("3000")):
                    result = self.service.identify_lost_projects(
                        start_date=date(2024, 1, 1),
                        end_date=date(2024, 12, 31)
                    )
        
        self.assertEqual(len(result), 1)

    def test_identify_lost_projects_include_abandoned(self):
        """测试识别未中标项目 - 包含放弃项目"""
        mock_projects = [
            Mock(
                spec=Project, id=1, project_code="P001", project_name="Lost",
                outcome=LeadOutcomeEnum.LOST.value, loss_reason="", stage="S1",
                salesperson_id=1, source_lead_id=None, opportunity_id=None
            ),
            Mock(
                spec=Project, id=2, project_code="P002", project_name="Abandoned",
                outcome=LeadOutcomeEnum.ABANDONED.value, loss_reason="", stage="S1",
                salesperson_id=2, source_lead_id=None, opportunity_id=None
            ),
        ]
        
        self.mock_db.query().filter().all.return_value = mock_projects
        
        with patch.object(self.service, '_has_detailed_design', return_value=False):
            with patch.object(self.service, '_get_project_hours', return_value=10.0):
                with patch.object(self.service, '_calculate_project_cost', return_value=Decimal("1500")):
                    result = self.service.identify_lost_projects(include_abandoned=True)
        
        self.assertEqual(len(result), 2)

    def test_expense_lost_projects_success(self):
        """测试费用化处理 - 成功"""
        mock_project = Mock(
            spec=Project,
            id=1,
            project_code="P001",
            project_name="Lost Project",
            outcome=LeadOutcomeEnum.LOST.value,
            loss_reason="Budget",
            salesperson_id=1,
            opportunity_id=10,
            source_lead_id=None,
            updated_at=datetime(2024, 1, 31, 12, 0)
        )
        
        mock_user = Mock(
            spec=User,
            id=1,
            real_name="Zhang San",
            username="zhangsan",
            department="Tech"
        )
        
        mock_timesheet = Mock(
            spec=Timesheet,
            user_id=1,
            hours=Decimal("8"),
            work_date=date(2024, 1, 15),
            department_id=1,
            department_name="Tech Dept"
        )
        
        self.mock_db.query().filter().all.side_effect = [
            [mock_project],  # Projects query
            [mock_timesheet],  # Timesheets query
        ]
        
        self.mock_db.query().filter().first.side_effect = [
            mock_user,  # User query in loop
            mock_user,  # User query for hourly rate
        ]
        
        self.service.hourly_rate_service.get_user_hourly_rate = Mock(return_value=Decimal("150"))
        
        result = self.service.expense_lost_projects(created_by=1)
        
        self.assertEqual(result["total_projects"], 1)
        self.assertEqual(result["total_expenses"], 1)
        self.assertEqual(result["total_amount"], 1200.0)
        self.assertEqual(result["total_hours"], 8.0)

    def test_expense_lost_projects_multiple_users(self):
        """测试费用化处理 - 多用户"""
        mock_project = Mock(
            spec=Project,
            id=1,
            project_code="P001",
            project_name="Lost Project",
            outcome=LeadOutcomeEnum.LOST.value,
            loss_reason="",
            salesperson_id=1,
            opportunity_id=None,
            source_lead_id=None,
            updated_at=datetime(2024, 1, 31)
        )
        
        mock_timesheets = [
            Mock(user_id=1, hours=Decimal("8"), work_date=date(2024, 1, 15), 
                 department_id=1, department_name="Tech"),
            Mock(user_id=2, hours=Decimal("6"), work_date=date(2024, 1, 16),
                 department_id=1, department_name="Tech"),
        ]
        
        mock_user1 = Mock(spec=User, id=1, real_name="User1", username="user1", department="Tech")
        mock_user2 = Mock(spec=User, id=2, real_name="User2", username="user2", department="Tech")
        
        self.mock_db.query().filter().all.side_effect = [
            [mock_project],
            mock_timesheets,
        ]
        
        self.mock_db.query().filter().first.side_effect = [
            mock_user1, mock_user1,
            mock_user2, mock_user2,
        ]
        
        self.service.hourly_rate_service.get_user_hourly_rate = Mock(return_value=Decimal("150"))
        
        result = self.service.expense_lost_projects()
        
        self.assertEqual(result["total_projects"], 1)
        self.assertEqual(result["total_expenses"], 2)
        self.assertEqual(result["total_amount"], 2100.0)

    def test_get_lost_project_expenses_basic(self):
        """测试获取费用列表 - 基本场景"""
        mock_project = Mock(
            spec=Project,
            id=1,
            project_code="P001",
            project_name="Lost Project",
            outcome=LeadOutcomeEnum.LOST.value,
            loss_reason="Price",
            salesperson_id=1,
            updated_at=datetime(2024, 1, 31),
            created_at=datetime(2024, 1, 1)
        )
        
        self.mock_db.query().filter().all.return_value = [mock_project]
        
        with patch.object(self.service, '_get_project_hours', return_value=40.0):
            with patch.object(self.service, '_calculate_project_cost', return_value=Decimal("6000")):
                with patch.object(self.service, '_get_user_name', return_value="Zhang San"):
                    result = self.service.get_lost_project_expenses()
        
        self.assertEqual(result["total_expenses"], 1)
        self.assertEqual(result["total_amount"], 6000.0)
        self.assertEqual(result["total_hours"], 40.0)

    def test_get_expense_statistics_by_person(self):
        """测试费用统计 - 按人员"""
        expenses = [
            {
                "project_id": 1,
                "amount": 6000.0,
                "labor_hours": 40.0,
                "salesperson_id": 1,
            },
            {
                "project_id": 2,
                "amount": 3000.0,
                "labor_hours": 20.0,
                "salesperson_id": 1,
            },
        ]
        
        with patch.object(self.service, 'get_lost_project_expenses') as mock_get:
            mock_get.return_value = {
                "total_expenses": 2,
                "total_amount": 9000.0,
                "total_hours": 60.0,
                "expenses": expenses
            }
            
            mock_user = Mock(spec=User, id=1, name="Zhang San", department_name="Sales")
            self.mock_db.query().filter().first.return_value = mock_user
            
            result = self.service.get_expense_statistics(group_by='person')
        
        self.assertEqual(result["group_by"], "person")
        self.assertEqual(result["summary"]["total_amount"], 9000.0)
        self.assertEqual(len(result["statistics"]), 1)
        self.assertEqual(result["statistics"][0]["total_amount"], 9000.0)

    def test_get_expense_statistics_by_time(self):
        """测试费用统计 - 按时间"""
        expenses = [
            {
                "project_id": 1,
                "amount": 6000.0,
                "labor_hours": 40.0,
                "expense_date": date(2024, 1, 15),
                "salesperson_id": 1,
            },
            {
                "project_id": 2,
                "amount": 3000.0,
                "labor_hours": 20.0,
                "expense_date": date(2024, 2, 10),
                "salesperson_id": 1,
            },
        ]
        
        with patch.object(self.service, 'get_lost_project_expenses') as mock_get:
            mock_get.return_value = {
                "total_expenses": 2,
                "total_amount": 9000.0,
                "total_hours": 60.0,
                "expenses": expenses
            }
            
            result = self.service.get_expense_statistics(group_by='time')
        
        self.assertEqual(result["group_by"], "time")
        self.assertEqual(len(result["statistics"]), 2)

    def test_has_detailed_design_by_stage(self):
        """测试详细设计判断 - 通过阶段"""
        mock_project = Mock(spec=Project, stage="S5")
        
        result = self.service._has_detailed_design(mock_project)
        
        self.assertTrue(result)

    def test_has_detailed_design_by_hours(self):
        """测试详细设计判断 - 通过工时"""
        mock_project = Mock(spec=Project, id=1, stage="S1")
        
        with patch.object(self.service, '_get_project_hours', return_value=100.0):
            result = self.service._has_detailed_design(mock_project)
        
        self.assertTrue(result)

    def test_has_detailed_design_false(self):
        """测试详细设计判断 - 否"""
        mock_project = Mock(spec=Project, id=1, stage="S2")
        
        with patch.object(self.service, '_get_project_hours', return_value=50.0):
            result = self.service._has_detailed_design(mock_project)
        
        self.assertFalse(result)

    def test_get_project_hours(self):
        """测试获取项目工时"""
        self.mock_db.query().filter().scalar.return_value = Decimal("45.5")
        
        result = self.service._get_project_hours(1)
        
        self.assertEqual(result, 45.5)

    def test_get_project_hours_zero(self):
        """测试获取项目工时 - 零工时"""
        self.mock_db.query().filter().scalar.return_value = None
        
        result = self.service._get_project_hours(1)
        
        self.assertEqual(result, 0.0)

    def test_calculate_project_cost(self):
        """测试计算项目成本"""
        mock_timesheets = [
            Mock(user_id=1, hours=Decimal("8"), work_date=date(2024, 1, 15)),
            Mock(user_id=2, hours=Decimal("6"), work_date=date(2024, 1, 16)),
        ]
        
        mock_user1 = Mock(spec=User, id=1)
        mock_user2 = Mock(spec=User, id=2)
        
        self.mock_db.query().filter().all.return_value = mock_timesheets
        self.mock_db.query().filter().first.side_effect = [mock_user1, mock_user2]
        
        self.service.hourly_rate_service.get_user_hourly_rate = Mock(
            side_effect=[Decimal("150"), Decimal("120")]
        )
        
        result = self.service._calculate_project_cost(1)
        
        self.assertEqual(result, Decimal("1920"))

    def test_calculate_project_cost_no_user(self):
        """测试计算项目成本 - 用户不存在"""
        mock_timesheet = Mock(user_id=999, hours=Decimal("8"), work_date=date(2024, 1, 15))
        
        self.mock_db.query().filter().all.return_value = [mock_timesheet]
        self.mock_db.query().filter().first.return_value = None
        
        result = self.service._calculate_project_cost(1)
        
        self.assertEqual(result, Decimal("2400"))  # 8 * 300

    def test_get_user_name_success(self):
        """测试获取用户名称 - 成功"""
        mock_user = Mock(spec=User, real_name="Zhang San", username="zhangsan")
        self.mock_db.query().filter().first.return_value = mock_user
        
        result = self.service._get_user_name(1)
        
        self.assertEqual(result, "Zhang San")

    def test_get_user_name_no_real_name(self):
        """测试获取用户名称 - 无真实姓名"""
        mock_user = Mock(spec=User, real_name=None, username="zhangsan")
        self.mock_db.query().filter().first.return_value = mock_user
        
        result = self.service._get_user_name(1)
        
        self.assertEqual(result, "zhangsan")

    def test_get_user_name_not_found(self):
        """测试获取用户名称 - 用户不存在"""
        self.mock_db.query().filter().first.return_value = None
        
        result = self.service._get_user_name(1)
        
        self.assertIsNone(result)

    def test_get_user_name_none_id(self):
        """测试获取用户名称 - ID为None"""
        result = self.service._get_user_name(None)
        
        self.assertIsNone(result)

    @patch('app.models.sales.Lead')
    def test_get_lead_id_from_project_success(self, mock_lead_model):
        """测试获取线索ID - 成功"""
        mock_project = Mock(spec=Project, source_lead_id="L001")
        mock_lead = Mock(id=100)
        self.mock_db.query().filter().first.return_value = mock_lead
        
        result = self.service._get_lead_id_from_project(mock_project)
        
        self.assertEqual(result, 100)

    def test_get_lead_id_from_project_no_source(self):
        """测试获取线索ID - 无来源线索"""
        mock_project = Mock(spec=Project, source_lead_id=None)
        
        result = self.service._get_lead_id_from_project(mock_project)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
