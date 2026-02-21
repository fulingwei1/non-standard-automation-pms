# -*- coding: utf-8 -*-
"""
团队绩效服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, date

from app.services.team_performance.service import TeamPerformanceService


class TestTeamPerformanceServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init(self):
        """测试初始化"""
        mock_db = MagicMock()
        service = TeamPerformanceService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestCheckPerformanceViewPermission(unittest.TestCase):
    """测试权限检查方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_superuser_can_view_all(self):
        """测试超级管理员可以查看所有人的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = True
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_user_can_view_own_performance(self):
        """测试用户可以查看自己的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 100

        result = self.service.check_performance_view_permission(current_user, 100)
        self.assertTrue(result)

    def test_target_user_not_found(self):
        """测试目标用户不存在"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1

        # Mock数据库查询返回None
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_non_manager_cannot_view_others(self):
        """测试非管理角色不能查看他人绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.roles = []

        target_user = MagicMock()
        target_user.id = 2

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_dept_manager_can_view_same_dept(self):
        """测试部门经理可以查看同部门员工绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 设置部门经理角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_dept_manager_cannot_view_different_dept(self):
        """测试部门经理不能查看其他部门员工绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 20  # 不同部门

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = target_user

        # 不在同一项目
        mock_query.filter.return_value.all.return_value = []

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_pm_can_view_project_member(self):
        """测试项目经理可以查看项目成员绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = None

        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = None

        # Mock项目查询
        project = MagicMock()
        project.id = 100
        project.pm_id = 1

        task = MagicMock()
        task.owner_id = 2

        mock_query = MagicMock()
        
        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "User":
                query.filter.return_value.first.return_value = target_user
            elif model.__name__ == "Project":
                query.filter.return_value.all.return_value = [project]
            elif model.__name__ == "Task":
                query.filter.return_value.first.return_value = task
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)


class TestGetTeamMembers(unittest.TestCase):
    """测试获取团队成员"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_team_members(self):
        """测试获取团队成员列表"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [user1, user2]

        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """测试团队无成员"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []

        result = self.service.get_team_members(10)
        self.assertEqual(result, [])


class TestGetDepartmentMembers(unittest.TestCase):
    """测试获取部门成员"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_department_members(self):
        """测试获取部门成员列表"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [user1, user2]

        result = self.service.get_department_members(10)
        self.assertEqual(result, [1, 2])


class TestGetTeamName(unittest.TestCase):
    """测试获取团队名称"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_team_name_exists(self):
        """测试获取存在的团队名称"""
        dept = MagicMock()
        dept.name = "研发部"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = dept

        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_exists(self):
        """测试获取不存在的团队名称"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = self.service.get_team_name(10)
        self.assertEqual(result, "团队10")


class TestGetDepartmentName(unittest.TestCase):
    """测试获取部门名称"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_department_name_exists(self):
        """测试获取存在的部门名称"""
        dept = MagicMock()
        dept.name = "产品部"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = dept

        result = self.service.get_department_name(20)
        self.assertEqual(result, "产品部")

    def test_get_department_name_not_exists(self):
        """测试获取不存在的部门名称"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = self.service.get_department_name(20)
        self.assertEqual(result, "部门20")


