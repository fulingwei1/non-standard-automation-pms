# -*- coding: utf-8 -*-
"""
员工绩效服务增强单元测试 V2

测试覆盖：
- 权限检查（多场景：自己/部门经理/项目经理/管理员）
- 团队成员管理（团队/部门成员获取）
- 评价人类型判断（部门经理/项目经理/双重角色）
- 团队/部门名称获取
- 月度工作总结（创建/草稿保存/历史查询）
- 绩效查看（当前状态/历史趋势/季度趋势）
- 边界条件和异常处理
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from fastapi import HTTPException

from app.services.employee_performance.employee_performance_service import (
    EmployeePerformanceService,
)


class TestEmployeePerformanceService(unittest.TestCase):
    """员工绩效服务测试基类"""

    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.service = EmployeePerformanceService(self.db)

    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()


class TestInitialization(TestEmployeePerformanceService):
    """测试初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        self.assertIs(self.service.db, self.db)

    def test_init_with_custom_session(self):
        """测试自定义Session初始化"""
        custom_db = MagicMock()
        service = EmployeePerformanceService(custom_db)
        self.assertIs(service.db, custom_db)


class TestCheckPerformanceViewPermission(TestEmployeePerformanceService):
    """测试绩效查看权限检查"""

    def test_permission_superuser(self):
        """测试超级管理员权限"""
        current_user = Mock()
        current_user.is_superuser = True
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_permission_view_own_performance(self):
        """测试查看自己的绩效"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 100

        result = self.service.check_performance_view_permission(current_user, 100)
        self.assertTrue(result)

    def test_permission_target_user_not_found(self):
        """测试目标用户不存在"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1

        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_permission_no_manager_role(self):
        """测试无管理角色用户"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.roles = []

        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 10

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_permission_dept_manager_same_dept(self):
        """测试部门经理查看同部门员工"""
        # 创建角色mock
        role_mock = Mock()
        role_mock.role_code = "dept_manager"
        role_mock.role_name = "部门经理"

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        current_user.roles = [user_role_mock]

        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 10

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_permission_dept_manager_different_dept(self):
        """测试部门经理不能查看其他部门员工"""
        role_mock = Mock()
        role_mock.role_code = "dept_manager"
        role_mock.role_name = "部门经理"

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        current_user.roles = [user_role_mock]

        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 20

        # Mock项目查询返回空
        self.db.query.return_value.filter.return_value.first.return_value = target_user
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_permission_project_manager_with_member(self):
        """测试项目经理查看项目成员"""
        role_mock = Mock()
        role_mock.role_code = "pm"
        role_mock.role_name = "项目经理"

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        current_user.roles = [user_role_mock]

        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 20

        project = Mock()
        project.id = 100

        task = Mock()
        task.project_id = 100
        task.owner_id = 2

        # 复杂的查询链Mock
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value

        # 第一次查询：target_user
        # 第二次查询：user_projects
        # 第三次查询：target_projects
        # 第四次查询：member_task
        filter_mock.first.side_effect = [target_user, task]
        filter_mock.all.side_effect = [[project], [project]]

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_permission_role_code_none(self):
        """测试角色代码为None的情况"""
        role_mock = Mock()
        role_mock.role_code = None
        role_mock.role_name = None

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.roles = [user_role_mock]

        target_user = Mock()
        target_user.id = 2

        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)


class TestGetTeamMembers(TestEmployeePerformanceService):
    """测试获取团队成员"""

    def test_get_team_members_success(self):
        """测试成功获取团队成员"""
        user1 = Mock()
        user1.id = 1
        user2 = Mock()
        user2.id = 2

        self.db.query.return_value.filter.return_value.all.return_value = [user1, user2]

        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """测试团队无成员"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_team_members(10)
        self.assertEqual(result, [])


