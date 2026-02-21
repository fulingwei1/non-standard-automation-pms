# -*- coding: utf-8 -*-
"""
项目绩效服务单元测试

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime
from decimal import Decimal

from app.services.project_performance.service import ProjectPerformanceService


class TestProjectPerformanceService(unittest.TestCase):
    """测试项目绩效服务类"""

    def setUp(self):
        """初始化测试"""
        self.db = MagicMock()
        self.service = ProjectPerformanceService(self.db)

    # ========== check_performance_view_permission 测试 ==========

    def test_check_permission_superuser(self):
        """测试超级管理员可以查看所有人"""
        current_user = MagicMock()
        current_user.is_superuser = True
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_check_permission_self(self):
        """测试用户可以查看自己的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 100

        result = self.service.check_performance_view_permission(current_user, 100)
        self.assertTrue(result)

    def test_check_permission_target_user_not_exist(self):
        """测试目标用户不存在"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1

        # Mock数据库查询返回None
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_check_permission_dept_manager_same_dept(self):
        """测试部门经理可以查看本部门员工"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 模拟部门经理角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        # 目标用户
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_permission_dept_manager_different_dept(self):
        """测试部门经理不能查看其他部门员工（无项目关系）"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 模拟部门经理角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        # 目标用户在不同部门
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 20

        # Mock数据库查询
        mock_query = MagicMock()
        
        # 第一次查询：返回目标用户
        mock_query.filter.return_value.first.return_value = target_user
        
        # 第二次查询：返回当前用户管理的项目（空列表）
        mock_query.filter.return_value.all.return_value = []
        
        self.db.query.return_value = mock_query

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_permission_project_manager_can_view_member(self):
        """测试项目经理可以查看项目成员"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 模拟项目经理角色
        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        current_user.roles = [role]

        # 目标用户在不同部门
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 20

        # Mock项目
        project = MagicMock()
        project.id = 100

        # Mock任务
        task = MagicMock()
        task.project_id = 100
        task.owner_id = 2

        # 设置复杂的mock链
        query_results = iter([
            target_user,  # 第一次filter().first() - 获取目标用户
            [project],    # 第一次filter().all() - 获取当前用户管理的项目
            [project],    # 第二次filter().all() - 获取项目列表
            task,         # 第二次filter().first() - 检查成员任务
        ])

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = next(query_results)
            if isinstance(result, list):
                mock_result.all.return_value = result
            else:
                mock_result.first.return_value = result
            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_permission_no_manager_role(self):
        """测试普通员工不能查看其他人"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 普通员工角色
        role = MagicMock()
        role.role.role_code = "employee"
        role.role.role_name = "员工"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_permission_admin_role(self):
        """测试管理员角色可以查看同部门的人"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 管理员角色
        role = MagicMock()
        role.role.role_code = "admin"
        role.role.role_name = "管理员"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10  # 同一部门

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    # ========== get_team_members 测试 ==========

    def test_get_team_members(self):
        """测试获取团队成员"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2

        self.db.query.return_value.filter.return_value.all.return_value = [user1, user2]

        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """测试获取空团队"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_team_members(10)
        self.assertEqual(result, [])

    # ========== get_department_members 测试 ==========

    def test_get_department_members(self):
        """测试获取部门成员"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2
        user3 = MagicMock()
        user3.id = 3

        self.db.query.return_value.filter.return_value.all.return_value = [
            user1,
            user2,
            user3,
        ]

        result = self.service.get_department_members(20)
        self.assertEqual(result, [1, 2, 3])

    def test_get_department_members_empty(self):
        """测试获取空部门"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_department_members(20)
        self.assertEqual(result, [])

    # ========== get_evaluator_type 测试 ==========

    def test_get_evaluator_type_dept_manager(self):
        """测试部门经理类型"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """测试项目经理类型"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_both(self):
        """测试同时是部门经理和项目经理"""
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

    def test_get_evaluator_type_other(self):
        """测试其他类型"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "employee"
        role.role.role_name = "员工"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_get_evaluator_type_no_roles(self):
        """测试无角色"""
        user = MagicMock()
        user.roles = []

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_get_evaluator_type_chinese_role_name(self):
        """测试中文角色名"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = None
        role.role.role_name = "部门经理"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    # ========== get_team_name 测试 ==========

    def test_get_team_name_found(self):
        """测试获取团队名称 - 找到"""
        dept = MagicMock()
        dept.name = "研发部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """测试获取团队名称 - 未找到"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(10)
        self.assertEqual(result, "团队10")

    # ========== get_department_name 测试 ==========

    def test_get_department_name_found(self):
        """测试获取部门名称 - 找到"""
        dept = MagicMock()
        dept.name = "销售部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_department_name(20)
        self.assertEqual(result, "销售部")

    def test_get_department_name_not_found(self):
        """测试获取部门名称 - 未找到"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_department_name(20)
        self.assertEqual(result, "部门20")

    # ========== get_project_performance 测试 ==========

    def test_get_project_performance_project_not_exist(self):
        """测试获取项目绩效 - 项目不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_project_performance(999)

        self.assertEqual(str(context.exception), "项目不存在")

    def test_get_project_performance_period_not_exist(self):
        """测试获取项目绩效 - 周期不存在"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"

        # 创建复杂的mock链
        mock_filter_1 = MagicMock()
        mock_filter_1.first.return_value = project

        mock_filter_2 = MagicMock()
        mock_order_by = MagicMock()
        mock_order_by.first.return_value = None  # 没有周期
        mock_filter_2.order_by.return_value = mock_order_by

        self.db.query.return_value.filter.side_effect = [mock_filter_1, mock_filter_2]

        with self.assertRaises(ValueError) as context:
            self.service.get_project_performance(100)

        self.assertEqual(str(context.exception), "未找到考核周期")

    def test_get_project_performance_success(self):
        """测试获取项目绩效 - 成功"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"

        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"

        user2 = MagicMock()
        user2.id = 2
        user2.real_name = "李四"
        user2.username = "lisi"

        contrib1 = MagicMock()
        contrib1.user_id = 1
        contrib1.contribution_score = Decimal("85.5")
        contrib1.hours_spent = Decimal("120")
        contrib1.task_count = 10

        contrib2 = MagicMock()
        contrib2.user_id = 2
        contrib2.contribution_score = Decimal("75.0")
        contrib2.hours_spent = Decimal("100")
        contrib2.task_count = 8

        # 复杂的mock链
        mock_queries = [
            project,  # 查询项目
            period,  # 查询周期
            [contrib1, contrib2],  # 查询贡献
            user1,  # 查询用户1
            user2,  # 查询用户2
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            if isinstance(result, list):
                mock_result.all.return_value = result
            else:
                mock_result.first.return_value = result

            mock_result.order_by.return_value = mock_result
            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.get_project_performance(100)

        self.assertEqual(result["project_id"], 100)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["period_id"], 1)
        self.assertEqual(result["period_name"], "2024Q1")
        self.assertEqual(result["member_count"], 2)
        self.assertEqual(result["total_contribution_score"], Decimal("160.5"))
        self.assertEqual(len(result["members"]), 2)

        # 验证成员按贡献分排序（从高到低）
        self.assertEqual(result["members"][0]["user_id"], 1)
        self.assertEqual(result["members"][0]["contribution_score"], 85.5)
        self.assertEqual(result["members"][1]["user_id"], 2)
        self.assertEqual(result["members"][1]["contribution_score"], 75.0)

    def test_get_project_performance_with_period_id(self):
        """测试获取项目绩效 - 指定周期ID"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"

        period = MagicMock()
        period.id = 2
        period.period_name = "2024Q2"

        mock_queries = [
            project,  # 查询项目
            period,  # 查询指定周期
            [],  # 空贡献列表
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            if isinstance(result, list):
                mock_result.all.return_value = result
            else:
                mock_result.first.return_value = result

            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.get_project_performance(100, period_id=2)

        self.assertEqual(result["period_id"], 2)
        self.assertEqual(result["member_count"], 0)

    # ========== get_project_progress_report 测试 ==========

    def test_get_project_progress_report_project_not_exist(self):
        """测试获取项目进展报告 - 项目不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_project_progress_report(999)

        self.assertEqual(str(context.exception), "项目不存在")

    def test_get_project_progress_report_success(self):
        """测试获取项目进展报告 - 成功"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 75

        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"

        user2 = MagicMock()
        user2.id = 2
        user2.real_name = None
        user2.username = "lisi"

        task1 = MagicMock()
        task1.id = 1
        task1.task_name = "任务1"
        task1.status = "DONE"
        task1.owner_id = 1
        task1.plan_end = None
        task1.description = "已完成的任务"
        task1.updated_at = datetime(2024, 1, 15, 10, 0, 0)
        task1.created_at = datetime(2024, 1, 1, 10, 0, 0)

        task2 = MagicMock()
        task2.id = 2
        task2.task_name = "任务2"
        task2.status = "IN_PROGRESS"
        task2.owner_id = 2
        task2.plan_end = date(2024, 1, 1)  # 已逾期
        task2.description = "进行中的任务"
        task2.updated_at = datetime(2024, 1, 10, 10, 0, 0)
        task2.created_at = datetime(2024, 1, 5, 10, 0, 0)

        task3 = MagicMock()
        task3.id = 3
        task3.task_name = "任务3"
        task3.status = "DONE"
        task3.owner_id = 1
        task3.plan_end = None
        task3.description = None
        task3.updated_at = datetime(2024, 1, 14, 10, 0, 0)
        task3.created_at = datetime(2024, 1, 2, 10, 0, 0)

        mock_queries = [
            project,  # 查询项目
            [task1, task2, task3],  # 查询任务
            user1,  # 查询用户1
            user2,  # 查询用户2
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            if isinstance(result, list):
                mock_result.all.return_value = result
            else:
                mock_result.first.return_value = result

            return mock_result

        self.db.query.return_value.filter = mock_filter

        report_date = date(2024, 1, 20)
        result = self.service.get_project_progress_report(
            100, report_type="WEEKLY", report_date=report_date
        )

        self.assertEqual(result["project_id"], 100)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["report_type"], "WEEKLY")
        self.assertEqual(result["report_date"], report_date)

        # 验证进度摘要
        progress = result["progress_summary"]
        self.assertEqual(progress["overall_progress"], 75)
        self.assertEqual(progress["completed_tasks"], 2)
        self.assertEqual(progress["total_tasks"], 3)
        self.assertFalse(progress["on_schedule"])  # 有逾期任务

        # 验证成员贡献
        members = result["member_contributions"]
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0]["user_id"], 1)
        self.assertEqual(members[0]["task_count"], 2)
        self.assertEqual(members[1]["user_id"], 2)
        self.assertEqual(members[1]["user_name"], "lisi")  # 使用username

        # 验证关键成果
        achievements = result["key_achievements"]
        self.assertEqual(len(achievements), 2)
        self.assertEqual(achievements[0]["task_name"], "任务1")  # 按更新时间倒序

        # 验证风险和问题
        risks = result["risks_and_issues"]
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0]["type"], "DELAYED_TASK")
        self.assertEqual(risks[0]["task_id"], 2)
        self.assertEqual(risks[0]["severity"], "HIGH")  # 逾期超过7天

    def test_get_project_progress_report_no_tasks(self):
        """测试获取项目进展报告 - 无任务"""
        project = MagicMock()
        project.id = 100
        project.project_name = "空项目"
        project.progress = 0

        mock_queries = [
            project,  # 查询项目
            [],  # 空任务列表
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            if isinstance(result, list):
                mock_result.all.return_value = result
            else:
                mock_result.first.return_value = result

            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.get_project_progress_report(100)

        self.assertEqual(result["progress_summary"]["total_tasks"], 0)
        self.assertEqual(result["progress_summary"]["completed_tasks"], 0)
        self.assertTrue(result["progress_summary"]["on_schedule"])  # 无任务视为按计划
        self.assertEqual(len(result["member_contributions"]), 0)
        self.assertEqual(len(result["key_achievements"]), 0)
        self.assertEqual(len(result["risks_and_issues"]), 0)

    def test_get_project_progress_report_default_date(self):
        """测试获取项目进展报告 - 默认日期"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 50

        mock_queries = [
            project,
            [],
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            if isinstance(result, list):
                mock_result.all.return_value = result
            else:
                mock_result.first.return_value = result

            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.get_project_progress_report(100)

        # 验证使用了当前日期
        self.assertEqual(result["report_date"], datetime.now().date())

    # ========== compare_performance 测试 ==========

    def test_compare_performance_period_not_exist(self):
        """测试绩效对比 - 周期不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        with self.assertRaises(ValueError) as context:
            self.service.compare_performance([1, 2])

        self.assertEqual(str(context.exception), "未找到考核周期")

    def test_compare_performance_success(self):
        """测试绩效对比 - 成功"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"

        user2 = MagicMock()
        user2.id = 2
        user2.real_name = None
        user2.username = "lisi"

        result1 = MagicMock()
        result1.total_score = Decimal("95.5")
        result1.level = "EXCELLENT"
        result1.department_name = "研发部"

        result2 = MagicMock()
        result2.total_score = Decimal("85.0")
        result2.level = "GOOD"
        result2.department_name = "销售部"

        mock_queries = [
            period,  # 查询周期
            user1,  # 查询用户1
            result1,  # 查询结果1
            user2,  # 查询用户2
            result2,  # 查询结果2
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            mock_result.first.return_value = result
            mock_result.order_by.return_value = mock_result

            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.compare_performance([1, 2])

        self.assertEqual(result["period_id"], 1)
        self.assertEqual(result["period_name"], "2024Q1")
        self.assertEqual(len(result["comparison_data"]), 2)

        # 验证第一个用户
        self.assertEqual(result["comparison_data"][0]["user_id"], 1)
        self.assertEqual(result["comparison_data"][0]["user_name"], "张三")
        self.assertEqual(result["comparison_data"][0]["score"], 95.5)
        self.assertEqual(result["comparison_data"][0]["level"], "EXCELLENT")

        # 验证第二个用户
        self.assertEqual(result["comparison_data"][1]["user_id"], 2)
        self.assertEqual(result["comparison_data"][1]["user_name"], "lisi")
        self.assertEqual(result["comparison_data"][1]["score"], 85.0)

    def test_compare_performance_with_period_id(self):
        """测试绩效对比 - 指定周期ID"""
        period = MagicMock()
        period.id = 2
        period.period_name = "2024Q2"

        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"

        mock_queries = [
            period,
            user1,
            None,  # 无绩效结果
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            mock_result.first.return_value = result
            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.compare_performance([1], period_id=2)

        self.assertEqual(result["period_id"], 2)
        self.assertEqual(len(result["comparison_data"]), 1)
        self.assertEqual(result["comparison_data"][0]["score"], 0)  # 无结果默认为0
        self.assertEqual(result["comparison_data"][0]["level"], "QUALIFIED")

    def test_compare_performance_user_not_exist(self):
        """测试绩效对比 - 用户不存在"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        mock_queries = [
            period,
            None,  # 用户不存在
        ]

        query_idx = [0]

        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            result = mock_queries[query_idx[0]]
            query_idx[0] += 1

            mock_result.first.return_value = result
            mock_result.order_by.return_value = mock_result

            return mock_result

        self.db.query.return_value.filter = mock_filter

        result = self.service.compare_performance([999])

        # 用户不存在时会跳过
        self.assertEqual(len(result["comparison_data"]), 0)

    def test_compare_performance_empty_user_list(self):
        """测试绩效对比 - 空用户列表"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"

        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            period
        )

        result = self.service.compare_performance([])

        self.assertEqual(len(result["comparison_data"]), 0)


if __name__ == "__main__":
    unittest.main()
