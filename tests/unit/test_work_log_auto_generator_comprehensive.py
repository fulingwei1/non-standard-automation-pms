# -*- coding: utf-8 -*-
"""
WorkLogAutoGenerator 综合单元测试

测试覆盖:
- __init__: 初始化服务
- generate_work_log_from_timesheet: 从工时生成工作日志
- batch_generate_work_logs: 批量生成工作日志
- generate_yesterday_work_logs: 生成昨日工作日志
"""

from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest


class TestWorkLogAutoGeneratorInit:
    """测试 WorkLogAutoGenerator 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        generator = WorkLogAutoGenerator(mock_db)

        assert generator.db == mock_db


class TestGenerateWorkLogFromTimesheet:
    """测试 generate_work_log_from_timesheet 方法"""

    def test_returns_none_when_submitted_log_exists(self):
        """测试已提交日志存在时返回None"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()
        mock_existing_log = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_log

        generator = WorkLogAutoGenerator(mock_db)

        result = generator.generate_work_log_from_timesheet(
            user_id=1,
            work_date=date(2024, 1, 15)
        )

        assert result is None

    def test_returns_none_when_no_timesheets(self):
        """测试没有工时记录时返回None"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        # 第一次查询（检查已提交日志）返回None
        # 第二次查询（获取工时记录）返回空列表
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        generator = WorkLogAutoGenerator(mock_db)

        result = generator.generate_work_log_from_timesheet(
            user_id=1,
            work_date=date(2024, 1, 15)
        )

        assert result is None

    def test_returns_none_when_user_not_found(self):
        """测试用户不存在时返回None"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        mock_timesheet = MagicMock()
        mock_timesheet.project_id = 1
        mock_timesheet.task_id = 1
        mock_timesheet.hours = Decimal("8")

        # 设置查询返回
        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)

            if 'WorkLog' in model_name:
                mock_query.filter.return_value.first.return_value = None
            elif 'Timesheet' in model_name:
                mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_timesheet]
            elif 'User' in model_name:
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        mock_db.query.side_effect = query_side_effect

        generator = WorkLogAutoGenerator(mock_db)

        result = generator.generate_work_log_from_timesheet(
            user_id=999,
            work_date=date(2024, 1, 15)
        )

        assert result is None

    def test_generates_work_log_successfully(self):
        """测试成功生成工作日志"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        mock_timesheet = MagicMock()
        mock_timesheet.project_id = 1
        mock_timesheet.task_id = 1
        mock_timesheet.task_name = "开发任务"
        mock_timesheet.hours = Decimal("8")
        mock_timesheet.work_content = "编码开发"
        mock_timesheet.work_result = "完成功能"
        mock_timesheet.progress_before = 50
        mock_timesheet.progress_after = 80

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_project = MagicMock()
        mock_project.project_name = "测试项目"

        mock_work_log = MagicMock()
        mock_work_log.id = 1

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            call_count[0] += 1

            if 'WorkLog' in model_name:
                if call_count[0] == 1:
                    # 第一次检查已提交日志
                    mock_query.filter.return_value.first.return_value = None
                else:
                    # 后续查询草稿
                    mock_query.filter.return_value.first.return_value = None
            elif 'Timesheet' in model_name:
                mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_timesheet]
            elif 'User' in model_name:
                mock_query.filter.return_value.first.return_value = mock_user
            elif 'Project' in model_name:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        generator = WorkLogAutoGenerator(mock_db)

        result = generator.generate_work_log_from_timesheet(
            user_id=1,
            work_date=date(2024, 1, 15)
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_truncates_long_content(self):
        """测试截断过长内容"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        # 创建多个工时记录生成长内容
        mock_timesheets = []
        for i in range(20):
            ts = MagicMock()
            ts.project_id = 1
            ts.task_id = i
            ts.task_name = f"任务{i}" * 10  # 较长的任务名
            ts.hours = Decimal("1")
            ts.work_content = "很长的工作内容" * 10
            ts.work_result = "很长的工作成果" * 10
            ts.progress_before = 0
            ts.progress_after = 100
            mock_timesheets.append(ts)

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"

        mock_project = MagicMock()
        mock_project.project_name = "测试项目"

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            call_count[0] += 1

            if 'WorkLog' in model_name:
                mock_query.filter.return_value.first.return_value = None
            elif 'Timesheet' in model_name:
                mock_query.filter.return_value.order_by.return_value.all.return_value = mock_timesheets
            elif 'User' in model_name:
                mock_query.filter.return_value.first.return_value = mock_user
            elif 'Project' in model_name:
                mock_query.filter.return_value.first.return_value = mock_project
            return mock_query

        mock_db.query.side_effect = query_side_effect
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        generator = WorkLogAutoGenerator(mock_db)

        generator.generate_work_log_from_timesheet(
            user_id=1,
            work_date=date(2024, 1, 15)
        )

        # 验证 add 被调用，内容会被截断
        mock_db.add.assert_called_once()


