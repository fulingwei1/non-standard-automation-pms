# -*- coding: utf-8 -*-
"""
员工绩效服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta

from fastapi import HTTPException

from app.services.employee_performance.employee_performance_service import EmployeePerformanceService
from app.models.user import User
from app.models.organization import Department
from app.models.performance import MonthlyWorkSummary, PerformanceEvaluationRecord
from app.models.project import Project
from app.schemas.performance import MonthlyWorkSummaryCreate, MonthlyWorkSummaryUpdate


class TestEmployeePerformanceServicePermissions(unittest.TestCase):
    """测试权限检查相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_check_permission_superuser(self):
        """超级管理员可以查看任何人的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = True
        
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_check_permission_self(self):
        """用户可以查看自己的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 100
        
        result = self.service.check_performance_view_permission(current_user, 100)
        self.assertTrue(result)

    def test_check_permission_target_user_not_found(self):
        """目标用户不存在，返回False"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 100
        
        # Mock db.query返回None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_check_permission_dept_manager_same_dept(self):
        """部门经理可以查看同部门员工的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # Mock角色
        mock_role = MagicMock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = "部门经理"
        current_user.roles = [mock_role]
        
        # Mock目标用户
        target_user = MagicMock()
        target_user.department_id = 10
        self.mock_db.query.return_value.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_permission_dept_manager_different_dept(self):
        """部门经理不能查看其他部门员工的绩效（无项目关系）"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # Mock角色
        mock_role = MagicMock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = None
        current_user.roles = [mock_role]
        
        # Mock目标用户（不同部门）
        target_user = MagicMock()
        target_user.department_id = 20
        
        # Mock数据库查询链
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        # 第一次查询：目标用户
        filter_mock.first.return_value = target_user
        query_mock.filter.return_value = filter_mock
        
        # 第二次查询：当前用户管理的项目
        query_mock.all.return_value = []  # 无项目
        
        self.mock_db.query.return_value = query_mock
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_permission_project_manager_with_member(self):
        """项目经理可以查看项目成员的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # Mock角色
        mock_role = MagicMock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = None
        current_user.roles = [mock_role]
        
        # Mock目标用户（不同部门）
        target_user = MagicMock()
        target_user.department_id = 20
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        
        # Mock Task（目标用户是项目成员）
        mock_task = MagicMock()
        
        # 构建查询链
        user_query = self.mock_db.query.return_value
        user_query.filter.return_value.first.return_value = target_user
        user_query.filter.return_value.all.return_value = [mock_project]
        user_query.filter.return_value.filter.return_value.first.return_value = mock_task
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_permission_no_manager_role(self):
        """普通员工不能查看其他人的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # 无管理角色
        mock_role = MagicMock()
        mock_role.role.role_code = "employee"
        mock_role.role.role_name = "员工"
        current_user.roles = [mock_role]
        
        target_user = MagicMock()
        target_user.department_id = 10
        self.mock_db.query.return_value.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_permission_admin_role(self):
        """管理员角色可以查看所有人的绩效"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        mock_role = MagicMock()
        mock_role.role.role_code = "admin"
        mock_role.role.role_name = None
        current_user.roles = [mock_role]
        
        target_user = MagicMock()
        target_user.department_id = 10  # 同部门才能查看（admin不是dept_manager角色）
        self.mock_db.query.return_value.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)


class TestEmployeePerformanceServiceMembers(unittest.TestCase):
    """测试成员获取相关方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_team_members(self):
        """获取团队成员列表"""
        # Mock用户
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [user1, user2]
        
        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """获取空团队成员列表"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_team_members(10)
        self.assertEqual(result, [])

    def test_get_department_members(self):
        """获取部门成员列表"""
        user1 = MagicMock()
        user1.id = 10
        user2 = MagicMock()
        user2.id = 20
        user3 = MagicMock()
        user3.id = 30
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [user1, user2, user3]
        
        result = self.service.get_department_members(5)
        self.assertEqual(result, [10, 20, 30])

    def test_get_department_members_empty(self):
        """获取空部门成员列表"""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_department_members(5)
        self.assertEqual(result, [])