class TestGetDepartmentMembers(TestEmployeePerformanceService):
    """测试获取部门成员"""

    def test_get_department_members_success(self):
        """测试成功获取部门成员"""
        user1 = Mock()
        user1.id = 10
        user2 = Mock()
        user2.id = 20
        user3 = Mock()
        user3.id = 30

        self.db.query.return_value.filter.return_value.all.return_value = [
            user1,
            user2,
            user3,
        ]

        result = self.service.get_department_members(5)
        self.assertEqual(result, [10, 20, 30])

    def test_get_department_members_empty(self):
        """测试部门无成员"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_department_members(5)
        self.assertEqual(result, [])


class TestGetEvaluatorType(TestEmployeePerformanceService):
    """测试评价人类型判断"""

    def test_evaluator_type_dept_manager(self):
        """测试部门经理类型"""
        role_mock = Mock()
        role_mock.role_code = "dept_manager"
        role_mock.role_name = "部门经理"

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        user = Mock()
        user.roles = [user_role_mock]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_evaluator_type_project_manager(self):
        """测试项目经理类型"""
        role_mock = Mock()
        role_mock.role_code = "pm"
        role_mock.role_name = "项目经理"

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        user = Mock()
        user.roles = [user_role_mock]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_evaluator_type_both(self):
        """测试双重角色（部门+项目经理）"""
        role1_mock = Mock()
        role1_mock.role_code = "dept_manager"
        role1_mock.role_name = "部门经理"

        role2_mock = Mock()
        role2_mock.role_code = "pm"
        role2_mock.role_name = "项目经理"

        user_role1_mock = Mock()
        user_role1_mock.role = role1_mock

        user_role2_mock = Mock()
        user_role2_mock.role = role2_mock

        user = Mock()
        user.roles = [user_role1_mock, user_role2_mock]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_evaluator_type_other(self):
        """测试其他角色"""
        role_mock = Mock()
        role_mock.role_code = "engineer"
        role_mock.role_name = "工程师"

        user_role_mock = Mock()
        user_role_mock.role = role_mock

        user = Mock()
        user.roles = [user_role_mock]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_evaluator_type_no_roles(self):
        """测试无角色"""
        user = Mock()
        user.roles = []

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_evaluator_type_none_roles(self):
        """测试roles为None"""
        user = Mock()
        user.roles = None

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")


class TestGetTeamName(TestEmployeePerformanceService):
    """测试获取团队名称"""

    def test_get_team_name_success(self):
        """测试成功获取团队名称"""
        dept = Mock()
        dept.id = 10
        dept.name = "研发部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """测试团队不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(999)
        self.assertEqual(result, "团队999")


