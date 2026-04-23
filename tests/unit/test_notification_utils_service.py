# -*- coding: utf-8 -*-
"""
通知工具函数单元测试
"""

from datetime import datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.notification import NotificationSettings
from app.models.user import User


class TestGetAlertIconUrl:
    """测试获取预警图标URL"""

    def test_urgent_icon(self):
        """测试紧急图标"""
        from app.services.notification_utils import get_alert_icon_url

        url = get_alert_icon_url("URGENT")
        assert "alarm" in url

    def test_critical_icon(self):
        """测试严重图标"""
        from app.services.notification_utils import get_alert_icon_url

        url = get_alert_icon_url("CRITICAL")
        assert "high-priority" in url

    def test_warning_icon(self):
        """测试警告图标"""
        from app.services.notification_utils import get_alert_icon_url

        url = get_alert_icon_url("WARNING")
        assert "warning" in url

    def test_info_icon(self):
        """测试信息图标"""
        from app.services.notification_utils import get_alert_icon_url

        url = get_alert_icon_url("INFO")
        assert "info" in url

    def test_unknown_level_default(self):
        """测试未知级别使用默认图标"""
        from app.services.notification_utils import get_alert_icon_url

        url = get_alert_icon_url("UNKNOWN")
        assert "info" in url  # 默认使用INFO图标

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        from app.services.notification_utils import get_alert_icon_url

        url = get_alert_icon_url("warning")
        assert "warning" in url


class TestResolveChannels:
    """测试解析通知渠道"""

    def test_no_rule(self):
        """测试无规则"""
        from app.services.notification_utils import resolve_channels

        alert = MagicMock()
        alert.rule = None

        channels = resolve_channels(alert)
        assert channels == ["SYSTEM"]

    def test_with_channels(self):
        """测试有渠道配置"""
        from app.services.notification_utils import resolve_channels

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.notify_channels = ["email", "wechat"]

        channels = resolve_channels(alert)
        assert "EMAIL" in channels
        assert "WECHAT" in channels

    def test_with_empty_channel_list_falls_back_to_system(self):
        from app.services.notification_utils import resolve_channels

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.notify_channels = []

        assert resolve_channels(alert) == ["SYSTEM"]


class TestResolveChannelTarget:
    """测试解析通道目标"""

    def test_system_channel(self):
        """测试系统通道"""
        from app.services.notification_utils import resolve_channel_target

        user = MagicMock()
        user.id = 123

        target = resolve_channel_target("SYSTEM", user)
        assert target == "123"

    def test_email_channel(self):
        """测试邮件通道"""
        from app.services.notification_utils import resolve_channel_target

        user = MagicMock()
        user.email = "test@example.com"

        target = resolve_channel_target("EMAIL", user)
        assert target == "test@example.com"

    def test_wechat_channel(self):
        """测试微信通道"""
        from app.services.notification_utils import resolve_channel_target

        user = MagicMock()
        user.username = "wechat_user"
        user.phone = "13800138000"

        target = resolve_channel_target("WECHAT", user)
        assert target == "wechat_user"

    def test_sms_channel(self):
        """测试短信通道"""
        from app.services.notification_utils import resolve_channel_target

        user = MagicMock()
        user.phone = "13800138000"

        target = resolve_channel_target("SMS", user)
        assert target == "13800138000"

    def test_no_user(self):
        """测试无用户"""
        from app.services.notification_utils import resolve_channel_target

        target = resolve_channel_target("SYSTEM", None)
        assert target is None

    def test_wecom_channel_uses_username_or_phone(self):
        from app.services.notification_utils import resolve_channel_target

        user = MagicMock()
        user.username = ""
        user.phone = "13800138000"

        assert resolve_channel_target("WE_COM", user) == "13800138000"

    def test_unknown_channel_returns_none(self):
        from app.services.notification_utils import resolve_channel_target

        user = MagicMock()
        user.id = 123

        assert resolve_channel_target("PUSH", user) is None


class TestChannelAllowed:
    """测试渠道是否允许"""

    def test_no_settings(self):
        """测试无设置"""
        from app.services.notification_utils import channel_allowed

        result = channel_allowed("SYSTEM", None)
        assert result is True

    def test_system_enabled(self):
        """测试系统通道启用"""
        from app.services.notification_utils import channel_allowed

        settings = MagicMock()
        settings.system_enabled = True

        result = channel_allowed("SYSTEM", settings)
        assert result is True

    def test_email_disabled(self):
        """测试邮件通道禁用"""
        from app.services.notification_utils import channel_allowed

        settings = MagicMock()
        settings.email_enabled = False

        result = channel_allowed("EMAIL", settings)
        assert result is False

    def test_wechat_and_sms_flags(self):
        from app.services.notification_utils import channel_allowed

        settings = MagicMock()
        settings.wechat_enabled = True
        settings.sms_enabled = False

        assert channel_allowed("WE_COM", settings) is True
        assert channel_allowed("SMS", settings) is False

    def test_unknown_channel_defaults_true(self):
        from app.services.notification_utils import channel_allowed

        settings = MagicMock()

        assert channel_allowed("PUSH", settings) is True


class TestParseTimeStr:
    """测试解析时间字符串"""

    def test_valid_time(self):
        """测试有效时间"""
        from app.services.notification_utils import parse_time_str

        result = parse_time_str("08:30")
        assert result == time(8, 30)

    def test_none_value(self):
        """测试None值"""
        from app.services.notification_utils import parse_time_str

        result = parse_time_str(None)
        assert result is None

    def test_invalid_format(self):
        """测试无效格式"""
        from app.services.notification_utils import parse_time_str

        result = parse_time_str("invalid")
        assert result is None


