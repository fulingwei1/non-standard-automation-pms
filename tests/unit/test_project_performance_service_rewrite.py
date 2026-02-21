# -*- coding: utf-8 -*-
"""
项目绩效服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率（499行 → 350+行）
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.services.project_performance.service import ProjectPerformanceService


class TestProjectPerformanceServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init(self):
        """测试初始化"""
        mock_db = MagicMock()
        service = ProjectPerformanceService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestCheckPerformanceViewPermission(unittest.TestCase):
    """测试权限检查"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_superuser_can_view_all(self):
        """测试超级用户可以查看所有人"""
        current_user = MagicMock()
        current_user.is_superuser = True
        current_user.id = 1
        
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_can_view_self(self):
        """测试可以查看自己的绩效"""
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
        
        # Mock db.query返回的查询对象
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_dept_manager_can_view_dept_members(self):
        """测试部门经理可以查看本部门成员"""
        # 创建当前用户（部门经理）
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # 创建角色
        role_obj = MagicMock()
        role_obj.role_code = "dept_manager"
        role_obj.role_name = "部门经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        current_user.roles = [user_role]
        
        # 创建目标用户（同部门）
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_dept_manager_cannot_view_other_dept(self):
        """测试部门经理不能查看其他部门"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        role_obj = MagicMock()
        role_obj.role_code = "dept_manager"
        role_obj.role_name = "部门经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        current_user.roles = [user_role]
        
        # 目标用户在不同部门
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 20
        
        # Mock项目查询返回空列表
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        
        # 第一次调用（查找target_user）
        mock_filter.first.return_value = target_user
        
        # 第二次调用（查找项目）
        mock_filter.all.return_value = []
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_project_manager_can_view_project_members(self):
        """测试项目经理可以查看项目成员"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        role_obj = MagicMock()
        role_obj.role_code = "pm"
        role_obj.role_name = "项目经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        current_user.roles = [user_role]
        
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 20  # 不同部门
        
        # 创建项目
        project = MagicMock()
        project.id = 100
        
        # Mock查询
        mock_query = self.mock_db.query.return_value
        
        # 设置调用序列
        call_sequence = []
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                # 第一次是查找target_user
                mock_q.filter.return_value.first.return_value = target_user
            elif model.__name__ == 'Project':
                # 第二次是查找当前用户管理的项目
                mock_q.filter.return_value.all.return_value = [project]
            elif model.__name__ == 'Task':
                # 第三次是查找任务
                task = MagicMock()
                mock_q.filter.return_value.first.return_value = task
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_no_manager_role_cannot_view_others(self):
        """测试非管理角色不能查看他人"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # 普通员工角色
        role_obj = MagicMock()
        role_obj.role_code = "employee"
        role_obj.role_name = "员工"
        
        user_role = MagicMock()
        user_role.role = role_obj
        current_user.roles = [user_role]
        
        target_user = MagicMock()
        target_user.id = 2
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_empty_roles(self):
        """测试空角色列表"""
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

    def test_role_code_none(self):
        """测试role_code为None的情况"""
        current_user = MagicMock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        role_obj = MagicMock()
        role_obj.role_code = None
        role_obj.role_name = "部门经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        current_user.roles = [user_role]
        
        target_user = MagicMock()
        target_user.id = 2
        target_user.department_id = 10
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)


class TestGetTeamMembers(unittest.TestCase):
    """测试获取团队成员"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_get_team_members(self):
        """测试获取团队成员"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [user1, user2]
        
        result = self.service.get_team_members(10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """测试空团队"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_team_members(10)
        self.assertEqual(result, [])


class TestGetDepartmentMembers(unittest.TestCase):
    """测试获取部门成员"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_get_department_members(self):
        """测试获取部门成员"""
        user1 = MagicMock()
        user1.id = 1
        user2 = MagicMock()
        user2.id = 2
        user3 = MagicMock()
        user3.id = 3
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = [user1, user2, user3]
        
        result = self.service.get_department_members(10)
        self.assertEqual(result, [1, 2, 3])

    def test_get_department_members_empty(self):
        """测试空部门"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_department_members(10)
        self.assertEqual(result, [])


