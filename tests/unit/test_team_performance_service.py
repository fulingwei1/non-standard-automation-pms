# -*- coding: utf-8 -*-
"""
团队绩效服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal
from datetime import datetime

from app.services.team_performance.service import TeamPerformanceService


class TestTeamPerformanceService(unittest.TestCase):
    """测试团队绩效服务"""

    def setUp(self):
        """每个测试前的设置"""
        self.db = MagicMock()
        self.service = TeamPerformanceService(self.db)

    # ==================== 权限检查测试 ====================

    def test_check_permission_superuser(self):
        """测试超级管理员权限"""
        current_user = Mock()
        current_user.is_superuser = True
        current_user.id = 1
        
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertTrue(result)

    def test_check_permission_self(self):
        """测试查看自己的绩效"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        
        result = self.service.check_performance_view_permission(current_user, 1)
        self.assertTrue(result)

    def test_check_permission_target_user_not_found(self):
        """测试目标用户不存在"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        
        # Mock query返回None
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.check_performance_view_permission(current_user, 999)
        self.assertFalse(result)

    def test_check_permission_no_manager_role(self):
        """测试无管理角色"""
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

    def test_check_permission_dept_manager_same_dept(self):
        """测试部门经理查看同部门员工"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # Mock部门经理角色
        role = Mock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]
        
        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 10
        
        self.db.query.return_value.filter.return_value.first.return_value = target_user
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    def test_check_permission_dept_manager_different_dept(self):
        """测试部门经理查看其他部门员工"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        role = Mock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        current_user.roles = [role]
        
        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 20  # 不同部门
        
        # Mock查询结果
        self.db.query.return_value.filter.return_value.first.return_value = target_user
        self.db.query.return_value.filter.return_value.all.return_value = []  # 无共同项目
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertFalse(result)

    def test_check_permission_project_manager_with_member(self):
        """测试项目经理查看项目成员"""
        current_user = Mock()
        current_user.is_superuser = False
        current_user.id = 1
        current_user.department_id = 10
        
        # Mock项目经理角色
        role = Mock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        current_user.roles = [role]
        
        target_user = Mock()
        target_user.id = 2
        target_user.department_id = 20
        
        # Mock项目
        project = Mock()
        project.id = 100
        
        # Mock任务
        task = Mock()
        task.project_id = 100
        task.owner_id = 2
        
        # 配置db.query的多个调用
        query_mock = self.db.query.return_value
        
        # 第一次调用：获取target_user
        filter_chain = Mock()
        filter_chain.first.return_value = target_user
        filter_chain.all.side_effect = [
            [project],  # user_projects
            [project],  # target_projects
            [task],     # member_task
        ]
        query_mock.filter.return_value = filter_chain
        
        result = self.service.check_performance_view_permission(current_user, 2)
        self.assertTrue(result)

    # ==================== 成员获取测试 ====================

    def test_get_team_members(self):
        """测试获取团队成员"""
        user1 = Mock()
        user1.id = 1
        user2 = Mock()
        user2.id = 2
        
        self.db.query.return_value.filter.return_value.all.return_value = [user1, user2]
        
        result = self.service.get_team_members(team_id=10)
        self.assertEqual(result, [1, 2])

    def test_get_team_members_empty(self):
        """测试获取空团队成员"""
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_team_members(team_id=10)
        self.assertEqual(result, [])

    def test_get_department_members(self):
        """测试获取部门成员"""
        user1 = Mock()
        user1.id = 1
        user2 = Mock()
        user2.id = 2
        user3 = Mock()
        user3.id = 3
        
        self.db.query.return_value.filter.return_value.all.return_value = [user1, user2, user3]
        
        result = self.service.get_department_members(dept_id=20)
        self.assertEqual(result, [1, 2, 3])

    # ==================== 名称获取测试 ====================

    def test_get_team_name_exists(self):
        """测试获取存在的团队名称"""
        dept = Mock()
        dept.name = "研发部"
        
        self.db.query.return_value.filter.return_value.first.return_value = dept
        
        result = self.service.get_team_name(team_id=10)
        self.assertEqual(result, "研发部")

    def test_get_team_name_not_exists(self):
        """测试获取不存在的团队名称"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_team_name(team_id=999)
        self.assertEqual(result, "团队999")

    def test_get_department_name_exists(self):
        """测试获取存在的部门名称"""
        dept = Mock()
        dept.name = "技术部"
        
        self.db.query.return_value.filter.return_value.first.return_value = dept
        
        result = self.service.get_department_name(dept_id=20)
        self.assertEqual(result, "技术部")

    def test_get_department_name_not_exists(self):
        """测试获取不存在的部门名称"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_department_name(dept_id=999)
        self.assertEqual(result, "部门999")

    # ==================== 周期获取测试 ====================

    def test_get_period_by_id(self):
        """测试根据ID获取周期"""
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        self.db.query.return_value.filter.return_value.first.return_value = period
        
        result = self.service.get_period(period_id=1)
        self.assertEqual(result.period_name, "2024Q1")

    def test_get_period_latest(self):
        """测试获取最新已完成周期"""
        period = Mock()
        period.id = 2
        period.period_name = "2024Q2"
        period.status = "FINALIZED"
        
        query_chain = self.db.query.return_value
        query_chain.filter.return_value.order_by.return_value.first.return_value = period
        
        result = self.service.get_period(period_id=None)
        self.assertEqual(result.period_name, "2024Q2")

    def test_get_period_not_found(self):
        """测试周期不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_period(period_id=999)
        self.assertIsNone(result)

    # ==================== 评价人类型判断测试 ====================

    def test_get_evaluator_type_dept_manager(self):
        """测试部门经理类型"""
        user = Mock()
        role = Mock()
        role.role.role_code = "dept_manager"
        role.role.role_name = "部门经理"
        user.roles = [role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "DEPT_MANAGER")

    def test_get_evaluator_type_project_manager(self):
        """测试项目经理类型"""
        user = Mock()
        role = Mock()
        role.role.role_code = "pm"
        role.role.role_name = "项目经理"
        user.roles = [role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "PROJECT_MANAGER")

    def test_get_evaluator_type_both(self):
        """测试同时是部门经理和项目经理"""
        user = Mock()
        role1 = Mock()
        role1.role.role_code = "dept_manager"
        role1.role.role_name = "部门经理"
        role2 = Mock()
        role2.role.role_code = "pm"
        role2.role.role_name = "项目经理"
        user.roles = [role1, role2]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "BOTH")

    def test_get_evaluator_type_other(self):
        """测试其他角色"""
        user = Mock()
        role = Mock()
        role.role.role_code = "employee"
        role.role.role_name = "普通员工"
        user.roles = [role]
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    def test_get_evaluator_type_no_roles(self):
        """测试无角色"""
        user = Mock()
        user.roles = []
        
        result = self.service.get_evaluator_type(user)
        self.assertEqual(result, "OTHER")

    # ==================== 团队绩效测试 ====================

    def test_get_team_performance_no_period(self):
        """测试无周期时的团队绩效"""
        dept = Mock()
        dept.name = "研发部"
        
        user1 = Mock()
        user1.id = 1
        user2 = Mock()
        user2.id = 2
        
        # Mock各种查询
        query_results = {
            'Department': dept,
            'User': [user1, user2],
            'PerformancePeriod': None,
        }
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'Department':
                mock_query.filter.return_value.first.return_value = query_results['Department']
            elif model.__name__ == 'User':
                mock_query.filter.return_value.all.return_value = query_results['User']
            elif model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.order_by.return_value.first.return_value = query_results['PerformancePeriod']
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_team_performance(team_id=10)
        
        self.assertEqual(result['team_id'], 10)
        self.assertEqual(result['team_name'], "研发部")
        self.assertEqual(result['member_count'], 2)
        self.assertEqual(result['avg_score'], Decimal("0"))
        self.assertIsNone(result['period_id'])

    def test_get_team_performance_with_results(self):
        """测试有绩效结果的团队绩效"""
        # Mock部门
        dept = Mock()
        dept.name = "研发部"
        
        # Mock团队成员
        user1 = Mock()
        user1.id = 1
        user2 = Mock()
        user2.id = 2
        
        # Mock周期
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        # Mock绩效结果
        result1 = Mock()
        result1.user_id = 1
        result1.total_score = Decimal("85.5")
        result1.level = "EXCELLENT"
        
        result2 = Mock()
        result2.user_id = 2
        result2.total_score = Decimal("75.0")
        result2.level = "QUALIFIED"
        
        # Mock用户信息
        mock_user1 = Mock()
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"
        
        mock_user2 = Mock()
        mock_user2.real_name = "李四"
        mock_user2.username = "lisi"
        
        # 配置复杂的query调用链
        user_detail_calls = [mock_user1, mock_user2]
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'Department':
                mock_query.filter.return_value.first.return_value = dept
            elif model.__name__ == 'User':
                filter_chain = Mock()
                # 第一次调用返回团队成员
                filter_chain.all.return_value = [user1, user2]
                # 后续调用返回用户详情
                filter_chain.first.side_effect = user_detail_calls
                mock_query.filter.return_value = filter_chain
            elif model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.first.return_value = period
            elif model.__name__ == 'PerformanceResult':
                mock_query.filter.return_value.all.return_value = [result1, result2]
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_team_performance(team_id=10, period_id=1)
        
        self.assertEqual(result['team_id'], 10)
        self.assertEqual(result['team_name'], "研发部")
        self.assertEqual(result['period_id'], 1)
        self.assertEqual(result['period_name'], "2024Q1")
        self.assertEqual(result['member_count'], 2)
        self.assertEqual(result['avg_score'], Decimal("80.25"))
        self.assertEqual(result['max_score'], Decimal("85.5"))
        self.assertEqual(result['min_score'], Decimal("75.0"))
        self.assertEqual(result['level_distribution'], {"EXCELLENT": 1, "QUALIFIED": 1})
        self.assertEqual(len(result['members']), 2)
        # 验证按分数降序排序
        self.assertEqual(result['members'][0]['user_name'], "张三")
        self.assertEqual(result['members'][0]['score'], 85.5)

    def test_get_team_performance_no_results(self):
        """测试无绩效结果的团队绩效"""
        dept = Mock()
        dept.name = "研发部"
        
        user1 = Mock()
        user1.id = 1
        
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'Department':
                mock_query.filter.return_value.first.return_value = dept
            elif model.__name__ == 'User':
                mock_query.filter.return_value.all.return_value = [user1]
            elif model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.first.return_value = period
            elif model.__name__ == 'PerformanceResult':
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_team_performance(team_id=10, period_id=1)
        
        self.assertEqual(result['member_count'], 1)
        self.assertEqual(result['avg_score'], Decimal("0"))
        self.assertEqual(result['members'], [])

    # ==================== 部门绩效测试 ====================

    def test_get_department_performance_no_period(self):
        """测试无周期时的部门绩效"""
        dept = Mock()
        dept.name = "技术部"
        
        user1 = Mock()
        user1.id = 1
        
        # 配置复杂的query链
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'Department':
                mock_query.filter.return_value.first.return_value = dept
            elif model.__name__ == 'User':
                mock_query.filter.return_value.all.return_value = [user1]
            elif model.__name__ == 'PerformancePeriod':
                # 关键：这里返回None
                mock_query.filter.return_value.order_by.return_value.first.return_value = None
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_department_performance(dept_id=10)
        self.assertIsNone(result)

    def test_get_department_performance_with_results(self):
        """测试有绩效结果的部门绩效"""
        dept = Mock()
        dept.name = "技术部"
        
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        user1 = Mock()
        user1.id = 1
        user2 = Mock()
        user2.id = 2
        
        result1 = Mock()
        result1.department_id = 10
        result1.total_score = Decimal("80.0")
        result1.level = "EXCELLENT"
        
        result2 = Mock()
        result2.department_id = 10
        result2.total_score = Decimal("90.0")
        result2.level = "EXCELLENT"
        
        sub_dept1 = Mock()
        sub_dept1.id = 101
        sub_dept1.name = "后端组"
        
        sub_dept2 = Mock()
        sub_dept2.id = 102
        sub_dept2.name = "前端组"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'Department':
                filter_chain = Mock()
                # 第一次调用：获取部门名称
                filter_chain.first.return_value = dept
                # 第二次调用：获取子部门
                filter_chain.all.return_value = [sub_dept1, sub_dept2]
                mock_query.filter.return_value = filter_chain
            elif model.__name__ == 'User':
                mock_query.filter.return_value.all.return_value = [user1, user2]
            elif model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.first.return_value = period
            elif model.__name__ == 'PerformanceResult':
                mock_query.filter.return_value.all.return_value = [result1, result2]
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_department_performance(dept_id=10, period_id=1)
        
        self.assertEqual(result['department_id'], 10)
        self.assertEqual(result['department_name'], "技术部")
        self.assertEqual(result['period_id'], 1)
        self.assertEqual(result['member_count'], 2)
        self.assertEqual(result['avg_score'], Decimal("85.0"))
        self.assertEqual(result['level_distribution'], {"EXCELLENT": 2})
        self.assertEqual(len(result['teams']), 2)

    # ==================== 绩效排行榜测试 ====================

    def test_get_performance_ranking_no_period(self):
        """测试无周期时的排行榜"""
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.service.get_performance_ranking("COMPANY")
        self.assertIsNone(result)

    def test_get_performance_ranking_company(self):
        """测试公司排行榜"""
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        result1 = Mock()
        result1.user_id = 1
        result1.total_score = Decimal("95.0")
        result1.level = "EXCELLENT"
        result1.department_name = "研发部"
        
        result2 = Mock()
        result2.user_id = 2
        result2.total_score = Decimal("85.0")
        result2.level = "QUALIFIED"
        result2.department_name = "技术部"
        
        user1 = Mock()
        user1.real_name = "张三"
        user1.username = "zhangsan"
        
        user2 = Mock()
        user2.real_name = "李四"
        user2.username = "lisi"
        
        user_calls = [user1, user2]
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.first.return_value = period
            elif model.__name__ == 'PerformanceResult':
                mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [result1, result2]
            elif model.__name__ == 'User':
                mock_query.filter.return_value.first.side_effect = user_calls
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_performance_ranking("COMPANY", period_id=1)
        
        self.assertEqual(result['ranking_type'], "COMPANY")
        self.assertEqual(result['period_id'], 1)
        self.assertEqual(len(result['rankings']), 2)
        self.assertEqual(result['rankings'][0]['rank'], 1)
        self.assertEqual(result['rankings'][0]['user_name'], "张三")
        self.assertEqual(result['rankings'][0]['score'], 95.0)

    def test_get_performance_ranking_team(self):
        """测试团队排行榜"""
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        dept1 = Mock()
        dept1.id = 10
        dept1.name = "研发部"
        
        dept2 = Mock()
        dept2.id = 20
        dept2.name = "技术部"
        
        result1 = Mock()
        result1.department_id = 10
        result1.total_score = Decimal("90.0")
        
        result2 = Mock()
        result2.department_id = 10
        result2.total_score = Decimal("80.0")
        
        result3 = Mock()
        result3.department_id = 20
        result3.total_score = Decimal("75.0")
        
        # 用于跟踪filter调用次数
        filter_call_count = [0]
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.first.return_value = period
            elif model.__name__ == 'Department':
                mock_query.all.return_value = [dept1, dept2]
            elif model.__name__ == 'PerformanceResult':
                # 每次filter调用创建新的chain
                filter_chain = Mock()
                # 根据调用次数返回不同结果
                call_num = filter_call_count[0]
                if call_num == 0:
                    filter_chain.all.return_value = [result1, result2]
                else:
                    filter_chain.all.return_value = [result3]
                filter_call_count[0] += 1
                mock_query.filter.return_value = filter_chain
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_performance_ranking("TEAM", period_id=1)
        
        self.assertEqual(result['ranking_type'], "TEAM")
        self.assertEqual(len(result['rankings']), 2)
        # 验证按平均分排序
        self.assertEqual(result['rankings'][0]['rank'], 1)
        self.assertEqual(result['rankings'][0]['entity_name'], "研发部")
        self.assertEqual(result['rankings'][0]['score'], 85.0)  # (90+80)/2
        self.assertEqual(result['rankings'][1]['rank'], 2)
        self.assertEqual(result['rankings'][1]['entity_name'], "技术部")
        self.assertEqual(result['rankings'][1]['score'], 75.0)

    def test_get_performance_ranking_department(self):
        """测试部门排行榜"""
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        dept = Mock()
        dept.id = 10
        dept.name = "研发部"
        
        result1 = Mock()
        result1.department_id = 10
        result1.total_score = Decimal("90.0")
        result1.level = "EXCELLENT"
        
        result2 = Mock()
        result2.department_id = 10
        result2.total_score = Decimal("80.0")
        result2.level = "QUALIFIED"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.order_by.return_value.first.return_value = period
            elif model.__name__ == 'Department':
                mock_query.all.return_value = [dept]
            elif model.__name__ == 'PerformanceResult':
                mock_query.filter.return_value.all.return_value = [result1, result2]
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_performance_ranking("DEPARTMENT", period_id=1)
        
        self.assertEqual(result['ranking_type'], "DEPARTMENT")
        self.assertEqual(len(result['rankings']), 1)
        self.assertEqual(result['rankings'][0]['entity_name'], "研发部")
        self.assertEqual(result['rankings'][0]['score'], 85.0)
        self.assertEqual(result['rankings'][0]['level_distribution'], {
            "EXCELLENT": 1,
            "QUALIFIED": 1
        })

    # ==================== 边界情况测试 ====================

    def test_empty_team_performance_method(self):
        """测试_empty_team_performance方法"""
        result = self.service._empty_team_performance(
            team_id=10,
            team_name="测试团队",
            member_ids=[1, 2, 3]
        )
        
        self.assertEqual(result['team_id'], 10)
        self.assertEqual(result['team_name'], "测试团队")
        self.assertEqual(result['member_count'], 3)
        self.assertEqual(result['avg_score'], Decimal("0"))
        self.assertIsNone(result['period_id'])

    def test_get_team_performance_with_null_scores(self):
        """测试分数为None的情况"""
        dept = Mock()
        dept.name = "研发部"
        
        user1 = Mock()
        user1.id = 1
        
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        result1 = Mock()
        result1.user_id = 1
        result1.total_score = None  # 分数为None
        result1.level = None
        
        mock_user = Mock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'Department':
                mock_query.filter.return_value.first.return_value = dept
            elif model.__name__ == 'User':
                filter_chain = Mock()
                filter_chain.all.return_value = [user1]
                filter_chain.first.return_value = mock_user
                mock_query.filter.return_value = filter_chain
            elif model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.first.return_value = period
            elif model.__name__ == 'PerformanceResult':
                mock_query.filter.return_value.all.return_value = [result1]
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_team_performance(team_id=10, period_id=1)
        
        self.assertEqual(result['avg_score'], Decimal("0"))
        self.assertEqual(result['members'][0]['score'], 0)
        self.assertEqual(result['members'][0]['level'], "QUALIFIED")

    def test_ranking_with_no_departments(self):
        """测试无部门时的排行榜"""
        period = Mock()
        period.id = 1
        period.period_name = "2024Q1"
        
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'PerformancePeriod':
                mock_query.filter.return_value.order_by.return_value.first.return_value = period
            elif model.__name__ == 'Department':
                mock_query.all.return_value = []
            return mock_query
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_performance_ranking("TEAM", period_id=1)
        
        self.assertEqual(len(result['rankings']), 0)


if __name__ == "__main__":
    unittest.main()
