# -*- coding: utf-8 -*-
"""
notification_utils 模块综合单元测试

测试覆盖:
- get_alert_icon_url: 获取预警图标URL
- resolve_channels: 解析通知渠道
- resolve_recipients: 解析接收者
- resolve_channel_target: 解析渠道目标
- channel_allowed: 检查渠道是否允许
- parse_time_str: 解析时间字符串
- is_quiet_hours: 检查是否在免打扰时间
- next_quiet_resume: 计算下次恢复时间
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, time, timedelta

import pytest


class TestGetAlertIconUrl:
    """测试 get_alert_icon_url 函数"""

    def test_returns_urgent_icon(self):
        """测试返回紧急图标"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("URGENT")

        assert "alarm" in result

    def test_returns_critical_icon(self):
        """测试返回严重图标"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("CRITICAL")

        assert "high-priority" in result

    def test_returns_warning_icon(self):
        """测试返回警告图标"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("WARNING")

        assert "warning" in result

    def test_returns_info_icon(self):
        """测试返回信息图标"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("INFO")

        assert "info" in result

    def test_returns_tips_icon(self):
        """测试返回提示图标"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("TIPS")

        assert "light-bulb" in result

    def test_handles_lowercase(self):
        """测试处理小写输入"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("urgent")

        assert "alarm" in result

    def test_returns_default_for_unknown(self):
        """测试未知级别返回默认图标"""
        from app.services.notification_utils import get_alert_icon_url

        result = get_alert_icon_url("UNKNOWN")

        assert "info" in result


class TestResolveChannels:
    """测试 resolve_channels 函数"""

    def test_returns_rule_channels(self):
        """测试返回规则配置的渠道"""
        from app.services.notification_utils import resolve_channels

        mock_alert = MagicMock()
        mock_alert.rule = MagicMock()
        mock_alert.rule.notify_channels = ["email", "wechat"]

        result = resolve_channels(mock_alert)

        assert "EMAIL" in result
        assert "WECHAT" in result

    def test_returns_system_when_no_rule(self):
        """测试没有规则时返回SYSTEM"""
        from app.services.notification_utils import resolve_channels

        mock_alert = MagicMock()
        mock_alert.rule = None

        result = resolve_channels(mock_alert)

        assert result == ["SYSTEM"]

    def test_returns_system_when_empty_channels(self):
        """测试渠道列表为空时返回SYSTEM"""
        from app.services.notification_utils import resolve_channels

        mock_alert = MagicMock()
        mock_alert.rule = MagicMock()
        mock_alert.rule.notify_channels = []

        result = resolve_channels(mock_alert)

        assert result == ["SYSTEM"]


class TestResolveRecipients:
    """测试 resolve_recipients 函数"""

    def test_includes_project_pm(self):
        """测试包含项目经理"""
        from app.services.notification_utils import resolve_recipients

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.project = MagicMock()
        mock_alert.project.pm_id = 1
        mock_alert.handler_id = None
        mock_alert.rule = None

        mock_user = MagicMock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_user]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = resolve_recipients(mock_db, mock_alert)

        assert 1 in result

    def test_includes_handler(self):
        """测试包含处理人"""
        from app.services.notification_utils import resolve_recipients

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.project = None
        mock_alert.handler_id = 2
        mock_alert.rule = None

        mock_user = MagicMock()
        mock_user.id = 2
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_user]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = resolve_recipients(mock_db, mock_alert)

        assert 2 in result

    def test_includes_rule_notify_users(self):
        """测试包含规则通知用户"""
        from app.services.notification_utils import resolve_recipients

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.project = None
        mock_alert.handler_id = None
        mock_alert.rule = MagicMock()
        mock_alert.rule.notify_users = [3, 4]

        mock_user3 = MagicMock()
        mock_user3.id = 3
        mock_user4 = MagicMock()
        mock_user4.id = 4

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_user3, mock_user4]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = resolve_recipients(mock_db, mock_alert)

        assert 3 in result
        assert 4 in result

    def test_defaults_to_user_1(self):
        """测试默认使用用户1"""
        from app.services.notification_utils import resolve_recipients

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.project = None
        mock_alert.handler_id = None
        mock_alert.rule = None

        mock_user = MagicMock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_user]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = resolve_recipients(mock_db, mock_alert)

        assert 1 in result


class TestResolveChannelTarget:
    """测试 resolve_channel_target 函数"""

    def test_returns_none_when_no_user(self):
        """测试没有用户时返回None"""
        from app.services.notification_utils import resolve_channel_target

        result = resolve_channel_target("EMAIL", None)

        assert result is None

    def test_returns_user_id_for_system(self):
        """测试SYSTEM渠道返回用户ID"""
        from app.services.notification_utils import resolve_channel_target

        mock_user = MagicMock()
        mock_user.id = 123

        result = resolve_channel_target("SYSTEM", mock_user)

        assert result == "123"

    def test_returns_email_for_email_channel(self):
        """测试EMAIL渠道返回邮箱"""
        from app.services.notification_utils import resolve_channel_target

        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        result = resolve_channel_target("EMAIL", mock_user)

        assert result == "test@example.com"

    def test_returns_username_for_wechat(self):
        """测试WECHAT渠道返回用户名"""
        from app.services.notification_utils import resolve_channel_target

        mock_user = MagicMock()
        mock_user.username = "zhangsan"
        mock_user.phone = "13800138000"

        result = resolve_channel_target("WECHAT", mock_user)

        assert result == "zhangsan"

    def test_returns_phone_for_sms(self):
        """测试SMS渠道返回手机号"""
        from app.services.notification_utils import resolve_channel_target

        mock_user = MagicMock()
        mock_user.phone = "13800138000"

        result = resolve_channel_target("SMS", mock_user)

        assert result == "13800138000"

    def test_handles_lowercase_channel(self):
        """测试处理小写渠道名"""
        from app.services.notification_utils import resolve_channel_target

        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        result = resolve_channel_target("email", mock_user)

        assert result == "test@example.com"


class TestChannelAllowed:
    """测试 channel_allowed 函数"""

    def test_returns_true_when_no_settings(self):
        """测试没有设置时返回True"""
        from app.services.notification_utils import channel_allowed

        result = channel_allowed("EMAIL", None)

        assert result is True

    def test_checks_system_enabled(self):
        """测试检查系统渠道"""
        from app.services.notification_utils import channel_allowed

        mock_settings = MagicMock()
        mock_settings.system_enabled = True

        result = channel_allowed("SYSTEM", mock_settings)

        assert result is True

    def test_checks_email_enabled(self):
        """测试检查邮件渠道"""
        from app.services.notification_utils import channel_allowed

        mock_settings = MagicMock()
        mock_settings.email_enabled = False

        result = channel_allowed("EMAIL", mock_settings)

        assert result is False

    def test_checks_wechat_enabled(self):
        """测试检查微信渠道"""
        from app.services.notification_utils import channel_allowed

        mock_settings = MagicMock()
        mock_settings.wechat_enabled = True

        result = channel_allowed("WECHAT", mock_settings)

        assert result is True

    def test_checks_sms_enabled(self):
        """测试检查短信渠道"""
        from app.services.notification_utils import channel_allowed

        mock_settings = MagicMock()
        mock_settings.sms_enabled = False

        result = channel_allowed("SMS", mock_settings)

        assert result is False

    def test_returns_true_for_unknown_channel(self):
        """测试未知渠道返回True"""
        from app.services.notification_utils import channel_allowed

        mock_settings = MagicMock()

        result = channel_allowed("UNKNOWN", mock_settings)

        assert result is True


class TestParseTimeStr:
    """测试 parse_time_str 函数"""

    def test_parses_valid_time(self):
        """测试解析有效时间"""
        from app.services.notification_utils import parse_time_str

        result = parse_time_str("22:30")

        assert result == time(22, 30)

    def test_returns_none_for_none(self):
        """测试空值返回None"""
        from app.services.notification_utils import parse_time_str

        result = parse_time_str(None)

        assert result is None

    def test_returns_none_for_invalid(self):
        """测试无效格式返回None"""
        from app.services.notification_utils import parse_time_str

        result = parse_time_str("invalid")

        assert result is None


class TestIsQuietHours:
    """测试 is_quiet_hours 函数"""

    def test_returns_false_when_no_settings(self):
        """测试没有设置时返回False"""
        from app.services.notification_utils import is_quiet_hours

        result = is_quiet_hours(None, datetime.now())

        assert result is False

    def test_returns_false_when_no_quiet_hours(self):
        """测试没有免打扰时间时返回False"""
        from app.services.notification_utils import is_quiet_hours

        mock_settings = MagicMock()
        mock_settings.quiet_hours_start = None
        mock_settings.quiet_hours_end = None

        result = is_quiet_hours(mock_settings, datetime.now())

        assert result is False

    def test_returns_true_during_quiet_hours(self):
        """测试在免打扰时间内返回True"""
        from app.services.notification_utils import is_quiet_hours

        mock_settings = MagicMock()
        mock_settings.quiet_hours_start = "22:00"
        mock_settings.quiet_hours_end = "08:00"

        # 测试晚上11点
        test_time = datetime(2024, 1, 15, 23, 0)

        result = is_quiet_hours(mock_settings, test_time)

        assert result is True

    def test_returns_false_outside_quiet_hours(self):
        """测试在免打扰时间外返回False"""
        from app.services.notification_utils import is_quiet_hours

        mock_settings = MagicMock()
        mock_settings.quiet_hours_start = "22:00"
        mock_settings.quiet_hours_end = "08:00"

        # 测试下午3点
        test_time = datetime(2024, 1, 15, 15, 0)

        result = is_quiet_hours(mock_settings, test_time)

        assert result is False


class TestNextQuietResume:
    """测试 next_quiet_resume 函数"""

    def test_returns_end_time(self):
        """测试返回结束时间"""
        from app.services.notification_utils import next_quiet_resume

        mock_settings = MagicMock()
        mock_settings.quiet_hours_end = "08:00"

        current = datetime(2024, 1, 15, 23, 0)

        result = next_quiet_resume(mock_settings, current)

        assert result.hour == 8
        assert result.minute == 0

    def test_adds_day_if_past(self):
        """测试如果已过则加一天"""
        from app.services.notification_utils import next_quiet_resume

        mock_settings = MagicMock()
        mock_settings.quiet_hours_end = "08:00"

        current = datetime(2024, 1, 15, 10, 0)  # 已过8点

        result = next_quiet_resume(mock_settings, current)

        assert result.day == 16

    def test_defaults_to_30_minutes(self):
        """测试没有结束时间时默认30分钟"""
        from app.services.notification_utils import next_quiet_resume

        mock_settings = MagicMock()
        mock_settings.quiet_hours_end = None

        current = datetime(2024, 1, 15, 10, 0)

        result = next_quiet_resume(mock_settings, current)

        expected = current + timedelta(minutes=30)
        assert result == expected