class TestGetPeriod(unittest.TestCase):
    """测试获取考核周期"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_period_by_id(self):
        """测试通过ID获取周期"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = period

        result = self.service.get_period(period_id=1)
        self.assertEqual(result, period)

    def test_get_latest_finalized_period(self):
        """测试获取最新的已完成周期"""
        period = MagicMock()
        period.id = 2
        period.period_name = "2024Q2"
        period.status = "FINALIZED"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = period

        result = self.service.get_period(period_id=None)
        self.assertEqual(result, period)

    def test_get_period_not_found(self):
        """测试周期不存在"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = self.service.get_period(period_id=999)
        self.assertIsNone(result)


class TestGetEvaluatorType(unittest.TestCase):
    """测试判断评价人类型"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_dept_manager_type(self):
        """测试部门经理类型"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_project_manager_type(self):
        """测试项目经理类型"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_both_type(self):
        """测试同时拥有两种角色"""
        user = MagicMock()
        role1 = MagicMock()
        role1.role.role_code = "dept_manager"
        role1.role.role_name = "部门经理"
        role2 = MagicMock()
        role2.role.role_code = "pm"
        role2.role.role_name = "项目经理"
        user.roles = [role1, role2]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_other_type(self):
        """测试其他角色"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "employee"
        role.role.role_name = "员工"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_no_roles(self):
        """测试无角色用户"""
        user = MagicMock()
        user.roles = []

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")


class TestGetTeamPerformance(unittest.TestCase):
    """测试获取团队绩效"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_team_performance_success(self):
        """测试成功获取团队绩效"""
        # Mock部门
        dept = MagicMock()
        dept.name = "研发部"

        # Mock周期
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        # Mock成员
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2

        # Mock绩效结果
        result1 = MagicMock()
        result1.user_id = 1
        result1.total_score = Decimal("85.5")
        result1.level = "EXCELLENT"

        result2 = MagicMock()
        result2.user_id = 2
        result2.total_score = Decimal("75.0")
        result2.level = "GOOD"

        # Mock用户
        mock_user1 = MagicMock()
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"

        mock_user2 = MagicMock()
        mock_user2.real_name = "李四"
        mock_user2.username = "lisi"

        # 设置查询返回值
        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "Department":
                query.filter.return_value.first.return_value = dept
            elif model.__name__ == "User":
                if hasattr(query, '_user_call_count'):
                    query._user_call_count += 1
                else:
                    query._user_call_count = 0
                
                # 第一次调用返回user1，第二次返回user2，之后的调用返回user1
                query.filter.return_value.all.return_value = [user1, user2]
                if query._user_call_count % 2 == 0:
                    query.filter.return_value.first.return_value = mock_user1
                else:
                    query.filter.return_value.first.return_value = mock_user2
            elif model.__name__ == "PerformancePeriod":
                query.filter.return_value.first.return_value = period
            elif model.__name__ == "PerformanceResult":
                query.filter.return_value.all.return_value = [result1, result2]
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_team_performance(10, period_id=1)

        self.assertEqual(result["team_id"], 10)
        self.assertEqual(result["team_name"], "研发部")
        self.assertEqual(result["period_id"], 1)
        self.assertEqual(result["period_name"], "2024Q1")
        self.assertEqual(result["member_count"], 2)
        self.assertEqual(result["avg_score"], Decimal("80.25"))
        self.assertEqual(result["max_score"], Decimal("85.5"))
        self.assertEqual(result["min_score"], Decimal("75.0"))
        self.assertEqual(len(result["members"]), 2)

    def test_get_team_performance_no_period(self):
        """测试周期不存在"""
        dept = MagicMock()
        dept.name = "研发部"

        user1 = MagicMock()
        user1.id = 1

        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "Department":
                query.filter.return_value.first.return_value = dept
            elif model.__name__ == "User":
                query.filter.return_value.all.return_value = [user1]
            elif model.__name__ == "PerformancePeriod":
                # 当period_id=None时，会调用order_by
                query.filter.return_value.order_by.return_value.first.return_value = None
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_team_performance(10)

        self.assertEqual(result["team_id"], 10)
        self.assertIsNone(result["period_id"])
        self.assertEqual(result["member_count"], 1)
        self.assertEqual(result["avg_score"], Decimal("0"))

    def test_get_team_performance_no_results(self):
        """测试无绩效结果"""
        dept = MagicMock()
        dept.name = "研发部"

        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        user1 = MagicMock()
        user1.id = 1

        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "Department":
                query.filter.return_value.first.return_value = dept
            elif model.__name__ == "User":
                query.filter.return_value.all.return_value = [user1]
            elif model.__name__ == "PerformancePeriod":
                query.filter.return_value.first.return_value = period
            elif model.__name__ == "PerformanceResult":
                query.filter.return_value.all.return_value = []
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_team_performance(10, period_id=1)

        self.assertEqual(result["member_count"], 1)
        self.assertEqual(result["avg_score"], Decimal("0"))
        self.assertEqual(len(result["members"]), 0)


