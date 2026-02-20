# -*- coding: utf-8 -*-
"""
员工绩效服务单元测试
测试 EmployeePerformanceService 的核心业务逻辑
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.employee_performance import EmployeePerformanceService


class TestEmployeePerformanceService(unittest.TestCase):
    """测试 EmployeePerformanceService"""

    def setUp(self):
        """测试前置设置"""
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_check_performance_view_permission_superuser(self):
        """测试超级管理员有权限查看所有人绩效"""
        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_user.id = 1

        result = self.service.check_performance_view_permission(mock_user, 2)
        self.assertTrue(result)

    def test_check_performance_view_permission_self(self):
        """测试用户可以查看自己的绩效"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        result = self.service.check_performance_view_permission(mock_user, 1)
        self.assertTrue(result)

    def test_check_performance_view_permission_no_permission(self):
        """测试用户无权限查看其他人绩效"""
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_user.roles = []
        mock_user.department_id = 1

        mock_target_user = MagicMock()
        mock_target_user.department_id = 2

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_target_user
        )

        result = self.service.check_performance_view_permission(mock_user, 2)
        self.assertFalse(result)

    def test_get_team_members(self):
        """测试获取团队成员ID列表"""
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

    def test_get_department_members(self):
        """测试获取部门成员ID列表"""
        mock_user1 = MagicMock()
        mock_user1.id = 10
        mock_user2 = MagicMock()
        mock_user2.id = 20

        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_user1,
            mock_user2,
        ]

        result = self.service.get_department_members(1)
        self.assertEqual(result, [10, 20])

    def test_get_team_name(self):
        """测试获取团队名称"""
        mock_dept = MagicMock()
        mock_dept.name = "技术部"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_dept
        )

        result = self.service.get_team_name(1)
        self.assertEqual(result, "技术部")

    def test_get_department_name(self):
        """测试获取部门名称"""
        mock_dept = MagicMock()
        mock_dept.name = "产品部"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_dept
        )

        result = self.service.get_department_name(2)
        self.assertEqual(result, "产品部")

    def test_create_monthly_work_summary_success(self):
        """测试成功创建月度工作总结"""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_summary_in = MagicMock()
        mock_summary_in.period = "2025-01"
        mock_summary_in.work_content = "完成了XXX工作"
        mock_summary_in.self_evaluation = "表现良好"
        mock_summary_in.highlights = "亮点内容"
        mock_summary_in.problems = "问题描述"
        mock_summary_in.next_month_plan = "下月计划"

        # Mock 查询返回 None（不存在）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.services.employee_performance.employee_performance_service.PerformanceService"
        ) as mock_perf_service:
            mock_perf_service.create_evaluation_tasks = MagicMock()

            result = self.service.create_monthly_work_summary(mock_user, mock_summary_in)

            # 验证调用了 add 和 commit
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()

    def test_create_monthly_work_summary_already_exists(self):
        """测试创建月度工作总结时已存在"""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_summary_in = MagicMock()
        mock_summary_in.period = "2025-01"

        # Mock 查询返回已存在的记录
        mock_existing = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing
        )

        with self.assertRaises(HTTPException) as context:
            self.service.create_monthly_work_summary(mock_user, mock_summary_in)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已提交过", context.exception.detail)

    def test_save_monthly_summary_draft_create_new(self):
        """测试保存新草稿"""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_summary_update = MagicMock()
        mock_summary_update.work_content = "草稿内容"
        mock_summary_update.self_evaluation = "自评草稿"
        mock_summary_update.highlights = None
        mock_summary_update.problems = None
        mock_summary_update.next_month_plan = None

        # Mock 查询返回 None（不存在）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.save_monthly_summary_draft(
            mock_user, "2025-02", mock_summary_update
        )

        # 验证调用了 add 和 commit
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_save_monthly_summary_draft_update_existing(self):
        """测试更新已存在的草稿"""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_summary_update = MagicMock()
        mock_summary_update.work_content = "更新后的内容"
        mock_summary_update.self_evaluation = None
        mock_summary_update.highlights = None
        mock_summary_update.problems = None
        mock_summary_update.next_month_plan = None

        # Mock 已存在的草稿
        mock_existing = MagicMock()
        mock_existing.status = "DRAFT"
        mock_existing.work_content = "旧内容"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing
        )

        result = self.service.save_monthly_summary_draft(
            mock_user, "2025-02", mock_summary_update
        )

        # 验证调用了 commit（不应该调用 add）
        self.mock_db.commit.assert_called_once()
        self.assertEqual(mock_existing.work_content, "更新后的内容")

    def test_save_monthly_summary_draft_non_draft_status(self):
        """测试尝试更新非草稿状态的总结"""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_summary_update = MagicMock()

        # Mock 已提交的记录
        mock_existing = MagicMock()
        mock_existing.status = "SUBMITTED"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_existing
        )

        with self.assertRaises(HTTPException) as context:
            self.service.save_monthly_summary_draft(
                mock_user, "2025-02", mock_summary_update
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只能更新草稿状态", context.exception.detail)

    def test_get_monthly_summary_history(self):
        """测试获取历史工作总结"""
        mock_user = MagicMock()
        mock_user.id = 1

        mock_summary1 = MagicMock()
        mock_summary1.id = 10
        mock_summary1.period = "2025-01"
        mock_summary1.status = "COMPLETED"
        mock_summary1.submit_date = datetime(2025, 2, 1)
        mock_summary1.created_at = datetime(2025, 1, 15)

        mock_summary2 = MagicMock()
        mock_summary2.id = 20
        mock_summary2.period = "2024-12"
        mock_summary2.status = "DRAFT"
        mock_summary2.submit_date = None
        mock_summary2.created_at = datetime(2024, 12, 15)

        # Mock 查询返回列表
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_summary1,
            mock_summary2,
        ]

        # Mock count 查询
        self.mock_db.query.return_value.filter.return_value.count.side_effect = [
            2,
            0,
        ]  # 第一个2个评价，第二个0个

        result = self.service.get_monthly_summary_history(mock_user, limit=12)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 10)
        self.assertEqual(result[0]["evaluation_count"], 2)
        self.assertEqual(result[1]["id"], 20)
        self.assertEqual(result[1]["evaluation_count"], 0)

    def test_get_my_performance_no_summary(self):
        """测试查看我的绩效（无提交记录）"""
        mock_user = MagicMock()
        mock_user.id = 1

        # Mock 查询返回 None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.services.employee_performance.employee_performance_service.PerformanceService"
        ) as mock_perf_service:
            mock_perf_service.get_historical_performance.return_value = []

            result = self.service.get_my_performance(mock_user)

            self.assertIn("current_status", result)
            self.assertEqual(result["current_status"]["summary_status"], "NOT_SUBMITTED")
            self.assertIsNone(result["latest_result"])

    def test_get_evaluator_type_dept_manager(self):
        """测试判断评价人类型为部门经理"""
        mock_user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        mock_user.roles = [mock_role]

        result = self.service.get_evaluator_type(mock_user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """测试判断评价人类型为项目经理"""
        mock_user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = "项目经理"
        mock_user.roles = [mock_role]

        result = self.service.get_evaluator_type(mock_user)
        self.assertEqual(result, "PROJECT_MANAGER")


if __name__ == "__main__":
    unittest.main()
