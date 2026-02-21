# -*- coding: utf-8 -*-
"""
员工绩效服务单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, call

from fastapi import HTTPException

from app.services.employee_performance.employee_performance_service import (
    EmployeePerformanceService,
)


class TestEmployeePerformanceServiceInit(unittest.TestCase):
    """测试初始化"""

    def test_init(self):
        """测试服务初始化"""
        mock_db = MagicMock()
        service = EmployeePerformanceService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestCheckPerformanceViewPermission(unittest.TestCase):
    """测试查看绩效权限检查"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_superuser_can_view_anyone(self):
        """测试超级管理员可以查看任何人的绩效"""
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

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_non_manager_cannot_view_others(self):
        """测试非管理者不能查看他人绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.roles = []

        target_user = MagicMock()
        target_user.id = 2

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_dept_manager_can_view_same_dept(self):
        """测试部门经理可以查看同部门员工绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # 模拟部门经理角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10

        mock_query = self.mock_db.query.return_value
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

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user
        mock_query.filter.return_value.all.return_value = []  # 没有共同项目

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_pm_can_view_project_member(self):
        """测试项目经理可以查看项目成员绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 20  # 不同部门

        # Mock数据库查询
        mock_project = MagicMock()
        mock_project.id = 100

        # Mock第一次query - 获取target_user
        # Mock第二次query - 获取current_user管理的项目
        # Mock第三次query - 再次获取项目
        # Mock第四次query - 获取task
        mock_task = MagicMock()

        def query_side_effect(*args):
            mock_q = MagicMock()
            # 根据调用次数返回不同结果
            if not hasattr(query_side_effect, "call_count"):
                query_side_effect.call_count = 0
            query_side_effect.call_count += 1

            if query_side_effect.call_count == 1:
                # 第一次: 查询target_user
                mock_q.filter.return_value.first.return_value = target_user
            elif query_side_effect.call_count == 2:
                # 第二次: 查询current_user管理的项目
                mock_q.filter.return_value.all.return_value = [mock_project]
            elif query_side_effect.call_count == 3:
                # 第三次: 再次查询项目
                mock_q.filter.return_value.all.return_value = [mock_project]
            else:
                # 第四次及之后: 查询task
                mock_q.filter.return_value.first.return_value = mock_task

            return mock_q

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_role_name_matching(self):
        """测试通过角色名称匹配"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        role = MagicMock()
        role.role.role_code = None
        role.role.role_name = "department_manager"
        current_user.roles = [role]

        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_target_user_no_department(self):
        """测试目标用户没有部门"""
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
        target_user.department_id = None  # 没有部门

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user
        mock_query.filter.return_value.all.return_value = []

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)


class TestTeamAndDepartmentMembers(unittest.TestCase):
    """测试团队和部门成员获取"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_team_members(self):
        """测试获取团队成员"""
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user2 = MagicMock()
        mock_user2.id = 2

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [mock_user1, mock_user2]

        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """测试获取空团队成员"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = []

        result = self.service.get_team_members(10)
        self.assertEqual(result, [])

    def test_get_department_members(self):
        """测试获取部门成员"""
        mock_user1 = MagicMock()
        mock_user1.id = 101
        mock_user2 = MagicMock()
        mock_user2.id = 102

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [mock_user1, mock_user2]

        result = self.service.get_department_members(20)
        self.assertEqual(result, [101, 102])

    def test_get_department_members_empty(self):
        """测试获取空部门成员"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = []

        result = self.service.get_department_members(20)
        self.assertEqual(result, [])


class TestEvaluatorType(unittest.TestCase):
    """测试评价人类型判断"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

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
        """测试既是部门经理又是项目经理"""
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
        """测试其他类型"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = "employee"
        role.role.role_name = "员工"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_no_roles(self):
        """测试没有角色"""
        user = MagicMock()
        user.roles = []

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_role_name_matching_dept(self):
        """测试通过角色名称匹配部门经理"""
        user = MagicMock()
        role = MagicMock()
        role.role.role_code = None
        role.role.role_name = "department_manager"
        user.roles = [role]

        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")


class TestTeamAndDepartmentNames(unittest.TestCase):
    """测试团队和部门名称获取"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_team_name(self):
        """测试获取团队名称"""
        mock_dept = MagicMock()
        mock_dept.name = "研发部"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_dept

        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """测试获取不存在的团队名称"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        result = self.service.get_team_name(999)
        self.assertEqual(result, "团队999")

    def test_get_department_name(self):
        """测试获取部门名称"""
        mock_dept = MagicMock()
        mock_dept.name = "技术部"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_dept

        result = self.service.get_department_name(20)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_found(self):
        """测试获取不存在的部门名称"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        result = self.service.get_department_name(999)
        self.assertEqual(result, "部门999")