class TestGetDepartmentPerformance(unittest.TestCase):
    """测试获取部门绩效"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_department_performance_success(self):
        """测试成功获取部门绩效"""
        dept = MagicMock()
        dept.name = "研发部"

        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        user1 = MagicMock()
        user1.id = 1

        result1 = MagicMock()
        result1.total_score = Decimal("85.0")
        result1.level = "EXCELLENT"
        result1.department_id = 10

        sub_dept = MagicMock()
        sub_dept.id = 101
        sub_dept.name = "后端组"

        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "Department":
                query.filter.return_value.first.return_value = dept
                query.filter.return_value.all.return_value = [sub_dept]
            elif model.__name__ == "User":
                query.filter.return_value.all.return_value = [user1]
            elif model.__name__ == "PerformancePeriod":
                query.filter.return_value.first.return_value = period
            elif model.__name__ == "PerformanceResult":
                query.filter.return_value.all.return_value = [result1]
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_department_performance(10, period_id=1)

        self.assertEqual(result["department_id"], 10)
        self.assertEqual(result["department_name"], "研发部")
        self.assertEqual(result["avg_score"], Decimal("85.0"))
        self.assertEqual(len(result["teams"]), 1)

    def test_get_department_performance_no_period(self):
        """测试周期不存在"""
        dept = MagicMock()
        dept.name = "研发部"

        user1 = MagicMock()
        user1.id = 1

        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "Department":
                query.filter.return_value.first.return_value = dept
            elif model.__name__ == "User":
                query.filter.return_value.all.return_value = [user1]
            elif model.__name__ == "PerformancePeriod":
                # 当period_id=None时，会调用order_by
                query.filter.return_value.order_by.return_value.first.return_value = None
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_department_performance(10)
        self.assertIsNone(result)


class TestGetPerformanceRanking(unittest.TestCase):
    """测试获取绩效排行榜"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_get_company_ranking(self):
        """测试公司排行榜"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        result1 = MagicMock()
        result1.user_id = 1
        result1.total_score = Decimal("95.0")
        result1.level = "EXCELLENT"
        result1.department_name = "研发部"

        result2 = MagicMock()
        result2.user_id = 2
        result2.total_score = Decimal("85.0")
        result2.level = "GOOD"
        result2.department_name = "产品部"

        user1 = MagicMock()
        user1.real_name = "张三"
        user1.username = "zhangsan"

        user2 = MagicMock()
        user2.real_name = "李四"
        user2.username = "lisi"

        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "PerformancePeriod":
                query.filter.return_value.first.return_value = period
            elif model.__name__ == "PerformanceResult":
                query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                    result1,
                    result2,
                ]
            elif model.__name__ == "User":
                # 交替返回user1和user2
                if not hasattr(query, '_call_count'):
                    query._call_count = 0
                query._call_count += 1
                if query._call_count % 2 == 1:
                    query.filter.return_value.first.return_value = user1
                else:
                    query.filter.return_value.first.return_value = user2
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_performance_ranking("COMPANY", period_id=1)

        self.assertEqual(result["ranking_type"], "COMPANY")
        self.assertEqual(len(result["rankings"]), 2)
        self.assertEqual(result["rankings"][0]["rank"], 1)
        self.assertEqual(result["rankings"][0]["score"], 95.0)

    def test_get_team_ranking(self):
        """测试团队排行榜"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        dept1 = MagicMock()
        dept1.id = 10
        dept1.name = "研发部"

        dept2 = MagicMock()
        dept2.id = 20
        dept2.name = "产品部"

        result1 = MagicMock()
        result1.total_score = Decimal("90.0")
        result1.department_id = 10

        result2 = MagicMock()
        result2.total_score = Decimal("80.0")
        result2.department_id = 20

        def mock_query_side_effect(model):
            query = MagicMock()
            if model.__name__ == "PerformancePeriod":
                query.filter.return_value.first.return_value = period
            elif model.__name__ == "Department":
                query.all.return_value = [dept1, dept2]
            elif model.__name__ == "PerformanceResult":
                # 根据department_id返回不同结果
                filter_chain = query.filter.return_value
                filter_chain.all.side_effect = [
                    [result1],  # dept1的结果
                    [result2],  # dept2的结果
                ]
            return query

        self.mock_db.query.side_effect = mock_query_side_effect

        result = self.service.get_performance_ranking("TEAM", period_id=1)

        self.assertEqual(result["ranking_type"], "TEAM")
        self.assertEqual(len(result["rankings"]), 2)
        self.assertEqual(result["rankings"][0]["rank"], 1)
        self.assertEqual(result["rankings"][0]["entity_name"], "研发部")

    def test_get_ranking_no_period(self):
        """测试周期不存在"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        # 当period_id=None时，会调用order_by
        mock_query.filter.return_value.order_by.return_value.first.return_value = None

        result = self.service.get_performance_ranking("COMPANY")
        self.assertIsNone(result)


class TestEmptyTeamPerformance(unittest.TestCase):
    """测试_empty_team_performance私有方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TeamPerformanceService(self.mock_db)

    def test_empty_team_performance(self):
        """测试空团队绩效数据生成"""
        result = self.service._empty_team_performance(10, "研发部", [1, 2, 3])

        self.assertEqual(result["team_id"], 10)
        self.assertEqual(result["team_name"], "研发部")
        self.assertIsNone(result["period_id"])
        self.assertIsNone(result["period_name"])
        self.assertEqual(result["member_count"], 3)
        self.assertEqual(result["avg_score"], Decimal("0"))
        self.assertEqual(result["max_score"], Decimal("0"))
        self.assertEqual(result["min_score"], Decimal("0"))
        self.assertEqual(result["level_distribution"], {})
        self.assertEqual(result["members"], [])


if __name__ == "__main__":
    unittest.main()
