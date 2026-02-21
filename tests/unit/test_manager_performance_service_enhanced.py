# -*- coding: utf-8 -*-
"""
经理绩效服务增强测试
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.organization import Department
from app.models.performance import MonthlyWorkSummary, PerformanceEvaluationRecord
from app.models.project import Project
from app.models.progress import Task
from app.models.user import User
from app.schemas.performance import PerformanceEvaluationRecordCreate
from app.services.manager_performance.manager_performance_service import (
    ManagerPerformanceService,
)


class TestManagerPerformanceServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        service = ManagerPerformanceService(db=mock_db)
        self.assertEqual(service.db, mock_db)


class TestCheckPerformanceViewPermission(unittest.TestCase):
    """测试查看绩效权限检查"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_superuser_has_permission(self):
        """测试超级管理员有权限查看所有人的绩效"""
        current_user = Mock(id=1, is_superuser=True)
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_user_can_view_own_performance(self):
        """测试用户可以查看自己的绩效"""
        current_user = Mock(id=1, is_superuser=False)
        result = self.service.check_performance_view_permission(current_user, 1)
        self.assertTrue(result)

    def test_return_false_when_target_user_not_exists(self):
        """测试目标用户不存在时返回False"""
        current_user = Mock(id=1, is_superuser=False)
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_no_manager_role_returns_false(self):
        """测试没有管理角色时返回False"""
        current_user = Mock(id=1, is_superuser=False, roles=[])
        target_user = Mock(id=2, department_id=10)
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            target_user
        )
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_dept_manager_can_view_same_department_employee(self):
        """测试部门经理可以查看同部门员工绩效"""
        mock_role = Mock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        mock_user_role = Mock(role=mock_role.role)

        current_user = Mock(
            id=1, is_superuser=False, department_id=10, roles=[mock_user_role]
        )
        target_user = Mock(id=2, department_id=10)

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            target_user
        )

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_dept_manager_cannot_view_different_department_employee(self):
        """测试部门经理不能查看其他部门员工绩效"""
        mock_role = Mock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        mock_user_role = Mock(role=mock_role.role)

        current_user = Mock(
            id=1, is_superuser=False, department_id=10, roles=[mock_user_role]
        )
        target_user = Mock(id=2, department_id=20)

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            target_user
        )
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_project_manager_can_view_project_member(self):
        """测试项目经理可以查看项目成员绩效"""
        mock_role = Mock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = "项目经理"
        mock_user_role = Mock(role=mock_role.role)

        current_user = Mock(
            id=1, is_superuser=False, department_id=10, roles=[mock_user_role]
        )
        target_user = Mock(id=2, department_id=20)

        # 模拟项目查询
        mock_project = Mock(id=100)
        mock_task = Mock()

        # 设置查询链
        query_mock = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_2 = MagicMock()

        self.mock_db.query.return_value = query_mock

        # 第一次查询：获取目标用户
        first_call_filter = MagicMock()
        first_call_filter.first.return_value = target_user

        # 第二次查询：获取当前用户管理的项目
        second_call_filter = MagicMock()
        second_call_filter.all.return_value = [mock_project]

        # 第三次查询：获取项目
        third_call_filter = MagicMock()
        third_call_filter.all.return_value = [mock_project]

        # 第四次查询：检查任务
        fourth_call_filter_1 = MagicMock()
        fourth_call_filter_2 = MagicMock()
        fourth_call_filter_2.first.return_value = mock_task

        query_mock.filter.side_effect = [
            first_call_filter,
            second_call_filter,
            third_call_filter,
            fourth_call_filter_1,
        ]
        fourth_call_filter_1.filter.return_value = fourth_call_filter_2

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_role_code_case_insensitive(self):
        """测试角色代码不区分大小写"""
        mock_role = Mock()
        mock_role.role.role_code = "DEPT_MANAGER"
        mock_role.role.role_name = "Department Manager"
        mock_user_role = Mock(role=mock_role.role)

        current_user = Mock(
            id=1, is_superuser=False, department_id=10, roles=[mock_user_role]
        )
        target_user = Mock(id=2, department_id=10)

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            target_user
        )

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_admin_role_has_permission_same_department(self):
        """测试admin角色有权限（同部门）"""
        mock_role = Mock()
        mock_role.role.role_code = "admin"
        mock_role.role.role_name = "管理员"
        mock_user_role = Mock(role=mock_role.role)

        current_user = Mock(
            id=1, is_superuser=False, department_id=10, roles=[mock_user_role]
        )
        target_user = Mock(id=2, department_id=10)

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            target_user
        )

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_target_user_without_department(self):
        """测试目标用户没有部门时的处理"""
        mock_role = Mock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        mock_user_role = Mock(role=mock_role.role)

        current_user = Mock(
            id=1, is_superuser=False, department_id=10, roles=[mock_user_role]
        )
        target_user = Mock(id=2, department_id=None)

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            target_user
        )
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)