class TestCreateMonthlyWorkSummary(unittest.TestCase):
    """测试创建月度工作总结"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_create_summary_success(self, mock_perf_service):
        """测试成功创建工作总结"""
        current_user = MagicMock()
        current_user.id = 1

        summary_in = MagicMock()
        summary_in.period = "2026-02"
        summary_in.work_content = "完成项目A"
        summary_in.self_evaluation = "表现良好"
        summary_in.highlights = "按时交付"
        summary_in.problems = "无"
        summary_in.next_month_plan = "开始项目B"

        # Mock查询不存在
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        result = self.service.create_monthly_work_summary(current_user, summary_in)

        # 验证add和commit被调用
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        # 验证创建评价任务
        mock_perf_service.create_evaluation_tasks.assert_called_once()

    def test_create_summary_duplicate(self):
        """测试重复创建工作总结"""
        current_user = MagicMock()
        current_user.id = 1

        summary_in = MagicMock()
        summary_in.period = "2026-02"

        # Mock已存在的总结
        existing_summary = MagicMock()
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = existing_summary

        with self.assertRaises(HTTPException) as context:
            self.service.create_monthly_work_summary(current_user, summary_in)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已提交过", context.exception.detail)


class TestSaveMonthlySummaryDraft(unittest.TestCase):
    """测试保存月度工作总结草稿"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_save_new_draft(self):
        """测试保存新草稿"""
        current_user = MagicMock()
        current_user.id = 1

        summary_update = MagicMock()
        summary_update.work_content = "草稿内容"
        summary_update.self_evaluation = "草稿评价"
        summary_update.highlights = None
        summary_update.problems = None
        summary_update.next_month_plan = None

        # Mock不存在草稿
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None

        result = self.service.save_monthly_summary_draft(
            current_user, "2026-02", summary_update
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_update_existing_draft(self):
        """测试更新现有草稿"""
        current_user = MagicMock()
        current_user.id = 1

        summary_update = MagicMock()
        summary_update.work_content = "更新的内容"
        summary_update.self_evaluation = "更新的评价"
        summary_update.highlights = "亮点"
        summary_update.problems = "问题"
        summary_update.next_month_plan = "计划"

        # Mock已存在的草稿
        existing_draft = MagicMock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "旧内容"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = existing_draft

        result = self.service.save_monthly_summary_draft(
            current_user, "2026-02", summary_update
        )

        # 验证字段被更新
        self.assertEqual(existing_draft.work_content, "更新的内容")
        self.assertEqual(existing_draft.self_evaluation, "更新的评价")
        self.mock_db.commit.assert_called_once()

    def test_cannot_update_submitted_summary(self):
        """测试不能更新已提交的总结"""
        current_user = MagicMock()
        current_user.id = 1

        summary_update = MagicMock()
        summary_update.work_content = "更新的内容"

        # Mock已提交的总结
        existing_summary = MagicMock()
        existing_summary.status = "SUBMITTED"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = existing_summary

        with self.assertRaises(HTTPException) as context:
            self.service.save_monthly_summary_draft(
                current_user, "2026-02", summary_update
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只能更新草稿状态", context.exception.detail)

    def test_update_draft_with_none_values(self):
        """测试使用None值更新草稿（不应更新）"""
        current_user = MagicMock()
        current_user.id = 1

        summary_update = MagicMock()
        summary_update.work_content = None
        summary_update.self_evaluation = None
        summary_update.highlights = None
        summary_update.problems = None
        summary_update.next_month_plan = None

        existing_draft = MagicMock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "原内容"

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = existing_draft

        result = self.service.save_monthly_summary_draft(
            current_user, "2026-02", summary_update
        )

        # 验证原内容没有被None覆盖
        self.assertEqual(existing_draft.work_content, "原内容")


class TestGetMonthlySummaryHistory(unittest.TestCase):
    """测试获取历史工作总结"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_history_success(self):
        """测试成功获取历史记录"""
        current_user = MagicMock()
        current_user.id = 1

        # Mock工作总结
        summary1 = MagicMock()
        summary1.id = 1
        summary1.period = "2026-02"
        summary1.status = "COMPLETED"
        summary1.submit_date = datetime(2026, 3, 1)
        summary1.created_at = datetime(2026, 2, 28)

        summary2 = MagicMock()
        summary2.id = 2
        summary2.period = "2026-01"
        summary2.status = "SUBMITTED"
        summary2.submit_date = datetime(2026, 2, 1)
        summary2.created_at = datetime(2026, 1, 31)

        # Mock查询
        mock_query_chain = MagicMock()
        mock_query_chain.filter.return_value = mock_query_chain
        mock_query_chain.order_by.return_value = mock_query_chain
        mock_query_chain.limit.return_value = mock_query_chain
        mock_query_chain.all.return_value = [summary1, summary2]

        # Mock评价数量查询
        def query_side_effect(*args):
            if hasattr(query_side_effect, "call_count"):
                query_side_effect.call_count += 1
            else:
                query_side_effect.call_count = 1

            if query_side_effect.call_count == 1:
                return mock_query_chain
            else:
                # 评价数量查询
                mock_count_query = MagicMock()
                mock_count_query.filter.return_value = mock_count_query
                if query_side_effect.call_count == 2:
                    mock_count_query.count.return_value = 2
                else:
                    mock_count_query.count.return_value = 1
                return mock_count_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_monthly_summary_history(current_user, limit=12)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["period"], "2026-02")
        self.assertEqual(result[0]["evaluation_count"], 2)
        self.assertEqual(result[1]["id"], 2)
        self.assertEqual(result[1]["evaluation_count"], 1)

    def test_get_history_empty(self):
        """测试获取空历史记录"""
        current_user = MagicMock()
        current_user.id = 1

        mock_query_chain = MagicMock()
        mock_query_chain.filter.return_value = mock_query_chain
        mock_query_chain.order_by.return_value = mock_query_chain
        mock_query_chain.limit.return_value = mock_query_chain
        mock_query_chain.all.return_value = []

        self.mock_db.query.return_value = mock_query_chain

        result = self.service.get_monthly_summary_history(current_user, limit=12)
        self.assertEqual(result, [])


class TestGetMyPerformance(unittest.TestCase):
    """测试查看我的绩效"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_performance_no_current_summary(self, mock_perf_service, mock_date):
        """测试当前周期没有工作总结"""
        # Mock当前日期
        mock_date.today.return_value = date(2026, 2, 21)

        current_user = MagicMock()
        current_user.id = 1

        # Mock查询返回None（没有当前周期的总结）
        def query_side_effect(*args):
            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q
            mock_q.first.return_value = None
            return mock_q

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_my_performance(current_user)

        self.assertEqual(result["current_status"]["period"], "2026-02")
        self.assertEqual(result["current_status"]["summary_status"], "NOT_SUBMITTED")
        self.assertIsNone(result["latest_result"])

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_performance_with_current_summary(
        self, mock_perf_service, mock_date
    ):
        """测试有当前周期的工作总结"""
        mock_date.today.return_value = date(2026, 2, 21)

        current_user = MagicMock()
        current_user.id = 1

        # Mock当前周期的工作总结
        current_summary = MagicMock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "SUBMITTED"

        # Mock部门经理评价
        dept_eval = MagicMock()
        dept_eval.status = "COMPLETED"
        dept_eval.evaluator = MagicMock()
        dept_eval.evaluator.real_name = "张经理"
        dept_eval.score = 85

        # Mock项目经理评价
        project_eval = MagicMock()
        project_eval.status = "PENDING"
        project_eval.evaluator = MagicMock()
        project_eval.evaluator.real_name = "李项目经理"
        project_eval.project = MagicMock()
        project_eval.project.project_name = "项目A"
        project_eval.project_weight = 0.3

        # Mock查询
        def query_side_effect(*args):
            if not hasattr(query_side_effect, "call_count"):
                query_side_effect.call_count = 0
            query_side_effect.call_count += 1

            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if query_side_effect.call_count == 1:
                # 获取当前周期工作总结
                mock_q.first.return_value = current_summary
            elif query_side_effect.call_count == 2:
                # 获取部门经理评价
                mock_q.first.return_value = dept_eval
            elif query_side_effect.call_count == 3:
                # 获取项目经理评价
                mock_q.all.return_value = [project_eval]
            else:
                # 其他查询
                mock_q.first.return_value = None
                mock_q.all.return_value = []

            return mock_q

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_my_performance(current_user)

        self.assertEqual(result["current_status"]["period"], "2026-02")
        self.assertEqual(result["current_status"]["summary_status"], "SUBMITTED")
        self.assertEqual(
            result["current_status"]["dept_evaluation"]["status"], "COMPLETED"
        )
        self.assertEqual(
            result["current_status"]["dept_evaluation"]["evaluator"], "张经理"
        )
        self.assertEqual(result["current_status"]["dept_evaluation"]["score"], 85)
        self.assertEqual(len(result["current_status"]["project_evaluations"]), 1)

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    def test_get_performance_with_completed_summary(
        self, mock_perf_service, mock_date
    ):
        """测试已完成的工作总结"""
        mock_date.today.return_value = date(2026, 2, 21)

        current_user = MagicMock()
        current_user.id = 1

        # Mock已完成的工作总结
        current_summary = MagicMock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "COMPLETED"

        # Mock计算结果
        mock_perf_service.calculate_final_score.return_value = {
            "final_score": 88.5,
            "dept_score": 85,
            "project_score": 90,
        }
        mock_perf_service.get_score_level.return_value = "A"
        mock_perf_service.get_historical_performance.return_value = []

        # Mock查询
        def query_side_effect(*args):
            if not hasattr(query_side_effect, "call_count"):
                query_side_effect.call_count = 0
            query_side_effect.call_count += 1

            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if query_side_effect.call_count == 1:
                mock_q.first.return_value = current_summary
            else:
                mock_q.first.return_value = None
                mock_q.all.return_value = []

            return mock_q

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.get_my_performance(current_user)

        self.assertIsNotNone(result["latest_result"])
        self.assertEqual(result["latest_result"]["final_score"], 88.5)
        self.assertEqual(result["latest_result"]["level"], "A")

    @patch("app.services.employee_performance.employee_performance_service.date")
    @patch("app.services.employee_performance.employee_performance_service.PerformanceService")
    @patch("app.services.employee_performance.employee_performance_service.timedelta")
    def test_get_performance_quarterly_trend(
        self, mock_timedelta, mock_perf_service, mock_date
    ):
        """测试季度趋势"""
        mock_date.today.return_value = date(2026, 2, 21)

        # Mock timedelta
        def timedelta_side_effect(days):
            return timedelta(days=days)

        mock_timedelta.side_effect = timedelta_side_effect

        current_user = MagicMock()
        current_user.id = 1

        # Mock历史总结
        past_summary = MagicMock()
        past_summary.id = 99
        past_summary.period = "2026-01"
        past_summary.status = "COMPLETED"

        # Mock查询
        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1

            mock_q = MagicMock()
            mock_q.filter.return_value = mock_q

            if call_count == 1:
                # 当前周期查询
                mock_q.first.return_value = None
            elif call_count in [2, 3, 4]:
                # 季度趋势查询
                if call_count == 2:
                    mock_q.first.return_value = None
                elif call_count == 3:
                    mock_q.first.return_value = past_summary
                else:
                    mock_q.first.return_value = None
            else:
                mock_q.first.return_value = None
                mock_q.all.return_value = []

            return mock_q

        self.mock_db.query.side_effect = query_side_effect

        # Mock计算分数
        mock_perf_service.calculate_final_score.return_value = {"final_score": 85.0}
        mock_perf_service.get_historical_performance.return_value = []

        result = self.service.get_my_performance(current_user)

        # 验证季度趋势
        self.assertIn("quarterly_trend", result)


if __name__ == "__main__":
    unittest.main()