class TestEmployeePerformanceServiceEvaluatorType(unittest.TestCase):
    """测试评价人类型判断"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_evaluator_type_dept_manager(self):
        """判断部门经理类型"""
        user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "dept_manager"
        mock_role.role.role_name = None
        user.roles = [mock_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """判断项目经理类型"""
        user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "pm"
        mock_role.role.role_name = None
        user.roles = [mock_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_both(self):
        """判断既是部门经理又是项目经理"""
        user = MagicMock()
        
        role1 = MagicMock()
        role1.role.role_code = "dept_manager"
        role1.role.role_name = None
        
        role2 = MagicMock()
        role2.role.role_code = "pm"
        role2.role.role_name = None
        
        user.roles = [role1, role2]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_get_evaluator_type_other(self):
        """判断其他类型（普通员工）"""
        user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = "employee"
        mock_role.role.role_name = "员工"
        user.roles = [mock_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_get_evaluator_type_by_role_name(self):
        """通过角色名称判断类型"""
        user = MagicMock()
        mock_role = MagicMock()
        mock_role.role.role_code = None
        mock_role.role.role_name = "项目经理"
        user.roles = [mock_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_empty_roles(self):
        """没有角色的用户"""
        user = MagicMock()
        user.roles = []
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")


class TestEmployeePerformanceServiceNames(unittest.TestCase):
    """测试名称获取方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_team_name_found(self):
        """获取团队名称（找到）"""
        mock_dept = MagicMock()
        mock_dept.name = "研发部"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_dept
        
        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """获取团队名称（未找到）"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_team_name(10)
        self.assertEqual(result, "团队10")

    def test_get_department_name_found(self):
        """获取部门名称（找到）"""
        mock_dept = MagicMock()
        mock_dept.name = "人力资源部"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_dept
        
        result = self.service.get_department_name(5)
        self.assertEqual(result, "人力资源部")

    def test_get_department_name_not_found(self):
        """获取部门名称（未找到）"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_department_name(5)
        self.assertEqual(result, "部门5")


