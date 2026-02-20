# -*- coding: utf-8 -*-
"""
团队绩效服务单元测试
Coverage: 基础功能测试
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.team_performance import TeamPerformanceService


class TestTeamPerformanceService(unittest.TestCase):
    """团队绩效服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_init(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.db, self.mock_db)

    def test_get_team_name_exists(self):
        """测试获取存在的团队名称"""
        mock_dept = MagicMock()
        mock_dept.name = "研发部"
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_dept
        )

        result = self.service.get_team_name(1)

        self.assertEqual(result, "研发部")

    def test_get_team_name_not_exists(self):
        """测试获取不存在的团队名称"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(99)

        self.assertEqual(result, "团队99")

    def test_get_department_name_exists(self):
        """测试获取存在的部门名称"""
        mock_dept = MagicMock()
        mock_dept.name = "技术部"
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_dept
        )

        result = self.service.get_department_name(1)

        self.assertEqual(result, "技术部")

    def test_get_department_name_not_exists(self):
        """测试获取不存在的部门名称"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_department_name(88)

        self.assertEqual(result, "部门88")

    def test_get_team_members(self):
        """测试获取团队成员"""
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user2 = MagicMock()
        mock_user2.id = 2

        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_user1,
            mock_user2,
        ]

        result = self.service.get_team_members(1)

        self.assertEqual(result, [1, 2])
        self.assertEqual(len(result), 2)

    def test_get_department_members(self):
        """测试获取部门成员"""
        mock_user1 = MagicMock()
        mock_user1.id = 10
        mock_user2 = MagicMock()
        mock_user2.id = 20
        mock_user3 = MagicMock()
        mock_user3.id = 30

        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_user1,
            mock_user2,
            mock_user3,
        ]

        result = self.service.get_department_members(5)

        self.assertEqual(result, [10, 20, 30])
        self.assertEqual(len(result), 3)

    def test_get_period_by_id(self):
        """测试通过ID获取周期"""
        mock_period = MagicMock()
        mock_period.id = 1
        mock_period.period_name = "2024Q1"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_period
        )

        result = self.service.get_period(period_id=1)

        self.assertEqual(result.id, 1)
        self.assertEqual(result.period_name, "2024Q1")

    def test_get_period_latest_finalized(self):
        """测试获取最新的已完成周期"""
        mock_period = MagicMock()
        mock_period.id = 2
        mock_period.period_name = "2024Q2"
        mock_period.status = "FINALIZED"

        (
            self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value
        ) = mock_period

        result = self.service.get_period(period_id=None)

        self.assertEqual(result.id, 2)
        self.assertEqual(result.status, "FINALIZED")

    def test_get_evaluator_type_dept_manager(self):
        """测试判断部门经理类型"""
        mock_user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        mock_user.roles = [mock_role]

        result = self.service.get_evaluator_type(mock_user)

        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """测试判断项目经理类型"""
        mock_user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = "项目经理"
        mock_user.roles = [mock_role]

        result = self.service.get_evaluator_type(mock_user)

        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_both(self):
        """测试判断双重角色类型"""
        mock_user = MagicMock()
        mock_role1 = MagicMock()
        mock_role1.role.role_code = "dept_manager"
        mock_role1.role.role_name = "部门经理"
        mock_role2 = MagicMock()
        mock_role2.role.role_code = "pm"
        mock_role2.role.role_name = "项目经理"
        mock_user.roles = [mock_role1, mock_role2]

        result = self.service.get_evaluator_type(mock_user)

        self.assertEqual(result, "BOTH")

    def test_get_evaluator_type_other(self):
        """测试判断普通用户类型"""
        mock_user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "employee"
        mock_role.role.role_name = "员工"
        mock_user.roles = [mock_role]

        result = self.service.get_evaluator_type(mock_user)

        self.assertEqual(result, "OTHER")

    def test_check_permission_superuser(self):
        """测试超级用户权限检查"""
        mock_user = MagicMock()
        mock_user.is_superuser = True

        result = self.service.check_performance_view_permission(mock_user, 999)

        self.assertTrue(result)

    def test_check_permission_self(self):
        """测试查看自己绩效的权限"""
        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.is_superuser = False

        result = self.service.check_performance_view_permission(mock_user, 5)

        self.assertTrue(result)

    def test_check_permission_same_department(self):
        """测试查看同部门成员绩效的权限"""
        mock_current_user = MagicMock()
        mock_current_user.id = 1
        mock_current_user.is_superuser = False
        mock_current_user.department_id = 10

        mock_role = MagicMock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        mock_current_user.roles = [mock_role]

        mock_target_user = MagicMock()
        mock_target_user.department_id = 10

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_target_user
        )

        result = self.service.check_performance_view_permission(
            mock_current_user, 2
        )

        self.assertTrue(result)

    def test_get_team_performance_with_results(self):
        """测试获取团队绩效（有结果）"""
        # Mock 周期
        mock_period = MagicMock()
        mock_period.id = 1
        mock_period.period_name = "2024Q1"

        # Mock 成员
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user2 = MagicMock()
        mock_user2.id = 2

        # Mock 绩效结果
        mock_result1 = MagicMock()
        mock_result1.user_id = 1
        mock_result1.total_score = Decimal("85.5")
        mock_result1.level = "EXCELLENT"

        mock_result2 = MagicMock()
        mock_result2.user_id = 2
        mock_result2.total_score = Decimal("75.0")
        mock_result2.level = "QUALIFIED"

        # Mock 用户信息
        mock_user_obj1 = MagicMock()
        mock_user_obj1.real_name = "张三"
        mock_user_obj1.username = "zhangsan"

        mock_user_obj2 = MagicMock()
        mock_user_obj2.real_name = "李四"
        mock_user_obj2.username = "lisi"

        # Mock 部门
        mock_dept = MagicMock()
        mock_dept.name = "研发部"

        # 设置 mock 返回值
        def query_side_effect(*args):
            mock_query = MagicMock()
            if "PerformancePeriod" in str(args):
                mock_query.filter.return_value.first.return_value = mock_period
            elif "Department" in str(args):
                mock_query.filter.return_value.first.return_value = mock_dept
            elif "User" in str(args):
                # 对于获取成员列表
                mock_query.filter.return_value.all.return_value = [
                    mock_user1,
                    mock_user2,
                ]
                # 对于获取单个用户
                def first_side_effect():
                    # 简化处理，返回第一个用户
                    return mock_user_obj1

                mock_query.filter.return_value.first.side_effect = [
                    mock_user_obj1,
                    mock_user_obj2,
                ]
            elif "PerformanceResult" in str(args):
                mock_query.filter.return_value.all.return_value = [
                    mock_result1,
                    mock_result2,
                ]
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_team_performance(team_id=1, period_id=1)

        self.assertEqual(result["team_id"], 1)
        self.assertEqual(result["team_name"], "研发部")
        self.assertEqual(result["member_count"], 2)
        self.assertEqual(len(result["members"]), 2)
        self.assertGreater(result["avg_score"], 0)

    def test_get_team_performance_no_period(self):
        """测试获取团队绩效（无周期）"""
        # Mock 部门
        mock_dept = MagicMock()
        mock_dept.name = "测试部"

        # Mock 成员
        mock_user1 = MagicMock()
        mock_user1.id = 1

        def query_side_effect(*args):
            mock_query = MagicMock()
            if "PerformancePeriod" in str(args):
                mock_query.filter.return_value.first.return_value = None
            elif "Department" in str(args):
                mock_query.filter.return_value.first.return_value = mock_dept
            elif "User" in str(args):
                mock_query.filter.return_value.all.return_value = [mock_user1]
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_team_performance(team_id=1, period_id=None)

        self.assertEqual(result["team_id"], 1)
        self.assertEqual(result["avg_score"], Decimal("0"))
        self.assertEqual(len(result["members"]), 0)

    def test_get_department_performance_success(self):
        """测试获取部门绩效（成功）"""
        # Mock 周期
        mock_period = MagicMock()
        mock_period.id = 1
        mock_period.period_name = "2024Q2"

        # Mock 部门
        mock_dept = MagicMock()
        mock_dept.name = "产品部"
        mock_dept.id = 5

        # Mock 子部门
        mock_sub_dept = MagicMock()
        mock_sub_dept.id = 51
        mock_sub_dept.name = "产品一组"

        # Mock 成员
        mock_user = MagicMock()
        mock_user.id = 10

        # Mock 绩效结果
        mock_result = MagicMock()
        mock_result.total_score = Decimal("90.0")
        mock_result.level = "EXCELLENT"

        def query_side_effect(*args):
            mock_query = MagicMock()
            if "PerformancePeriod" in str(args):
                mock_query.filter.return_value.first.return_value = mock_period
            elif "Department" in str(args):
                # 判断是获取部门名称还是子部门
                filter_mock = MagicMock()
                filter_mock.first.return_value = mock_dept
                filter_mock.all.return_value = [mock_sub_dept]
                mock_query.filter.return_value = filter_mock
            elif "User" in str(args):
                mock_query.filter.return_value.all.return_value = [mock_user]
            elif "PerformanceResult" in str(args):
                mock_query.filter.return_value.all.return_value = [mock_result]
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_department_performance(dept_id=5, period_id=1)

        self.assertEqual(result["department_id"], 5)
        self.assertEqual(result["department_name"], "产品部")
        self.assertEqual(result["member_count"], 1)
        self.assertGreater(result["avg_score"], 0)
        self.assertEqual(len(result["teams"]), 1)

    def test_get_performance_ranking_company(self):
        """测试获取公司排行榜"""
        # Mock 周期
        mock_period = MagicMock()
        mock_period.id = 1
        mock_period.period_name = "2024Q1"

        # Mock 绩效结果
        mock_result1 = MagicMock()
        mock_result1.user_id = 1
        mock_result1.total_score = Decimal("95.0")
        mock_result1.level = "EXCELLENT"
        mock_result1.department_name = "研发部"

        # Mock 用户
        mock_user = MagicMock()
        mock_user.real_name = "王五"
        mock_user.username = "wangwu"

        def query_side_effect(*args):
            mock_query = MagicMock()
            if "PerformancePeriod" in str(args):
                mock_query.filter.return_value.first.return_value = mock_period
            elif "PerformanceResult" in str(args):
                (
                    mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value
                ) = [mock_result1]
            elif "User" in str(args):
                mock_query.filter.return_value.first.return_value = mock_user
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_performance_ranking(
            ranking_type="COMPANY", period_id=1
        )

        self.assertEqual(result["ranking_type"], "COMPANY")
        self.assertEqual(result["period_id"], 1)
        self.assertEqual(len(result["rankings"]), 1)
        self.assertEqual(result["rankings"][0]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
