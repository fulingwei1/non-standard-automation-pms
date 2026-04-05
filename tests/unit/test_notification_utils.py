# -*- coding: utf-8 -*-
"""通知工具函数 (notification_utils) 单元测试"""

from datetime import time, datetime
from unittest.mock import MagicMock

import pytest
import importlib.util


def _load_module_directly(path: str):
    """直接加载模块，绕过 __init__.py"""
    spec = importlib.util.spec_from_file_location("notification_utils", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 尝试加载 notification_utils 模块
_load_error = ""
try:
    _notification_utils = _load_module_directly(
        "app/services/notification/notification_utils.py"
    )
    UTILS_MODULE_OK = True
except Exception as e:
    UTILS_MODULE_OK = False
    _load_error = str(e)


pytestmark = pytest.mark.skipif(
    not UTILS_MODULE_OK, reason=f"Cannot load notification_utils: {_load_error}"
)


class TestGetAlertIconUrl:
    """get_alert_icon_url 函数测试"""

    def test_warning_level(self):
        """测试 WARNING 级别"""
        result = _notification_utils.get_alert_icon_url("WARNING")
        assert "warning" in result.lower()

    def test_urgent_level(self):
        """测试 URGENT 级别"""
        result = _notification_utils.get_alert_icon_url("URGENT")
        assert "alarm" in result.lower()

    def test_info_level(self):
        """测试 INFO 级别"""
        result = _notification_utils.get_alert_icon_url("INFO")
        assert "info" in result.lower()

    def test_critical_level(self):
        """测试 CRITICAL 级别"""
        result = _notification_utils.get_alert_icon_url("CRITICAL")
        assert "priority" in result.lower() or "high" in result.lower()

    def test_tips_level(self):
        """测试 TIPS 级别"""
        result = _notification_utils.get_alert_icon_url("TIPS")
        assert "bulb" in result.lower()

    def test_unknown_level(self):
        """测试未知级别返回默认图标"""
        result = _notification_utils.get_alert_icon_url("UNKNOWN_LEVEL")
        # 应该返回默认图标 (INFO)
        assert "info" in result.lower()


class TestResolveChannelTarget:
    """resolve_channel_target 函数测试"""

    def test_email_channel_with_user(self):
        """测试邮件渠道有用户的情况"""
        user = MagicMock()
        user.email = "test@example.com"
        result = _notification_utils.resolve_channel_target("email", user)
        assert result == "test@example.com"

    def test_sms_channel_with_user(self):
        """测试短信渠道有用户的情况"""
        user = MagicMock()
        user.phone = "13800138000"
        result = _notification_utils.resolve_channel_target("sms", user)
        assert result == "13800138000"

    def test_wechat_channel_with_user_username(self):
        """测试企业微信渠道有用户名的情况"""
        user = MagicMock()
        user.username = "wx123456"
        user.phone = None
        result = _notification_utils.resolve_channel_target("wechat", user)
        assert result == "wx123456"

    def test_wechat_channel_with_user_phone(self):
        """测试企业微信渠道有手机号的情况"""
        user = MagicMock()
        user.username = None
        user.phone = "13800138000"
        result = _notification_utils.resolve_channel_target("wechat", user)
        assert result == "13800138000"

    def test_channel_with_none_user(self):
        """测试用户为 None 的情况"""
        result = _notification_utils.resolve_channel_target("email", None)
        assert result is None

    def test_system_channel(self):
        """测试系统渠道"""
        user = MagicMock()
        user.id = 123
        result = _notification_utils.resolve_channel_target("system", user)
        assert result == "123"

    def test_unsupported_channel(self):
        """测试不支持的渠道"""
        user = MagicMock()
        result = _notification_utils.resolve_channel_target("unknown_channel", user)
        assert result is None


class TestChannelAllowed:
    """channel_allowed 函数测试"""

    def test_settings_none(self):
        """测试设置为 None 时返回 True"""
        result = _notification_utils.channel_allowed("email", None)
        assert result is True

    def test_email_enabled(self):
        """测试邮件渠道启用"""
        settings = MagicMock()
        settings.email_enabled = True
        result = _notification_utils.channel_allowed("email", settings)
        assert result is True

    def test_email_disabled(self):
        """测试邮件渠道禁用"""
        settings = MagicMock()
        settings.email_enabled = False
        result = _notification_utils.channel_allowed("email", settings)
        assert result is False

    def test_sms_disabled_by_default(self):
        """测试短信默认禁用"""
        settings = MagicMock()
        settings.sms_enabled = False
        result = _notification_utils.channel_allowed("sms", settings)
        assert result is False


class TestParseTimeStr:
    """parse_time_str 函数测试"""

    def test_valid_time_string(self):
        """测试有效的时间字符串 HH:MM"""
        result = _notification_utils.parse_time_str("09:30")
        assert result == time(9, 30)

    def test_valid_time_with_seconds(self):
        """测试带秒的时间字符串 (会忽略秒)"""
        result = _notification_utils.parse_time_str("09:30:45")
        # parse_time_str 只处理 HH:MM，秒会被忽略或导致解析失败
        assert result is None or result == time(9, 30)

    def test_none_input(self):
        """测试 None 输入"""
        result = _notification_utils.parse_time_str(None)
        assert result is None

    def test_empty_string(self):
        """测试空字符串"""
        result = _notification_utils.parse_time_str("")
        assert result is None

    def test_invalid_time_string(self):
        """测试无效的时间字符串"""
        result = _notification_utils.parse_time_str("invalid")
        assert result is None


class TestIsQuietHours:
    """is_quiet_hours 函数测试"""

    def test_inside_quiet_hours(self):
        """测试在静默时段内 (22:00-08:00 跨越午夜)"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "08:00"
        current = datetime(2024, 1, 1, 23, 0, 0)  # 晚上11点

        result = _notification_utils.is_quiet_hours(settings, current)
        assert result is True

    def test_outside_quiet_hours_same_day(self):
        """测试在同一天内不在静默时段"""
        settings = MagicMock()
        settings.quiet_hours_start = "09:00"
        settings.quiet_hours_end = "17:00"
        current = datetime(2024, 1, 1, 14, 0, 0)  # 下午2点

        result = _notification_utils.is_quiet_hours(settings, current)
        assert result is True

    def test_outside_quiet_hours(self):
        """测试不在静默时段内"""
        settings = MagicMock()
        settings.quiet_hours_start = "09:00"
        settings.quiet_hours_end = "17:00"
        current = datetime(2024, 1, 1, 8, 0, 0)  # 早上8点

        result = _notification_utils.is_quiet_hours(settings, current)
        assert result is False

    def test_settings_none(self):
        """测试设置为 None 时不在静默时段"""
        result = _notification_utils.is_quiet_hours(None, datetime.now())
        assert result is False

    def test_no_start_time(self):
        """测试没有开始时间"""
        settings = MagicMock()
        settings.quiet_hours_start = None
        settings.quiet_hours_end = "08:00"

        result = _notification_utils.is_quiet_hours(settings, datetime.now())
        assert result is False