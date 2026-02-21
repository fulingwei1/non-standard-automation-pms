# -*- coding: utf-8 -*-
"""
项目成员服务层单元测试（完整版）

覆盖 ProjectMembersService 核心业务逻辑
目标覆盖率：60%+
"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch, call

from fastapi import HTTPException

from app.services.project_members.service import ProjectMembersService


class TestProjectMembersService(unittest.TestCase):
    """项目成员服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ProjectMembersService(self.db)
    
    # ==================== 成员信息填充测试 ====================
    
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
    
    # ==================== 成员存在性检查测试 ====================
    
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
    
    # ==================== 获取成员详情测试 ====================
    
    def test_get_member_by_id_success_with_enrich(self):
        """测试获取成员详情 - 成功（填充用户信息）"""
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "testuser"
        mock_member.user.real_name = "Test User"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = self.service.get_member_by_id(1, 10, enrich=True)
        
        self.assertEqual(result.username, "testuser")
        self.assertEqual(result.real_name, "Test User")
    
    def test_get_member_by_id_success_without_enrich(self):
        """测试获取成员详情 - 成功（不填充用户信息）"""
        mock_member = MagicMock()
        # 确保 mock 对象在未填充时没有这些属性
        del mock_member.username
        del mock_member.real_name
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        result = self.service.get_member_by_id(1, 10, enrich=False)
        
        # 不应该设置 username 和 real_name
        # enrich=False 时，enrich_member_response 不会被调用
        self.assertEqual(result, mock_member)
    
    def test_get_member_by_id_not_found(self):
        """测试获取成员详情 - 未找到"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_member_by_id(1, 10)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目成员不存在")
    
    # ==================== 列表查询测试 ====================
    
    @patch('app.services.project_members.service.apply_pagination')
    @patch('app.services.project_members.service.apply_keyword_filter')
    def test_list_members_basic(self, mock_keyword_filter, mock_pagination):
        """测试列表查询 - 基本查询"""
        mock_member1 = MagicMock()
        mock_member1.user = MagicMock()
        mock_member1.user.username = "user1"
        mock_member1.user.real_name = "User One"
        
        mock_member2 = MagicMock()
        mock_member2.user = MagicMock()
        mock_member2.user.username = "user2"
        mock_member2.user.real_name = "User Two"
        
        query_mock = self.db.query.return_value.filter.return_value
        mock_keyword_filter.return_value = query_mock
        # 设置排序后的 count
        query_mock.order_by.return_value.count.return_value = 2
        mock_pagination.return_value.all.return_value = [mock_member1, mock_member2]
        
        members, total = self.service.list_members(project_id=1)
        
        self.assertEqual(len(members), 2)
        self.assertEqual(total, 2)
        self.assertEqual(members[0].username, "user1")
        self.assertEqual(members[1].username, "user2")
    
    @patch('app.services.project_members.service.apply_pagination')
    @patch('app.services.project_members.service.apply_keyword_filter')
    def test_list_members_with_role_filter(self, mock_keyword_filter, mock_pagination):
        """测试列表查询 - 角色筛选"""
        query_mock = self.db.query.return_value.filter.return_value
        mock_keyword_filter.return_value = query_mock.filter.return_value
        # 设置排序后的 count
        query_mock.filter.return_value.order_by.return_value.count.return_value = 1
        
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "dev1"
        mock_member.user.real_name = "Developer One"
        
        mock_pagination.return_value.all.return_value = [mock_member]
        
        members, total = self.service.list_members(project_id=1, role="dev")
        
        self.assertEqual(len(members), 1)
        self.assertEqual(total, 1)
    
    @patch('app.services.project_members.service.apply_pagination')
    @patch('app.services.project_members.service.apply_keyword_filter')
    def test_list_members_with_keyword(self, mock_keyword_filter, mock_pagination):
        """测试列表查询 - 关键词搜索"""
        query_mock = MagicMock()
        mock_keyword_filter.return_value = query_mock
        query_mock.count.return_value = 1
        
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "searchuser"
        mock_member.user.real_name = "Search User"
        
        mock_pagination.return_value.all.return_value = [mock_member]
        
        members, total = self.service.list_members(project_id=1, keyword="search")
        
        # 验证 apply_keyword_filter 被调用
        mock_keyword_filter.assert_called_once()
        self.assertEqual(len(members), 1)
    
    @patch('app.services.project_members.service.apply_pagination')
    @patch('app.services.project_members.service.apply_keyword_filter')
    def test_list_members_with_order_asc(self, mock_keyword_filter, mock_pagination):
        """测试列表查询 - 升序排序"""
        query_mock = MagicMock()
        mock_keyword_filter.return_value = query_mock
        query_mock.order_by.return_value.count.return_value = 0
        
        mock_pagination.return_value.all.return_value = []
        
        members, total = self.service.list_members(
            project_id=1,
            order_by="created_at",
            order_direction="asc"
        )
        
        # 验证排序被调用
        query_mock.order_by.assert_called_once()
        self.assertEqual(len(members), 0)
    
    @patch('app.services.project_members.service.apply_pagination')
    @patch('app.services.project_members.service.apply_keyword_filter')
    def test_list_members_with_order_desc(self, mock_keyword_filter, mock_pagination):
        """测试列表查询 - 降序排序"""
        query_mock = MagicMock()
        mock_keyword_filter.return_value = query_mock
        query_mock.order_by.return_value.count.return_value = 0
        
        mock_pagination.return_value.all.return_value = []
        
        members, total = self.service.list_members(
            project_id=1,
            order_by="created_at",
            order_direction="desc"
        )
        
        # 验证排序被调用
        query_mock.order_by.assert_called_once()
    
    @patch('app.services.project_members.service.apply_pagination')
    @patch('app.services.project_members.service.apply_keyword_filter')
    def test_list_members_without_enrich(self, mock_keyword_filter, mock_pagination):
        """测试列表查询 - 不填充用户信息"""
        mock_member = MagicMock(spec=['id', 'user_id', 'project_id', 'role_code'])
        
        query_mock = MagicMock()
        mock_keyword_filter.return_value = query_mock
        query_mock.order_by.return_value.count.return_value = 1
        mock_pagination.return_value.all.return_value = [mock_member]
        
        members, total = self.service.list_members(project_id=1, enrich=False)
        
        # 成员不应该被填充
        self.assertEqual(len(members), 1)
        # enrich=False 时不会调用 enrich_member_response，所以不会有 username
        self.assertEqual(members[0], mock_member)
    
    # ==================== 创建成员测试 ====================
    
    @patch('app.services.project_members.service.save_obj')
    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_success(self, mock_get_or_404, mock_save_obj):
        """测试创建成员 - 成功"""
        # Mock 项目和用户存在
        mock_project = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "newuser"
        mock_user.real_name = "New User"
        mock_get_or_404.side_effect = [mock_project, mock_user]
        
        # Mock 成员不存在
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock 保存
        def save_side_effect(db, obj):
            obj.user = mock_user
            return obj
        
        mock_save_obj.side_effect = save_side_effect
        
        result = self.service.create_member(
            project_id=1,
            user_id=100,
            role_code="dev",
            allocation_pct=80.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            commitment_level="high",
            reporting_to_pm=True,
            remark="New team member",
            created_by=1
        )
        
        # 验证调用
        mock_save_obj.assert_called_once()
        self.assertEqual(result.username, "newuser")
    
    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_project_not_found(self, mock_get_or_404):
        """测试创建成员 - 项目不存在"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="项目不存在")
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_member(project_id=999, user_id=100, role_code="dev")
        
        self.assertEqual(context.exception.status_code, 404)
    
    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_user_not_found(self, mock_get_or_404):
        """测试创建成员 - 用户不存在"""
        mock_project = MagicMock()
        mock_get_or_404.side_effect = [
            mock_project,
            HTTPException(status_code=404, detail="用户不存在")
        ]
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_member(project_id=1, user_id=999, role_code="dev")
        
        self.assertEqual(context.exception.status_code, 404)
    
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
            self.service.create_member(project_id=1, user_id=100, role_code="dev")
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "该用户已是项目成员")
    
    # ==================== 更新成员测试 ====================
    
    @patch('app.services.project_members.service.save_obj')
    def test_update_member_success(self, mock_save_obj):
        """测试更新成员 - 成功"""
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "testuser"
        mock_member.user.real_name = "Test User"
        mock_member.allocation_pct = 80.0
        mock_member.role_code = "dev"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        update_data = {'allocation_pct': 90.0, 'role_code': 'lead'}
        result = self.service.update_member(1, 10, update_data)
        
        mock_save_obj.assert_called_once()
        self.assertEqual(mock_member.allocation_pct, 90.0)
        self.assertEqual(mock_member.role_code, 'lead')
    
    def test_update_member_not_found(self):
        """测试更新成员 - 成员不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.update_member(1, 999, {'allocation_pct': 90.0})
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目成员不存在")
    
    @patch('app.services.project_members.service.save_obj')
    def test_update_member_ignore_invalid_fields(self, mock_save_obj):
        """测试更新成员 - 忽略无效字段"""
        mock_member = MagicMock()
        mock_member.user = MagicMock()
        mock_member.user.username = "testuser"
        mock_member.user.real_name = "Test User"
        
        # 设置 hasattr 模拟
        def custom_hasattr(obj, name):
            return name in ['allocation_pct', 'role_code']
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        with patch('builtins.hasattr', side_effect=custom_hasattr):
            update_data = {
                'allocation_pct': 90.0,
                'invalid_field': 'should_be_ignored'
            }
            result = self.service.update_member(1, 10, update_data)
        
        # invalid_field 不应该被设置
        mock_save_obj.assert_called_once()
    
    # ==================== 删除成员测试 ====================
    
    @patch('app.services.project_members.service.delete_obj')
    def test_delete_member_success(self, mock_delete_obj):
        """测试删除成员 - 成功"""
        mock_member = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_member
        
        self.service.delete_member(1, 10)
        
        mock_delete_obj.assert_called_once_with(self.db, mock_member)
    
    def test_delete_member_not_found(self):
        """测试删除成员 - 成员不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.delete_member(1, 999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目成员不存在")
    
    # ==================== 冲突检查测试 ====================
    
    def test_check_member_conflicts_no_dates(self):
        """测试冲突检查 - 无日期"""
        result = self.service.check_member_conflicts(100, None, None)
        
        self.assertFalse(result['has_conflict'])
    
    def test_check_member_conflicts_no_start_date(self):
        """测试冲突检查 - 无开始日期"""
        result = self.service.check_member_conflicts(100, None, date(2024, 12, 31))
        
        self.assertFalse(result['has_conflict'])
    
    def test_check_member_conflicts_no_end_date(self):
        """测试冲突检查 - 无结束日期"""
        result = self.service.check_member_conflicts(100, date(2024, 1, 1), None)
        
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
        call_count = [0]
        
        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:  # 第一次调用是查找冲突成员
                m = MagicMock()
                m.filter.return_value.all.return_value = [mock_member]
                return m
            elif model.__name__ == 'Project':
                return self._create_project_query_mock(mock_project)
            elif model.__name__ == 'User':
                return self._create_user_query_mock(mock_user)
            return MagicMock()
        
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
        self.assertEqual(result['conflict_count'], 1)
    
    def test_check_member_conflicts_user_not_found(self):
        """测试冲突检查 - 用户不存在时使用默认名称"""
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
        
        # 设置查询返回值
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.all.return_value = [mock_member]
        
        # 用户不存在
        def query_side_effect(model):
            if model.__name__ == 'Project':
                return self._create_project_query_mock(mock_project)
            elif model.__name__ == 'User':
                return self._create_user_query_mock(None)
            else:
                return query_mock
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.check_member_conflicts(
            user_id=999,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 9, 30)
        )
        
        self.assertTrue(result['has_conflict'])
        self.assertEqual(result['user_name'], 'User 999')
    
    # ==================== 批量添加成员测试 ====================
    
    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_all_success(self, mock_get_or_404):
        """测试批量添加成员 - 全部成功"""
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
            allocation_pct=80.0,
            created_by=1
        )
        
        self.assertEqual(result['added_count'], 3)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['conflicts']), 0)
        self.assertIn('成功添加 3 位成员', result['message'])
        self.db.commit.assert_called_once()
    
    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_partial_skip(self, mock_get_or_404):
        """测试批量添加成员 - 部分跳过（已存在）"""
        # Mock 项目存在
        mock_project = MagicMock()
        mock_get_or_404.return_value = mock_project
        
        # Mock 部分成员已存在
        def check_member_side_effect(*args):
            # 第一个用户已存在
            if args[0].filter.call_count == 1:
                return MagicMock()
            return None
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            MagicMock(),  # 第一个成员已存在
            None,  # 第二个不存在
            None   # 第三个不存在
        ]
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.batch_add_members(
            project_id=1,
            user_ids=[100, 101, 102],
            role_code="dev"
        )
        
        self.assertEqual(result['added_count'], 2)
        self.assertEqual(result['skipped_count'], 1)
        self.assertIn('跳过 1 位', result['message'])
    
    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_with_conflicts(self, mock_get_or_404):
        """测试批量添加成员 - 有时间冲突"""
        # Mock 项目存在
        mock_project = MagicMock()
        mock_get_or_404.return_value = mock_project
        
        # Mock 第一个用户有冲突
        mock_conflict_member = MagicMock()
        mock_conflict_member.project_id = 2
        mock_conflict_member.allocation_pct = 100
        mock_conflict_member.start_date = date(2024, 1, 1)
        mock_conflict_member.end_date = date(2024, 12, 31)
        
        mock_conflict_project = MagicMock()
        mock_conflict_project.id = 2
        mock_conflict_project.project_code = "PRJ002"
        mock_conflict_project.project_name = "Conflict Project"
        
        mock_user = MagicMock()
        mock_user.id = 100
        mock_user.username = "user100"
        mock_user.real_name = "User 100"
        
        # 设置查询
        call_count = [0]
        
        def query_side_effect(model):
            call_count[0] += 1
            if model.__name__ == 'ProjectMember':
                if call_count[0] in [1, 4]:  # check_member_exists
                    m = MagicMock()
                    m.filter.return_value.first.return_value = None
                    return m
                elif call_count[0] == 2:  # check_conflicts 第一个用户
                    m = MagicMock()
                    m.filter.return_value.all.return_value = [mock_conflict_member]
                    return m
                elif call_count[0] == 5:  # check_conflicts 第二个用户
                    m = MagicMock()
                    m.filter.return_value.all.return_value = []
                    return m
                else:
                    m = MagicMock()
                    m.filter.return_value.first.return_value = None
                    m.filter.return_value.all.return_value = []
                    return m
            elif model.__name__ == 'Project':
                return self._create_project_query_mock(mock_conflict_project)
            elif model.__name__ == 'User':
                return self._create_user_query_mock(mock_user)
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.batch_add_members(
            project_id=1,
            user_ids=[100, 101],
            role_code="dev",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 12, 31)
        )
        
        self.assertEqual(result['added_count'], 1)
        self.assertEqual(len(result['conflicts']), 1)
        self.assertIn('发现 1 个时间冲突', result['message'])
    
    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_project_not_found(self, mock_get_or_404):
        """测试批量添加成员 - 项目不存在"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="项目不存在")
        
        with self.assertRaises(HTTPException) as context:
            self.service.batch_add_members(
                project_id=999,
                user_ids=[100, 101],
                role_code="dev"
            )
        
        self.assertEqual(context.exception.status_code, 404)
    
    # ==================== 通知部门经理测试 ====================
    
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
    
    def test_notify_dept_manager_not_found(self):
        """测试通知部门经理 - 成员不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.notify_dept_manager(1, 999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目成员不存在")
    
    # ==================== 获取部门用户测试 ====================
    
    @patch('app.services.project_members.service.get_or_404')
    def test_get_dept_users_for_project_success(self, mock_get_or_404):
        """测试获取部门用户列表 - 成功"""
        # Mock 部门
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"
        mock_get_or_404.return_value = mock_dept
        
        # Mock 员工
        mock_employee1 = MagicMock()
        mock_employee1.id = 10
        mock_employee2 = MagicMock()
        mock_employee2.id = 11
        
        # Mock 用户
        mock_user1 = MagicMock()
        mock_user1.id = 100
        mock_user1.username = "user1"
        mock_user1.real_name = "User One"
        mock_user1.employee_id = 10
        
        mock_user2 = MagicMock()
        mock_user2.id = 101
        mock_user2.username = "user2"
        mock_user2.real_name = "User Two"
        mock_user2.employee_id = 11
        
        # Mock 已存在的成员
        existing_members = [(100,)]
        
        # 设置查询 - 使用 call_count 来跟踪调用顺序
        call_count = [0]
        
        def query_side_effect(*args, **kwargs):
            call_count[0] += 1
            # 第1次: Employee 查询
            if call_count[0] == 1:
                m = MagicMock()
                m.filter.return_value.all.return_value = [mock_employee1, mock_employee2]
                return m
            # 第2次: User 查询
            elif call_count[0] == 2:
                m = MagicMock()
                m.filter.return_value.all.return_value = [mock_user1, mock_user2]
                return m
            # 第3次: ProjectMember.user_id 查询
            elif call_count[0] == 3:
                m = MagicMock()
                m.filter.return_value.all.return_value = existing_members
                return m
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        result = self.service.get_dept_users_for_project(project_id=1, dept_id=1)
        
        self.assertEqual(result['dept_id'], 1)
        self.assertEqual(result['dept_name'], "研发部")
        self.assertEqual(len(result['users']), 2)
        self.assertTrue(result['users'][0]['is_member'])  # user1 是成员
        self.assertFalse(result['users'][1]['is_member'])  # user2 不是成员
    
    @patch('app.services.project_members.service.get_or_404')
    def test_get_dept_users_for_project_dept_not_found(self, mock_get_or_404):
        """测试获取部门用户列表 - 部门不存在"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="部门不存在")
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_dept_users_for_project(project_id=1, dept_id=999)
        
        self.assertEqual(context.exception.status_code, 404)
    
    # ==================== 辅助方法 ====================
    
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


if __name__ == '__main__':
    unittest.main()