class TestGetDepartmentName(TestEmployeePerformanceService):
    """测试获取部门名称"""

    def test_get_department_name_success(self):
        """测试成功获取部门名称"""
        dept = Mock()
        dept.id = 20
        dept.name = "技术部"

        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_department_name(20)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_found(self):
        """测试部门不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_department_name(888)
        self.assertEqual(result, "部门888")


class TestCreateMonthlyWorkSummary(TestEmployeePerformanceService):
    """测试创建月度工作总结"""

    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_create_summary_success(self, mock_perf_service):
        """测试成功创建工作总结"""
        current_user = Mock()
        current_user.id = 1

        summary_in = Mock()
        summary_in.period = "2026-01"
        summary_in.work_content = "完成项目A"
        summary_in.self_evaluation = "表现良好"
        summary_in.highlights = "创新方案"
        summary_in.problems = "时间紧张"
        summary_in.next_month_plan = "继续优化"

        # Mock不存在现有总结
        self.db.query.return_value.filter.return_value.first.return_value = None

        # Mock新创建的summary
        new_summary = Mock()
        new_summary.id = 100
        new_summary.employee_id = 1
        new_summary.period = "2026-01"
        new_summary.status = "SUBMITTED"

        # 模拟db.refresh行为
        def mock_refresh(obj):
            pass

        self.db.refresh = mock_refresh

        result = self.service.create_monthly_work_summary(current_user, summary_in)

        # 验证调用
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        mock_perf_service.create_evaluation_tasks.assert_called_once_with(
            self.db, unittest.mock.ANY
        )

    def test_create_summary_already_exists(self):
        """测试创建已存在的总结"""
        current_user = Mock()
        current_user.id = 1

        summary_in = Mock()
        summary_in.period = "2026-01"

        # Mock已存在的总结
        existing_summary = Mock()
        existing_summary.id = 50
        existing_summary.period = "2026-01"

        self.db.query.return_value.filter.return_value.first.return_value = (
            existing_summary
        )

        with self.assertRaises(HTTPException) as context:
            self.service.create_monthly_work_summary(current_user, summary_in)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已提交过", context.exception.detail)


class TestSaveMonthlySummaryDraft(TestEmployeePerformanceService):
    """测试保存工作总结草稿"""

    def test_save_draft_create_new(self):
        """测试创建新草稿"""
        current_user = Mock()
        current_user.id = 1

        summary_update = Mock()
        summary_update.work_content = "草稿内容"
        summary_update.self_evaluation = "草稿评价"
        summary_update.highlights = "亮点"
        summary_update.problems = None
        summary_update.next_month_plan = None

        # Mock不存在现有草稿
        self.db.query.return_value.filter.return_value.first.return_value = None

        def mock_refresh(obj):
            pass

        self.db.refresh = mock_refresh

        result = self.service.save_monthly_summary_draft(
            current_user, "2026-02", summary_update
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_save_draft_update_existing(self):
        """测试更新现有草稿"""
        current_user = Mock()
        current_user.id = 1

        summary_update = Mock()
        summary_update.work_content = "更新内容"
        summary_update.self_evaluation = "更新评价"
        summary_update.highlights = "新亮点"
        summary_update.problems = "新问题"
        summary_update.next_month_plan = "新计划"

        # Mock现有草稿
        existing_draft = Mock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "旧内容"

        self.db.query.return_value.filter.return_value.first.return_value = (
            existing_draft
        )

        def mock_refresh(obj):
            pass

        self.db.refresh = mock_refresh

        result = self.service.save_monthly_summary_draft(
            current_user, "2026-02", summary_update
        )

        self.db.commit.assert_called_once()
        self.assertEqual(existing_draft.work_content, "更新内容")
        self.assertEqual(existing_draft.self_evaluation, "更新评价")

    def test_save_draft_non_draft_status(self):
        """测试更新非草稿状态的总结"""
        current_user = Mock()
        current_user.id = 1

        summary_update = Mock()

        # Mock已提交的总结
        submitted_summary = Mock()
        submitted_summary.status = "SUBMITTED"

        self.db.query.return_value.filter.return_value.first.return_value = (
            submitted_summary
        )

        with self.assertRaises(HTTPException) as context:
            self.service.save_monthly_summary_draft(
                current_user, "2026-02", summary_update
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只能更新草稿", context.exception.detail)

    def test_save_draft_partial_update(self):
        """测试部分字段更新"""
        current_user = Mock()
        current_user.id = 1

        summary_update = Mock()
        summary_update.work_content = "新内容"
        summary_update.self_evaluation = None
        summary_update.highlights = None
        summary_update.problems = None
        summary_update.next_month_plan = "新计划"

        existing_draft = Mock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "旧内容"
        existing_draft.self_evaluation = "旧评价"

        self.db.query.return_value.filter.return_value.first.return_value = (
            existing_draft
        )

        def mock_refresh(obj):
            pass

        self.db.refresh = mock_refresh

        result = self.service.save_monthly_summary_draft(
            current_user, "2026-02", summary_update
        )

        # 验证只更新了非None字段
        self.assertEqual(existing_draft.work_content, "新内容")
        self.assertEqual(existing_draft.self_evaluation, "旧评价")  # 未更新


class TestGetMonthlySummaryHistory(TestEmployeePerformanceService):
    """测试查看历史工作总结"""

    def test_get_history_success(self):
        """测试成功获取历史记录"""
        current_user = Mock()
        current_user.id = 1

        # Mock历史总结
        summary1 = Mock()
        summary1.id = 1
        summary1.period = "2026-01"
        summary1.status = "COMPLETED"
        summary1.submit_date = datetime(2026, 2, 1)
        summary1.created_at = datetime(2026, 1, 25)

        summary2 = Mock()
        summary2.id = 2
        summary2.period = "2025-12"
        summary2.status = "SUBMITTED"
        summary2.submit_date = datetime(2026, 1, 1)
        summary2.created_at = datetime(2025, 12, 25)

        # Mock查询
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_mock = filter_mock.order_by.return_value
        order_mock.limit.return_value.all.return_value = [summary1, summary2]

        # Mock评价数量查询
        self.db.query.return_value.filter.return_value.count.side_effect = [3, 2]

        result = self.service.get_monthly_summary_history(current_user, limit=12)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["period"], "2026-01")
        self.assertEqual(result[0]["evaluation_count"], 3)
        self.assertEqual(result[1]["evaluation_count"], 2)

    def test_get_history_empty(self):
        """测试无历史记录"""
        current_user = Mock()
        current_user.id = 1

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_mock = filter_mock.order_by.return_value
        order_mock.limit.return_value.all.return_value = []

        result = self.service.get_monthly_summary_history(current_user, limit=12)

        self.assertEqual(result, [])

    def test_get_history_custom_limit(self):
        """测试自定义查询数量"""
        current_user = Mock()
        current_user.id = 1

        summary = Mock()
        summary.id = 1

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        order_mock = filter_mock.order_by.return_value
        order_mock.limit.return_value.all.return_value = [summary]

        self.db.query.return_value.filter.return_value.count.return_value = 1

        result = self.service.get_monthly_summary_history(current_user, limit=5)

        # 验证limit调用
        order_mock.limit.assert_called_once_with(5)


class TestGetMyPerformance(TestEmployeePerformanceService):
    """测试查看我的绩效"""

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_my_performance_with_current_summary(self, mock_perf_service, mock_date):
        """测试有当前周期总结的情况"""
        # Mock当前日期
        mock_today = date(2026, 2, 15)
        mock_date.today.return_value = mock_today

        current_user = Mock()
        current_user.id = 1

        # Mock当前总结
        current_summary = Mock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "COMPLETED"

        # Mock部门经理评价
        dept_eval = Mock()
        dept_eval.status = "COMPLETED"
        dept_eval.evaluator = Mock(real_name="张经理")
        dept_eval.score = Decimal("85.5")

        # Mock项目评价
        project1 = Mock(project_name="项目A")
        proj_eval1 = Mock()
        proj_eval1.status = "COMPLETED"
        proj_eval1.project = project1
        proj_eval1.evaluator = Mock(real_name="李经理")
        proj_eval1.score = Decimal("90.0")
        proj_eval1.project_weight = Decimal("0.6")

        # 配置查询返回
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value

        # 需要提供足够的返回值：
        # 1. current_summary查询
        # 2. dept_eval查询
        # 3. 3个季度趋势查询 (循环3次)
        filter_mock.first.side_effect = [
            current_summary,  # 当前总结
            dept_eval,        # 部门评价
            None,             # 季度趋势1 (2026-02)
            None,             # 季度趋势2 (2026-01)
            None,             # 季度趋势3 (2025-12)
        ]
        filter_mock.all.side_effect = [[proj_eval1]]

        # Mock绩效计算
        mock_perf_service.calculate_final_score.return_value = {
            "final_score": Decimal("88.0"),
            "dept_score": Decimal("85.5"),
            "project_score": Decimal("90.0"),
        }
        mock_perf_service.get_score_level.return_value = "优秀"
        mock_perf_service.get_historical_performance.return_value = []

        result = self.service.get_my_performance(current_user)

        # 验证结果结构
        self.assertIn("current_status", result)
        self.assertIn("latest_result", result)
        self.assertIn("quarterly_trend", result)
        self.assertIn("history", result)

        # 验证当前状态
        self.assertEqual(result["current_status"]["period"], "2026-02")
        self.assertEqual(result["current_status"]["summary_status"], "COMPLETED")
        self.assertEqual(
            result["current_status"]["dept_evaluation"]["status"], "COMPLETED"
        )

    @patch("app.services.employee_performance.employee_performance_service.date")
    def test_get_my_performance_no_current_summary(self, mock_date):
        """测试无当前周期总结的情况"""
        mock_today = date(2026, 2, 15)
        mock_date.today.return_value = mock_today

        current_user = Mock()
        current_user.id = 1

        # Mock无当前总结
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_my_performance(current_user)

        # 验证默认状态
        self.assertEqual(result["current_status"]["summary_status"], "NOT_SUBMITTED")
        self.assertEqual(
            result["current_status"]["dept_evaluation"]["status"], "PENDING"
        )
        self.assertEqual(result["current_status"]["project_evaluations"], [])
        self.assertIsNone(result["latest_result"])

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_my_performance_dept_eval_none(self, mock_perf_service, mock_date):
        """测试部门经理评价为空的情况"""
        mock_today = date(2026, 2, 15)
        mock_date.today.return_value = mock_today

        current_user = Mock()
        current_user.id = 1

        current_summary = Mock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "SUBMITTED"

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value

        # 需要提供：current_summary, dept_eval, 3个季度趋势查询
        filter_mock.first.side_effect = [
            current_summary,  # 当前总结
            None,            # 部门评价为None
            None,            # 季度趋势1
            None,            # 季度趋势2
            None,            # 季度趋势3
        ]
        filter_mock.all.return_value = []

        mock_perf_service.get_historical_performance.return_value = []

        result = self.service.get_my_performance(current_user)

        # 验证部门评价默认值
        self.assertEqual(
            result["current_status"]["dept_evaluation"]["status"], "PENDING"
        )
        self.assertEqual(result["current_status"]["dept_evaluation"]["evaluator"], "未知")
        self.assertIsNone(result["current_status"]["dept_evaluation"]["score"])

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_my_performance_project_eval_no_project(self, mock_perf_service, mock_date):
        """测试项目评价无项目信息的情况"""
        mock_today = date(2026, 2, 15)
        mock_date.today.return_value = mock_today

        current_user = Mock()
        current_user.id = 1

        current_summary = Mock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "SUBMITTED"

        # Mock项目评价但project为None
        proj_eval = Mock()
        proj_eval.status = "PENDING"
        proj_eval.project = None
        proj_eval.evaluator = None
        proj_eval.score = None
        proj_eval.project_weight = Decimal("0.5")

        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value

        # 需要提供：current_summary, dept_eval, 3个季度趋势查询
        filter_mock.first.side_effect = [
            current_summary,  # 当前总结
            None,            # 部门评价为None
            None,            # 季度趋势1
            None,            # 季度趋势2
            None,            # 季度趋势3
        ]
        filter_mock.all.return_value = [proj_eval]

        mock_perf_service.get_historical_performance.return_value = []

        result = self.service.get_my_performance(current_user)

        # 验证项目评价默认值
        project_evals = result["current_status"]["project_evaluations"]
        self.assertEqual(len(project_evals), 1)
        self.assertEqual(project_evals[0]["project_name"], "未知项目")
        self.assertEqual(project_evals[0]["evaluator"], "未知")


if __name__ == "__main__":
    unittest.main()
