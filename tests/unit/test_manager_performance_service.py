# -*- coding: utf-8 -*-
"""
经理绩效服务单元测试

策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行（不要mock业务方法）
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from app.services.manager_performance.manager_performance_service import (
    ManagerPerformanceService,
)
from app.schemas.performance import PerformanceEvaluationRecordCreate


class TestManagerPerformanceService(unittest.TestCase):
    """测试经理绩效服务类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ManagerPerformanceService(self.db)

    # ========== check_performance_view_permission() 测试 ==========

    def test_check_permission_superuser(self):
        """测试超级管理员权限"""
        current_user = MagicMock()
        current_user.is_superuser = True

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_check_permission_self(self):
        """测试查看自己的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1

        result = self.service.check_performance_view_permission(current_user, 1)
        self.assertTrue(result)

    def test_check_permission_target_user_not_found(self):
        """测试目标用户不存在"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1

        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_check_permission_dept_manager_same_dept(self):
        """测试部门经理查看本部门员工"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # Mock角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        # Mock目标用户
        target_user = MagicMock()
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

        # Mock角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        # Mock目标用户（不同部门）
        target_user = MagicMock()
        target_user.department_id = 20
        self.db.query.return_value.filter.return_value.first.return_value = target_user

        # Mock项目查询：无项目
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_permission_project_manager_with_member(self):
        """测试项目经理查看项目成员"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # Mock角色
        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        current_user.roles = [role]

        # Mock目标用户（不同部门）
        target_user = MagicMock()
        target_user.department_id = 20

        # Mock项目查询
        project = MagicMock()
        project.id = 100

        # 需要按调用顺序设置mock
        mock_query = MagicMock()

        # 第一次query: 目标用户
        mock_first_call = MagicMock()
        mock_first_call.filter.return_value.first.return_value = target_user

        # 第二次query: 用户项目
        mock_second_call = MagicMock()
        mock_second_call.filter.return_value.all.return_value = [project]

        # 第三次query: 项目列表
        mock_third_call = MagicMock()
        mock_third_call.filter.return_value.all.return_value = [project]

        # 第四次query: 成员任务
        task = MagicMock()
        mock_fourth_call = MagicMock()
        mock_fourth_call.filter.return_value.first.return_value = task

        self.db.query.side_effect = [
            mock_first_call,
            mock_second_call,
            mock_third_call,
            mock_fourth_call,
        ]

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_permission_no_manager_role(self):
        """测试无管理角色"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10

        # Mock普通角色
        role = MagicMock()
        role.role.role_code = "employee"
        role.role.role_name = "员工"
        current_user.roles = [role]

        # Mock目标用户
        target_user = MagicMock()
        target_user.department_id = 20
        self.db.query.return_value.filter.return_value.first.return_value = target_user

        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    # ========== get_team_members() 测试 ==========

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
        """测试空团队"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service.get_team_members(10)
        self.assertEqual(result, [])

    # ========== get_department_members() 测试 ==========

    def test_get_department_members(self):
        """测试获取部门成员"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2

        self.db.query.return_value.filter.return_value.all.return_value = [user1, user2]

        result = self.service.get_department_members(10)
        self.assertEqual(result, [1, 2])

    # ========== get_evaluator_type() 测试 ==========

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
        """测试双重角色"""
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
        """测试其他角色"""
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

    # ========== get_team_name() 测试 ==========

    def test_get_team_name_found(self):
        """测试获取团队名称"""
        dept = MagicMock()
        dept.name = "研发部"
        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """测试团队不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_team_name(10)
        self.assertEqual(result, "团队10")

    # ========== get_department_name() 测试 ==========

    def test_get_department_name_found(self):
        """测试获取部门名称"""
        dept = MagicMock()
        dept.name = "技术部"
        self.db.query.return_value.filter.return_value.first.return_value = dept

        result = self.service.get_department_name(10)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_found(self):
        """测试部门不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.get_department_name(10)
        self.assertEqual(result, "部门10")

    # ========== get_evaluation_tasks() 测试 ==========

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_not_manager(self, mock_perf_service):
        """测试非经理角色获取评价任务"""
        current_user = MagicMock()
        mock_perf_service.get_manageable_employees.return_value = []

        result = self.service.get_evaluation_tasks(current_user)

        self.assertEqual(result["total"], 0)
        self.assertEqual(result["pending_count"], 0)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(result["tasks"], [])

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_pending(self, mock_perf_service):
        """测试有待评价任务"""
        current_user = MagicMock()
        current_user.id = 1

        mock_perf_service.get_manageable_employees.return_value = [2, 3]
        mock_perf_service.get_user_manager_roles.return_value = None

        # Mock summary
        summary = MagicMock()
        summary.id = 100
        summary.employee_id = 2
        summary.period = "2026-02"
        summary.status = "SUBMITTED"
        summary.submit_date = date(2026, 2, 28)

        employee = MagicMock()
        employee.real_name = "张三"
        employee.department = "研发部"  # Mock为字符串而不是MagicMock
        summary.employee = employee

        # Mock query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [summary]
        mock_query.filter.return_value = mock_filter

        # Mock evaluation query (无评价记录)
        mock_eval_query = MagicMock()
        mock_eval_filter = MagicMock()
        mock_eval_filter.first.return_value = None
        mock_eval_query.filter.return_value = mock_eval_filter

        self.db.query.side_effect = [mock_query, mock_eval_query]

        result = self.service.get_evaluation_tasks(current_user)

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["pending_count"], 1)
        self.assertEqual(result["completed_count"], 0)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0].employee_name, "张三")
        self.assertEqual(result["tasks"][0].status, "PENDING")

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_completed(self, mock_perf_service):
        """测试已完成评价任务"""
        current_user = MagicMock()
        current_user.id = 1

        mock_perf_service.get_manageable_employees.return_value = [2]
        mock_perf_service.get_user_manager_roles.return_value = None

        # Mock summary
        summary = MagicMock()
        summary.id = 100
        summary.employee_id = 2
        summary.period = "2026-02"
        summary.status = "COMPLETED"
        summary.submit_date = date(2026, 2, 28)

        employee = MagicMock()
        employee.real_name = "李四"
        employee.department = "技术部"  # Mock为字符串
        summary.employee = employee

        # Mock evaluation (已完成)
        evaluation = MagicMock()
        evaluation.status = "COMPLETED"
        evaluation.evaluator_type = "DEPT_MANAGER"

        # Mock query chains
        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.all.return_value = [summary]

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = evaluation

        self.db.query.side_effect = [mock_summary_query, mock_eval_query]

        result = self.service.get_evaluation_tasks(current_user)

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["pending_count"], 0)
        self.assertEqual(result["completed_count"], 1)

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_status_filter(self, mock_perf_service):
        """测试状态筛选"""
        current_user = MagicMock()
        current_user.id = 1

        mock_perf_service.get_manageable_employees.return_value = [2, 3]
        mock_perf_service.get_user_manager_roles.return_value = None

        # Mock 2个summary
        summary1 = MagicMock()
        summary1.id = 100
        summary1.employee_id = 2
        summary1.period = "2026-02"
        summary1.status = "SUBMITTED"
        summary1.submit_date = date(2026, 2, 28)
        summary1.employee = MagicMock()
        summary1.employee.real_name = "张三"
        summary1.employee.department = "研发部"  # 字符串

        summary2 = MagicMock()
        summary2.id = 101
        summary2.employee_id = 3
        summary2.period = "2026-02"
        summary2.status = "COMPLETED"
        summary2.submit_date = date(2026, 2, 28)
        summary2.employee = MagicMock()
        summary2.employee.real_name = "李四"
        summary2.employee.department = "技术部"  # 字符串

        # Mock evaluations
        eval_completed = MagicMock()
        eval_completed.status = "COMPLETED"
        eval_completed.evaluator_type = "DEPT_MANAGER"

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.all.return_value = [summary1, summary2]

        mock_eval_query1 = MagicMock()
        mock_eval_query1.filter.return_value.first.return_value = None  # pending

        mock_eval_query2 = MagicMock()
        mock_eval_query2.filter.return_value.first.return_value = eval_completed

        self.db.query.side_effect = [
            mock_summary_query,
            mock_eval_query1,
            mock_eval_query2,
        ]

        # 只返回PENDING的
        result = self.service.get_evaluation_tasks(current_user, status_filter="PENDING")

        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0].employee_name, "张三")

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_tasks_with_project_evaluation(self, mock_perf_service):
        """测试项目评价类型"""
        current_user = MagicMock()
        current_user.id = 1

        mock_perf_service.get_manageable_employees.return_value = [2]
        mock_perf_service.get_user_manager_roles.return_value = None

        summary = MagicMock()
        summary.id = 100
        summary.employee_id = 2
        summary.period = "2026-02"
        summary.status = "SUBMITTED"
        summary.submit_date = date(2026, 2, 28)
        summary.employee = MagicMock()
        summary.employee.real_name = "王五"
        summary.employee.department = "项目部"  # 字符串

        # Mock项目评价
        evaluation = MagicMock()
        evaluation.status = "COMPLETED"
        evaluation.evaluator_type = "PROJECT_MANAGER"
        evaluation.project_id = 200

        # Mock项目
        project = MagicMock()
        project.project_name = "测试项目"

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.all.return_value = [summary]

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = evaluation

        # Mock项目查询 - 修复StopIteration
        mock_project_query = MagicMock()
        mock_project_query.get.return_value = project

        self.db.query.side_effect = [mock_summary_query, mock_eval_query, mock_project_query]

        result = self.service.get_evaluation_tasks(current_user)

        task = result["tasks"][0]
        self.assertEqual(task.evaluation_type, "project")
        self.assertEqual(task.project_id, 200)
        self.assertEqual(task.project_name, "测试项目")

    # ========== get_evaluation_detail() 测试 ==========

    @patch("app.services.manager_performance.manager_performance_service.PerformanceService")
    def test_get_evaluation_detail_success(self, mock_perf_service):
        """测试获取评价详情"""
        current_user = MagicMock()
        current_user.id = 1

        # Mock summary
        summary = MagicMock()
        summary.id = 100
        summary.employee_id = 2

        employee = MagicMock()
        employee.id = 2
        employee.real_name = "张三"
        employee.username = "zhangsan"
        employee.department = MagicMock()
        employee.position = "高级工程师"
        summary.employee = employee

        # Mock historical performance
        mock_perf_service.get_historical_performance.return_value = []

        # Mock evaluation
        evaluation = MagicMock()
        evaluation.summary_id = 100
        evaluation.evaluator_id = 1

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.first.return_value = summary

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = evaluation

        self.db.query.side_effect = [mock_summary_query, mock_eval_query]

        result = self.service.get_evaluation_detail(current_user, 100)

        self.assertEqual(result["summary"], summary)
        self.assertEqual(result["employee_info"]["id"], 2)
        self.assertEqual(result["employee_info"]["name"], "张三")
        self.assertEqual(result["my_evaluation"], evaluation)

    def test_get_evaluation_detail_not_found(self):
        """测试工作总结不存在"""
        current_user = MagicMock()

        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.get_evaluation_detail(current_user, 999)

        self.assertIn("工作总结不存在", str(context.exception))

    # ========== submit_evaluation() 测试 ==========

    def test_submit_evaluation_summary_not_found(self):
        """测试提交评价-总结不存在"""
        current_user = MagicMock()
        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85,
            comment="表现良好，工作认真负责，态度积极主动。",
        )

        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(current_user, 999, evaluation_in)

        self.assertIn("工作总结不存在", str(context.exception))

    def test_submit_evaluation_already_completed(self):
        """测试重复提交已完成的评价"""
        current_user = MagicMock()
        current_user.id = 1
        
        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85,
            comment="表现良好，工作认真负责，态度积极主动。",
        )

        summary = MagicMock()
        summary.id = 100

        # Mock已完成的评价
        existing_eval = MagicMock()
        existing_eval.status = "COMPLETED"

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.first.return_value = summary

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = existing_eval

        self.db.query.side_effect = [mock_summary_query, mock_eval_query]

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(current_user, 100, evaluation_in)

        self.assertIn("已完成该评价", str(context.exception))

    def test_submit_evaluation_create_new(self):
        """测试创建新评价"""
        current_user = MagicMock()
        current_user.id = 1

        # Mock角色
        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85,
            comment="表现良好，工作认真负责，态度积极主动。",
            project_id=None,
            project_weight=None,
        )

        summary = MagicMock()
        summary.id = 100
        summary.status = "SUBMITTED"

        # 无现有评价
        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.first.return_value = summary

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = None

        # Mock所有评价查询
        mock_all_eval_query = MagicMock()
        new_eval = MagicMock()
        new_eval.status = "COMPLETED"
        mock_all_eval_query.filter.return_value.all.return_value = [new_eval]

        self.db.query.side_effect = [
            mock_summary_query,
            mock_eval_query,
            mock_all_eval_query,
        ]

        result = self.service.submit_evaluation(current_user, 100, evaluation_in)

        # 验证add被调用
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    def test_submit_evaluation_update_existing(self):
        """测试更新现有评价"""
        current_user = MagicMock()
        current_user.id = 1

        # Mock角色
        role = MagicMock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        current_user.roles = [role]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=90,
            comment="工作表现优秀，超额完成任务指标。",
            project_id=200,
            project_weight=80,  # 整数0-100
        )

        summary = MagicMock()
        summary.id = 100
        summary.status = "EVALUATING"

        # Mock现有评价（未完成）
        existing_eval = MagicMock()
        existing_eval.status = "PENDING"
        existing_eval.score = 80
        existing_eval.comment = "旧评价"

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.first.return_value = summary

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = existing_eval

        # Mock所有评价查询（还有其他未完成的）
        other_eval = MagicMock()
        other_eval.status = "PENDING"
        mock_all_eval_query = MagicMock()
        mock_all_eval_query.filter.return_value.all.return_value = [
            existing_eval,
            other_eval,
        ]

        self.db.query.side_effect = [
            mock_summary_query,
            mock_eval_query,
            mock_all_eval_query,
        ]

        result = self.service.submit_evaluation(current_user, 100, evaluation_in)

        # 验证评价被更新
        self.assertEqual(existing_eval.score, 90)
        self.assertEqual(existing_eval.comment, "工作表现优秀，超额完成任务指标。")
        self.assertEqual(existing_eval.project_id, 200)
        self.assertEqual(existing_eval.project_weight, 80)
        self.assertEqual(existing_eval.status, "COMPLETED")

        # summary应保持EVALUATING（因为还有未完成的评价）
        self.assertEqual(summary.status, "EVALUATING")

        self.db.commit.assert_called_once()

    def test_submit_evaluation_complete_all(self):
        """测试所有评价完成后更新summary状态"""
        current_user = MagicMock()
        current_user.id = 1

        role = MagicMock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]

        evaluation_in = PerformanceEvaluationRecordCreate(
            score=85,
            comment="表现良好，工作认真负责，态度积极主动。",
        )

        summary = MagicMock()
        summary.id = 100
        summary.status = "EVALUATING"

        # Mock现有评价
        existing_eval = MagicMock()
        existing_eval.status = "PENDING"

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value.first.return_value = summary

        mock_eval_query = MagicMock()
        mock_eval_query.filter.return_value.first.return_value = existing_eval

        # Mock所有评价都已完成
        mock_all_eval_query = MagicMock()
        mock_all_eval_query.filter.return_value.all.return_value = [existing_eval]

        self.db.query.side_effect = [
            mock_summary_query,
            mock_eval_query,
            mock_all_eval_query,
        ]

        result = self.service.submit_evaluation(current_user, 100, evaluation_in)

        # summary应该变为COMPLETED
        self.assertEqual(summary.status, "COMPLETED")
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
