# -*- coding: utf-8 -*-
"""
工时记录服务单元测试

Mock策略：
- 只mock外部依赖（db.query, db.add, db.commit等）
- 让业务逻辑真正执行
- 覆盖主要方法和边界情况
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from fastapi import HTTPException

from app.services.timesheet_records.service import TimesheetRecordsService
from app.schemas.timesheet import TimesheetCreate, TimesheetUpdate


class TestTimesheetRecordsService(unittest.TestCase):
    """工时记录服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TimesheetRecordsService(self.db)
        
        # Mock当前用户
        self.current_user = MagicMock()
        self.current_user.id = 1
        self.current_user.username = "test_user"
        self.current_user.real_name = "测试用户"
        self.current_user.department_id = 10
        self.current_user.is_superuser = False

    # ==================== list_timesheets 测试 ====================

    @patch('app.core.permissions.timesheet.apply_timesheet_access_filter')
    def test_list_timesheets_basic(self, mock_access_filter):
        """测试基本的工时记录列表获取"""
        # 准备mock数据
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_access_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        
        # Mock工时记录
        mock_ts1 = self._create_mock_timesheet(1, "2025-01-15")
        mock_ts2 = self._create_mock_timesheet(2, "2025-01-16")
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            mock_ts1, mock_ts2
        ]
        
        # Mock相关查询
        self._setup_user_project_mocks()
        
        # 执行
        items, total = self.service.list_timesheets(
            current_user=self.current_user,
            offset=0,
            limit=10
        )
        
        # 验证
        self.assertEqual(len(items), 2)
        self.assertEqual(total, 2)
        self.db.query.assert_called()

    @patch('app.core.permissions.timesheet.apply_timesheet_access_filter')
    def test_list_timesheets_with_filters(self, mock_access_filter):
        """测试带筛选条件的列表获取"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_access_filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        
        # 执行带筛选
        items, total = self.service.list_timesheets(
            current_user=self.current_user,
            offset=0,
            limit=10,
            user_id=1,
            project_id=100,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status="APPROVED"
        )
        
        # 验证filter被多次调用（每个筛选条件一次）
        self.assertGreaterEqual(mock_query.filter.call_count, 5)

    # ==================== create_timesheet 测试 ====================

    @patch('app.services.timesheet_records.service.save_obj')
    @patch('app.services.timesheet_records.service.get_or_404')
    def test_create_timesheet_success(self, mock_get_or_404, mock_save_obj):
        """测试成功创建工时记录"""
        # 准备输入数据
        timesheet_in = TimesheetCreate(
            project_id=100,
            rd_project_id=None,
            task_id=200,
            work_date=date(2025, 1, 15),
            work_hours=Decimal("8.0"),
            work_type="NORMAL",
            description="开发功能A"
        )
        
        # Mock项目存在
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        mock_get_or_404.return_value = mock_project
        
        # Mock用户部门信息
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "测试用户"
        mock_user.department_id = 10
        
        mock_dept = MagicMock()
        mock_dept.id = 10
        mock_dept.name = "研发部"
        
        # 设置query返回值（用于_check_duplicate_timesheet, _get_user_info和_get_project_info）
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Timesheet':
                # 重复检查：返回None表示无重复
                mock_q.filter.return_value.first.return_value = None
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = mock_user
            elif model.__name__ == 'Department':
                mock_q.filter.return_value.first.return_value = mock_dept
            elif model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = mock_project
            return mock_q
        
        self.db.query.side_effect = query_side_effect
        
        # Mock get_timesheet_detail返回值
        with patch.object(self.service, 'get_timesheet_detail') as mock_detail:
            mock_detail.return_value = MagicMock()
            
            # 执行
            result = self.service.create_timesheet(timesheet_in, self.current_user)
            
            # 验证
            mock_save_obj.assert_called_once()
            mock_detail.assert_called_once()

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_create_timesheet_no_project_ids(self, mock_get_or_404):
        """测试未提供项目ID时抛出异常"""
        timesheet_in = TimesheetCreate(
            project_id=None,
            rd_project_id=None,
            task_id=200,
            work_date=date(2025, 1, 15),
            work_hours=Decimal("8.0"),
            work_type="NORMAL",
            description="测试"
        )
        
        # 执行并验证异常
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_timesheet(timesheet_in, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("必须指定项目ID", ctx.exception.detail)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_create_timesheet_project_not_found(self, mock_get_or_404):
        """测试项目不存在时抛出异常"""
        timesheet_in = TimesheetCreate(
            project_id=999,
            rd_project_id=None,
            task_id=200,
            work_date=date(2025, 1, 15),
            work_hours=Decimal("8.0"),
            work_type="NORMAL",
            description="测试"
        )
        
        # Mock项目不存在
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="项目不存在")
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_timesheet(timesheet_in, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 404)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_create_timesheet_duplicate(self, mock_get_or_404):
        """测试重复工时记录时抛出异常"""
        timesheet_in = TimesheetCreate(
            project_id=100,
            rd_project_id=None,
            task_id=200,
            work_date=date(2025, 1, 15),
            work_hours=Decimal("8.0"),
            work_type="NORMAL",
            description="测试"
        )
        
        # Mock项目存在
        mock_get_or_404.return_value = MagicMock()
        
        # Mock存在重复记录
        mock_existing = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_existing
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_timesheet(timesheet_in, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("已有工时记录", ctx.exception.detail)

    # ==================== batch_create_timesheets 测试 ====================

    def test_batch_create_timesheets_all_success(self):
        """测试批量创建全部成功"""
        timesheets_data = [
            TimesheetCreate(
                project_id=100,
                task_id=200,
                work_date=date(2025, 1, 15),
                work_hours=Decimal("8.0"),
                work_type="NORMAL",
                description="任务1"
            ),
            TimesheetCreate(
                project_id=100,
                task_id=201,
                work_date=date(2025, 1, 16),
                work_hours=Decimal("7.5"),
                work_type="NORMAL",
                description="任务2"
            ),
        ]
        
        # Mock项目存在
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        
        # Mock无重复
        mock_user = MagicMock()
        mock_user.real_name = "测试用户"
        mock_dept = MagicMock()
        mock_dept.name = "研发部"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Timesheet':
                mock_q.filter.return_value.first.return_value = None  # 无重复
            elif model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = mock_user
            elif model.__name__ == 'Department':
                mock_q.filter.return_value.first.return_value = mock_dept
            return mock_q
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = self.service.batch_create_timesheets(timesheets_data, self.current_user)
        
        # 验证
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(len(result["errors"]), 0)
        self.db.commit.assert_called_once()

    def test_batch_create_timesheets_partial_fail(self):
        """测试批量创建部分失败"""
        timesheets_data = [
            TimesheetCreate(
                project_id=100,
                task_id=200,
                work_date=date(2025, 1, 15),
                work_hours=Decimal("8.0"),
                work_type="NORMAL",
                description="任务1"
            ),
            TimesheetCreate(
                project_id=999,  # 不存在的项目
                task_id=201,
                work_date=date(2025, 1, 16),
                work_hours=Decimal("7.5"),
                work_type="NORMAL",
                description="任务2"
            ),
        ]
        
        # Mock第一个项目存在，第二个不存在
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                def filter_side_effect(*args):
                    filter_mock = MagicMock()
                    # 根据调用次数返回不同结果
                    if not hasattr(query_side_effect, 'call_count'):
                        query_side_effect.call_count = 0
                    query_side_effect.call_count += 1
                    
                    if query_side_effect.call_count == 1:
                        # 第一次调用：项目100存在
                        mock_project = MagicMock()
                        mock_project.project_code = "PRJ001"
                        mock_project.project_name = "测试项目"
                        filter_mock.first.return_value = mock_project
                    else:
                        # 第二次调用：项目999不存在
                        filter_mock.first.return_value = None
                    return filter_mock
                mock_q.filter.side_effect = filter_side_effect
            elif model.__name__ == 'Timesheet':
                mock_q.filter.return_value.first.return_value = None
            elif model.__name__ == 'User':
                mock_user = MagicMock()
                mock_user.real_name = "测试用户"
                mock_q.filter.return_value.first.return_value = mock_user
            elif model.__name__ == 'Department':
                mock_q.filter.return_value.first.return_value = None
            return mock_q
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = self.service.batch_create_timesheets(timesheets_data, self.current_user)
        
        # 验证
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("项目不存在", result["errors"][0]["error"])

    def test_batch_create_timesheets_duplicate(self):
        """测试批量创建时遇到重复记录"""
        timesheets_data = [
            TimesheetCreate(
                project_id=100,
                task_id=200,
                work_date=date(2025, 1, 15),
                work_hours=Decimal("8.0"),
                work_type="NORMAL",
                description="任务1"
            ),
        ]
        
        # Mock项目存在
        mock_project = MagicMock()
        
        # Mock存在重复记录
        mock_existing = MagicMock()
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Timesheet':
                mock_q.filter.return_value.first.return_value = mock_existing  # 重复
            return mock_q
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = self.service.batch_create_timesheets(timesheets_data, self.current_user)
        
        # 验证
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["failed_count"], 1)
        self.assertIn("已有记录", result["errors"][0]["error"])

    # ==================== get_timesheet_detail 测试 ====================

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_get_timesheet_detail_success(self, mock_get_or_404):
        """测试成功获取工时详情"""
        # Mock工时记录
        mock_ts = self._create_mock_timesheet(1, "2025-01-15")
        mock_ts.user_id = self.current_user.id
        mock_get_or_404.return_value = mock_ts
        
        # Mock相关查询
        self._setup_user_project_mocks()
        
        # 执行
        result = self.service.get_timesheet_detail(1, self.current_user)
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_get_timesheet_detail_not_found(self, mock_get_or_404):
        """测试工时记录不存在"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="工时记录不存在")
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.get_timesheet_detail(999, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 404)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_get_timesheet_detail_permission_denied(self, mock_get_or_404):
        """测试无权访问他人记录"""
        # Mock他人的工时记录
        mock_ts = self._create_mock_timesheet(1, "2025-01-15")
        mock_ts.user_id = 999  # 不是当前用户
        mock_get_or_404.return_value = mock_ts
        
        self.current_user.is_superuser = False
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.get_timesheet_detail(1, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 403)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_get_timesheet_detail_superuser_access(self, mock_get_or_404):
        """测试超级用户可以访问他人记录"""
        # Mock他人的工时记录
        mock_ts = self._create_mock_timesheet(1, "2025-01-15")
        mock_ts.user_id = 999
        mock_get_or_404.return_value = mock_ts
        
        self.current_user.is_superuser = True
        
        # Mock查询
        self._setup_user_project_mocks()
        
        # 执行（不应抛出异常）
        result = self.service.get_timesheet_detail(1, self.current_user)
        self.assertIsNotNone(result)

    # ==================== update_timesheet 测试 ====================

    @patch('app.services.timesheet_records.service.save_obj')
    @patch('app.services.timesheet_records.service.get_or_404')
    def test_update_timesheet_success(self, mock_get_or_404, mock_save_obj):
        """测试成功更新工时记录"""
        # Mock工时记录（草稿状态）
        mock_ts = self._create_mock_timesheet(1, "2025-01-15")
        mock_ts.user_id = self.current_user.id
        mock_ts.status = "DRAFT"
        mock_get_or_404.return_value = mock_ts
        
        # 准备更新数据
        update_data = TimesheetUpdate(
            work_hours=Decimal("9.0"),
            description="更新后的描述"
        )
        
        # Mock get_timesheet_detail
        with patch.object(self.service, 'get_timesheet_detail') as mock_detail:
            mock_detail.return_value = MagicMock()
            
            # 执行
            result = self.service.update_timesheet(1, update_data, self.current_user)
            
            # 验证
            mock_save_obj.assert_called_once()
            self.assertEqual(mock_ts.hours, Decimal("9.0"))
            self.assertEqual(mock_ts.work_content, "更新后的描述")

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_update_timesheet_not_owner(self, mock_get_or_404):
        """测试无权更新他人记录"""
        mock_ts = MagicMock()
        mock_ts.user_id = 999  # 不是当前用户
        mock_get_or_404.return_value = mock_ts
        
        update_data = TimesheetUpdate(work_hours=Decimal("9.0"))
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.update_timesheet(1, update_data, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("无权修改", ctx.exception.detail)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_update_timesheet_not_draft(self, mock_get_or_404):
        """测试不能更新非草稿状态的记录"""
        mock_ts = MagicMock()
        mock_ts.user_id = self.current_user.id
        mock_ts.status = "APPROVED"  # 已审批
        mock_get_or_404.return_value = mock_ts
        
        update_data = TimesheetUpdate(work_hours=Decimal("9.0"))
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.update_timesheet(1, update_data, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("只能修改草稿", ctx.exception.detail)

    # ==================== delete_timesheet 测试 ====================

    @patch('app.services.timesheet_records.service.delete_obj')
    @patch('app.services.timesheet_records.service.get_or_404')
    def test_delete_timesheet_success(self, mock_get_or_404, mock_delete_obj):
        """测试成功删除工时记录"""
        mock_ts = MagicMock()
        mock_ts.user_id = self.current_user.id
        mock_ts.status = "DRAFT"
        mock_get_or_404.return_value = mock_ts
        
        # 执行
        self.service.delete_timesheet(1, self.current_user)
        
        # 验证
        mock_delete_obj.assert_called_once_with(self.db, mock_ts)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_delete_timesheet_not_owner(self, mock_get_or_404):
        """测试无权删除他人记录"""
        mock_ts = MagicMock()
        mock_ts.user_id = 999
        mock_get_or_404.return_value = mock_ts
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.delete_timesheet(1, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("无权删除", ctx.exception.detail)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_delete_timesheet_not_draft(self, mock_get_or_404):
        """测试不能删除非草稿状态的记录"""
        mock_ts = MagicMock()
        mock_ts.user_id = self.current_user.id
        mock_ts.status = "SUBMITTED"
        mock_get_or_404.return_value = mock_ts
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service.delete_timesheet(1, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("只能删除草稿", ctx.exception.detail)

    # ==================== 私有方法测试 ====================

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_validate_projects_rd_project(self, mock_get_or_404):
        """测试验证研发项目ID"""
        # Mock研发项目存在
        mock_rd_project = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_rd_project
        
        # 执行（不应抛出异常）
        self.service._validate_projects(None, 100)

    @patch('app.services.timesheet_records.service.get_or_404')
    def test_validate_projects_rd_project_not_found(self, mock_get_or_404):
        """测试研发项目不存在"""
        # Mock研发项目不存在
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service._validate_projects(None, 100)
        
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("研发项目不存在", ctx.exception.detail)

    def test_check_duplicate_timesheet_with_project(self):
        """测试检查重复记录（项目ID）"""
        # Mock存在重复
        mock_existing = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_existing
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service._check_duplicate_timesheet(
                1, date(2025, 1, 15), 100, None
            )
        
        self.assertEqual(ctx.exception.status_code, 400)

    def test_check_duplicate_timesheet_no_duplicate(self):
        """测试无重复记录"""
        # Mock不存在重复
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行（不应抛出异常）
        self.service._check_duplicate_timesheet(
            1, date(2025, 1, 15), 100, None
        )

    def test_get_user_info_with_department(self):
        """测试获取用户信息（含部门）"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.department_id = 10
        
        mock_dept = MagicMock()
        mock_dept.id = 10
        mock_dept.name = "研发部"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = mock_user
            elif model.__name__ == 'Department':
                mock_q.filter.return_value.first.return_value = mock_dept
            return mock_q
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = self.service._get_user_info(1)
        
        # 验证
        self.assertEqual(result["user_name"], "张三")
        self.assertEqual(result["department_id"], 10)
        self.assertEqual(result["department_name"], "研发部")

    def test_get_user_info_without_department(self):
        """测试获取用户信息（无部门）"""
        mock_user = MagicMock()
        mock_user.real_name = "李四"
        mock_user.username = "lisi"
        mock_user.department_id = None
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 执行
        result = self.service._get_user_info(1)
        
        # 验证
        self.assertEqual(result["user_name"], "李四")
        self.assertIsNone(result["department_id"])
        self.assertIsNone(result["department_name"])

    def test_get_project_info_success(self):
        """测试获取项目信息"""
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # 执行
        result = self.service._get_project_info(100)
        
        # 验证
        self.assertEqual(result["project_code"], "PRJ001")
        self.assertEqual(result["project_name"], "测试项目")

    def test_get_project_info_none(self):
        """测试获取项目信息（项目ID为None）"""
        # 执行
        result = self.service._get_project_info(None)
        
        # 验证
        self.assertIsNone(result["project_code"])
        self.assertIsNone(result["project_name"])

    def test_check_access_permission_owner(self):
        """测试访问权限检查（所有者）"""
        mock_ts = MagicMock()
        mock_ts.user_id = self.current_user.id
        
        # 执行（不应抛出异常）
        self.service._check_access_permission(mock_ts, self.current_user)

    def test_check_access_permission_superuser(self):
        """测试访问权限检查（超级用户）"""
        mock_ts = MagicMock()
        mock_ts.user_id = 999
        self.current_user.is_superuser = True
        
        # 执行（不应抛出异常）
        self.service._check_access_permission(mock_ts, self.current_user)

    def test_check_access_permission_denied(self):
        """测试访问权限检查（拒绝）"""
        mock_ts = MagicMock()
        mock_ts.user_id = 999
        self.current_user.is_superuser = False
        
        # 执行并验证
        with self.assertRaises(HTTPException) as ctx:
            self.service._check_access_permission(mock_ts, self.current_user)
        
        self.assertEqual(ctx.exception.status_code, 403)

    def test_build_timesheet_response(self):
        """测试构建工时记录响应"""
        mock_ts = self._create_mock_timesheet(1, "2025-01-15")
        
        # Mock相关查询
        self._setup_user_project_mocks()
        
        # 执行
        result = self.service._build_timesheet_response(mock_ts)
        
        # 验证
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    def test_build_timesheet_detail_response_with_rd_project(self):
        """测试构建详情响应（含研发项目）"""
        mock_ts = self._create_mock_timesheet(1, "2025-01-15")
        mock_ts.project_id = None
        mock_ts.rd_project_id = 200
        
        # Mock用户
        mock_user = MagicMock()
        mock_user.real_name = "测试用户"
        
        # Mock研发项目
        mock_rd_project = MagicMock()
        mock_rd_project.project_name = "研发项目A"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = mock_user
            elif model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = None
            elif model.__name__ == 'RdProject':
                mock_q.filter.return_value.first.return_value = mock_rd_project
            return mock_q
        
        self.db.query.side_effect = query_side_effect
        
        # 执行
        result = self.service._build_timesheet_detail_response(mock_ts)
        
        # 验证
        self.assertEqual(result.project_name, "研发项目A")

    # ==================== 辅助方法 ====================

    def _create_mock_timesheet(self, ts_id: int, work_date_str: str):
        """创建mock工时记录"""
        mock_ts = MagicMock()
        mock_ts.id = ts_id
        mock_ts.user_id = 1
        mock_ts.project_id = 100
        mock_ts.rd_project_id = None
        mock_ts.task_id = 200
        mock_ts.work_date = datetime.strptime(work_date_str, "%Y-%m-%d").date()
        mock_ts.hours = Decimal("8.0")
        mock_ts.overtime_type = "NORMAL"
        mock_ts.work_content = "测试工作内容"
        mock_ts.status = "DRAFT"
        mock_ts.approver_id = None
        mock_ts.approve_time = None
        mock_ts.created_at = datetime.now()
        mock_ts.updated_at = datetime.now()
        return mock_ts

    def _setup_user_project_mocks(self):
        """设置用户和项目相关的mock"""
        mock_user = MagicMock()
        mock_user.real_name = "测试用户"
        mock_user.username = "test_user"
        
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        
        mock_task = MagicMock()
        mock_task.task_name = "测试任务"
        
        def query_side_effect(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                mock_q.filter.return_value.first.return_value = mock_user
            elif model.__name__ == 'Project':
                mock_q.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Task':
                mock_q.filter.return_value.first.return_value = mock_task
            return mock_q
        
        self.db.query.side_effect = query_side_effect


if __name__ == "__main__":
    unittest.main()
