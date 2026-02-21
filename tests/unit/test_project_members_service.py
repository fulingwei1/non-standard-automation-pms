# -*- coding: utf-8 -*-
"""
项目成员服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit, get_or_404等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from datetime import date
from unittest.mock import MagicMock, Mock, patch
from fastapi import HTTPException

from app.services.project_members.service import ProjectMembersService
from app.models.project import ProjectMember, Project
from app.models.user import User
from app.models.organization import Department, Employee


class TestProjectMembersService(unittest.TestCase):
    """项目成员服务核心测试"""

    def setUp(self):
        """初始化测试环境"""
        self.db_mock = MagicMock()
        self.service = ProjectMembersService(self.db_mock)

    # ========== enrich_member_response() 测试 ==========

    def test_enrich_member_response_with_user(self):
        """测试填充成员信息（用户存在）"""
        member = Mock(spec=ProjectMember)
        user = Mock(spec=User)
        user.username = "test_user"
        user.real_name = "张三"
        member.user = user

        result = self.service.enrich_member_response(member)

        self.assertEqual(result.username, "test_user")
        self.assertEqual(result.real_name, "张三")

    def test_enrich_member_response_without_user(self):
        """测试填充成员信息（用户不存在）"""
        member = Mock(spec=ProjectMember)
        member.user = None

        result = self.service.enrich_member_response(member)

        self.assertEqual(result.username, "Unknown")
        self.assertEqual(result.real_name, "Unknown")

    # ========== get_member_by_id() 测试 ==========

    def test_get_member_by_id_success(self):
        """测试获取成员成功"""
        member = Mock(spec=ProjectMember)
        member.id = 1
        member.project_id = 100
        member.user = Mock(username="test_user", real_name="张三")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        result = self.service.get_member_by_id(100, 1, enrich=True)

        self.assertEqual(result.username, "test_user")
        self.db_mock.query.assert_called_once_with(ProjectMember)

    def test_get_member_by_id_not_found(self):
        """测试获取成员失败（不存在）"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.service.get_member_by_id(100, 999)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "项目成员不存在")

    def test_get_member_by_id_no_enrich(self):
        """测试获取成员不填充信息"""
        member = Mock(spec=ProjectMember)
        member.id = 1

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        result = self.service.get_member_by_id(100, 1, enrich=False)

        # 应该没有username/real_name属性
        self.assertFalse(hasattr(result, 'username'))

    # ========== list_members() 测试 ==========

    def test_list_members_basic(self):
        """测试获取成员列表（基础）"""
        member1 = Mock(spec=ProjectMember, id=1, user=Mock(username="user1", real_name="张三"))
        member2 = Mock(spec=ProjectMember, id=2, user=Mock(username="user2", real_name="李四"))

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 2
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [member1, member2]
        self.db_mock.query.return_value = query_mock

        members, total = self.service.list_members(100)

        self.assertEqual(len(members), 2)
        self.assertEqual(total, 2)
        self.assertEqual(members[0].username, "user1")

    def test_list_members_with_role_filter(self):
        """测试角色筛选"""
        member = Mock(spec=ProjectMember, role_code="PM", user=Mock(username="pm1", real_name="PM"))

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [member]
        self.db_mock.query.return_value = query_mock

        members, total = self.service.list_members(100, role="PM")

        self.assertEqual(len(members), 1)
        self.assertEqual(total, 1)

    def test_list_members_with_keyword(self):
        """测试关键词搜索"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        self.db_mock.query.return_value = query_mock

        members, total = self.service.list_members(100, keyword="test")

        self.assertEqual(len(members), 0)
        self.assertEqual(total, 0)

    def test_list_members_with_order_asc(self):
        """测试升序排序"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value.limit.return_value.all.return_value = []

        members, total = self.service.list_members(
            100, order_by="created_at", order_direction="asc"
        )

        self.assertEqual(len(members), 0)

    def test_list_members_pagination(self):
        """测试分页"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 50
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        self.db_mock.query.return_value = query_mock

        members, total = self.service.list_members(100, offset=20, limit=10)

        self.assertEqual(total, 50)

    # ========== check_member_exists() 测试 ==========

    def test_check_member_exists_true(self):
        """测试成员存在"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = Mock(spec=ProjectMember)

        result = self.service.check_member_exists(100, 1)

        self.assertTrue(result)

    def test_check_member_exists_false(self):
        """测试成员不存在"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None

        result = self.service.check_member_exists(100, 1)

        self.assertFalse(result)

    # ========== create_member() 测试 ==========

    @patch('app.services.project_members.service.get_or_404')
    @patch('app.services.project_members.service.save_obj')
    def test_create_member_success(self, save_obj_mock, get_or_404_mock):
        """测试创建成员成功"""
        project = Mock(spec=Project, id=100)
        user = Mock(spec=User, id=1, username="test_user", real_name="张三")
        get_or_404_mock.side_effect = [project, user]

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None  # 不存在

        member = self.service.create_member(
            project_id=100,
            user_id=1,
            role_code="PM",
            allocation_pct=80,
            created_by=999
        )

        save_obj_mock.assert_called_once()
        self.assertEqual(get_or_404_mock.call_count, 2)

    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_project_not_found(self, get_or_404_mock):
        """测试创建成员失败（项目不存在）"""
        get_or_404_mock.side_effect = HTTPException(status_code=404, detail="项目不存在")

        with self.assertRaises(HTTPException) as context:
            self.service.create_member(100, 1, "PM")

        self.assertEqual(context.exception.status_code, 404)

    @patch('app.services.project_members.service.get_or_404')
    def test_create_member_already_exists(self, get_or_404_mock):
        """测试创建成员失败（已存在）"""
        project = Mock(spec=Project)
        user = Mock(spec=User)
        get_or_404_mock.side_effect = [project, user]

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = Mock(spec=ProjectMember)  # 已存在

        with self.assertRaises(HTTPException) as context:
            self.service.create_member(100, 1, "PM")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "该用户已是项目成员")

    @patch('app.services.project_members.service.get_or_404')
    @patch('app.services.project_members.service.save_obj')
    def test_create_member_with_dates(self, save_obj_mock, get_or_404_mock):
        """测试创建成员（包含日期）"""
        project = Mock(spec=Project)
        user = Mock(spec=User, username="test", real_name="测试")
        get_or_404_mock.side_effect = [project, user]

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None

        member = self.service.create_member(
            project_id=100,
            user_id=1,
            role_code="DEV",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        save_obj_mock.assert_called_once()

    # ========== update_member() 测试 ==========

    @patch('app.services.project_members.service.save_obj')
    def test_update_member_success(self, save_obj_mock):
        """测试更新成员成功"""
        member = Mock(spec=ProjectMember, id=1, allocation_pct=100)
        member.user = Mock(username="test", real_name="测试")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        update_data = {"allocation_pct": 50, "remark": "更新备注"}
        result = self.service.update_member(100, 1, update_data)

        self.assertEqual(result.allocation_pct, 50)
        self.assertEqual(result.remark, "更新备注")
        save_obj_mock.assert_called_once()

    def test_update_member_not_found(self):
        """测试更新成员失败（不存在）"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.service.update_member(100, 999, {})

        self.assertEqual(context.exception.status_code, 404)

    @patch('app.services.project_members.service.save_obj')
    def test_update_member_ignore_invalid_fields(self, save_obj_mock):
        """测试更新成员忽略无效字段"""
        member = Mock(spec=ProjectMember, id=1)
        member.user = Mock(username="test", real_name="测试")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        update_data = {"invalid_field": "should_ignore", "remark": "valid"}
        result = self.service.update_member(100, 1, update_data)

        # invalid_field不应该被设置
        self.assertFalse(hasattr(result, 'invalid_field'))

    # ========== delete_member() 测试 ==========

    @patch('app.services.project_members.service.delete_obj')
    def test_delete_member_success(self, delete_obj_mock):
        """测试删除成员成功"""
        member = Mock(spec=ProjectMember, id=1)

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        self.service.delete_member(100, 1)

        delete_obj_mock.assert_called_once_with(self.db_mock, member)

    def test_delete_member_not_found(self):
        """测试删除成员失败（不存在）"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.service.delete_member(100, 999)

        self.assertEqual(context.exception.status_code, 404)

    # ========== check_member_conflicts() 测试 ==========

    def test_check_member_conflicts_no_dates(self):
        """测试冲突检查（无日期）"""
        result = self.service.check_member_conflicts(1, None, None)

        self.assertFalse(result['has_conflict'])

    def test_check_member_conflicts_no_conflict(self):
        """测试冲突检查（无冲突）"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = []

        result = self.service.check_member_conflicts(
            1,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )

        self.assertFalse(result['has_conflict'])

    def test_check_member_conflicts_has_conflict(self):
        """测试冲突检查（有冲突）"""
        member = Mock(
            spec=ProjectMember,
            project_id=200,
            allocation_pct=80,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 10, 31)
        )
        project = Mock(
            spec=Project,
            id=200,
            project_code="PRJ-002",
            project_name="冲突项目"
        )

        user = Mock(spec=User, id=1, username="test", real_name="张三")

        # Mock ProjectMember query
        query_mock_member = MagicMock()
        query_mock_member.filter.return_value = query_mock_member
        query_mock_member.all.return_value = [member]

        # Mock Project query
        query_mock_project = MagicMock()
        query_mock_project.filter.return_value = query_mock_project
        query_mock_project.first.return_value = project

        # Mock User query
        query_mock_user = MagicMock()
        query_mock_user.filter.return_value = query_mock_user
        query_mock_user.first.return_value = user

        self.db_mock.query.side_effect = [query_mock_member, query_mock_project, query_mock_user]

        result = self.service.check_member_conflicts(
            1,
            date(2024, 6, 1),
            date(2024, 9, 30),
            exclude_project_id=100
        )

        self.assertTrue(result['has_conflict'])
        self.assertEqual(result['user_id'], 1)
        self.assertEqual(result['user_name'], "张三")
        self.assertEqual(len(result['conflicting_projects']), 1)
        self.assertEqual(result['conflict_count'], 1)
        self.assertEqual(result['conflicting_projects'][0]['project_code'], "PRJ-002")

    def test_check_member_conflicts_exclude_project(self):
        """测试冲突检查（排除指定项目）"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []
        self.db_mock.query.return_value = query_mock

        result = self.service.check_member_conflicts(
            1,
            date(2024, 1, 1),
            date(2024, 12, 31),
            exclude_project_id=100
        )

        self.assertFalse(result['has_conflict'])

    # ========== batch_add_members() 测试 ==========

    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_success(self, get_or_404_mock):
        """测试批量添加成员成功"""
        project = Mock(spec=Project)
        get_or_404_mock.return_value = project

        query_mock = self.db_mock.query.return_value
        # Mock check_member_exists: all return False (不存在)
        query_mock.filter.return_value.first.return_value = None
        # Mock check_member_conflicts: no conflicts
        query_mock.filter.return_value.all.return_value = []

        result = self.service.batch_add_members(
            project_id=100,
            user_ids=[1, 2, 3],
            role_code="DEV"
        )

        self.assertEqual(result['added_count'], 3)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(len(result['conflicts']), 0)
        self.assertEqual(self.db_mock.add.call_count, 3)
        self.db_mock.commit.assert_called_once()

    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_with_skip(self, get_or_404_mock):
        """测试批量添加成员（部分跳过）"""
        project = Mock(spec=Project)
        get_or_404_mock.return_value = project

        # 第一个用户已存在，其他不存在
        existing_member = Mock(spec=ProjectMember)
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.side_effect = [
            existing_member,  # user 1 exists
            None,  # user 2 doesn't exist
            None,  # user 3 doesn't exist
        ]
        query_mock.filter.return_value.all.return_value = []  # no conflicts

        result = self.service.batch_add_members(
            project_id=100,
            user_ids=[1, 2, 3],
            role_code="DEV"
        )

        self.assertEqual(result['added_count'], 2)
        self.assertEqual(result['skipped_count'], 1)

    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_with_conflicts(self, get_or_404_mock):
        """测试批量添加成员（有冲突）"""
        project = Mock(spec=Project)
        get_or_404_mock.return_value = project

        conflicting_member = Mock(
            spec=ProjectMember,
            project_id=200,
            allocation_pct=100,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 10, 31)
        )
        conflicting_project = Mock(
            spec=Project,
            id=200,
            project_code="PRJ-200",
            project_name="冲突项目"
        )
        user1 = Mock(spec=User, id=1, username="user1", real_name="用户1")

        # Mock check_member_exists for 3 users (all don't exist)
        query_mock_exists1 = MagicMock()
        query_mock_exists1.filter.return_value = query_mock_exists1
        query_mock_exists1.first.return_value = None

        query_mock_exists2 = MagicMock()
        query_mock_exists2.filter.return_value = query_mock_exists2
        query_mock_exists2.first.return_value = None

        query_mock_exists3 = MagicMock()
        query_mock_exists3.filter.return_value = query_mock_exists3
        query_mock_exists3.first.return_value = None

        # Mock conflict check for user 1 (has conflict)
        query_mock_conflict1 = MagicMock()
        query_mock_conflict1.filter.return_value = query_mock_conflict1
        query_mock_conflict1.all.return_value = [conflicting_member]

        query_mock_project1 = MagicMock()
        query_mock_project1.filter.return_value = query_mock_project1
        query_mock_project1.first.return_value = conflicting_project

        query_mock_user1 = MagicMock()
        query_mock_user1.filter.return_value = query_mock_user1
        query_mock_user1.first.return_value = user1

        # Mock conflict check for user 2 (no conflict)
        query_mock_conflict2 = MagicMock()
        query_mock_conflict2.filter.return_value = query_mock_conflict2
        query_mock_conflict2.all.return_value = []

        # Mock conflict check for user 3 (no conflict)
        query_mock_conflict3 = MagicMock()
        query_mock_conflict3.filter.return_value = query_mock_conflict3
        query_mock_conflict3.all.return_value = []

        self.db_mock.query.side_effect = [
            query_mock_exists1,  # check user 1 exists
            query_mock_conflict1,  # check user 1 conflict
            query_mock_project1,  # get conflicting project
            query_mock_user1,  # get user 1
            query_mock_exists2,  # check user 2 exists
            query_mock_conflict2,  # check user 2 conflict (no conflict)
            query_mock_exists3,  # check user 3 exists
            query_mock_conflict3,  # check user 3 conflict (no conflict)
        ]

        result = self.service.batch_add_members(
            project_id=100,
            user_ids=[1, 2, 3],
            role_code="DEV",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        # 第一个有冲突，第二、三个成功
        self.assertEqual(result['added_count'], 2)
        self.assertEqual(len(result['conflicts']), 1)

    @patch('app.services.project_members.service.get_or_404')
    def test_batch_add_members_project_not_found(self, get_or_404_mock):
        """测试批量添加成员（项目不存在）"""
        get_or_404_mock.side_effect = HTTPException(status_code=404, detail="项目不存在")

        with self.assertRaises(HTTPException) as context:
            self.service.batch_add_members(100, [1, 2], "DEV")

        self.assertEqual(context.exception.status_code, 404)

    # ========== notify_dept_manager() 测试 ==========

    def test_notify_dept_manager_success(self):
        """测试通知部门经理成功"""
        member = Mock(spec=ProjectMember, dept_manager_notified=False)

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        result = self.service.notify_dept_manager(100, 1)

        self.assertTrue(member.dept_manager_notified)
        self.assertEqual(result['message'], "部门经理通知已发送")
        self.db_mock.commit.assert_called_once()

    def test_notify_dept_manager_already_notified(self):
        """测试重复通知"""
        member = Mock(spec=ProjectMember, dept_manager_notified=True)

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        result = self.service.notify_dept_manager(100, 1)

        self.assertEqual(result['message'], "部门经理已通知")
        # 不应该再次commit
        self.db_mock.commit.assert_not_called()

    def test_notify_dept_manager_not_found(self):
        """测试通知部门经理（成员不存在）"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.service.notify_dept_manager(100, 999)

        self.assertEqual(context.exception.status_code, 404)

    # ========== get_dept_users_for_project() 测试 ==========

    @patch('app.services.project_members.service.get_or_404')
    def test_get_dept_users_for_project_success(self, get_or_404_mock):
        """测试获取部门用户列表成功"""
        dept = Mock(spec=Department, id=1, dept_name="研发部")
        get_or_404_mock.return_value = dept

        employee1 = Mock(spec=Employee, id=10, department="研发部", is_active=True)
        employee2 = Mock(spec=Employee, id=11, department="研发部", is_active=True)

        user1 = Mock(spec=User, id=1, employee_id=10, username="user1", real_name="张三", is_active=True)
        user2 = Mock(spec=User, id=2, employee_id=11, username="user2", real_name="李四", is_active=True)

        # Mock Employee query
        query_mock_employee = MagicMock()
        query_mock_employee.filter.return_value = query_mock_employee
        query_mock_employee.all.return_value = [employee1, employee2]

        # Mock User query
        query_mock_user = MagicMock()
        query_mock_user.filter.return_value = query_mock_user
        query_mock_user.all.return_value = [user1, user2]

        # Mock ProjectMember query (user1 is already a member)
        query_mock_member = MagicMock()
        query_mock_member.filter.return_value = query_mock_member
        query_mock_member.all.return_value = [(1,)]

        self.db_mock.query.side_effect = [query_mock_employee, query_mock_user, query_mock_member]

        result = self.service.get_dept_users_for_project(100, 1)

        self.assertEqual(result['dept_id'], 1)
        self.assertEqual(result['dept_name'], "研发部")
        self.assertEqual(len(result['users']), 2)
        self.assertTrue(result['users'][0]['is_member'])  # user1 is member
        self.assertFalse(result['users'][1]['is_member'])  # user2 is not member

    @patch('app.services.project_members.service.get_or_404')
    def test_get_dept_users_for_project_dept_not_found(self, get_or_404_mock):
        """测试获取部门用户列表（部门不存在）"""
        get_or_404_mock.side_effect = HTTPException(status_code=404, detail="部门不存在")

        with self.assertRaises(HTTPException) as context:
            self.service.get_dept_users_for_project(100, 999)

        self.assertEqual(context.exception.status_code, 404)

    @patch('app.services.project_members.service.get_or_404')
    def test_get_dept_users_for_project_no_employees(self, get_or_404_mock):
        """测试获取部门用户列表（无员工）"""
        dept = Mock(spec=Department, id=1, dept_name="空部门")
        get_or_404_mock.return_value = dept

        # Mock Employee query (empty)
        query_mock_employee = MagicMock()
        query_mock_employee.filter.return_value = query_mock_employee
        query_mock_employee.all.return_value = []

        # Mock User query (empty)
        query_mock_user = MagicMock()
        query_mock_user.filter.return_value = query_mock_user
        query_mock_user.all.return_value = []

        # Mock ProjectMember query (empty)
        query_mock_member = MagicMock()
        query_mock_member.filter.return_value = query_mock_member
        query_mock_member.all.return_value = []

        self.db_mock.query.side_effect = [query_mock_employee, query_mock_user, query_mock_member]

        result = self.service.get_dept_users_for_project(100, 1)

        self.assertEqual(len(result['users']), 0)


class TestProjectMembersServiceEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.service = ProjectMembersService(self.db_mock)

    def test_list_members_empty_result(self):
        """测试空列表"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        self.db_mock.query.return_value = query_mock

        members, total = self.service.list_members(100)

        self.assertEqual(len(members), 0)
        self.assertEqual(total, 0)

    def test_list_members_invalid_order_field(self):
        """测试无效的排序字段"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.offset.return_value.limit.return_value.all.return_value = []

        # 无效字段应该被忽略
        members, total = self.service.list_members(100, order_by="invalid_field")

        self.assertEqual(len(members), 0)

    @patch('app.services.project_members.service.save_obj')
    def test_update_member_empty_data(self, save_obj_mock):
        """测试空更新数据"""
        member = Mock(spec=ProjectMember)
        member.user = Mock(username="test", real_name="测试")

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = member

        result = self.service.update_member(100, 1, {})

        save_obj_mock.assert_called_once()

    def test_batch_add_members_empty_list(self):
        """测试空用户列表"""
        with patch('app.services.project_members.service.get_or_404') as get_or_404_mock:
            project = Mock(spec=Project)
            get_or_404_mock.return_value = project

            result = self.service.batch_add_members(100, [], "DEV")

            self.assertEqual(result['added_count'], 0)
            self.assertEqual(result['skipped_count'], 0)

    def test_check_member_conflicts_user_not_found(self):
        """测试冲突检查（用户不存在）"""
        member = Mock(
            spec=ProjectMember,
            project_id=200,
            allocation_pct=80,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 10, 31)
        )
        project = Mock(spec=Project, id=200, project_code="PRJ-200", project_name="测试")

        query_mock_member = MagicMock()
        query_mock_member.filter.return_value = query_mock_member
        query_mock_member.all.return_value = [member]

        query_mock_project = MagicMock()
        query_mock_project.filter.return_value = query_mock_project
        query_mock_project.first.return_value = project

        query_mock_user = MagicMock()
        query_mock_user.filter.return_value = query_mock_user
        query_mock_user.first.return_value = None  # User not found

        self.db_mock.query.side_effect = [query_mock_member, query_mock_project, query_mock_user]

        result = self.service.check_member_conflicts(
            999,
            date(2024, 1, 1),
            date(2024, 12, 31)
        )

        self.assertTrue(result['has_conflict'])
        self.assertEqual(result['user_name'], 'User 999')


if __name__ == "__main__":
    unittest.main()
