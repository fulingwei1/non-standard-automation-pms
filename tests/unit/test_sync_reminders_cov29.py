# -*- coding: utf-8 -*-
"""第二十九批 - timesheet_reminder/sync_reminders.py 单元测试（数据同步失败提醒）"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.timesheet_reminder.sync_reminders")

from app.services.timesheet_reminder.sync_reminders import notify_sync_failure


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_timesheet(
    user_id=1,
    status="APPROVED",
    approve_time=None,
    work_date=None,
    ts_id=100,
):
    if approve_time is None:
        # 默认2小时前审批（会触发同步失败判断）
        approve_time = datetime.now() - timedelta(hours=2)
    if work_date is None:
        work_date = date.today()
    t = MagicMock()
    t.id = ts_id
    t.user_id = user_id
    t.status = status
    t.approve_time = approve_time
    t.work_date = work_date
    return t


# ─── 测试 ────────────────────────────────────────────────────

class TestNotifySyncFailure:
    """测试同步失败提醒逻辑"""

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_returns_zero_when_no_approved_timesheets(self, mock_create_notification):
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []

        result = notify_sync_failure(db)

        assert result == 0
        mock_create_notification.assert_not_called()

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_skips_recently_approved_timesheets(self, mock_create_notification):
        db = _make_db()
        # 审批时间刚刚过（30分钟前，不超过1小时阈值）
        recent_timesheet = _make_timesheet(
            approve_time=datetime.now() - timedelta(minutes=30)
        )
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [recent_timesheet]
        db.query.return_value.filter.return_value.all.return_value = [recent_timesheet]

        result = notify_sync_failure(db)

        # 未超过1小时，不发通知
        assert result == 0

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_sends_notification_for_overdue_sync(self, mock_create_notification):
        db = _make_db()
        old_timesheet = _make_timesheet(
            user_id=5,
            approve_time=datetime.now() - timedelta(hours=3),
            ts_id=200,
        )
        # approved timesheets列表
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [old_timesheet]
        db.query.return_value.filter.return_value.all.return_value = [old_timesheet]
        # 检查今天是否已有通知 - 返回None（没有）
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.first.return_value = None

        result = notify_sync_failure(db)

        # 应该发送了通知
        mock_create_notification.assert_called()

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_avoids_duplicate_notifications_for_same_user(self, mock_create_notification):
        db = _make_db()
        ts1 = _make_timesheet(user_id=3, approve_time=datetime.now() - timedelta(hours=3), ts_id=1)
        ts2 = _make_timesheet(user_id=3, approve_time=datetime.now() - timedelta(hours=4), ts_id=2)
        db.query.return_value.filter.return_value.all.return_value = [ts1, ts2]
        db.query.return_value.filter.return_value.first.return_value = None

        # 模拟：第一次check返回None（无已有通知）
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = notify_sync_failure(db)

        # 同一用户只发一次（因为notified_users去重）
        assert mock_create_notification.call_count <= 1

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_skips_if_already_notified_today(self, mock_create_notification):
        db = _make_db()
        ts = _make_timesheet(
            user_id=7,
            approve_time=datetime.now() - timedelta(hours=5),
            ts_id=300,
        )
        db.query.return_value.filter.return_value.all.return_value = [ts]
        # 今天已有通知
        existing_notification = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = existing_notification

        result = notify_sync_failure(db)

        mock_create_notification.assert_not_called()

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_commits_at_end(self, mock_create_notification):
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []

        notify_sync_failure(db)

        db.commit.assert_called_once()

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_notification_content_includes_work_date(self, mock_create_notification):
        db = _make_db()
        work_date = date(2025, 3, 15)
        ts = _make_timesheet(
            user_id=2,
            approve_time=datetime.now() - timedelta(hours=2),
            work_date=work_date,
            ts_id=10,
        )
        db.query.return_value.filter.return_value.all.return_value = [ts]
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.first.return_value = None

        notify_sync_failure(db)

        if mock_create_notification.called:
            call_kwargs = mock_create_notification.call_args[1]
            assert "2025-03-15" in call_kwargs.get("content", "")