class TestGetTeamMembers(unittest.TestCase):
    """测试获取团队成员"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_get_team_members_success(self):
        """测试成功获取团队成员"""
        mock_users = [Mock(id=1), Mock(id=2), Mock(id=3)]
        self.mock_db.query.return_value.filter.return_value.all.return_value = (
            mock_users
        )

        result = self.service.get_team_members(team_id=10)
        self.assertEqual(result, [1, 2, 3])

    def test_get_team_members_empty(self):
        """测试团队无成员时返回空列表"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_team_members(team_id=10)
        self.assertEqual(result, [])


class TestGetDepartmentMembers(unittest.TestCase):
    """测试获取部门成员"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_get_department_members_success(self):
        """测试成功获取部门成员"""
        mock_users = [Mock(id=1), Mock(id=2), Mock(id=3)]
        self.mock_db.query.return_value.filter.return_value.all.return_value = (
            mock_users
        )

        result = self.service.get_department_members(dept_id=10)
        self.assertEqual(result, [1, 2, 3])

    def test_get_department_members_empty(self):
        """测试部门无成员时返回空列表"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_department_members(dept_id=10)
        self.assertEqual(result, [])


class TestGetEvaluatorType(unittest.TestCase):
    """测试获取评价人类型"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_dept_manager_type(self):
        """测试部门经理类型"""
        mock_role = Mock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        user = Mock(roles=[Mock(role=mock_role.role)])

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_project_manager_type(self):
        """测试项目经理类型"""
        mock_role = Mock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = "项目经理"
        user = Mock(roles=[Mock(role=mock_role.role)])

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_both_manager_type(self):
        """测试同时是部门经理和项目经理"""
        mock_role_1 = Mock()
        mock_role_1.role.role_code = "dept_manager"
        mock_role_1.role.role_name = "部门经理"

        mock_role_2 = Mock()
        mock_role_2.role.role_code = "pm"
        mock_role_2.role.role_name = "项目经理"

        user = Mock(roles=[Mock(role=mock_role_1.role), Mock(role=mock_role_2.role)])

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_other_type(self):
        """测试非管理角色"""
        mock_role = Mock()
        mock_role.role.role_code = "employee"
        mock_role.role.role_name = "员工"
        user = Mock(roles=[Mock(role=mock_role.role)])

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_no_roles(self):
        """测试用户没有角色"""
        user = Mock(roles=[])
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_none_roles(self):
        """测试用户角色为None"""
        user = Mock(roles=None)
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")


class TestGetTeamName(unittest.TestCase):
    """测试获取团队名称"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_get_team_name_success(self):
        """测试成功获取团队名称"""
        mock_dept = Mock()
        mock_dept.name = "研发部"
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_dept
        )

        result = self.service.get_team_name(team_id=10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """测试团队不存在时返回默认名称"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(team_id=10)
        self.assertEqual(result, "团队10")


class TestGetDepartmentName(unittest.TestCase):
    """测试获取部门名称"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_get_department_name_success(self):
        """测试成功获取部门名称"""
        mock_dept = Mock()
        mock_dept.name = "技术部"
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_dept
        )

        result = self.service.get_department_name(dept_id=10)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_found(self):
        """测试部门不存在时返回默认名称"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_department_name(dept_id=10)
        self.assertEqual(result, "部门10")


class TestGetEvaluationTasks(unittest.TestCase):
    """测试获取评价任务列表"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_no_manageable_employees(self, mock_perf_service):
        """测试没有可管理的员工时返回空列表"""
        mock_perf_service.get_manageable_employees.return_value = []
        current_user = Mock(id=1)

        result = self.service.get_evaluation_tasks(current_user)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["pending_count"], 0)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(result["tasks"], [])

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_default_period(self, mock_perf_service):
        """测试使用默认周期（当前月份）"""
        mock_perf_service.get_manageable_employees.return_value = [1, 2, 3]
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        current_user = Mock(id=1)
        result = self.service.get_evaluation_tasks(current_user)

        expected_period = date.today().strftime("%Y-%m")
        mock_perf_service.get_manageable_employees.assert_called_with(
            self.mock_db, current_user, expected_period
        )

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_pending_status(self, mock_perf_service):
        """测试获取待评价任务"""
        mock_perf_service.get_manageable_employees.return_value = [1, 2]
        mock_perf_service.get_user_manager_roles.return_value = None

        mock_employee = Mock(id=1, real_name="张三", department="技术部")
        mock_summary = Mock(
            id=100,
            employee_id=1,
            employee=mock_employee,
            period="2024-01",
            status="SUBMITTED",
            submit_date=datetime(2024, 2, 1),
        )

        # 设置查询链
        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.all.return_value = [mock_summary]
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = None  # 没有评价记录
        query_mock_2.filter.return_value = filter_mock_2

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2]

        current_user = Mock(id=1)
        result = self.service.get_evaluation_tasks(current_user, period="2024-01")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["pending_count"], 1)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(len(result["tasks"]), 1)

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_completed_status(self, mock_perf_service):
        """测试获取已完成评价任务"""
        mock_perf_service.get_manageable_employees.return_value = [1]
        mock_perf_service.get_user_manager_roles.return_value = None

        mock_employee = Mock(id=1, real_name="李四", department="产品部")
        mock_summary = Mock(
            id=101,
            employee_id=1,
            employee=mock_employee,
            period="2024-01",
            status="COMPLETED",
            submit_date=datetime(2024, 2, 1),
        )

        mock_evaluation = Mock(status="COMPLETED", evaluator_type="DEPT_MANAGER")

        # 设置查询链
        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.all.return_value = [mock_summary]
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = mock_evaluation
        query_mock_2.filter.return_value = filter_mock_2

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2]

        current_user = Mock(id=1)
        result = self.service.get_evaluation_tasks(
            current_user, period="2024-01", status_filter="COMPLETED"
        )

        self.assertEqual(result["completed_count"], 1)

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_filter_pending(self, mock_perf_service):
        """测试筛选待评价任务"""
        mock_perf_service.get_manageable_employees.return_value = [1, 2]
        mock_perf_service.get_user_manager_roles.return_value = None

        mock_employee_1 = Mock(id=1, real_name="张三", department="技术部")
        mock_summary_1 = Mock(
            id=100,
            employee_id=1,
            employee=mock_employee_1,
            period="2024-01",
            status="SUBMITTED",
            submit_date=datetime(2024, 2, 1),
        )

        # 设置查询链
        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.all.return_value = [mock_summary_1]
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = None  # 待评价
        query_mock_2.filter.return_value = filter_mock_2

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2]

        current_user = Mock(id=1)
        result = self.service.get_evaluation_tasks(
            current_user, period="2024-01", status_filter="PENDING"
        )

        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0].status, "PENDING")