class TestIsQuietHours:
    """测试是否为免打扰时间"""

    def test_no_settings(self):
        """测试无设置"""
        from app.services.notification_utils import is_quiet_hours

        result = is_quiet_hours(None, datetime.now())
        assert result is False

    def test_in_quiet_hours(self):
        """测试在免打扰时间内"""
        from app.services.notification_utils import is_quiet_hours

        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "08:00"

        # 凌晨3点
        current_time = datetime(2025, 1, 15, 3, 0)
        result = is_quiet_hours(settings, current_time)

        assert result is True

    def test_outside_quiet_hours(self):
        """测试在免打扰时间外"""
        from app.services.notification_utils import is_quiet_hours

        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "08:00"

        # 下午3点
        current_time = datetime(2025, 1, 15, 15, 0)
        result = is_quiet_hours(settings, current_time)

        assert result is False

    def test_invalid_quiet_hours_config_returns_false(self):
        from app.services.notification_utils import is_quiet_hours

        settings = MagicMock()
        settings.quiet_hours_start = "invalid"
        settings.quiet_hours_end = "08:00"

        assert is_quiet_hours(settings, datetime.now()) is False

    def test_same_day_quiet_hours_range(self):
        from app.services.notification_utils import is_quiet_hours

        settings = MagicMock()
        settings.quiet_hours_start = "09:00"
        settings.quiet_hours_end = "18:00"

        current_time = datetime(2025, 1, 15, 10, 0)
        assert is_quiet_hours(settings, current_time) is True


class TestNextQuietResume:
    """测试下次免打扰结束时间"""

    def test_resume_same_day(self):
        """测试同一天恢复"""
        from app.services.notification_utils import next_quiet_resume

        settings = MagicMock()
        settings.quiet_hours_end = "08:00"

        # 凌晨3点
        current_time = datetime(2025, 1, 15, 3, 0)
        result = next_quiet_resume(settings, current_time)

        assert result.hour == 8
        assert result.date() == current_time.date()

    def test_resume_next_day(self):
        """测试第二天恢复"""
        from app.services.notification_utils import next_quiet_resume

        settings = MagicMock()
        settings.quiet_hours_end = "08:00"

        # 上午10点（已过今天的结束时间）
        current_time = datetime(2025, 1, 15, 10, 0)
        result = next_quiet_resume(settings, current_time)

        assert result.date() == (current_time + timedelta(days=1)).date()

    def test_no_end_time(self):
        """测试无结束时间"""
        from app.services.notification_utils import next_quiet_resume

        settings = MagicMock()
        settings.quiet_hours_end = None

        current_time = datetime(2025, 1, 15, 3, 0)
        result = next_quiet_resume(settings, current_time)

        # 默认30分钟后
        assert result == current_time + timedelta(minutes=30)


class TestResolveRecipients:
    """测试解析接收人"""

    def test_with_project_pm(self, db_session):
        """测试有项目经理"""
        from app.services.notification_utils import resolve_recipients

        alert = MagicMock()
        alert.project = MagicMock()
        alert.project.pm_id = 1
        alert.handler_id = None
        alert.rule = None

        result = resolve_recipients(db_session, alert)
        assert isinstance(result, dict)

    def test_includes_handler_and_rule_users_with_settings(self):
        from app.services.notification_utils import resolve_recipients

        user1 = SimpleNamespace(id=1, is_active=True)
        user2 = SimpleNamespace(id=2, is_active=True)
        settings = SimpleNamespace(user_id=2)

        user_query = Mock()
        user_query.filter.return_value = user_query
        user_query.all.return_value = [user1, user2]

        settings_query = Mock()
        settings_query.filter.return_value = settings_query
        settings_query.all.return_value = [settings]

        db = Mock()

        def query_side_effect(model):
            if model is User:
                return user_query
            if model is NotificationSettings:
                return settings_query
            raise AssertionError(model)

        db.query.side_effect = query_side_effect

        alert = SimpleNamespace(
            project=None,
            handler_id=2,
            rule=SimpleNamespace(notify_users=[1, "x", 2]),
        )

        result = resolve_recipients(db, alert)

        assert set(result.keys()) == {1, 2}
        assert result[1]["settings"] is None
        assert result[2]["settings"] == settings

    def test_defaults_to_admin_user_when_no_recipients(self):
        from app.services.notification_utils import resolve_recipients

        user = SimpleNamespace(id=1, is_active=True)
        user_query = Mock()
        user_query.filter.return_value = user_query
        user_query.all.return_value = [user]

        settings_query = Mock()
        settings_query.filter.return_value = settings_query
        settings_query.all.return_value = []

        db = Mock()

        def query_side_effect(model):
            if model is User:
                return user_query
            if model is NotificationSettings:
                return settings_query
            raise AssertionError(model)

        db.query.side_effect = query_side_effect

        alert = SimpleNamespace(project=None, handler_id=None, rule=None)

        result = resolve_recipients(db, alert)

        assert result == {1: {"user": user, "settings": None}}

    def test_returns_empty_when_user_lookup_is_empty(self):
        from app.services.notification_utils import resolve_recipients

        user_query = Mock()
        user_query.filter.return_value = user_query
        user_query.all.return_value = []

        db = Mock()
        db.query.return_value = user_query

        alert = SimpleNamespace(project=None, handler_id=9, rule=None)

        assert resolve_recipients(db, alert) == {}


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