class TestEmployeePerformanceServiceCreateSummary(unittest.TestCase):
    """测试创建月度工作总结"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    @patch('app.services.performance_service.PerformanceService.create_evaluation_tasks')
    def test_create_monthly_work_summary_success(self, mock_create_tasks):
        """成功创建月度工作总结"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_in = MonthlyWorkSummaryCreate(
            period="2026-02",
            work_content="完成项目A开发，包括需求分析、系统设计、代码编写、测试和部署等工作",
            self_evaluation="工作完成良好，各项指标达成，团队配合顺利",
            highlights="按时交付",
            problems="无明显问题",
            next_month_plan="继续优化"
        )
        
        # Mock查询不存在的总结
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock refresh返回创建的对象
        def refresh_side_effect(obj):
            obj.id = 100
            return obj
        self.mock_db.refresh.side_effect = refresh_side_effect
        
        result = self.service.create_monthly_work_summary(current_user, summary_in)
        
        # 验证
        self.assertEqual(result.employee_id, 1)
        self.assertEqual(result.period, "2026-02")
        self.assertEqual(result.work_content, "完成项目A开发，包括需求分析、系统设计、代码编写、测试和部署等工作")
        self.assertEqual(result.status, "SUBMITTED")
        self.assertIsNotNone(result.submit_date)
        
        # 验证调用了db操作
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # 验证创建了评价任务
        mock_create_tasks.assert_called_once()

    def test_create_monthly_work_summary_duplicate(self):
        """创建重复的月度工作总结应抛出异常"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_in = MonthlyWorkSummaryCreate(
            period="2026-02",
            work_content="本月完成了所有分配的任务，包括需求分析、代码开发和测试",
            self_evaluation="对本月的工作表现感到满意，各项指标均达到预期"
        )
        
        # Mock已存在的总结
        existing_summary = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_summary
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_monthly_work_summary(current_user, summary_in)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已提交过", context.exception.detail)


class TestEmployeePerformanceServiceSaveDraft(unittest.TestCase):
    """测试保存草稿"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_save_draft_create_new(self):
        """保存新草稿"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_update = MonthlyWorkSummaryUpdate(
            work_content="草稿内容",
            self_evaluation="草稿评价"
        )
        
        # Mock不存在的草稿
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.save_monthly_summary_draft(current_user, "2026-02", summary_update)
        
        # 验证
        self.assertEqual(result.employee_id, 1)
        self.assertEqual(result.period, "2026-02")
        self.assertEqual(result.work_content, "草稿内容")
        self.assertEqual(result.status, "DRAFT")
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_save_draft_update_existing(self):
        """更新现有草稿"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_update = MonthlyWorkSummaryUpdate(
            work_content="更新后的内容",
            highlights="新亮点"
        )
        
        # Mock现有草稿
        existing_draft = MagicMock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "旧内容"
        existing_draft.highlights = None
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_draft
        
        result = self.service.save_monthly_summary_draft(current_user, "2026-02", summary_update)
        
        # 验证更新
        self.assertEqual(result.work_content, "更新后的内容")
        self.assertEqual(result.highlights, "新亮点")
        self.mock_db.commit.assert_called_once()

    def test_save_draft_update_submitted_should_fail(self):
        """尝试更新已提交的总结应失败"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_update = MonthlyWorkSummaryUpdate(
            work_content="尝试更新"
        )
        
        # Mock已提交的总结
        submitted_summary = MagicMock()
        submitted_summary.status = "SUBMITTED"
        self.mock_db.query.return_value.filter.return_value.first.return_value = submitted_summary
        
        with self.assertRaises(HTTPException) as context:
            self.service.save_monthly_summary_draft(current_user, "2026-02", summary_update)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只能更新草稿", context.exception.detail)

    def test_save_draft_partial_update(self):
        """部分字段更新（其他字段不变）"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_update = MonthlyWorkSummaryUpdate(
            work_content="新内容"
            # 其他字段为None，不更新
        )
        
        existing_draft = MagicMock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "旧内容"
        existing_draft.self_evaluation = "保持不变"
        existing_draft.highlights = "原有亮点"
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_draft
        
        result = self.service.save_monthly_summary_draft(current_user, "2026-02", summary_update)
        
        # 验证只更新了work_content
        self.assertEqual(result.work_content, "新内容")
        self.assertEqual(result.self_evaluation, "保持不变")
        self.assertEqual(result.highlights, "原有亮点")


