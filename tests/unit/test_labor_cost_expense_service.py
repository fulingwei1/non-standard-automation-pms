# -*- coding: utf-8 -*-
"""
工时费用化处理服务单元测试

测试 LaborCostExpenseService 的核心功能:
- 识别未中标项目
- 将未中标项目工时费用化
- 获取未中标项目费用列表
- 获取费用统计
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.labor_cost_expense_service import LaborCostExpenseService


class TestLaborCostExpenseService:
    """工时费用化处理服务测试"""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = LaborCostExpenseService(db_session)
        assert service.db == db_session
        assert service.hourly_rate_service is not None


class TestIdentifyLostProjects:
    """识别未中标项目测试"""

    def test_identify_lost_projects_empty(self, db_session: Session):
        """测试无未中标项目时返回空列表"""
        service = LaborCostExpenseService(db_session)
        projects = service.identify_lost_projects()
        assert isinstance(projects, list)

    def test_identify_lost_projects_with_date_range(self, db_session: Session):
        """测试按日期范围筛选"""
        service = LaborCostExpenseService(db_session)
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        projects = service.identify_lost_projects(
        start_date=start_date,
        end_date=end_date
        )
        assert isinstance(projects, list)

    def test_identify_lost_projects_include_abandoned(self, db_session: Session):
        """测试包含放弃的项目"""
        service = LaborCostExpenseService(db_session)
        projects = service.identify_lost_projects(include_abandoned=True)
        assert isinstance(projects, list)

    def test_identify_lost_projects_exclude_abandoned(self, db_session: Session):
        """测试不包含放弃的项目"""
        service = LaborCostExpenseService(db_session)
        projects = service.identify_lost_projects(include_abandoned=False)
        assert isinstance(projects, list)

    def test_identify_lost_projects_result_structure(self, db_session: Session):
        """测试返回结果的数据结构"""
        service = LaborCostExpenseService(db_session)
        projects = service.identify_lost_projects()

        for project in projects:
            assert "project_id" in project
            assert "project_code" in project
            assert "project_name" in project
            assert "outcome" in project
            assert "loss_reason" in project
            assert "has_detailed_design" in project
            assert "total_hours" in project
            assert "total_cost" in project


class TestExpenseLostProjects:
    """将未中标项目工时费用化测试"""

    def test_expense_lost_projects_empty(self, db_session: Session):
        """测试无未中标项目时的处理"""
        service = LaborCostExpenseService(db_session)
        result = service.expense_lost_projects()

        assert result["total_projects"] == 0
        assert result["total_expenses"] == 0
        assert result["total_amount"] == 0.0
        assert result["total_hours"] == 0.0
        assert result["expenses"] == []

    def test_expense_lost_projects_with_project_ids(self, db_session: Session):
        """测试按项目ID列表处理"""
        service = LaborCostExpenseService(db_session)
        result = service.expense_lost_projects(project_ids=[1, 2, 3])

        assert "total_projects" in result
        assert "total_expenses" in result
        assert "total_amount" in result
        assert "total_hours" in result
        assert "expenses" in result

    def test_expense_lost_projects_with_date_range(self, db_session: Session):
        """测试按日期范围处理"""
        service = LaborCostExpenseService(db_session)
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        result = service.expense_lost_projects(
        start_date=start_date,
        end_date=end_date
        )

        assert isinstance(result, dict)

    def test_expense_lost_projects_result_structure(self, db_session: Session):
        """测试返回结果的数据结构"""
        service = LaborCostExpenseService(db_session)
        result = service.expense_lost_projects()

        assert "total_projects" in result
        assert "total_expenses" in result
        assert "total_amount" in result
        assert "total_hours" in result
        assert "expenses" in result

        assert isinstance(result["total_projects"], int)
        assert isinstance(result["total_expenses"], int)
        assert isinstance(result["total_amount"], float)
        assert isinstance(result["total_hours"], float)
        assert isinstance(result["expenses"], list)


class TestGetLostProjectExpenses:
    """获取未中标项目费用列表测试"""

    def test_get_expenses_empty(self, db_session: Session):
        """测试无费用数据时的返回"""
        service = LaborCostExpenseService(db_session)
        result = service.get_lost_project_expenses()

        assert result["total_expenses"] == 0
        assert result["total_amount"] == 0
        assert result["total_hours"] == 0
        assert result["expenses"] == []

    def test_get_expenses_with_date_range(self, db_session: Session):
        """测试按日期范围筛选"""
        service = LaborCostExpenseService(db_session)
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        result = service.get_lost_project_expenses(
        start_date=start_date,
        end_date=end_date
        )

        assert isinstance(result, dict)

    def test_get_expenses_with_salesperson_filter(
        self, db_session: Session, test_sales_user
    ):
        """测试按销售人员筛选"""
        service = LaborCostExpenseService(db_session)
        result = service.get_lost_project_expenses(
        salesperson_id=test_sales_user.id
        )

        assert isinstance(result, dict)

    def test_get_expenses_result_structure(self, db_session: Session):
        """测试返回结果的数据结构"""
        service = LaborCostExpenseService(db_session)
        result = service.get_lost_project_expenses()

        assert "total_expenses" in result
        assert "total_amount" in result
        assert "total_hours" in result
        assert "expenses" in result


class TestGetExpenseStatistics:
    """获取费用统计测试"""

    def test_get_statistics_by_person(self, db_session: Session):
        """测试按人员统计"""
        service = LaborCostExpenseService(db_session)
        result = service.get_expense_statistics(group_by="person")

        assert result["group_by"] == "person"
        assert "statistics" in result
        assert "summary" in result
        assert isinstance(result["statistics"], list)

    def test_get_statistics_by_department(self, db_session: Session):
        """测试按部门统计"""
        service = LaborCostExpenseService(db_session)
        result = service.get_expense_statistics(group_by="department")

        assert result["group_by"] == "department"
        assert "statistics" in result
        assert "summary" in result

    def test_get_statistics_by_time(self, db_session: Session):
        """测试按时间统计"""
        service = LaborCostExpenseService(db_session)
        result = service.get_expense_statistics(group_by="time")

        assert result["group_by"] == "time"
        assert "statistics" in result
        assert "summary" in result

    def test_get_statistics_with_date_range(self, db_session: Session):
        """测试按日期范围统计"""
        service = LaborCostExpenseService(db_session)
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        result = service.get_expense_statistics(
        start_date=start_date,
        end_date=end_date,
        group_by="person"
        )

        assert isinstance(result, dict)

    def test_get_statistics_summary_structure(self, db_session: Session):
        """测试统计汇总的数据结构"""
        service = LaborCostExpenseService(db_session)
        result = service.get_expense_statistics()

        assert "summary" in result
        summary = result["summary"]
        assert "total_amount" in summary
        assert "total_hours" in summary
        assert "total_projects" in summary


class TestInternalMethods:
    """内部方法测试"""

    def test_has_detailed_design_by_stage(
        self, db_session: Session, mock_project
    ):
        """测试通过阶段判断是否有详细设计"""
        service = LaborCostExpenseService(db_session)

        # 测试早期阶段
        mock_project.stage = "S1"
        result = service._has_detailed_design(mock_project)
        # S1阶段如果工时不超过80小时，应该返回False
        assert isinstance(result, bool)

    def test_has_detailed_design_by_hours(
        self, db_session: Session, mock_project
    ):
        """测试通过工时判断是否有详细设计"""
        service = LaborCostExpenseService(db_session)

        # 设置早期阶段
        mock_project.stage = "S1"
        result = service._has_detailed_design(mock_project)
        assert isinstance(result, bool)

    def test_get_project_hours_empty(
        self, db_session: Session, mock_project
    ):
        """测试无工时记录时返回0"""
        service = LaborCostExpenseService(db_session)
        hours = service._get_project_hours(mock_project.id)
        assert hours == 0.0

    def test_calculate_project_cost_empty(
        self, db_session: Session, mock_project
    ):
        """测试无工时记录时成本为0"""
        service = LaborCostExpenseService(db_session)
        cost = service._calculate_project_cost(mock_project.id)
        assert cost == Decimal("0")

    def test_get_user_name_valid_user(
        self, db_session: Session, test_user
    ):
        """测试获取有效用户名称"""
        service = LaborCostExpenseService(db_session)
        name = service._get_user_name(test_user.id)
        assert name is not None

    def test_get_user_name_invalid_user(self, db_session: Session):
        """测试获取无效用户名称"""
        service = LaborCostExpenseService(db_session)
        name = service._get_user_name(99999)
        assert name is None

    def test_get_user_name_none_user_id(self, db_session: Session):
        """测试用户ID为None时返回None"""
        service = LaborCostExpenseService(db_session)
        name = service._get_user_name(None)
        assert name is None


class TestEdgeCases:
    """边界条件测试"""

    def test_identify_lost_projects_future_dates(self, db_session: Session):
        """测试未来日期范围"""
        service = LaborCostExpenseService(db_session)
        future_start = date.today() + timedelta(days=30)
        future_end = date.today() + timedelta(days=60)

        projects = service.identify_lost_projects(
        start_date=future_start,
        end_date=future_end
        )
        assert projects == []

    def test_expense_lost_projects_empty_project_ids(self, db_session: Session):
        """测试空项目ID列表"""
        service = LaborCostExpenseService(db_session)
        result = service.expense_lost_projects(project_ids=[])

        assert result["total_projects"] == 0

    def test_get_statistics_invalid_group_by(self, db_session: Session):
        """测试无效的分组方式（使用默认time）"""
        service = LaborCostExpenseService(db_session)
        result = service.get_expense_statistics(group_by="invalid")

        # 无效的分组方式会走到else分支（time）
        assert "statistics" in result