class TestGetEvaluationDetail(unittest.TestCase):
    """测试获取评价详情"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_get_evaluation_detail_summary_not_found(self):
        """测试工作总结不存在时抛出异常"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        current_user = Mock(id=1)

        with self.assertRaises(ValueError) as context:
            self.service.get_evaluation_detail(current_user, task_id=999)

        self.assertEqual(str(context.exception), "工作总结不存在")

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_detail_success(self, mock_perf_service):
        """测试成功获取评价详情"""
        mock_employee = Mock(
            id=1, real_name="张三", username="zhangsan", department="技术部", position="工程师"
        )
        mock_summary = Mock(id=100, employee_id=1, employee=mock_employee)

        mock_perf_service.get_historical_performance.return_value = []
        mock_evaluation = Mock(id=1, score=85)

        # 设置查询链
        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.first.return_value = mock_summary
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = mock_evaluation
        query_mock_2.filter.return_value = filter_mock_2

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2]

        current_user = Mock(id=1)
        result = self.service.get_evaluation_detail(current_user, task_id=100)

        self.assertEqual(result["summary"], mock_summary)
        self.assertEqual(result["employee_info"]["id"], 1)
        self.assertEqual(result["employee_info"]["name"], "张三")
        self.assertEqual(result["my_evaluation"], mock_evaluation)

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_detail_no_my_evaluation(self, mock_perf_service):
        """测试没有我的评价记录"""
        mock_employee = Mock(
            id=1, real_name="", username="zhangsan", department="技术部", position="工程师"
        )
        mock_summary = Mock(id=100, employee_id=1, employee=mock_employee)

        mock_perf_service.get_historical_performance.return_value = []

        # 设置查询链
        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.first.return_value = mock_summary
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = None  # 没有评价记录
        query_mock_2.filter.return_value = filter_mock_2

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2]

        current_user = Mock(id=1)
        result = self.service.get_evaluation_detail(current_user, task_id=100)

        self.assertIsNone(result["my_evaluation"])
        # 测试使用username作为name
        self.assertEqual(result["employee_info"]["name"], "zhangsan")


