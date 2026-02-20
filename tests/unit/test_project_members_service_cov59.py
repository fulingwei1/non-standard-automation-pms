# -*- coding: utf-8 -*-
"""
项目成员服务层单元测试

覆盖 ProjectMembersService 核心业务逻辑
"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.project_members.service import ProjectMembersService


class TestProjectMembersService(unittest.TestCase):
    """项目成员服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ProjectMembersService(self.db)
    
    def test_enrich_member_response_with_user(self):
        """测试填充成员信息 - 用户存在"""
        member = MagicMock()
        member.user = MagicMock()
        member.user.username = "testuser"
        member.user.real_name = "Test User"
        
        result = self.service.enrich_member_response(member)
        
        self.assertEqual(result.username, "testuser")
        self.assertEqual(result.real_name, "Test User")
    
    def test_enrich_member_response_without_user(self):
        """测试填充成员信息 - 用户不存在"""
        member = MagicMock()
        member.user = None
        
        result = self.service.enrich_member_response(member)
        
        self.assertEqual(result.username, "Unknown")
        self.assertEqual(result.real_name, "Unknown")
    
    def test_check_member_exists_true(self):
        """测试成员存在性检查 - 存在"""
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()
        
        result = self.service.check_member_exists(1, 100)
        
        self.assertTrue(result)
    
    def test_check_member_exists_false(self):
        """测试成员存在性检查 - 不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.check_member_exists(1, 100)
        
        self.assertFalse(result)
    
    @patch('app.services.project_members.service.get_or_404')
    def test_get_member_by_id_success(self, mock_get_or_404):
        """测试获取成员详情 - 成功"""
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "testuser"
        mock_member.user.real_name = "Test User"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = self.service.get_member_by_id(1, 10)
        
        self.assertEqual(result.username, "testuser")
        self.assertEqual(result.real_name, "Test User")
    
    def test_get_member_by_id_not_found(self):
        """测试获取成员详情 - 未找到"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_member_by_id(1, 10)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目成员不存在")
    
    @patch('app.services.project_members.service.save_obj')
    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_success(self, mock_get_or_404, mock_save_obj):
        """测试创建成员 - 成功"""
        # Mock 项目和用户存在
        mock_project = MagicMock()
        mock_user = MagicMock()
        mock_get_or_404.side_effect = [mock_project, mock_user]
        
        # Mock 成员不存在
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock 保存成功的成员
        mock_member = MagicMock()
        mock_member.user = mock_user
        mock_user.username = "newuser"
        mock_user.real_name = "New User"
        mock_save_obj.return_value = mock_member
        
        result = self.service.create_member(
            project_id=1,
            user_id=100,
            role_code="dev",
            allocation_pct=80.0
        )
        
        # 验证调用
        mock_save_obj.assert_called_once()
        self.assertEqual(result.username, "newuser")
    
    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_already_exists(self, mock_get_or_404):
        """测试创建成员 - 成员已存在"""
        # Mock 项目和用户存在
        mock_project = MagicMock()
        mock_user = MagicMock()
        mock_get_or_404.side_effect = [mock_project, mock_user]
        
        # Mock 成员已存在
        existing_member = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = existing_member
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_member(
                project_id=1,
                user_id=100,
                role_code="dev"
            )
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "该用户已是项目成员")
    
    def test_check_member_conflicts_no_dates(self):
        """测试冲突检查 - 无日期"""
        result = self.service.check_member_conflicts(100, None, None)
        
        self.assertFalse(result['has_conflict'])
    
    def test_check_member_conflicts_no_conflict(self):
        """测试冲突检查 - 无冲突"""
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.check_member_conflicts(
            user_id=100,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        self.assertFalse(result['has_conflict'])
    
    def test_check_member_conflicts_with_conflict(self):
        """测试冲突检查 - 有冲突"""
        # Mock 冲突的成员
        mock_member = MagicMock()
        mock_member.project_id = 2
        mock_member.allocation_pct = 50
        mock_member.start_date = date(2024, 1, 1)
        mock_member.end_date = date(2024, 6, 30)
        
        # Mock 冲突的项目
        mock_project = MagicMock()
        mock_project.id = 2
        mock_project.project_code = "PRJ002"
        mock_project.project_name = "Conflict Project"
        
        # Mock 用户
        mock_user = MagicMock()
        mock_user.id = 100
        mock_user.username = "testuser"
        mock_user.real_name = "Test User"
        
        # 设置查询返回值
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [mock_member]
        
        # 为不同的查询设置不同的返回值
        def query_side_effect(model):
            if model.__name__ == 'Project':
                return self._create_project_query_mock(mock_project)
            elif model.__name__ == 'User':
                return self._create_user_query_mock(mock_user)
            else:
                return query_mock
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.check_member_conflicts(
            user_id=100,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 9, 30),
            exclude_project_id=1
        )
        
        self.assertTrue(result['has_conflict'])
        self.assertEqual(result['user_id'], 100)
        self.assertEqual(result['user_name'], "Test User")
        self.assertEqual(len(result['conflicting_projects']), 1)
        self.assertEqual(result['conflicting_projects'][0]['project_code'], "PRJ002")
    
    def _create_project_query_mock(self, project):
        """创建项目查询 mock"""
        mock = MagicMock()
        mock.filter.return_value.first.return_value = project
        return mock
    
    def _create_user_query_mock(self, user):
        """创建用户查询 mock"""
        mock = MagicMock()
        mock.filter.return_value.first.return_value = user
        return mock
    
    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_success(self, mock_get_or_404):
        """测试批量添加成员 - 成功"""
        # Mock 项目存在
        mock_project = MagicMock()
        mock_get_or_404.return_value = mock_project
        
        # Mock 成员不存在
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.batch_add_members(
            project_id=1,
            user_ids=[100, 101, 102],
            role_code="dev",
            created_by=1
        )
        
        self.assertEqual(result['added_count'], 3)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['conflicts']), 0)
        self.db.commit.assert_called_once()
    
    @patch('app.services.project_members.service.save_obj')
    def test_update_member_success(self, mock_save_obj):
        """测试更新成员 - 成功"""
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "testuser"
        mock_member.user.real_name = "Test User"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        update_data = {'allocation_pct': 90.0, 'role_code': 'lead'}
        result = self.service.update_member(1, 10, update_data)
        
        mock_save_obj.assert_called_once()
        self.assertEqual(result.username, "testuser")
    
    @patch('app.services.project_members.service.delete_obj')
    def test_delete_member_success(self, mock_delete_obj):
        """测试删除成员 - 成功"""
        mock_member = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        self.service.delete_member(1, 10)
        
        mock_delete_obj.assert_called_once_with(self.db, mock_member)
    
    def test_notify_dept_manager_already_notified(self):
        """测试通知部门经理 - 已通知"""
        mock_member = MagicMock()
        mock_member.dept_manager_notified = True
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = self.service.notify_dept_manager(1, 10)
        
        self.assertEqual(result['message'], "部门经理已通知")
        self.db.commit.assert_not_called()
    
    def test_notify_dept_manager_success(self):
        """测试通知部门经理 - 成功"""
        mock_member = MagicMock()
        mock_member.dept_manager_notified = False
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = self.service.notify_dept_manager(1, 10)
        
        self.assertEqual(result['message'], "部门经理通知已发送")
        self.assertTrue(mock_member.dept_manager_notified)
        self.db.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
