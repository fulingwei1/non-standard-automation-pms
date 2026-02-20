# -*- coding: utf-8 -*-
"""
员工绩效服务单元测试
测试 EmployeePerformanceService 的所有核心方法
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.performance import (
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.performance import MonthlyWorkSummaryCreate, MonthlyWorkSummaryUpdate
from app.services.employee_performance.employee_performance_service import (
    EmployeePerformanceService,
)


class TestEmployeePerformanceServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)
        assert service.db == mock_db


class TestCheckPerformanceViewPermission:
    """测试权限检查方法"""

    def test_superuser_can_view_any_performance(self):
        """测试超级用户可以查看任何人的绩效"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.is_superuser = True
        current_user.id = 1

        assert service.check_performance_view_permission(current_user, 999) is True

    def test_user_can_view_own_performance(self):
        """测试用户可以查看自己的绩效"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 100

        assert service.check_performance_view_permission(current_user, 100) is True

    def test_target_user_not_found(self):
        """测试目标用户不存在时返回False"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = None

        assert service.check_performance_view_permission(current_user, 999) is False

    def test_dept_manager_can_view_dept_member(self):
        """测试部门经理可以查看部门员工的绩效"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 模拟角色
        role_mock = Mock()
        role_mock.role.role_code = "dept_manager"
        role_mock.role.role_name = "部门经理"
        current_user.roles = [role_mock]

        target_user = Mock(spec=User)
        target_user.id = 2
        target_user.department_id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = target_user

        assert service.check_performance_view_permission(current_user, 2) is True

    def test_user_without_manager_role_cannot_view_others(self):
        """测试没有管理角色的用户不能查看他人绩效"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        current_user.roles = []  # 无角色

        target_user = Mock(spec=User)
        target_user.id = 2
        target_user.department_id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = target_user

        assert service.check_performance_view_permission(current_user, 2) is False

    def test_dept_manager_cannot_view_other_dept_member(self):
        """测试部门经理不能查看其他部门员工的绩效"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        role_mock = Mock()
        role_mock.role.role_code = "dept_manager"
        role_mock.role.role_name = "部门经理"
        current_user.roles = [role_mock]

        target_user = Mock(spec=User)
        target_user.id = 2
        target_user.department_id = 20  # 不同部门

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = target_user
        mock_query.filter.return_value.all.return_value = []  # 无项目

        assert service.check_performance_view_permission(current_user, 2) is False


class TestGetTeamMembers:
    """测试获取团队成员"""

    def test_get_team_members_success(self):
        """测试成功获取团队成员"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        user1 = Mock(spec=User)
        user1.id = 1
        user2 = Mock(spec=User)
        user2.id = 2

        mock_db.query.return_value.filter.return_value.all.return_value = [user1, user2]

        members = service.get_team_members(10)
        assert members == [1, 2]

    def test_get_team_members_empty(self):
        """测试获取空团队成员列表"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        mock_db.query.return_value.filter.return_value.all.return_value = []

        members = service.get_team_members(10)
        assert members == []


class TestGetDepartmentMembers:
    """测试获取部门成员"""

    def test_get_department_members_success(self):
        """测试成功获取部门成员"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        user1 = Mock(spec=User)
        user1.id = 10
        user2 = Mock(spec=User)
        user2.id = 20

        mock_db.query.return_value.filter.return_value.all.return_value = [user1, user2]

        members = service.get_department_members(5)
        assert members == [10, 20]


class TestGetEvaluatorType:
    """测试判断评价人类型"""

    def test_evaluator_type_dept_manager(self):
        """测试部门经理类型"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        user = Mock(spec=User)
        role_mock = Mock()
        role_mock.role.role_code = "dept_manager"
        role_mock.role.role_name = "部门经理"
        user.roles = [role_mock]

        result = service.get_evaluator_type(user)
        assert result == "DEPT_MANAGER"

    def test_evaluator_type_project_manager(self):
        """测试项目经理类型"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        user = Mock(spec=User)
        role_mock = Mock()
        role_mock.role.role_code = "pm"
        role_mock.role.role_name = "项目经理"
        user.roles = [role_mock]

        result = service.get_evaluator_type(user)
        assert result == "PROJECT_MANAGER"

    def test_evaluator_type_both(self):
        """测试同时是部门经理和项目经理"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        user = Mock(spec=User)
        role1_mock = Mock()
        role1_mock.role.role_code = "dept_manager"
        role1_mock.role.role_name = "部门经理"

        role2_mock = Mock()
        role2_mock.role.role_code = "pm"
        role2_mock.role.role_name = "项目经理"

        user.roles = [role1_mock, role2_mock]

        result = service.get_evaluator_type(user)
        assert result == "BOTH"

    def test_evaluator_type_other(self):
        """测试其他类型（非管理角色）"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        user = Mock(spec=User)
        role_mock = Mock()
        role_mock.role.role_code = "employee"
        role_mock.role.role_name = "员工"
        user.roles = [role_mock]

        result = service.get_evaluator_type(user)
        assert result == "OTHER"


