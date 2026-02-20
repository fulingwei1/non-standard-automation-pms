# -*- coding: utf-8 -*-
"""
ManagerPerformanceService 单元测试
测试经理绩效服务层的业务逻辑
"""

import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

from app.models.organization import Department
from app.models.performance import MonthlyWorkSummary, PerformanceEvaluationRecord
from app.models.project import Project
from app.models.progress import Task
from app.models.user import User
from app.schemas.performance import PerformanceEvaluationRecordCreate
from app.services.manager_performance import ManagerPerformanceService


class TestManagerPerformanceService(unittest.TestCase):
    """ManagerPerformanceService 测试类"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.service = ManagerPerformanceService(self.db)

    def test_check_performance_view_permission_superuser(self):
        """测试管理员可以查看所有人的绩效"""
        current_user = Mock(spec=User)
        current_user.is_superuser = True
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 999)

        self.assertTrue(result)

    def test_check_performance_view_permission_self(self):
        """测试用户可以查看自己的绩效"""
        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 100

        result = self.service.check_performance_view_permission(current_user, 100)

        self.assertTrue(result)

    def test_check_performance_view_permission_dept_manager(self):
        """测试部门经理可以查看本部门员工的绩效"""
        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        current_user.roles = []

        # 创建角色
        role_mock = Mock()
        role_mock.role.role_code = "dept_manager"
        role_mock.role.role_name = "部门经理"
        current_user.roles = [role_mock]

        target_user = Mock(spec=User)
        target_user.id = 2
        target_user.department_id = 10

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)

        self.assertTrue(result)

    def test_check_performance_view_permission_no_permission(self):
        """测试无权限查看其他部门员工的绩效"""
        current_user = Mock(spec=User)
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        current_user.roles = []

        target_user = Mock(spec=User)
        target_user.id = 2
        target_user.department_id = 20

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)

        self.assertFalse(result)

    def test_get_team_members(self):
        """测试获取团队成员ID列表"""
        user1 = Mock(spec=User)
        user1.id = 1
        user2 = Mock(spec=User)
        user2.id = 2

        self.db.query.return_value.filter.return_value.all.return_value = [
            user1,
            user2,
        ]

        result = self.service.get_team_members(10)

        self.assertEqual(result, [1, 2])

    def test_get_department_members(self):
        """测试获取部门成员ID列表"""
        user1 = Mock(spec=User)
        user1.id = 10
        user2 = Mock(spec=User)
        user2.id = 20
        user3 = Mock(spec=User)
        user3.id = 30

        self.db.query.return_value.filter.return_value.all.return_value = [
            user1,
            user2,
            user3,
        ]

        result = self.service.get_department_members(5)

        self.assertEqual(result, [10, 20, 30])

    def test_get_evaluator_type_dept_manager(self):
        """测试判断评价人类型为部门经理"""
        user = Mock(spec=User)
        role_mock = Mock()
        role_mock.role.role_code = "dept_manager"
        role_mock.role.role_name = "部门经理"
        user.roles = [role_mock]

        result = self.service.get_evaluator_type(user)

        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """测试判断评价人类型为项目经理"""
        user = Mock(spec=User)
        role_mock = Mock()
        role_mock.role.role_code = "pm"
        role_mock.role.role_name = "项目经理"
        user.roles = [role_mock]

        result = self.service.get_evaluator_type(user)

        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_both(self):
        """测试判断评价人类型为双重角色"""
        user = Mock(spec=User)
        role_mock1 = Mock()
        role_mock1.role.role_code = "dept_manager"
        role_mock1.role.role_name = "部门经理"
        role_mock2 = Mock()
        role_mock2.role.role_code = "pm"
        role_mock2.role.role_name = "项目经理"
        user.roles = [role_mock1, role_mock2]

        result = self.service.get_evaluator_type(user)

        self.assertEqual(result, "BOTH")

    def test_get_team_name(self):
        """测试获取团队名称"""
        dept = Mock(spec=Department)
        dept.id = 10
        dept.name = "技术部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_team_name(10)

        self.assertEqual(result, "技术部")

    def test_get_team_name_not_found(self):
        """测试获取不存在的团队名称"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(999)

        self.assertEqual(result, "团队999")

    def test_get_department_name(self):
        """测试获取部门名称"""
        dept = Mock(spec=Department)
        dept.id = 5
        dept.name = "市场部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_department_name(5)

        self.assertEqual(result, "市场部")

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_empty(self, mock_perf_service):
        """测试非经理角色获取空任务列表"""
        mock_perf_service.get_manageable_employees.return_value = []

        current_user = Mock(spec=User)
        current_user.id = 1

        result = self.service.get_evaluation_tasks(current_user)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["pending_count"], 0)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(result["tasks"], [])

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_detail_success(self, mock_perf_service):
        """测试成功获取评价详情"""
        summary = Mock(spec=MonthlyWorkSummary)
        summary.id = 100
        summary.employee_id = 50

        employee = Mock(spec=User)
        employee.id = 50
        employee.real_name = "张三"
        employee.username = "zhangsan"
        employee.department = "技术部"
        employee.position = "工程师"
        summary.employee = employee

        mock_perf_service.get_historical_performance.return_value = []

        self.db.query.return_value.filter.return_value.first.side_effect = [
            summary,  # 第一次查询：获取工作总结
            None,  # 第二次查询：获取评价记录
        ]

        current_user = Mock(spec=User)
        current_user.id = 1

        result = self.service.get_evaluation_detail(current_user, 100)

        self.assertEqual(result["summary"], summary)
        self.assertEqual(result["employee_info"]["id"], 50)
        self.assertEqual(result["employee_info"]["name"], "张三")
        self.assertIsNone(result["my_evaluation"])

    def test_get_evaluation_detail_not_found(self):
        """测试获取不存在的评价详情"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        current_user = Mock(spec=User)
        current_user.id = 1

        with self.assertRaises(ValueError) as context:
            self.service.get_evaluation_detail(current_user, 999)

        self.assertEqual(str(context.exception), "工作总结不存在")

    def test_submit_evaluation_create_new(self):
        """测试提交新评价"""
        summary = Mock(spec=MonthlyWorkSummary)
        summary.id = 100
        summary.status = "SUBMITTED"

        current_user = Mock(spec=User)
        current_user.id = 1
        role_mock = Mock()
        role_mock.role.role_code = "dept_manager"
        role_mock.role.role_name = "部门经理"
        current_user.roles = [role_mock]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85, comment="表现良好", project_id=None, project_weight=None
        )

        # 模拟数据库查询
        self.db.query.return_value.filter.return_value.first.side_effect = [
            summary,  # 第一次查询：获取工作总结
            None,  # 第二次查询：检查是否已评价
        ]
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.submit_evaluation(current_user, 100, evaluation_in)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_submit_evaluation_already_completed(self):
        """测试重复提交已完成的评价"""
        summary = Mock(spec=MonthlyWorkSummary)
        summary.id = 100

        existing_eval = Mock(spec=PerformanceEvaluationRecord)
        existing_eval.status = "COMPLETED"

        current_user = Mock(spec=User)
        current_user.id = 1

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=90, comment="优秀", project_id=None, project_weight=None
        )

        self.db.query.return_value.filter.return_value.first.side_effect = [
            summary,  # 第一次查询：获取工作总结
            existing_eval,  # 第二次查询：检查是否已评价
        ]

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(current_user, 100, evaluation_in)

        self.assertEqual(str(context.exception), "您已完成该评价")


if __name__ == "__main__":
    unittest.main()
