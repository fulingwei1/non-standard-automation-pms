# -*- coding: utf-8 -*-
"""
工时记录服务层单元测试
覆盖率目标：60%+
"""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.schemas.timesheet import TimesheetCreate, TimesheetUpdate
from app.services.timesheet_records import TimesheetRecordsService


class TestTimesheetRecordsService(unittest.TestCase):
    """工时记录服务层测试"""

    def setUp(self):
        """测试前置准备"""
        self.mock_db = MagicMock()
        self.service = TimesheetRecordsService(self.mock_db)
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "test_user"
        self.mock_user.real_name = "测试用户"
        self.mock_user.is_superuser = False

    def test_validate_projects_no_project_id(self):
        """测试验证项目：没有提供任何项目ID"""
        with self.assertRaises(HTTPException) as context:
            self.service._validate_projects(None, None)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("必须指定项目ID", context.exception.detail)

    @patch("app.services.timesheet_records.service.get_or_404")
    def test_validate_projects_valid_project_id(self, mock_get_or_404):
        """测试验证项目：有效的项目ID"""
        mock_project = MagicMock()
        mock_get_or_404.return_value = mock_project

        # 不应该抛出异常
        self.service._validate_projects(project_id=1, rd_project_id=None)
        mock_get_or_404.assert_called_once()

    def test_check_duplicate_timesheet_exists(self):
        """测试重复检查：存在重复记录"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock()  # 有记录

        with self.assertRaises(HTTPException) as context:
            self.service._check_duplicate_timesheet(
                user_id=1,
                work_date=date(2026, 1, 1),
                project_id=1,
                rd_project_id=None,
            )
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已有工时记录", context.exception.detail)

    def test_check_duplicate_timesheet_not_exists(self):
        """测试重复检查：不存在重复记录"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # 无记录

        # 不应该抛出异常
        self.service._check_duplicate_timesheet(
            user_id=1,
            work_date=date(2026, 1, 1),
            project_id=1,
            rd_project_id=None,
        )

    def test_get_user_info_with_department(self):
        """测试获取用户信息：包含部门"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.department_id = 10

        mock_department = MagicMock()
        mock_department.id = 10
        mock_department.name = "研发部"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # 第一次查询返回用户，第二次查询返回部门
        mock_query.first.side_effect = [mock_user, mock_department]

        result = self.service._get_user_info(1)

        self.assertEqual(result["user_name"], "张三")
        self.assertEqual(result["department_id"], 10)
        self.assertEqual(result["department_name"], "研发部")

    def test_get_user_info_without_department(self):
        """测试获取用户信息：无部门"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = None
        mock_user.username = "testuser"
        mock_user.department_id = None

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        result = self.service._get_user_info(1)

        self.assertEqual(result["user_name"], "testuser")
        self.assertIsNone(result["department_id"])
        self.assertIsNone(result["department_name"])

    def test_get_project_info_with_project(self):
        """测试获取项目信息：有项目"""
        mock_project = MagicMock()
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project

        result = self.service._get_project_info(1)

        self.assertEqual(result["project_code"], "PRJ001")
        self.assertEqual(result["project_name"], "测试项目")

    def test_get_project_info_without_project(self):
        """测试获取项目信息：无项目"""
        result = self.service._get_project_info(None)

        self.assertIsNone(result["project_code"])
        self.assertIsNone(result["project_name"])

    def test_check_access_permission_owner(self):
        """测试访问权限检查：所有者访问"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1

        # 不应该抛出异常
        self.service._check_access_permission(mock_timesheet, self.mock_user)

    def test_check_access_permission_not_owner_not_superuser(self):
        """测试访问权限检查：非所有者且非超级管理员"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 999  # 不同的用户

        with self.assertRaises(HTTPException) as context:
            self.service._check_access_permission(mock_timesheet, self.mock_user)
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("无权访问", context.exception.detail)

    def test_check_access_permission_superuser(self):
        """测试访问权限检查：超级管理员"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 999  # 不同的用户

        superuser = MagicMock()
        superuser.id = 1
        superuser.is_superuser = True

        # 不应该抛出异常
        self.service._check_access_permission(mock_timesheet, superuser)

    @patch("app.services.timesheet_records.service.get_or_404")
    def test_delete_timesheet_not_owner(self, mock_get_or_404):
        """测试删除工时：非所有者"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 999
        mock_timesheet.status = "DRAFT"
        mock_get_or_404.return_value = mock_timesheet

        with self.assertRaises(HTTPException) as context:
            self.service.delete_timesheet(1, self.mock_user)
        self.assertEqual(context.exception.status_code, 403)

    @patch("app.services.timesheet_records.service.get_or_404")
    def test_delete_timesheet_not_draft(self, mock_get_or_404):
        """测试删除工时：非草稿状态"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.status = "APPROVED"
        mock_get_or_404.return_value = mock_timesheet

        with self.assertRaises(HTTPException) as context:
            self.service.delete_timesheet(1, self.mock_user)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("草稿状态", context.exception.detail)

    @patch("app.services.timesheet_records.service.delete_obj")
    @patch("app.services.timesheet_records.service.get_or_404")
    def test_delete_timesheet_success(self, mock_get_or_404, mock_delete_obj):
        """测试删除工时：成功删除"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.status = "DRAFT"
        mock_get_or_404.return_value = mock_timesheet

        # 不应该抛出异常
        self.service.delete_timesheet(1, self.mock_user)
        mock_delete_obj.assert_called_once()

    @patch("app.services.timesheet_records.service.get_or_404")
    def test_update_timesheet_not_draft(self, mock_get_or_404):
        """测试更新工时：非草稿状态"""
        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.status = "SUBMITTED"
        mock_get_or_404.return_value = mock_timesheet

        update_data = TimesheetUpdate(work_hours=Decimal("8.0"))

        with self.assertRaises(HTTPException) as context:
            self.service.update_timesheet(1, update_data, self.mock_user)
        self.assertEqual(context.exception.status_code, 400)

    def test_list_timesheets_with_filters(self):
        """测试列表查询：带筛选条件"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.all.return_value = []

        with patch(
            "app.services.timesheet_records.service.apply_timesheet_access_filter"
        ) as mock_filter:
            mock_filter.return_value = mock_query

            items, total = self.service.list_timesheets(
                current_user=self.mock_user,
                offset=0,
                limit=10,
                user_id=1,
                project_id=2,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                status="DRAFT",
            )

            self.assertEqual(total, 10)
            self.assertEqual(len(items), 0)
            # 验证调用了 filter 方法（5次：user_id, project_id, start_date, end_date, status）
            self.assertEqual(mock_query.filter.call_count, 5)


if __name__ == "__main__":
    unittest.main()