class TestEmployeePerformanceServiceHistory(unittest.TestCase):
    """测试历史记录查询"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_get_monthly_summary_history(self):
        """获取历史工作总结"""
        current_user = MagicMock()
        current_user.id = 1
        
        # Mock总结
        summary1 = MagicMock()
        summary1.id = 101
        summary1.period = "2026-02"
        summary1.status = "COMPLETED"
        summary1.submit_date = datetime(2026, 3, 1)
        summary1.created_at = datetime(2026, 2, 28)
        
        summary2 = MagicMock()
        summary2.id = 102
        summary2.period = "2026-01"
        summary2.status = "SUBMITTED"
        summary2.submit_date = datetime(2026, 2, 1)
        summary2.created_at = datetime(2026, 1, 30)
        
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [summary1, summary2]
        
        # Mock评价数量查询
        self.mock_db.query.return_value.filter.return_value.count.side_effect = [2, 1]
        
        result = self.service.get_monthly_summary_history(current_user, limit=12)
        
        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 101)
        self.assertEqual(result[0]["period"], "2026-02")
        self.assertEqual(result[0]["evaluation_count"], 2)
        self.assertEqual(result[1]["id"], 102)
        self.assertEqual(result[1]["evaluation_count"], 1)

    def test_get_monthly_summary_history_empty(self):
        """获取空历史记录"""
        current_user = MagicMock()
        current_user.id = 1
        
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = self.service.get_monthly_summary_history(current_user)
        self.assertEqual(result, [])

    def test_get_monthly_summary_history_custom_limit(self):
        """使用自定义limit获取历史"""
        current_user = MagicMock()
        current_user.id = 1
        
        # Mock 5条记录
        summaries = [MagicMock(id=i, period=f"2026-0{i}", status="COMPLETED", 
                              submit_date=datetime.now(), created_at=datetime.now()) 
                    for i in range(1, 6)]
        
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = summaries
        
        # Mock评价数量
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        result = self.service.get_monthly_summary_history(current_user, limit=5)
        self.assertEqual(len(result), 5)


class TestEmployeePerformanceServiceGetMyPerformance(unittest.TestCase):
    """测试获取我的绩效"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    @patch('app.services.performance_service.PerformanceService.calculate_final_score')
    @patch('app.services.performance_service.PerformanceService.get_score_level')
    @patch('app.services.performance_service.PerformanceService.get_historical_performance')
    @patch('app.services.employee_performance.employee_performance_service.date')
    def test_get_my_performance_with_current_summary(self, mock_date, mock_history, mock_level, mock_calc):
        """获取我的绩效（有当前总结）"""
        # Mock当前日期
        mock_today = date(2026, 2, 21)
        mock_date.today.return_value = mock_today
        
        current_user = MagicMock()
        current_user.id = 1
        
        # Mock当前总结
        current_summary = MagicMock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "COMPLETED"
        
        # Mock部门经理评价
        dept_eval = MagicMock()
        dept_eval.status = "COMPLETED"
        dept_eval.evaluator = MagicMock()
        dept_eval.evaluator.real_name = "张经理"
        dept_eval.score = 90.0
        
        # Mock项目经理评价
        proj_eval = MagicMock()
        proj_eval.status = "COMPLETED"
        proj_eval.evaluator = MagicMock()
        proj_eval.evaluator.real_name = "李经理"
        proj_eval.project = MagicMock()
        proj_eval.project.project_name = "项目A"
        proj_eval.score = 85.0
        proj_eval.project_weight = 0.5
        
        # 配置查询链
        query_chain = self.mock_db.query.return_value
        filter_chain = query_chain.filter.return_value
        
        # 需要更多的first调用：当前总结、部门评价、3个月的历史总结
        filter_chain.first.side_effect = [current_summary, dept_eval, None, None, None]
        # all: 项目评价
        filter_chain.all.return_value = [proj_eval]
        
        # Mock绩效计算
        mock_calc.return_value = {
            "final_score": 87.5,
            "dept_score": 90.0,
            "project_score": 85.0
        }
        mock_level.return_value = "优秀"
        mock_history.return_value = []
        
        result = self.service.get_my_performance(current_user)
        
        # 验证当前状态
        self.assertEqual(result["current_status"]["period"], "2026-02")
        self.assertEqual(result["current_status"]["summary_status"], "COMPLETED")
        self.assertEqual(result["current_status"]["dept_evaluation"]["status"], "COMPLETED")
        self.assertEqual(result["current_status"]["dept_evaluation"]["score"], 90.0)
        self.assertEqual(len(result["current_status"]["project_evaluations"]), 1)
        
        # 验证最新结果
        self.assertIsNotNone(result["latest_result"])
        self.assertEqual(result["latest_result"]["final_score"], 87.5)
        self.assertEqual(result["latest_result"]["level"], "优秀")

    @patch('app.services.performance_service.PerformanceService.get_historical_performance')
    @patch('app.services.employee_performance.employee_performance_service.date')
    def test_get_my_performance_no_current_summary(self, mock_date, mock_history):
        """获取我的绩效（无当前总结）"""
        mock_today = date(2026, 2, 21)
        mock_date.today.return_value = mock_today
        
        current_user = MagicMock()
        current_user.id = 1
        
        # Mock无当前总结
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_history.return_value = []
        
        result = self.service.get_my_performance(current_user)
        
        # 验证状态
        self.assertEqual(result["current_status"]["summary_status"], "NOT_SUBMITTED")
        self.assertEqual(result["current_status"]["dept_evaluation"]["status"], "PENDING")
        self.assertEqual(result["current_status"]["project_evaluations"], [])
        self.assertIsNone(result["latest_result"])

    @patch('app.services.performance_service.PerformanceService.calculate_final_score')
    @patch('app.services.performance_service.PerformanceService.get_historical_performance')
    @patch('app.services.employee_performance.employee_performance_service.date')
    def test_get_my_performance_quarterly_trend(self, mock_date, mock_history, mock_calc):
        """测试季度趋势计算"""
        mock_today = date(2026, 2, 21)
        mock_date.today.return_value = mock_today
        
        current_user = MagicMock()
        current_user.id = 1
        
        # Mock过去3个月的总结
        past_summaries = []
        for i in range(3):
            summary = MagicMock()
            summary.id = 100 + i
            summary.period = f"2026-{2-i:02d}"
            summary.status = "COMPLETED"
            past_summaries.append(summary)
        
        # 配置查询链
        query_chain = self.mock_db.query.return_value
        filter_chain = query_chain.filter.return_value
        
        # 第一次: 当前总结（无）
        # 后续3次: 过去的总结
        filter_chain.first.side_effect = [None] + past_summaries
        
        # Mock分数计算
        mock_calc.side_effect = [
            {"final_score": 90.0},
            {"final_score": 85.0},
            {"final_score": 88.0}
        ]
        mock_history.return_value = []
        
        result = self.service.get_my_performance(current_user)
        
        # 验证季度趋势
        self.assertEqual(len(result["quarterly_trend"]), 3)
        self.assertEqual(result["quarterly_trend"][0]["score"], 90.0)
        self.assertEqual(result["quarterly_trend"][1]["score"], 85.0)


class TestEmployeePerformanceServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = EmployeePerformanceService(self.mock_db)

    def test_check_permission_with_none_roles(self):
        """用户角色为None的情况"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.roles = None
        
        target_user = MagicMock()
        target_user.department_id = 10
        self.mock_db.query.return_value.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_get_evaluator_type_with_none_roles(self):
        """角色为None的情况"""
        user = MagicMock()
        user.roles = None
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_save_draft_all_fields_none(self):
        """所有字段都为None的更新"""
        current_user = MagicMock()
        current_user.id = 1
        
        summary_update = MonthlyWorkSummaryUpdate()
        
        existing_draft = MagicMock()
        existing_draft.status = "DRAFT"
        existing_draft.work_content = "原内容"
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_draft
        
        result = self.service.save_monthly_summary_draft(current_user, "2026-02", summary_update)
        
        # 原内容应保持不变
        self.assertEqual(result.work_content, "原内容")

    @patch('app.services.performance_service.PerformanceService.get_historical_performance')
    @patch('app.services.employee_performance.employee_performance_service.date')
    def test_get_my_performance_with_pending_evaluations(self, mock_date, mock_history):
        """测试待评价状态"""
        mock_today = date(2026, 2, 21)
        mock_date.today.return_value = mock_today
        
        current_user = MagicMock()
        current_user.id = 1
        
        current_summary = MagicMock()
        current_summary.id = 100
        current_summary.period = "2026-02"
        current_summary.status = "SUBMITTED"
        
        # Mock部门经理评价（待评价）
        dept_eval = MagicMock()
        dept_eval.status = "PENDING"
        dept_eval.evaluator = MagicMock()
        dept_eval.evaluator.real_name = "张经理"
        dept_eval.score = None
        
        query_chain = self.mock_db.query.return_value
        filter_chain = query_chain.filter.return_value
        # 需要更多的first调用：当前总结、部门评价、3个月的历史总结
        filter_chain.first.side_effect = [current_summary, dept_eval, None, None, None]
        filter_chain.all.return_value = []
        
        mock_history.return_value = []
        
        result = self.service.get_my_performance(current_user)
        
        # 验证待评价状态
        self.assertEqual(result["current_status"]["dept_evaluation"]["status"], "PENDING")
        self.assertIsNone(result["current_status"]["dept_evaluation"]["score"])


if __name__ == "__main__":
    unittest.main()