class TestGetTeamName:
    """测试获取团队名称"""

    def test_get_team_name_exists(self):
        """测试获取存在的团队名称"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        dept = Mock(spec=Department)
        dept.name = "研发部"

        mock_db.query.return_value.filter.return_value.first.return_value = dept

        name = service.get_team_name(1)
        assert name == "研发部"

    def test_get_team_name_not_exists(self):
        """测试获取不存在的团队名称"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        name = service.get_team_name(999)
        assert name == "团队999"


class TestGetDepartmentName:
    """测试获取部门名称"""

    def test_get_department_name_exists(self):
        """测试获取存在的部门名称"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        dept = Mock(spec=Department)
        dept.name = "技术部"

        mock_db.query.return_value.filter.return_value.first.return_value = dept

        name = service.get_department_name(5)
        assert name == "技术部"

    def test_get_department_name_not_exists(self):
        """测试获取不存在的部门名称"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        name = service.get_department_name(999)
        assert name == "部门999"


class TestCreateMonthlyWorkSummary:
    """测试创建月度工作总结"""

    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_create_monthly_work_summary_success(self, mock_perf_service):
        """测试成功创建月度工作总结"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        summary_in = MonthlyWorkSummaryCreate(
            period="2024-01",
            work_content="本月完成了核心模块开发和系统优化工作",
            self_evaluation="工作完成质量较好，按时交付项目任务",
            highlights="成功优化了系统性能，提升了50%的响应速度",
            problems="部分文档编写不够及时，需要改进",
            next_month_plan="下月将重点关注新功能开发和团队协作",
        )

        # Mock查询不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.create_monthly_work_summary(current_user, summary_in)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        mock_perf_service.create_evaluation_tasks.assert_called_once()

    def test_create_monthly_work_summary_duplicate(self):
        """测试重复创建月度工作总结（应抛出异常）"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        summary_in = MonthlyWorkSummaryCreate(
            period="2024-01",
            work_content="本月完成了核心模块开发和系统优化工作",
            self_evaluation="工作完成质量较好，按时交付项目任务",
        )

        # Mock查询已存在
        existing_summary = Mock(spec=MonthlyWorkSummary)
        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_summary
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_monthly_work_summary(current_user, summary_in)

        assert exc_info.value.status_code == 400
        assert "已提交过" in exc_info.value.detail