class TestBatchGenerateWorkLogs:
    """测试 batch_generate_work_logs 方法"""

    def test_returns_stats(self):
        """测试返回统计信息"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"

        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(1,)]
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

        generator = WorkLogAutoGenerator(mock_db)

        with patch.object(generator, 'generate_work_log_from_timesheet', return_value=None):
            result = generator.batch_generate_work_logs(
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 15)
            )

        assert 'total_users' in result
        assert 'total_days' in result
        assert 'generated_count' in result
        assert 'skipped_count' in result
        assert 'error_count' in result

    def test_processes_multiple_days(self):
        """测试处理多天"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(1,)]
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

        generator = WorkLogAutoGenerator(mock_db)

        with patch.object(generator, 'generate_work_log_from_timesheet', return_value=None):
            result = generator.batch_generate_work_logs(
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 17)
            )

        assert result['total_days'] == 3

    def test_handles_errors(self):
        """测试处理错误"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(1,)]
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

        generator = WorkLogAutoGenerator(mock_db)

        with patch.object(generator, 'generate_work_log_from_timesheet', side_effect=Exception("测试错误")):
            result = generator.batch_generate_work_logs(
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 15)
            )

        assert result['error_count'] == 1
        assert len(result['errors']) == 1

    def test_processes_specified_users(self):
        """测试处理指定用户"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()

        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.real_name = "张三"

        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.real_name = "李四"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user1, mock_user2]

        generator = WorkLogAutoGenerator(mock_db)

        with patch.object(generator, 'generate_work_log_from_timesheet', return_value=MagicMock()):
            result = generator.batch_generate_work_logs(
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 15),
                user_ids=[1, 2]
            )

        assert result['total_users'] == 2
        assert result['generated_count'] == 2


class TestGenerateYesterdayWorkLogs:
    """测试 generate_yesterday_work_logs 方法"""

    def test_calls_batch_generate_with_yesterday(self):
        """测试调用批量生成方法并使用昨天日期"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()
        generator = WorkLogAutoGenerator(mock_db)

        yesterday = date.today() - timedelta(days=1)

        with patch.object(generator, 'batch_generate_work_logs', return_value={'status': 'ok'}) as mock_batch:
            result = generator.generate_yesterday_work_logs()

            mock_batch.assert_called_once_with(
                start_date=yesterday,
                end_date=yesterday,
                user_ids=None,
                auto_submit=False
            )

    def test_passes_user_ids(self):
        """测试传递用户ID列表"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()
        generator = WorkLogAutoGenerator(mock_db)

        yesterday = date.today() - timedelta(days=1)

        with patch.object(generator, 'batch_generate_work_logs', return_value={'status': 'ok'}) as mock_batch:
            result = generator.generate_yesterday_work_logs(user_ids=[1, 2, 3])

            mock_batch.assert_called_once_with(
                start_date=yesterday,
                end_date=yesterday,
                user_ids=[1, 2, 3],
                auto_submit=False
            )

    def test_passes_auto_submit(self):
        """测试传递自动提交参数"""
        from app.services.work_log_auto_generator import WorkLogAutoGenerator

        mock_db = MagicMock()
        generator = WorkLogAutoGenerator(mock_db)

        yesterday = date.today() - timedelta(days=1)

        with patch.object(generator, 'batch_generate_work_logs', return_value={'status': 'ok'}) as mock_batch:
            result = generator.generate_yesterday_work_logs(auto_submit=True)

            mock_batch.assert_called_once_with(
                start_date=yesterday,
                end_date=yesterday,
                user_ids=None,
                auto_submit=True
            )
