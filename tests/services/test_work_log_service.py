# -*- coding: utf-8 -*-
"""
WorkLogService 单元测试 - N5组
覆盖：日志创建/更新验证、@提及处理、工时联动、选项查询
"""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch, call

from app.services.work_log_service import WorkLogService


def _make_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.join.return_value = q
    q.all.return_value = []
    q.first.return_value = None
    q.delete.return_value = None
    return db, q


def _make_create_data(**overrides):
    """构造 WorkLogCreate mock"""
    data = MagicMock()
    defaults = dict(
        work_date=date(2025, 6, 1),
        content="今日完成了产品调试工作",
        status="SUBMITTED",
        mentioned_projects=[],
        mentioned_machines=[],
        mentioned_users=[],
        work_hours=None,
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(data, k, v)
    return data


def _make_update_data(**overrides):
    """构造 WorkLogUpdate mock"""
    data = MagicMock()
    defaults = dict(
        content=None,
        status=None,
        mentioned_projects=None,
        mentioned_machines=None,
        mentioned_users=None,
        work_hours=None,
        work_type=None,
        project_id=None,
        rd_project_id=None,
        task_id=None,
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(data, k, v)
    return data


class TestCreateWorkLog(unittest.TestCase):
    """create_work_log 主流程测试"""

    def setUp(self):
        self.db, self.q = _make_db()
        self.svc = WorkLogService(self.db)

    def test_content_too_long_raises(self):
        """内容超过300字时应抛出 ValueError"""
        data = _make_create_data(content="x" * 301)

        with self.assertRaises(ValueError) as ctx:
            self.svc.create_work_log(user_id=1, work_log_in=data)
        self.assertIn("300", str(ctx.exception))

    def test_duplicate_submission_raises(self):
        """同一天已提交（非草稿）时抛出 ValueError"""
        existing = MagicMock(id=10)  # existing log found
        data = _make_create_data()

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = existing  # existing log
            return q

        self.db.query.side_effect = make_query

        with self.assertRaises(ValueError) as ctx:
            self.svc.create_work_log(user_id=1, work_log_in=data)
        self.assertIn("已提交", str(ctx.exception))

    def test_user_not_found_raises(self):
        """用户不存在时抛出 ValueError"""
        data = _make_create_data()

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = None  # no existing log
            elif call_count[0] == 2:
                q.first.return_value = None  # user not found
            return q

        self.db.query.side_effect = make_query

        with self.assertRaises(ValueError) as ctx:
            self.svc.create_work_log(user_id=99, work_log_in=data)
        self.assertIn("用户不存在", str(ctx.exception))

    def test_create_success_with_no_mentions(self):
        """无@提及时正常创建日志"""
        user = MagicMock(id=1, real_name="张三", username="zhangsan")
        data = _make_create_data(mentioned_projects=[], mentioned_machines=[], mentioned_users=[])

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = None  # no existing log
            else:
                q.first.return_value = user  # user found
            return q

        self.db.query.side_effect = make_query
        work_log = MagicMock(id=1)
        self.db.flush = MagicMock()

        with patch('app.services.work_log_service.WorkLog', return_value=work_log):
            result = self.svc.create_work_log(user_id=1, work_log_in=data)

        self.db.add.assert_called()
        self.db.commit.assert_called_once()

    def test_create_with_work_hours_creates_timesheet(self):
        """提供 work_hours 时自动创建工时记录"""
        user = MagicMock(id=1, real_name="张三", username="zhangsan", department_id=None)
        data = _make_create_data(work_hours=8.0, project_id=None, rd_project_id=None, task_id=None)

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = None  # no existing log
            else:
                q.first.return_value = user
            return q

        self.db.query.side_effect = make_query
        work_log = MagicMock(id=1, timesheet_id=None)
        timesheet = MagicMock(id=99)

        with patch('app.services.work_log_service.WorkLog', return_value=work_log), \
             patch('app.services.work_log_service.Timesheet', return_value=timesheet):
            with patch.object(self.svc, '_create_mentions'), \
                 patch.object(self.svc, '_link_to_progress'), \
                 patch.object(self.svc, '_create_timesheet_from_worklog', return_value=timesheet) as mock_ts:
                result = self.svc.create_work_log(user_id=1, work_log_in=data)
                mock_ts.assert_called_once()


class TestUpdateWorkLog(unittest.TestCase):
    """update_work_log 更新流程测试"""

    def setUp(self):
        self.db, self.q = _make_db()
        self.svc = WorkLogService(self.db)

    def test_not_found_raises(self):
        """工作日志不存在时抛出 ValueError"""
        self.q.first.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.svc.update_work_log(work_log_id=999, user_id=1, work_log_in=_make_update_data())
        self.assertIn("不存在", str(ctx.exception))

    def test_wrong_user_raises(self):
        """非日志所有者更新时抛出 ValueError"""
        log = MagicMock(id=1, user_id=2, status="DRAFT")  # owned by user 2
        self.q.first.return_value = log

        with self.assertRaises(ValueError) as ctx:
            self.svc.update_work_log(work_log_id=1, user_id=1, work_log_in=_make_update_data())
        self.assertIn("自己", str(ctx.exception))

    def test_non_draft_status_raises(self):
        """非草稿状态的日志不允许更新"""
        log = MagicMock(id=1, user_id=1, status="SUBMITTED")  # not DRAFT
        self.q.first.return_value = log

        with self.assertRaises(ValueError) as ctx:
            self.svc.update_work_log(work_log_id=1, user_id=1, work_log_in=_make_update_data())
        self.assertIn("草稿", str(ctx.exception))

    def test_update_content_too_long_raises(self):
        """更新内容超过300字时抛出 ValueError"""
        log = MagicMock(id=1, user_id=1, status="DRAFT")
        self.q.first.return_value = log
        data = _make_update_data(content="x" * 301)

        with self.assertRaises(ValueError) as ctx:
            self.svc.update_work_log(work_log_id=1, user_id=1, work_log_in=data)
        self.assertIn("300", str(ctx.exception))

    def test_update_content_success(self):
        """合法内容更新应成功"""
        log = MagicMock(id=1, user_id=1, status="DRAFT",
                        work_date=date(2025, 6, 1), content="旧内容",
                        timesheet_id=None)
        self.q.first.return_value = log
        data = _make_update_data(content="新内容")

        result = self.svc.update_work_log(work_log_id=1, user_id=1, work_log_in=data)
        self.assertEqual(log.content, "新内容")
        self.db.commit.assert_called_once()

    def test_update_status_to_submitted(self):
        """可以更新状态"""
        log = MagicMock(id=1, user_id=1, status="DRAFT",
                        work_date=date(2025, 6, 1), content="内容",
                        timesheet_id=None)
        self.q.first.return_value = log
        data = _make_update_data(status="SUBMITTED")

        self.svc.update_work_log(work_log_id=1, user_id=1, work_log_in=data)
        self.assertEqual(log.status, "SUBMITTED")


class TestCreateMentions(unittest.TestCase):
    """_create_mentions 提及创建测试"""

    def setUp(self):
        self.db, self.q = _make_db()
        self.svc = WorkLogService(self.db)

    def test_project_mention_creates_record(self):
        """@项目时创建项目类型提及记录"""
        project = MagicMock(id=1, project_name="测试项目")
        self.q.first.return_value = project
        data = _make_create_data(mentioned_projects=[1], mentioned_machines=[], mentioned_users=[])

        with patch('app.services.work_log_service.WorkLogMention') as MockMention:
            MockMention.return_value = MagicMock()
            self.svc._create_mentions(work_log_id=100, work_log_in=data)

        MockMention.assert_called_once()
        call_kwargs = MockMention.call_args.kwargs
        self.assertEqual(call_kwargs.get("mention_id"), 1)

    def test_machine_mention_creates_record(self):
        """@设备时创建设备类型提及记录"""
        machine = MagicMock(id=2, machine_name="设备A")
        self.q.first.return_value = machine
        data = _make_create_data(mentioned_projects=[], mentioned_machines=[2], mentioned_users=[])

        with patch('app.services.work_log_service.WorkLogMention') as MockMention:
            MockMention.return_value = MagicMock()
            self.svc._create_mentions(work_log_id=100, work_log_in=data)

        MockMention.assert_called_once()

    def test_user_mention_creates_record(self):
        """@用户时创建用户类型提及记录"""
        user = MagicMock(id=3, real_name="李四", username="lisi")
        self.q.first.return_value = user
        data = _make_create_data(mentioned_projects=[], mentioned_machines=[], mentioned_users=[3])

        with patch('app.services.work_log_service.WorkLogMention') as MockMention:
            MockMention.return_value = MagicMock()
            self.svc._create_mentions(work_log_id=100, work_log_in=data)

        MockMention.assert_called_once()

    def test_nonexistent_mention_target_skipped(self):
        """@的目标不存在时跳过（不抛异常）"""
        self.q.first.return_value = None  # project not found
        data = _make_create_data(mentioned_projects=[999], mentioned_machines=[], mentioned_users=[])

        with patch('app.services.work_log_service.WorkLogMention') as MockMention:
            self.svc._create_mentions(work_log_id=100, work_log_in=data)

        MockMention.assert_not_called()


class TestGetMentionOptions(unittest.TestCase):
    """get_mention_options 选项查询测试"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = WorkLogService(self.db)

    def test_returns_all_options(self):
        """返回包含项目、设备、用户三类选项"""
        project = MagicMock(id=1, project_name="项目A", is_active=True)
        machine = MagicMock(id=2, machine_name="设备B")
        user = MagicMock(id=3, real_name="王五", username="wangwu", is_active=True)

        call_count = [0]
        def make_query(*args):
            q = MagicMock()
            q.filter.return_value = q
            q.join.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.all.return_value = [project]
            elif call_count[0] == 2:
                q.all.return_value = [machine]
            else:
                q.all.return_value = [user]
            return q

        self.db.query.side_effect = make_query

        result = self.svc.get_mention_options(user_id=1)
        self.assertEqual(len(result.projects), 1)
        self.assertEqual(len(result.machines), 1)
        self.assertEqual(len(result.users), 1)
        self.assertEqual(result.projects[0].name, "项目A")
        self.assertEqual(result.machines[0].name, "设备B")

    def test_empty_options(self):
        """无数据时返回空列表"""
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        result = self.svc.get_mention_options(user_id=1)
        self.assertEqual(result.projects, [])
        self.assertEqual(result.machines, [])
        self.assertEqual(result.users, [])


if __name__ == "__main__":
    unittest.main()