class TestGetEvaluatorType(unittest.TestCase):
    """测试判断评价人类型"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_dept_manager_type(self):
        """测试部门经理类型"""
        user = MagicMock()
        
        role_obj = MagicMock()
        role_obj.role_code = "dept_manager"
        role_obj.role_name = "部门经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        user.roles = [user_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_project_manager_type(self):
        """测试项目经理类型"""
        user = MagicMock()
        
        role_obj = MagicMock()
        role_obj.role_code = "pm"
        role_obj.role_name = "项目经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        user.roles = [user_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_both_types(self):
        """测试同时拥有两种角色"""
        user = MagicMock()
        
        role_obj1 = MagicMock()
        role_obj1.role_code = "dept_manager"
        role_obj1.role_name = "部门经理"
        
        role_obj2 = MagicMock()
        role_obj2.role_code = "pm"
        role_obj2.role_name = "项目经理"
        
        user_role1 = MagicMock()
        user_role1.role = role_obj1
        user_role2 = MagicMock()
        user_role2.role = role_obj2
        
        user.roles = [user_role1, user_role2]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_other_type(self):
        """测试其他角色"""
        user = MagicMock()
        
        role_obj = MagicMock()
        role_obj.role_code = "employee"
        role_obj.role_name = "员工"
        
        user_role = MagicMock()
        user_role.role = role_obj
        user.roles = [user_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_empty_roles(self):
        """测试空角色"""
        user = MagicMock()
        user.roles = []
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_role_code_none(self):
        """测试role_code为None"""
        user = MagicMock()
        
        role_obj = MagicMock()
        role_obj.role_code = None
        role_obj.role_name = "部门经理"
        
        user_role = MagicMock()
        user_role.role = role_obj
        user.roles = [user_role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")


class TestGetTeamName(unittest.TestCase):
    """测试获取团队名称"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_get_team_name_found(self):
        """测试找到团队名称"""
        dept = MagicMock()
        dept.name = "研发部"
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = dept
        
        result = self.service.get_team_name(10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_found(self):
        """测试未找到团队"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        result = self.service.get_team_name(10)
        self.assertEqual(result, "团队10")


class TestGetDepartmentName(unittest.TestCase):
    """测试获取部门名称"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_get_department_name_found(self):
        """测试找到部门名称"""
        dept = MagicMock()
        dept.name = "技术部"
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = dept
        
        result = self.service.get_department_name(10)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_found(self):
        """测试未找到部门"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        result = self.service.get_department_name(10)
        self.assertEqual(result, "部门10")


class TestGetProjectPerformance(unittest.TestCase):
    """测试获取项目绩效"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_get_project_performance_with_period_id(self):
        """测试指定周期获取项目绩效"""
        # Mock项目
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        
        # Mock周期
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        # Mock贡献记录
        contrib1 = MagicMock()
        contrib1.user_id = 1
        contrib1.contribution_score = Decimal("85.5")
        contrib1.hours_spent = Decimal("120")
        contrib1.task_count = 10
        
        contrib2 = MagicMock()
        contrib2.user_id = 2
        contrib2.contribution_score = Decimal("90.0")
        contrib2.hours_spent = Decimal("150")
        contrib2.task_count = 12
        
        # Mock用户
        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"
        
        user2 = MagicMock()
        user2.id = 2
        user2.real_name = "李四"
        user2.username = "lisi"
        
        # 设置查询返回值
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'ProjectContribution':
                mock_q.filter.return_value.all.return_value = [contrib1, contrib2]
            elif model.__name__ == 'User':
                # 模拟两次用户查询
                user_mock = MagicMock()
                returns = [user1, user2]
                user_mock.filter.return_value.first.side_effect = returns
                return user_mock
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_performance(100, period_id=1)
        
        self.assertEqual(result['project_id'], 100)
        self.assertEqual(result['project_name'], "测试项目")
        self.assertEqual(result['period_id'], 1)
        self.assertEqual(result['member_count'], 2)
        self.assertEqual(result['total_contribution_score'], Decimal("175.5"))
        
        # 验证成员按贡献分排序（降序）
        self.assertEqual(result['members'][0]['user_id'], 2)  # 李四90分
        self.assertEqual(result['members'][1]['user_id'], 1)  # 张三85.5分

    def test_get_project_performance_without_period_id(self):
        """测试不指定周期（使用最近FINALIZED周期）"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        
        period = MagicMock()
        period.id = 2
        period.period_name = "2024Q2"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'PerformancePeriod':
                # 不指定period_id时，order_by返回最新的FINALIZED
                mock_order = MagicMock()
                mock_order.first.return_value = period
                mock_q.filter.return_value.order_by.return_value = mock_order
            elif model.__name__ == 'ProjectContribution':
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_performance(100)
        
        self.assertEqual(result['period_id'], 2)
        self.assertEqual(result['period_name'], "2024Q2")
        self.assertEqual(result['member_count'], 0)

    def test_get_project_performance_project_not_found(self):
        """测试项目不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_project_performance(999)
        
        self.assertEqual(str(context.exception), "项目不存在")

    def test_get_project_performance_period_not_found(self):
        """测试周期不存在"""
        project = MagicMock()
        project.id = 100
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = None
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        with self.assertRaises(ValueError) as context:
            self.service.get_project_performance(100, period_id=999)
        
        self.assertEqual(str(context.exception), "未找到考核周期")

    def test_get_project_performance_no_contributions(self):
        """测试无贡献记录"""
        project = MagicMock()
        project.id = 100
        project.project_name = "空项目"
        
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'ProjectContribution':
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_performance(100, period_id=1)
        
        self.assertEqual(result['member_count'], 0)
        self.assertEqual(result['total_contribution_score'], Decimal("0"))
        self.assertEqual(result['members'], [])

    def test_get_project_performance_null_scores(self):
        """测试空分数处理"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        contrib = MagicMock()
        contrib.user_id = 1
        contrib.contribution_score = None
        contrib.hours_spent = None
        contrib.task_count = None
        
        user = MagicMock()
        user.id = 1
        user.real_name = None
        user.username = "user1"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'ProjectContribution':
                mock_q.filter.return_value.all.return_value = [contrib]
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = user
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_performance(100, period_id=1)
        
        self.assertEqual(result['members'][0]['contribution_score'], 0)
        self.assertEqual(result['members'][0]['work_hours'], 0)
        self.assertEqual(result['members'][0]['task_count'], 0)
        self.assertEqual(result['members'][0]['user_name'], "user1")


class TestGetProjectProgressReport(unittest.TestCase):
    """测试获取项目进展报告"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_get_project_progress_report_weekly(self):
        """测试获取周报"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 75
        
        # Mock任务
        task1 = MagicMock()
        task1.id = 1
        task1.task_name = "任务1"
        task1.status = "DONE"
        task1.owner_id = 1
        task1.plan_end = date(2024, 1, 10)
        task1.updated_at = datetime(2024, 1, 15, 10, 0)
        task1.created_at = datetime(2024, 1, 1, 10, 0)
        task1.description = "已完成的任务"
        
        task2 = MagicMock()
        task2.id = 2
        task2.task_name = "任务2"
        task2.status = "IN_PROGRESS"
        task2.owner_id = 2
        task2.plan_end = date(2024, 1, 18)  # 修改为未来，不算逾期
        task2.updated_at = datetime(2024, 1, 15, 10, 0)
        task2.created_at = datetime(2024, 1, 1, 10, 0)
        task2.description = None
        
        # 逾期任务
        task3 = MagicMock()
        task3.id = 3
        task3.task_name = "逾期任务"
        task3.status = "IN_PROGRESS"
        task3.owner_id = 1
        task3.plan_end = date(2020, 1, 1)  # 严重逾期
        task3.updated_at = datetime(2024, 1, 15, 10, 0)
        task3.created_at = datetime(2024, 1, 1, 10, 0)
        task3.description = "这是一个逾期任务"
        
        # Mock用户
        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"
        
        user2 = MagicMock()
        user2.id = 2
        user2.real_name = "李四"
        user2.username = "lisi"
        
        # 使用计数器来跟踪User查询次数
        user_call_count = [0]  # 使用列表来在内部函数中修改
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.all.return_value = [task1, task2, task3]
            elif model.__name__ == 'User':
                # 第一次返回user1，第二次返回user2
                user_call_count[0] += 1
                user = user1 if user_call_count[0] == 1 else user2
                mock_q.filter.return_value.first.return_value = user
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_progress_report(
            100, 
            report_type="WEEKLY",
            report_date=date(2024, 1, 15)
        )
        
        self.assertEqual(result['project_id'], 100)
        self.assertEqual(result['project_name'], "测试项目")
        self.assertEqual(result['report_type'], "WEEKLY")
        self.assertEqual(result['report_date'], date(2024, 1, 15))
        
        # 进度摘要
        progress = result['progress_summary']
        self.assertEqual(progress['overall_progress'], 75)
        self.assertEqual(progress['completed_tasks'], 1)
        self.assertEqual(progress['total_tasks'], 3)
        self.assertFalse(progress['on_schedule'])  # 有逾期任务
        
        # 成员贡献
        members = result['member_contributions']
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0]['user_id'], 1)  # 张三2个任务
        self.assertEqual(members[0]['task_count'], 2)
        self.assertEqual(members[0]['estimated_hours'], 8)  # 2*4
        
        # 关键成果（最多5个）
        achievements = result['key_achievements']
        self.assertEqual(len(achievements), 1)
        self.assertEqual(achievements[0]['task_name'], "任务1")
        
        # 风险和问题（注意：源代码使用datetime.now()判断逾期，不是report_date）
        # task2的plan_end是2024-01-18，现在是2026年，所以也算逾期
        # task3的plan_end是2020-01-01，严重逾期
        risks = result['risks_and_issues']
        self.assertEqual(len(risks), 2)
        self.assertEqual(risks[0]['type'], "DELAYED_TASK")
        self.assertEqual(risks[1]['type'], "DELAYED_TASK")

    def test_get_project_progress_report_monthly(self):
        """测试获取月报"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 50
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_progress_report(100, report_type="MONTHLY")
        
        self.assertEqual(result['report_type'], "MONTHLY")

    def test_get_project_progress_report_project_not_found(self):
        """测试项目不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.get_project_progress_report(999)
        
        self.assertEqual(str(context.exception), "项目不存在")

    def test_get_project_progress_report_default_date(self):
        """测试默认使用今天的日期"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 0
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_progress_report(100)
        
        self.assertEqual(result['report_date'], datetime.now().date())

    def test_get_project_progress_report_null_progress(self):
        """测试进度为None"""
        project = MagicMock()
        project.id = 100
        project.project_name = "新项目"
        project.progress = None
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.all.return_value = []
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_progress_report(100)
        
        self.assertEqual(result['progress_summary']['overall_progress'], 0)

    def test_get_project_progress_report_delayed_task_medium(self):
        """测试中等严重逾期任务（<=7天）"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 50
        
        # 逾期5天的任务
        task = MagicMock()
        task.id = 1
        task.task_name = "轻微逾期任务"
        task.status = "IN_PROGRESS"
        task.owner_id = 1
        task.plan_end = date.today() - timedelta(days=5)
        task.updated_at = datetime.now()
        task.created_at = datetime.now()
        task.description = "5天逾期"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.all.return_value = [task]
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_progress_report(100)
        
        risks = result['risks_and_issues']
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0]['severity'], "MEDIUM")

    def test_get_project_progress_report_truncate_description(self):
        """测试成果描述截断（100字符）"""
        project = MagicMock()
        project.id = 100
        project.project_name = "测试项目"
        project.progress = 50
        
        task = MagicMock()
        task.id = 1
        task.task_name = "长描述任务"
        task.status = "DONE"
        task.owner_id = 1
        task.plan_end = date.today()
        task.updated_at = datetime.now()
        task.created_at = datetime.now()
        task.description = "这是一个非常长的描述" * 20  # 超过100字符
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.all.return_value = [task]
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.get_project_progress_report(100)
        
        achievements = result['key_achievements']
        self.assertEqual(len(achievements[0]['description']), 100)


class TestComparePerformance(unittest.TestCase):
    """测试绩效对比"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = ProjectPerformanceService(self.mock_db)

    def test_compare_performance_with_period_id(self):
        """测试指定周期的绩效对比"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        # 用户1
        user1 = MagicMock()
        user1.id = 1
        user1.real_name = "张三"
        user1.username = "zhangsan"
        
        result1 = MagicMock()
        result1.total_score = Decimal("85.5")
        result1.level = "EXCELLENT"
        result1.department_name = "研发部"
        
        # 用户2
        user2 = MagicMock()
        user2.id = 2
        user2.real_name = "李四"
        user2.username = "lisi"
        
        result2 = MagicMock()
        result2.total_score = Decimal("90.0")
        result2.level = "OUTSTANDING"
        result2.department_name = "产品部"
        
        # 使用计数器来区分不同的调用
        call_counts = {'user': 0, 'result': 0}
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'User':
                call_counts['user'] += 1
                user = user1 if call_counts['user'] == 1 else user2
                mock_q.filter.return_value.first.return_value = user
            elif model.__name__ == 'PerformanceResult':
                call_counts['result'] += 1
                result = result1 if call_counts['result'] == 1 else result2
                mock_q.filter.return_value.first.return_value = result
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.compare_performance([1, 2], period_id=1)
        
        self.assertEqual(result['user_ids'], [1, 2])
        self.assertEqual(result['period_id'], 1)
        self.assertEqual(result['period_name'], "2024Q1")
        self.assertEqual(len(result['comparison_data']), 2)
        
        # 验证数据
        self.assertEqual(result['comparison_data'][0]['user_id'], 1)
        self.assertEqual(result['comparison_data'][0]['score'], 85.5)
        self.assertEqual(result['comparison_data'][0]['level'], "EXCELLENT")
        
        self.assertEqual(result['comparison_data'][1]['user_id'], 2)
        self.assertEqual(result['comparison_data'][1]['score'], 90.0)

    def test_compare_performance_without_period_id(self):
        """测试不指定周期（使用最近FINALIZED）"""
        period = MagicMock()
        period.id = 2
        period.period_name = "2024Q2"
        
        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        
        result_obj = MagicMock()
        result_obj.total_score = Decimal("80")
        result_obj.level = "GOOD"
        result_obj.department_name = "研发部"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'PerformancePeriod':
                mock_order = MagicMock()
                mock_order.first.return_value = period
                mock_q.filter.return_value.order_by.return_value = mock_order
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = user
            elif model.__name__ == 'PerformanceResult':
                mock_q.filter.return_value.first.return_value = result_obj
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.compare_performance([1])
        
        self.assertEqual(result['period_id'], 2)

    def test_compare_performance_period_not_found(self):
        """测试周期不存在"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.service.compare_performance([1, 2], period_id=999)
        
        self.assertEqual(str(context.exception), "未找到考核周期")

    def test_compare_performance_user_not_found(self):
        """测试用户不存在（跳过）"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = None
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.compare_performance([999], period_id=1)
        
        self.assertEqual(len(result['comparison_data']), 0)

    def test_compare_performance_no_result(self):
        """测试无绩效结果"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = user
            elif model.__name__ == 'PerformanceResult':
                mock_q.filter.return_value.first.return_value = None
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.compare_performance([1], period_id=1)
        
        # 没有绩效结果时应使用默认值
        self.assertEqual(result['comparison_data'][0]['score'], 0)
        self.assertEqual(result['comparison_data'][0]['level'], "QUALIFIED")
        self.assertIsNone(result['comparison_data'][0]['department_name'])

    def test_compare_performance_null_score(self):
        """测试分数为None"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        user = MagicMock()
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        
        result_obj = MagicMock()
        result_obj.total_score = None
        result_obj.level = "QUALIFIED"
        result_obj.department_name = "研发部"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'PerformancePeriod':
                mock_q.filter.return_value.first.return_value = period
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = user
            elif model.__name__ == 'PerformanceResult':
                mock_q.filter.return_value.first.return_value = result_obj
            return mock_q
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.service.compare_performance([1], period_id=1)
        
        self.assertEqual(result['comparison_data'][0]['score'], 0)

    def test_compare_performance_empty_user_list(self):
        """测试空用户列表"""
        period = MagicMock()
        period.id = 1
        period.period_name = "2024Q1"
        
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = period
        
        result = self.service.compare_performance([], period_id=1)
        
        self.assertEqual(len(result['comparison_data']), 0)


if __name__ == "__main__":
    unittest.main()
