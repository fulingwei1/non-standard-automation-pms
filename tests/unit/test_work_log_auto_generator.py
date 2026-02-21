# -*- coding: utf-8 -*-
"""
工作日志自动生成服务单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, call

from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.work_log import WorkLog
from app.services.work_log_auto_generator import WorkLogAutoGenerator


class TestWorkLogAutoGeneratorCore(unittest.TestCase):
    """测试工作日志自动生成核心功能"""

    def setUp(self):
        """测试前准备"""
        # Mock数据库Session
        self.db = MagicMock()
        self.generator = WorkLogAutoGenerator(self.db)
        
        # 准备测试数据
        self.test_user_id = 1
        self.test_work_date = date(2024, 1, 15)
        
        # Mock用户对象
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = self.test_user_id
        self.mock_user.real_name = "张三"
        self.mock_user.username = "zhangsan"
        
        # Mock项目对象
        self.mock_project = MagicMock(spec=Project)
        self.mock_project.id = 100
        self.mock_project.project_name = "测试项目A"

    # ========== generate_work_log_from_timesheet() 主方法测试 ==========
    
    def test_generate_work_log_success(self):
        """测试成功生成工作日志"""
        # Mock: 不存在已提交的日志
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 第一次查询：不存在已提交日志
            self.mock_user,  # 第二次查询：获取用户信息
            self.mock_project,  # 第三次查询：获取项目信息
            None,  # 第四次查询：不存在草稿日志
        ]
        
        # Mock: 返回工时记录
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "开发功能模块"
        mock_timesheet.hours = Decimal('8.0')
        mock_timesheet.work_content = "完成用户模块开发"
        mock_timesheet.work_result = "用户模块功能正常"
        mock_timesheet.progress_before = 30
        mock_timesheet.progress_after = 50
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date,
            auto_submit=False
        )
        
        # 验证数据库操作
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        
        # 验证添加的对象
        added_work_log = self.db.add.call_args[0][0]
        self.assertIsInstance(added_work_log, WorkLog)
        self.assertEqual(added_work_log.user_id, self.test_user_id)
        self.assertEqual(added_work_log.user_name, "张三")
        self.assertEqual(added_work_log.work_date, self.test_work_date)
        self.assertEqual(added_work_log.status, 'DRAFT')
        self.assertIn("测试项目A", added_work_log.content)
        self.assertIn("开发功能模块", added_work_log.content)

    def test_generate_work_log_auto_submit(self):
        """测试自动提交模式"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            None,  # 不存在草稿
        ]
        
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "任务A"
        mock_timesheet.hours = Decimal('4.0')
        mock_timesheet.work_content = "测试内容"
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行（启用自动提交）
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date,
            auto_submit=True
        )
        
        # 验证状态为SUBMITTED
        added_work_log = self.db.add.call_args[0][0]
        self.assertEqual(added_work_log.status, 'SUBMITTED')

    def test_generate_work_log_existing_submitted(self):
        """测试已存在已提交日志时返回None"""
        # Mock: 存在已提交的日志
        existing_log = MagicMock(spec=WorkLog)
        existing_log.status = 'SUBMITTED'
        
        self.db.query.return_value.filter.return_value.first.return_value = existing_log
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证返回None，不执行后续操作
        self.assertIsNone(result)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_generate_work_log_no_timesheet(self):
        """测试无工时记录时返回None"""
        # Mock: 不存在已提交日志
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock: 无工时记录
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证返回None
        self.assertIsNone(result)
        self.db.add.assert_not_called()

    def test_generate_work_log_user_not_found(self):
        """测试用户不存在时返回None"""
        # Mock: 不存在已提交日志
        # Mock: 有工时记录
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.hours = Decimal('8.0')
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            None,  # 用户不存在
        ]
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证返回None
        self.assertIsNone(result)
        self.db.add.assert_not_called()

    def test_generate_work_log_multiple_projects(self):
        """测试多个项目的工时聚合"""
        # Mock配置
        mock_user = MagicMock(spec=User)
        mock_user.id = self.test_user_id
        mock_user.real_name = "李四"
        mock_user.username = "lisi"
        
        mock_project1 = MagicMock(spec=Project)
        mock_project1.id = 100
        mock_project1.project_name = "项目A"
        
        mock_project2 = MagicMock(spec=Project)
        mock_project2.id = 200
        mock_project2.project_name = "项目B"
        
        # Mock数据库查询
        query_results = [
            None,  # 不存在已提交日志
            mock_user,  # 用户信息
            mock_project1,  # 项目A
            mock_project2,  # 项目B
            None,  # 不存在草稿
        ]
        self.db.query.return_value.filter.return_value.first.side_effect = query_results
        
        # Mock工时记录（两个项目）
        ts1 = MagicMock(spec=Timesheet)
        ts1.project_id = 100
        ts1.task_id = 1001
        ts1.task_name = "任务A1"
        ts1.hours = Decimal('4.0')
        ts1.work_content = "内容A1"
        ts1.work_result = None
        ts1.progress_before = None
        ts1.progress_after = None
        
        ts2 = MagicMock(spec=Timesheet)
        ts2.project_id = 200
        ts2.task_id = 2001
        ts2.task_name = "任务B1"
        ts2.hours = Decimal('4.0')
        ts2.work_content = "内容B1"
        ts2.work_result = None
        ts2.progress_before = None
        ts2.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            ts1, ts2
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证生成的日志包含两个项目
        added_work_log = self.db.add.call_args[0][0]
        self.assertIn("项目A", added_work_log.content)
        self.assertIn("项目B", added_work_log.content)
        self.assertIn("4.0小时", added_work_log.content)

    def test_generate_work_log_no_project(self):
        """测试无关联项目的工时记录"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            None,  # 项目不存在
            None,  # 不存在草稿
        ]
        
        # Mock工时记录（无项目）
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = None
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "独立任务"
        mock_timesheet.hours = Decimal('2.0')
        mock_timesheet.work_content = "其他工作"
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证生成的日志包含"未关联项目"
        added_work_log = self.db.add.call_args[0][0]
        self.assertIn("未关联项目", added_work_log.content)

    def test_generate_work_log_update_existing_draft(self):
        """测试更新已存在的草稿日志"""
        # Mock: 存在草稿日志
        existing_draft = MagicMock(spec=WorkLog)
        existing_draft.status = 'DRAFT'
        existing_draft.user_id = self.test_user_id
        existing_draft.work_date = self.test_work_date
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            existing_draft,  # 存在草稿
        ]
        
        # Mock工时记录
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "新任务"
        mock_timesheet.hours = Decimal('6.0')
        mock_timesheet.work_content = "更新内容"
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证更新了草稿而不是创建新记录
        self.db.add.assert_not_called()
        self.assertIsNotNone(existing_draft.content)
        self.assertIsNotNone(existing_draft.updated_at)

    def test_generate_work_log_content_truncation(self):
        """测试内容超过300字时的截断"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            None,  # 不存在草稿
        ]
        
        # 创建一个超长的工作内容
        long_content = "这是一个非常长的工作内容描述" * 50  # 远超300字
        
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "任务"
        mock_timesheet.hours = Decimal('8.0')
        mock_timesheet.work_content = long_content
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证内容被截断为300字
        added_work_log = self.db.add.call_args[0][0]
        self.assertLessEqual(len(added_work_log.content), 300)
        self.assertTrue(added_work_log.content.endswith("..."))

    def test_generate_work_log_multiple_tasks_same_project(self):
        """测试同一项目下的多个任务"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            None,  # 不存在草稿
        ]
        
        # Mock多个任务
        ts1 = MagicMock(spec=Timesheet)
        ts1.project_id = 100
        ts1.task_id = 1001
        ts1.task_name = "任务A"
        ts1.hours = Decimal('3.0')
        ts1.work_content = "内容A"
        ts1.work_result = None
        ts1.progress_before = None
        ts1.progress_after = None
        
        ts2 = MagicMock(spec=Timesheet)
        ts2.project_id = 100
        ts2.task_id = 1002
        ts2.task_name = "任务B"
        ts2.hours = Decimal('5.0')
        ts2.work_content = "内容B"
        ts2.work_result = None
        ts2.progress_before = None
        ts2.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            ts1, ts2
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证总工时和任务列表
        added_work_log = self.db.add.call_args[0][0]
        self.assertIn("8.0小时", added_work_log.content)  # 总工时
        self.assertIn("任务A", added_work_log.content)
        self.assertIn("任务B", added_work_log.content)
        self.assertIn("3.0小时", added_work_log.content)
        self.assertIn("5.0小时", added_work_log.content)

    def test_generate_work_log_with_progress_update(self):
        """测试包含进度更新的工时记录"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            None,  # 不存在草稿
        ]
        
        # Mock工时记录（包含进度）
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "开发任务"
        mock_timesheet.hours = Decimal('8.0')
        mock_timesheet.work_content = "编写代码"
        mock_timesheet.work_result = "完成核心功能"
        mock_timesheet.progress_before = 20
        mock_timesheet.progress_after = 60
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证包含进度更新信息
        added_work_log = self.db.add.call_args[0][0]
        self.assertIn("进度更新", added_work_log.content)
        self.assertIn("20%", added_work_log.content)
        self.assertIn("60%", added_work_log.content)

    # ========== batch_generate_work_logs() 批量生成测试 ==========
    
    def test_batch_generate_work_logs_success(self):
        """测试批量生成工作日志"""
        # 准备测试数据
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 16)
        user_ids = [1, 2]
        
        # Mock用户列表
        mock_user1 = MagicMock(spec=User)
        mock_user1.id = 1
        mock_user1.real_name = "用户1"
        mock_user1.username = "user1"
        
        mock_user2 = MagicMock(spec=User)
        mock_user2.id = 2
        mock_user2.real_name = "用户2"
        mock_user2.username = "user2"
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_user1, mock_user2
        ]
        
        # Mock generate_work_log_from_timesheet方法
        def mock_generate(user_id, work_date, auto_submit=False):
            # 模拟生成成功
            return MagicMock(spec=WorkLog)
        
        self.generator.generate_work_log_from_timesheet = MagicMock(
            side_effect=mock_generate
        )
        
        # 执行
        stats = self.generator.batch_generate_work_logs(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_ids,
            auto_submit=False
        )
        
        # 验证统计信息
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['total_days'], 2)
        self.assertEqual(stats['generated_count'], 4)  # 2用户 * 2天
        self.assertEqual(stats['skipped_count'], 0)
        self.assertEqual(stats['error_count'], 0)
        self.assertEqual(len(stats['errors']), 0)

    def test_batch_generate_work_logs_all_users(self):
        """测试批量生成（所有用户）"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 15)
        
        # Mock: 获取有工时记录的用户ID
        self.db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (1,), (2,), (3,)
        ]
        
        # Mock: 获取用户对象
        mock_users = [
            MagicMock(spec=User, id=1, real_name="用户1", username="user1"),
            MagicMock(spec=User, id=2, real_name="用户2", username="user2"),
            MagicMock(spec=User, id=3, real_name="用户3", username="user3"),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = mock_users
        
        # Mock generate方法
        self.generator.generate_work_log_from_timesheet = MagicMock(
            return_value=MagicMock(spec=WorkLog)
        )
        
        # 执行（user_ids=None表示所有用户）
        stats = self.generator.batch_generate_work_logs(
            start_date=start_date,
            end_date=end_date,
            user_ids=None,
            auto_submit=False
        )
        
        # 验证
        self.assertEqual(stats['total_users'], 3)
        self.assertEqual(stats['generated_count'], 3)  # 3用户 * 1天

    def test_batch_generate_work_logs_with_skips(self):
        """测试批量生成（含跳过记录）"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 15)
        user_ids = [1, 2]
        
        # Mock用户
        mock_users = [
            MagicMock(spec=User, id=1, real_name="用户1", username="user1"),
            MagicMock(spec=User, id=2, real_name="用户2", username="user2"),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = mock_users
        
        # Mock generate方法（第一个成功，第二个返回None）
        self.generator.generate_work_log_from_timesheet = MagicMock(
            side_effect=[MagicMock(spec=WorkLog), None]
        )
        
        # 执行
        stats = self.generator.batch_generate_work_logs(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_ids
        )
        
        # 验证
        self.assertEqual(stats['generated_count'], 1)
        self.assertEqual(stats['skipped_count'], 1)
        self.assertEqual(stats['error_count'], 0)

    def test_batch_generate_work_logs_with_errors(self):
        """测试批量生成（含错误）"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 15)
        user_ids = [1]
        
        # Mock用户
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.real_name = "用户1"
        mock_user.username = "user1"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_user]
        
        # Mock generate方法（抛出异常）
        self.generator.generate_work_log_from_timesheet = MagicMock(
            side_effect=Exception("数据库连接失败")
        )
        
        # 执行
        stats = self.generator.batch_generate_work_logs(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_ids
        )
        
        # 验证
        self.assertEqual(stats['generated_count'], 0)
        self.assertEqual(stats['error_count'], 1)
        self.assertEqual(len(stats['errors']), 1)
        self.assertEqual(stats['errors'][0]['user_id'], 1)
        self.assertIn("数据库连接失败", stats['errors'][0]['error'])

    def test_batch_generate_work_logs_date_range(self):
        """测试批量生成（跨多天）"""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 20)  # 6天
        user_ids = [1]
        
        # Mock用户
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        self.db.query.return_value.filter.return_value.all.return_value = [mock_user]
        
        # Mock generate方法
        self.generator.generate_work_log_from_timesheet = MagicMock(
            return_value=MagicMock(spec=WorkLog)
        )
        
        # 执行
        stats = self.generator.batch_generate_work_logs(
            start_date=start_date,
            end_date=end_date,
            user_ids=user_ids
        )
        
        # 验证调用次数
        self.assertEqual(stats['total_days'], 6)
        self.assertEqual(stats['generated_count'], 6)
        self.assertEqual(
            self.generator.generate_work_log_from_timesheet.call_count,
            6
        )

    # ========== generate_yesterday_work_logs() 测试 ==========
    
    def test_generate_yesterday_work_logs(self):
        """测试生成昨日工作日志"""
        # Mock batch_generate_work_logs
        expected_stats = {
            'total_users': 5,
            'total_days': 1,
            'generated_count': 5,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }
        self.generator.batch_generate_work_logs = MagicMock(
            return_value=expected_stats
        )
        
        # 执行
        stats = self.generator.generate_yesterday_work_logs(
            user_ids=[1, 2, 3, 4, 5],
            auto_submit=True
        )
        
        # 验证调用参数
        yesterday = date.today() - timedelta(days=1)
        self.generator.batch_generate_work_logs.assert_called_once_with(
            start_date=yesterday,
            end_date=yesterday,
            user_ids=[1, 2, 3, 4, 5],
            auto_submit=True
        )
        
        # 验证返回结果
        self.assertEqual(stats, expected_stats)

    def test_generate_yesterday_work_logs_all_users(self):
        """测试生成昨日日志（所有用户）"""
        expected_stats = {
            'total_users': 10,
            'total_days': 1,
            'generated_count': 10,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }
        self.generator.batch_generate_work_logs = MagicMock(
            return_value=expected_stats
        )
        
        # 执行（user_ids=None）
        stats = self.generator.generate_yesterday_work_logs(
            user_ids=None,
            auto_submit=False
        )
        
        # 验证
        yesterday = date.today() - timedelta(days=1)
        self.generator.batch_generate_work_logs.assert_called_once_with(
            start_date=yesterday,
            end_date=yesterday,
            user_ids=None,
            auto_submit=False
        )

    # ========== 边界情况和异常处理测试 ==========
    
    def test_generate_work_log_empty_task_name(self):
        """测试任务名称为空的情况"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            self.mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            None,  # 不存在草稿
        ]
        
        # Mock工时记录（任务名为None）
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = None
        mock_timesheet.hours = Decimal('4.0')
        mock_timesheet.work_content = None
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证使用默认任务名
        added_work_log = self.db.add.call_args[0][0]
        self.assertIn("未指定任务", added_work_log.content)

    def test_generate_work_log_decimal_hours(self):
        """测试小数工时的处理"""
        # Mock配置
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,
            self.mock_user,
            self.mock_project,
            None,
        ]
        
        # Mock工时记录（小数工时）
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "任务"
        mock_timesheet.hours = Decimal('3.5')
        mock_timesheet.work_content = None
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证工时格式
        added_work_log = self.db.add.call_args[0][0]
        self.assertIn("3.5小时", added_work_log.content)

    def test_generate_work_log_user_without_real_name(self):
        """测试用户没有真实姓名的情况"""
        # Mock用户（无真实姓名）
        mock_user = MagicMock(spec=User)
        mock_user.id = self.test_user_id
        mock_user.real_name = None
        mock_user.username = "testuser"
        
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 不存在已提交日志
            mock_user,  # 用户信息
            self.mock_project,  # 项目信息
            None,  # 不存在草稿
        ]
        
        # Mock工时记录
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.project_id = 100
        mock_timesheet.task_id = 1001
        mock_timesheet.task_name = "任务"
        mock_timesheet.hours = Decimal('8.0')
        mock_timesheet.work_content = None
        mock_timesheet.work_result = None
        mock_timesheet.progress_before = None
        mock_timesheet.progress_after = None
        
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]
        
        # 执行
        result = self.generator.generate_work_log_from_timesheet(
            user_id=self.test_user_id,
            work_date=self.test_work_date
        )
        
        # 验证使用username
        added_work_log = self.db.add.call_args[0][0]
        self.assertEqual(added_work_log.user_name, "testuser")


if __name__ == "__main__":
    unittest.main()