class TestSaveMonthlySummaryDraft:
    """测试保存工作总结草稿"""

    def test_save_new_draft(self):
        """测试保存新草稿"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        summary_update = MonthlyWorkSummaryUpdate(
            work_content="草稿内容", self_evaluation="草稿评价"
        )

        # Mock查询不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.save_monthly_summary_draft(
            current_user, "2024-02", summary_update
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_existing_draft(self):
        """测试更新现有草稿"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        summary_update = MonthlyWorkSummaryUpdate(
            work_content="更新内容", self_evaluation="更新评价"
        )

        # Mock现有草稿
        existing_summary = Mock(spec=MonthlyWorkSummary)
        existing_summary.status = "DRAFT"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_summary
        )

        result = service.save_monthly_summary_draft(
            current_user, "2024-02", summary_update
        )

        assert existing_summary.work_content == "更新内容"
        assert existing_summary.self_evaluation == "更新评价"
        mock_db.commit.assert_called_once()

    def test_cannot_update_submitted_summary(self):
        """测试不能更新已提交的总结"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        summary_update = MonthlyWorkSummaryUpdate(work_content="尝试更新")

        # Mock已提交的总结
        existing_summary = Mock(spec=MonthlyWorkSummary)
        existing_summary.status = "SUBMITTED"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_summary
        )

        with pytest.raises(HTTPException) as exc_info:
            service.save_monthly_summary_draft(current_user, "2024-02", summary_update)

        assert exc_info.value.status_code == 400
        assert "只能更新草稿状态" in exc_info.value.detail


class TestGetMonthlySummaryHistory:
    """测试获取历史工作总结"""

    def test_get_monthly_summary_history_with_evaluations(self):
        """测试获取带评价数量的历史工作总结"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        # Mock工作总结
        summary1 = Mock(spec=MonthlyWorkSummary)
        summary1.id = 10
        summary1.period = "2024-01"
        summary1.status = "COMPLETED"
        summary1.submit_date = datetime(2024, 2, 1)
        summary1.created_at = datetime(2024, 1, 31)

        mock_query_summary = MagicMock()
        mock_db.query.side_effect = [
            mock_query_summary,  # 第一次查询summary
            MagicMock(),  # 第一次查询评价数量
        ]

        mock_query_summary.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            summary1
        ]

        # Mock评价数量查询
        mock_count_query = MagicMock()
        mock_db.query.side_effect = [mock_query_summary, mock_count_query]
        mock_count_query.filter.return_value.count.return_value = 2

        result = service.get_monthly_summary_history(current_user, limit=12)

        assert len(result) == 1
        assert result[0]["period"] == "2024-01"
        assert result[0]["evaluation_count"] == 2

    def test_get_monthly_summary_history_empty(self):
        """测试获取空的历史记录"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.get_monthly_summary_history(current_user, limit=12)
        assert result == []


class TestGetMyPerformance:
    """测试查看我的绩效"""

    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_my_performance_not_submitted(self, mock_perf_service):
        """测试未提交工作总结时的绩效状态"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        # Mock当前周期无总结
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_my_performance(current_user)

        assert result["current_status"]["summary_status"] == "NOT_SUBMITTED"
        assert result["current_status"]["dept_evaluation"]["status"] == "PENDING"

    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_my_performance_with_completed_summary(self, mock_perf_service):
        """测试已完成的工作总结和评价"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        # Mock当前总结
        current_summary = Mock(spec=MonthlyWorkSummary)
        current_summary.id = 100
        current_summary.period = date.today().strftime("%Y-%m")
        current_summary.status = "COMPLETED"

        # Mock部门评价
        dept_eval = Mock(spec=PerformanceEvaluationRecord)
        dept_eval.status = "COMPLETED"
        dept_eval.score = 85
        dept_eval.evaluator = Mock()
        dept_eval.evaluator.real_name = "张经理"

        # 设置多个query调用的返回值
        summary_query = MagicMock()
        dept_eval_query = MagicMock()
        project_eval_query = MagicMock()
        history_summary_query = MagicMock()

        summary_query.filter.return_value.first.return_value = current_summary
        dept_eval_query.filter.return_value.first.return_value = dept_eval
        project_eval_query.filter.return_value.all.return_value = []
        history_summary_query.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [
            summary_query,
            dept_eval_query,
            project_eval_query,
            history_summary_query,
            history_summary_query,
            history_summary_query,
        ]

        # Mock PerformanceService
        mock_perf_service.calculate_final_score.return_value = {
            "final_score": 85,
            "dept_score": 85,
            "project_score": 0,
        }
        mock_perf_service.get_score_level.return_value = "优秀"
        mock_perf_service.get_historical_performance.return_value = []

        result = service.get_my_performance(current_user)

        assert result["current_status"]["summary_status"] == "COMPLETED"
        assert result["current_status"]["dept_evaluation"]["score"] == 85
        assert result["latest_result"]["final_score"] == 85

    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_my_performance_with_project_evaluations(self, mock_perf_service):
        """测试包含项目评价的绩效"""
        mock_db = MagicMock(spec=Session)
        service = EmployeePerformanceService(mock_db)

        current_user = Mock(spec=User)
        current_user.id = 1

        # Mock当前总结
        current_summary = Mock(spec=MonthlyWorkSummary)
        current_summary.id = 100
        current_summary.period = date.today().strftime("%Y-%m")
        current_summary.status = "SUBMITTED"

        # Mock项目评价
        project_eval = Mock(spec=PerformanceEvaluationRecord)
        project_eval.status = "COMPLETED"
        project_eval.score = 90
        project_eval.project_weight = 0.5
        project_eval.evaluator = Mock()
        project_eval.evaluator.real_name = "李PM"
        project_eval.project = Mock()
        project_eval.project.project_name = "项目A"

        summary_query = MagicMock()
        dept_eval_query = MagicMock()
        project_eval_query = MagicMock()
        history_summary_query1 = MagicMock()
        history_summary_query2 = MagicMock()
        history_summary_query3 = MagicMock()

        summary_query.filter.return_value.first.return_value = current_summary
        dept_eval_query.filter.return_value.first.return_value = None
        project_eval_query.filter.return_value.all.return_value = [project_eval]
        history_summary_query1.filter.return_value.first.return_value = None
        history_summary_query2.filter.return_value.first.return_value = None
        history_summary_query3.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [
            summary_query,
            dept_eval_query,
            project_eval_query,
            history_summary_query1,
            history_summary_query2,
            history_summary_query3,
        ]

        mock_perf_service.get_historical_performance.return_value = []

        result = service.get_my_performance(current_user)

        assert len(result["current_status"]["project_evaluations"]) == 1
        assert (
            result["current_status"]["project_evaluations"][0]["project_name"]
            == "项目A"
        )
        assert result["current_status"]["project_evaluations"][0]["score"] == 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
