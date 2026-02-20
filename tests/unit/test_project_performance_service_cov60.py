# -*- coding: utf-8 -*-
"""
项目绩效服务层单元测试
目标覆盖率: 60%+
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.project_performance import ProjectPerformanceService


class TestProjectPerformanceService(unittest.TestCase):
    """项目绩效服务层测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ProjectPerformanceService(self.db)

    def test_check_performance_view_permission_superuser(self):
        """测试超级管理员权限"""
        current_user = MagicMock()
        current_user.is_superuser = True
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_performance_view_permission_self(self):
        """测试查看自己的权限"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 1)
        self.assertTrue(result)

    def test_check_performance_view_permission_no_target_user(self):
        """测试目标用户不存在"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1

        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_performance_view_permission_dept_manager(self):
        """测试部门经理查看同部门员工"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 创建部门经理角色 - 修复嵌套结构
        role_obj = MagicMock()
        role_obj.role_code = "dept_manager"
        role_obj.role_name = "部门经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        current_user.roles = [user_role]

        target_user = MagicMock()
        target_user.department_id = 10

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    @patch("app.services.project_performance.service.User")
    def test_get_team_members(self, mock_user_class):
        """测试获取团队成员"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2

        # Mock完整的查询链
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [user1, user2]
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    @patch("app.services.project_performance.service.User")
    def test_get_department_members(self, mock_user_class):
        """测试获取部门成员"""
        user1 = MagicMock()
        user1.id = 3
        user2 = MagicMock()
        user2.id = 4

        # Mock完整的查询链
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [user1, user2]
        mock_query.filter.return_value = mock_filter
        self.db.query.return_value = mock_query

        result = self.service.get_department_members(20)
        self.assertEqual(result, [3, 4])

    def test_get_evaluator_type_both(self):
        """测试评价人类型判断 - BOTH"""
        user = MagicMock()

        # 修复嵌套结构 - 部门经理角色
        dept_role_obj = MagicMock()
        dept_role_obj.role_code = "dept_manager"
        dept_role_obj.role_name = "部门经理"
        dept_role = MagicMock()
        dept_role.role = dept_role_obj

        # 修复嵌套结构 - 项目经理角色
        pm_role_obj = MagicMock()
        pm_role_obj.role_code = "pm"
        pm_role_obj.role_name = "项目经理"
        pm_role = MagicMock()
        pm_role.role = pm_role_obj

        user.roles = [dept_role, pm_role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_get_evaluator_type_dept_manager(self):
        """测试评价人类型判断 - DEPT_MANAGER"""
        user = MagicMock()

        # 修复嵌套结构
        role_obj = MagicMock()
        role_obj.role_code = "dept_manager"
        role_obj.role_name = "部门经理"
        dept_role = MagicMock()
        dept_role.role = role_obj

        user.roles = [dept_role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """测试评价人类型判断 - PROJECT_MANAGER"""
        user = MagicMock()

        # 修复嵌套结构
        role_obj = MagicMock()
        role_obj.role_code = "pm"
        role_obj.role_name = "项目经理"
        pm_role = MagicMock()
        pm_role.role = role_obj

        user.roles = [pm_role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_other(self):
        """测试评价人类型判断 - OTHER"""
        user = MagicMock()

        # 修复嵌套结构
        role_obj = MagicMock()
        role_obj.role_code = "employee"
        role_obj.role_name = "员工"
        role = MagicMock()
        role.role = role_obj

        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_get_team_name_exists(self):
        """测试获取团队名称 - 存在"""
        dept = MagicMock()
        dept.name = "研发部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_exists(self):
        """测试获取团队名称 - 不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(10)
        self.assertEqual(result, "团队10")

    def test_get_department_name_exists(self):
        """测试获取部门名称 - 存在"""
        dept = MagicMock()
        dept.name = "技术部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_department_name(20)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_exists(self):
        """测试获取部门名称 - 不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_department_name(20)
        self.assertEqual(result, "部门20")

    def test_get_project_performance_project_not_found(self):
        """测试获取项目绩效 - 项目不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_project_performance(1)

        self.assertEqual(str(context.exception), "项目不存在")

    @patch("app.services.project_performance.service.desc")
    def test_get_project_performance_success(self, mock_desc):
        """测试获取项目绩效 - 成功"""
        # Mock project
        project = MagicMock()
        project.id = 1
        project.project_name = "测试项目"

        # Mock period
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        # Mock contributions
        contrib1 = MagicMock()
        contrib1.user_id = 10
        contrib1.contribution_score = Decimal("85.5")
        contrib1.hours_spent = Decimal("120.0")
        contrib1.task_count = 5

        user1 = MagicMock()
        user1.real_name = "张三"
        user1.username = "zhangsan"

        # Setup query chain
        query_mock = MagicMock()
        self.db.query.return_value = query_mock

        # First query: Project
        filter1 = MagicMock()
        filter1.first.return_value = project
        query_mock.filter.return_value = filter1

        # Second query: Period (需要设置 order_by)
        filter2 = MagicMock()
        order_by_mock = MagicMock()
        order_by_mock.first.return_value = period
        filter2.order_by.return_value = order_by_mock
        query_mock.filter.side_effect = [filter1, filter2]

        # Reset for contributions query
        contrib_filter = MagicMock()
        contrib_filter.all.return_value = [contrib1]

        # Reset for user query
        user_filter = MagicMock()
        user_filter.first.return_value = user1

        # Configure side effects
        self.db.query.side_effect = [
            query_mock,  # Project query
            query_mock,  # Period query
            MagicMock(filter=MagicMock(return_value=contrib_filter)),  # Contributions
            MagicMock(filter=MagicMock(return_value=user_filter)),  # User
        ]

        result = self.service.get_project_performance(1)

        self.assertEqual(result["project_id"], 1)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["member_count"], 1)
        self.assertEqual(len(result["members"]), 1)
        self.assertEqual(result["members"][0]["user_id"], 10)

    def test_get_project_progress_report_project_not_found(self):
        """测试获取项目进展报告 - 项目不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_project_progress_report(1)

        self.assertEqual(str(context.exception), "项目不存在")

    def test_compare_performance_period_not_found(self):
        """测试绩效对比 - 周期不存在"""
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        with self.assertRaises(ValueError) as context:
            self.service.compare_performance([1, 2])

        self.assertEqual(str(context.exception), "未找到考核周期")


if __name__ == "__main__":
    unittest.main()