class TestSubmitEvaluation(unittest.TestCase):
    """测试提交评价"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ManagerPerformanceService(db=self.mock_db)

    def test_submit_evaluation_summary_not_found(self):
        """测试工作总结不存在时抛出异常"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock.filter.return_value = filter_mock
        self.mock_db.query.return_value = query_mock

        current_user = Mock(id=1)
        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85, comment="表现良好，工作认真负责"
        )

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(current_user, task_id=999, evaluation_in=evaluation_in)

        self.assertEqual(str(context.exception), "工作总结不存在")

    def test_submit_evaluation_already_completed(self):
        """测试已完成评价时抛出异常"""
        mock_summary = Mock(id=100, status="SUBMITTED")
        mock_evaluation = Mock(status="COMPLETED")

        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.first.return_value = mock_summary
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = mock_evaluation
        query_mock_2.filter.return_value = filter_mock_2

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2]

        current_user = Mock(id=1)
        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85, comment="表现良好，工作认真负责"
        )

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(current_user, task_id=100, evaluation_in=evaluation_in)

        self.assertEqual(str(context.exception), "您已完成该评价")

    def test_submit_evaluation_create_new(self):
        """测试创建新评价"""
        mock_summary = Mock(id=100, status="SUBMITTED")

        mock_role = Mock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        current_user = Mock(id=1, roles=[Mock(role=mock_role.role)])

        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.first.return_value = mock_summary
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = None  # 没有现有评价
        query_mock_2.filter.return_value = filter_mock_2

        # 模拟还有其他评价人未完成评价
        mock_other_eval = Mock(status="PENDING")
        query_mock_3 = MagicMock()
        filter_mock_3 = MagicMock()
        filter_mock_3.all.return_value = [mock_other_eval]
        query_mock_3.filter.return_value = filter_mock_3

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2, query_mock_3]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85,
            comment="表现良好，工作认真负责，能按时完成任务",
            project_id=10,
            project_weight=50
        )

        result = self.service.submit_evaluation(current_user, task_id=100, evaluation_in=evaluation_in)

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.assertEqual(mock_summary.status, "EVALUATING")

    def test_submit_evaluation_update_existing(self):
        """测试更新现有评价"""
        mock_summary = Mock(id=100, status="EVALUATING")
        mock_existing_eval = Mock(status="PENDING")

        mock_role = Mock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = "项目经理"
        current_user = Mock(id=1, roles=[Mock(role=mock_role.role)])

        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.first.return_value = mock_summary
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = mock_existing_eval
        query_mock_2.filter.return_value = filter_mock_2

        query_mock_3 = MagicMock()
        filter_mock_3 = MagicMock()
        filter_mock_3.all.return_value = [mock_existing_eval]
        query_mock_3.filter.return_value = filter_mock_3

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2, query_mock_3]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=90,
            comment="表现优秀，超额完成任务，团队协作能力强",
            project_id=20,
            project_weight=80
        )

        result = self.service.submit_evaluation(current_user, task_id=100, evaluation_in=evaluation_in)

        self.assertEqual(mock_existing_eval.score, 90)
        self.assertEqual(mock_existing_eval.comment, "表现优秀，超额完成任务，团队协作能力强")
        self.assertEqual(mock_existing_eval.project_id, 20)
        self.assertEqual(mock_existing_eval.project_weight, 80)
        self.assertEqual(mock_existing_eval.status, "COMPLETED")
        self.mock_db.commit.assert_called_once()

    def test_submit_evaluation_all_completed_updates_summary_status(self):
        """测试所有评价都完成时更新总结状态"""
        mock_summary = Mock(id=100, status="EVALUATING")
        mock_eval_1 = Mock(status="COMPLETED")
        mock_eval_2 = Mock(status="COMPLETED")

        mock_role = Mock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        current_user = Mock(id=1, roles=[Mock(role=mock_role.role)])

        query_mock_1 = MagicMock()
        filter_mock_1 = MagicMock()
        filter_mock_1.first.return_value = mock_summary
        query_mock_1.filter.return_value = filter_mock_1

        query_mock_2 = MagicMock()
        filter_mock_2 = MagicMock()
        filter_mock_2.first.return_value = None
        query_mock_2.filter.return_value = filter_mock_2

        query_mock_3 = MagicMock()
        filter_mock_3 = MagicMock()
        filter_mock_3.all.return_value = [mock_eval_1, mock_eval_2]
        query_mock_3.filter.return_value = filter_mock_3

        self.mock_db.query.side_effect = [query_mock_1, query_mock_2, query_mock_3]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85,
            comment="表现良好，工作态度积极，持续改进"
        )

        result = self.service.submit_evaluation(current_user, task_id=100, evaluation_in=evaluation_in)

        self.assertEqual(mock_summary.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
