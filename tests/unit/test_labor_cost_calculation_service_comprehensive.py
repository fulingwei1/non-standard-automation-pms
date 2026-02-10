# -*- coding: utf-8 -*-
"""
labor_cost_calculation_service 综合单元测试

测试覆盖:
- query_approved_timesheets: 查询已审批的工时记录
- delete_existing_costs: 删除现有成本记录
- group_timesheets_by_user: 按用户分组工时记录
- find_existing_cost: 查找现有成本记录
- update_existing_cost: 更新现有成本记录
- create_new_cost: 创建新的成本记录
- check_budget_alert: 检查预算预警
- process_user_costs: 处理用户成本
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch



class TestQueryApprovedTimesheets:
    """测试 query_approved_timesheets 函数"""

    def test_returns_approved_timesheets(self):
        """测试返回已审批的工时记录"""
        from app.services.labor_cost_calculation_service import query_approved_timesheets

        mock_db = MagicMock()
        mock_timesheet = MagicMock()
        mock_timesheet.id = 1
        mock_timesheet.project_id = 100
        mock_timesheet.status = "APPROVED"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_timesheet]

        result = query_approved_timesheets(mock_db, 100, None, None)

        assert len(result) == 1
        assert result[0].id == 1

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.labor_cost_calculation_service import query_approved_timesheets

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        result = query_approved_timesheets(mock_db, 100, start_date, end_date)

        assert result == []

    def test_returns_empty_when_no_timesheets(self):
        """测试无工时记录时返回空"""
        from app.services.labor_cost_calculation_service import query_approved_timesheets

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = query_approved_timesheets(mock_db, 100, None, None)

        assert result == []


class TestDeleteExistingCosts:
    """测试 delete_existing_costs 函数"""

    def test_deletes_existing_costs(self):
        """测试删除现有成本记录"""
        from app.services.labor_cost_calculation_service import delete_existing_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 1000.0

        mock_cost = MagicMock()
        mock_cost.amount = 500.0

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

        delete_existing_costs(mock_db, mock_project, 100)

        mock_db.delete.assert_called_once_with(mock_cost)
        assert mock_project.actual_cost == 500.0  # 1000 - 500

    def test_handles_no_existing_costs(self):
        """测试无现有成本记录时不报错"""
        from app.services.labor_cost_calculation_service import delete_existing_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 1000.0

        mock_db.query.return_value.filter.return_value.all.return_value = []

        delete_existing_costs(mock_db, mock_project, 100)

        mock_db.delete.assert_not_called()
        assert mock_project.actual_cost == 1000.0

    def test_handles_none_actual_cost(self):
        """测试处理actual_cost为None的情况"""
        from app.services.labor_cost_calculation_service import delete_existing_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = None

        mock_cost = MagicMock()
        mock_cost.amount = 500.0

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cost]

        delete_existing_costs(mock_db, mock_project, 100)

        # actual_cost should be 0 - 500 = -500, but capped at 0
        assert mock_project.actual_cost == 0


class TestGroupTimesheetsByUser:
    """测试 group_timesheets_by_user 函数"""

    def test_groups_timesheets_correctly(self):
        """测试正确分组工时记录"""
        from app.services.labor_cost_calculation_service import group_timesheets_by_user

        mock_ts1 = MagicMock()
        mock_ts1.id = 1
        mock_ts1.user_id = 10
        mock_ts1.user_name = "张三"
        mock_ts1.hours = 8
        mock_ts1.work_date = date.today()

        mock_ts2 = MagicMock()
        mock_ts2.id = 2
        mock_ts2.user_id = 10
        mock_ts2.user_name = "张三"
        mock_ts2.hours = 4
        mock_ts2.work_date = date.today() - timedelta(days=1)

        result = group_timesheets_by_user([mock_ts1, mock_ts2])

        assert 10 in result
        assert result[10]["total_hours"] == Decimal("12")
        assert len(result[10]["timesheet_ids"]) == 2

    def test_groups_multiple_users(self):
        """测试分组多个用户"""
        from app.services.labor_cost_calculation_service import group_timesheets_by_user

        mock_ts1 = MagicMock()
        mock_ts1.id = 1
        mock_ts1.user_id = 10
        mock_ts1.user_name = "张三"
        mock_ts1.hours = 8
        mock_ts1.work_date = date.today()

        mock_ts2 = MagicMock()
        mock_ts2.id = 2
        mock_ts2.user_id = 20
        mock_ts2.user_name = "李四"
        mock_ts2.hours = 6
        mock_ts2.work_date = date.today()

        result = group_timesheets_by_user([mock_ts1, mock_ts2])

        assert 10 in result
        assert 20 in result
        assert result[10]["total_hours"] == Decimal("8")
        assert result[20]["total_hours"] == Decimal("6")

    def test_returns_empty_for_no_timesheets(self):
        """测试无工时记录时返回空"""
        from app.services.labor_cost_calculation_service import group_timesheets_by_user

        result = group_timesheets_by_user([])

        assert result == {}

    def test_handles_none_hours(self):
        """测试处理hours为None的情况"""
        from app.services.labor_cost_calculation_service import group_timesheets_by_user

        mock_ts = MagicMock()
        mock_ts.id = 1
        mock_ts.user_id = 10
        mock_ts.user_name = "张三"
        mock_ts.hours = None
        mock_ts.work_date = date.today()

        result = group_timesheets_by_user([mock_ts])

        assert result[10]["total_hours"] == Decimal("0")


class TestFindExistingCost:
    """测试 find_existing_cost 函数"""

    def test_finds_existing_cost(self):
        """测试查找现有成本记录"""
        from app.services.labor_cost_calculation_service import find_existing_cost

        mock_db = MagicMock()
        mock_cost = MagicMock()
        mock_cost.id = 1
        mock_cost.project_id = 100
        mock_cost.source_id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_cost

        result = find_existing_cost(mock_db, 100, 10)

        assert result is not None
        assert result.id == 1

    def test_returns_none_when_not_found(self):
        """测试未找到时返回None"""
        from app.services.labor_cost_calculation_service import find_existing_cost

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = find_existing_cost(mock_db, 100, 10)

        assert result is None


class TestUpdateExistingCost:
    """测试 update_existing_cost 函数"""

    def test_updates_cost_correctly(self):
        """测试正确更新成本记录"""
        from app.services.labor_cost_calculation_service import update_existing_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 1000.0

        mock_cost = MagicMock()
        mock_cost.amount = Decimal("500")

        user_data = {
            "user_name": "张三",
            "total_hours": Decimal("10")
        }

        update_existing_cost(
            mock_db, mock_project, mock_cost,
            Decimal("800"), user_data, date.today()
        )

        assert mock_cost.amount == Decimal("800")
        # 1000 - 500 + 800 = 1300
        assert mock_project.actual_cost == 1300.0
        mock_db.add.assert_called_once_with(mock_cost)

    def test_uses_today_when_no_end_date(self):
        """测试无结束日期时使用今天"""
        from app.services.labor_cost_calculation_service import update_existing_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 1000.0

        mock_cost = MagicMock()
        mock_cost.amount = Decimal("500")

        user_data = {
            "user_name": "张三",
            "total_hours": Decimal("10")
        }

        update_existing_cost(
            mock_db, mock_project, mock_cost,
            Decimal("800"), user_data, None
        )

        assert mock_cost.cost_date == date.today()


class TestCreateNewCost:
    """测试 create_new_cost 函数"""

    def test_creates_new_cost(self):
        """测试创建新成本记录"""
        from app.services.labor_cost_calculation_service import create_new_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 1000.0

        user_data = {
            "user_name": "张三",
            "total_hours": Decimal("10")
        }

        result = create_new_cost(
            mock_db, mock_project, 100, 10,
            Decimal("800"), user_data, date.today()
        )

        assert result is not None
        assert result.amount == Decimal("800")
        assert result.project_id == 100
        assert result.source_id == 10
        # 1000 + 800 = 1800
        assert mock_project.actual_cost == 1800.0
        mock_db.add.assert_called_once()

    def test_handles_none_actual_cost(self):
        """测试处理actual_cost为None的情况"""
        from app.services.labor_cost_calculation_service import create_new_cost

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = None

        user_data = {
            "user_name": "张三",
            "total_hours": Decimal("10")
        }

        create_new_cost(
            mock_db, mock_project, 100, 10,
            Decimal("800"), user_data, date.today()
        )

        assert mock_project.actual_cost == 800.0


class TestCheckBudgetAlert:
    """测试 check_budget_alert 函数"""

    def test_calls_cost_alert_service(self):
        """测试调用成本预警服务"""
        from app.services.labor_cost_calculation_service import check_budget_alert

        mock_db = MagicMock()

        with patch('app.services.cost_alert_service.CostAlertService') as mock_alert_service:
            check_budget_alert(mock_db, 100, 10)

            mock_alert_service.check_budget_execution.assert_called_once_with(
                mock_db, 100, trigger_source="TIMESHEET", source_id=10
            )

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        from app.services.labor_cost_calculation_service import check_budget_alert

        mock_db = MagicMock()

        with patch('app.services.cost_alert_service.CostAlertService') as mock_alert_service:
            mock_alert_service.check_budget_execution.side_effect = Exception("测试异常")

            # 不应该抛出异常
            check_budget_alert(mock_db, 100, 10)


class TestProcessUserCosts:
    """测试 process_user_costs 函数"""

    def test_processes_user_costs(self):
        """测试处理用户成本"""
        from app.services.labor_cost_calculation_service import process_user_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 0

        user_costs = {
            10: {
                "user_id": 10,
                "user_name": "张三",
                "total_hours": Decimal("8"),
                "timesheet_ids": [1],
                "cost_amount": Decimal("0"),
                "work_date": date.today()
            }
        }

        with patch('app.services.labor_cost_service.LaborCostService') as mock_labor_service:
            mock_labor_service.get_user_hourly_rate.return_value = Decimal("100")

            with patch('app.services.labor_cost.utils.find_existing_cost') as mock_find:
                mock_find.return_value = None

                with patch('app.services.labor_cost.utils.check_budget_alert'):
                    created_costs, total_cost = process_user_costs(
                        mock_db, mock_project, 100,
                        user_costs, date.today(), False
                    )

                    assert len(created_costs) == 1
                    assert total_cost == Decimal("800")  # 8小时 * 100元/小时

    def test_updates_existing_cost_when_found(self):
        """测试找到现有成本时更新"""
        from app.services.labor_cost_calculation_service import process_user_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 500

        mock_existing_cost = MagicMock()
        mock_existing_cost.amount = Decimal("400")

        user_costs = {
            10: {
                "user_id": 10,
                "user_name": "张三",
                "total_hours": Decimal("8"),
                "timesheet_ids": [1],
                "cost_amount": Decimal("0"),
                "work_date": date.today()
            }
        }

        with patch('app.services.labor_cost_service.LaborCostService') as mock_labor_service:
            mock_labor_service.get_user_hourly_rate.return_value = Decimal("100")

            with patch('app.services.labor_cost.utils.find_existing_cost') as mock_find:
                mock_find.return_value = mock_existing_cost

                with patch('app.services.labor_cost.utils.update_existing_cost') as mock_update:
                    with patch('app.services.labor_cost.utils.check_budget_alert'):
                        created_costs, total_cost = process_user_costs(
                            mock_db, mock_project, 100,
                            user_costs, date.today(), False
                        )

                        mock_update.assert_called_once()

    def test_skips_find_when_recalculate(self):
        """测试recalculate模式下跳过查找"""
        from app.services.labor_cost_calculation_service import process_user_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 0

        user_costs = {
            10: {
                "user_id": 10,
                "user_name": "张三",
                "total_hours": Decimal("8"),
                "timesheet_ids": [1],
                "cost_amount": Decimal("0"),
                "work_date": date.today()
            }
        }

        with patch('app.services.labor_cost_service.LaborCostService') as mock_labor_service:
            mock_labor_service.get_user_hourly_rate.return_value = Decimal("100")

            with patch('app.services.labor_cost.utils.find_existing_cost') as mock_find:
                with patch('app.services.labor_cost.utils.check_budget_alert'):
                    process_user_costs(
                        mock_db, mock_project, 100,
                        user_costs, date.today(), True  # recalculate=True
                    )

                    # find_existing_cost should not be called when recalculate=True
                    mock_find.assert_not_called()

    def test_handles_empty_user_costs(self):
        """测试处理空用户成本"""
        from app.services.labor_cost_calculation_service import process_user_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 0

        with patch('app.services.labor_cost_service.LaborCostService'):
            created_costs, total_cost = process_user_costs(
                mock_db, mock_project, 100,
                {}, date.today(), False
            )

            assert created_costs == []
            assert total_cost == Decimal("0")

    def test_uses_work_date_from_user_data(self):
        """测试使用用户数据中的工作日期"""
        from app.services.labor_cost_calculation_service import process_user_costs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.actual_cost = 0

        work_date = date.today() - timedelta(days=5)
        user_costs = {
            10: {
                "user_id": 10,
                "user_name": "张三",
                "total_hours": Decimal("8"),
                "timesheet_ids": [1],
                "cost_amount": Decimal("0"),
                "work_date": work_date
            }
        }

        with patch('app.services.labor_cost_service.LaborCostService') as mock_labor_service:
            mock_labor_service.get_user_hourly_rate.return_value = Decimal("100")

            with patch('app.services.labor_cost.utils.find_existing_cost') as mock_find:
                mock_find.return_value = None

                with patch('app.services.labor_cost.utils.check_budget_alert'):
                    process_user_costs(
                        mock_db, mock_project, 100,
                        user_costs, None, False
                    )

                    # 应该使用work_date调用get_user_hourly_rate
                    mock_labor_service.get_user_hourly_rate.assert_called_with(
                        mock_db, 10, work_date
                    )
