# -*- coding: utf-8 -*-
"""
通知工具函数单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库和模型对象）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock
from datetime import datetime, time, timedelta

from app.services.notification_utils import (
    get_alert_icon_url,
    resolve_channels,
    resolve_recipients,
    resolve_channel_target,
    channel_allowed,
    parse_time_str,
    is_quiet_hours,
    next_quiet_resume,
)


class TestGetAlertIconUrl(unittest.TestCase):
    """测试预警图标URL获取"""

    def test_urgent_level(self):
        """测试URGENT级别"""
        url = get_alert_icon_url("URGENT")
        self.assertEqual(url, "https://img.icons8.com/color/96/alarm--v1.png")

    def test_critical_level(self):
        """测试CRITICAL级别"""
        url = get_alert_icon_url("CRITICAL")
        self.assertEqual(url, "https://img.icons8.com/color/96/high-priority--v1.png")

    def test_warning_level(self):
        """测试WARNING级别"""
        url = get_alert_icon_url("WARNING")
        self.assertEqual(url, "https://img.icons8.com/color/96/warning--v1.png")

    def test_info_level(self):
        """测试INFO级别"""
        url = get_alert_icon_url("INFO")
        self.assertEqual(url, "https://img.icons8.com/color/96/info--v1.png")

    def test_tips_level(self):
        """测试TIPS级别"""
        url = get_alert_icon_url("TIPS")
        self.assertEqual(url, "https://img.icons8.com/color/96/light-bulb--v1.png")

    def test_lowercase_level(self):
        """测试小写级别（应转大写）"""
        url = get_alert_icon_url("warning")
        self.assertEqual(url, "https://img.icons8.com/color/96/warning--v1.png")

    def test_unknown_level(self):
        """测试未知级别（应返回INFO）"""
        url = get_alert_icon_url("UNKNOWN")
        self.assertEqual(url, "https://img.icons8.com/color/96/info--v1.png")

    def test_empty_level(self):
        """测试空级别（应返回INFO）"""
        url = get_alert_icon_url("")
        self.assertEqual(url, "https://img.icons8.com/color/96/info--v1.png")


class TestResolveChannels(unittest.TestCase):
    """测试渠道解析"""

    def test_with_configured_channels(self):
        """测试已配置渠道"""
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.notify_channels = ["email", "wechat"]
        
        channels = resolve_channels(alert)
        self.assertEqual(channels, ["EMAIL", "WECHAT"])

    def test_with_single_channel(self):
        """测试单个渠道"""
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.notify_channels = ["sms"]
        
        channels = resolve_channels(alert)
        self.assertEqual(channels, ["SMS"])

    def test_with_empty_channels(self):
        """测试空渠道列表（应返回SYSTEM）"""
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.notify_channels = []
        
        channels = resolve_channels(alert)
        self.assertEqual(channels, ["SYSTEM"])

    def test_with_none_channels(self):
        """测试None渠道（应返回SYSTEM）"""
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.notify_channels = None
        
        channels = resolve_channels(alert)
        self.assertEqual(channels, ["SYSTEM"])

    def test_without_rule(self):
        """测试无规则（应返回SYSTEM）"""
        alert = MagicMock()
        alert.rule = None
        
        channels = resolve_channels(alert)
        self.assertEqual(channels, ["SYSTEM"])


class TestResolveRecipients(unittest.TestCase):
    """测试接收者解析"""

    def test_with_pm_only(self):
        """测试仅有项目经理"""
        db = MagicMock()
        alert = MagicMock()
        alert.project = MagicMock()
        alert.project.pm_id = 1
        alert.handler_id = None
        alert.rule = None

        # 模拟用户查询
        user = MagicMock()
        user.id = 1
        user.is_active = True
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user]
        
        # 模拟通知设置查询
        db.query.return_value.filter.return_value.all.return_value = []

        recipients = resolve_recipients(db, alert)
        
        self.assertIn(1, recipients)
        self.assertEqual(recipients[1]["user"], user)
        self.assertIsNone(recipients[1]["settings"])

    def test_with_handler(self):
        """测试有处理人"""
        db = MagicMock()
        alert = MagicMock()
        alert.project = None
        alert.handler_id = 2
        alert.rule = None

        user = MagicMock()
        user.id = 2
        user.is_active = True
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user]
        db.query.return_value.filter.return_value.all.return_value = []

        recipients = resolve_recipients(db, alert)
        
        self.assertIn(2, recipients)

    def test_with_rule_users(self):
        """测试规则中的通知用户"""
        db = MagicMock()
        alert = MagicMock()
        alert.project = None
        alert.handler_id = None
        alert.rule = MagicMock()
        alert.rule.notify_users = [3, 4]

        user1 = MagicMock()
        user1.id = 3
        user1.is_active = True
        user2 = MagicMock()
        user2.id = 4
        user2.is_active = True
        
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user1, user2]
        db.query.return_value.filter.return_value.all.return_value = []

        recipients = resolve_recipients(db, alert)
        
        self.assertIn(3, recipients)
        self.assertIn(4, recipients)

    def test_with_notification_settings(self):
        """测试有通知设置的用户"""
        db = MagicMock()
        alert = MagicMock()
        alert.project = MagicMock()
        alert.project.pm_id = 1
        alert.handler_id = None
        alert.rule = None

        user = MagicMock()
        user.id = 1
        user.is_active = True
        
        setting = MagicMock()
        setting.user_id = 1
        
        # 第一个query返回用户
        # 第二个query返回通知设置
        query_mock = MagicMock()
        query_mock.filter.return_value.filter.return_value.all.return_value = [user]
        query_mock.filter.return_value.all.return_value = [setting]
        
        db.query.return_value = query_mock

        recipients = resolve_recipients(db, alert)
        
        self.assertEqual(recipients[1]["settings"], setting)

    def test_with_no_users(self):
        """测试无用户（应使用默认用户ID=1）"""
        db = MagicMock()
        alert = MagicMock()
        alert.project = None
        alert.handler_id = None
        alert.rule = None

        user = MagicMock()
        user.id = 1
        user.is_active = True
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user]
        db.query.return_value.filter.return_value.all.return_value = []

        recipients = resolve_recipients(db, alert)
        
        self.assertIn(1, recipients)

    def test_with_non_integer_user_id(self):
        """测试规则中包含非整数用户ID（应忽略）"""
        db = MagicMock()
        alert = MagicMock()
        alert.project = None
        alert.handler_id = None
        alert.rule = MagicMock()
        alert.rule.notify_users = [5, "invalid", 6]  # 包含非整数

        user1 = MagicMock()
        user1.id = 5
        user1.is_active = True
        user2 = MagicMock()
        user2.id = 6
        user2.is_active = True
        
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [user1, user2]
        db.query.return_value.filter.return_value.all.return_value = []

        recipients = resolve_recipients(db, alert)
        
        self.assertIn(5, recipients)
        self.assertIn(6, recipients)
        self.assertEqual(len(recipients), 2)


class TestResolveChannelTarget(unittest.TestCase):
    """测试渠道目标解析"""

    def test_system_channel(self):
        """测试SYSTEM渠道"""
        user = MagicMock()
        user.id = 1
        
        target = resolve_channel_target("SYSTEM", user)
        self.assertEqual(target, "1")

    def test_email_channel(self):
        """测试EMAIL渠道"""
        user = MagicMock()
        user.email = "test@example.com"
        
        target = resolve_channel_target("EMAIL", user)
        self.assertEqual(target, "test@example.com")

    def test_wechat_channel(self):
        """测试WECHAT渠道"""
        user = MagicMock()
        user.username = "wechat_user"
        user.phone = "13800138000"
        
        target = resolve_channel_target("WECHAT", user)
        self.assertEqual(target, "wechat_user")

    def test_wechat_channel_no_username(self):
        """测试WECHAT渠道无用户名（使用手机）"""
        user = MagicMock()
        user.username = None
        user.phone = "13800138000"
        
        target = resolve_channel_target("WECHAT", user)
        self.assertEqual(target, "13800138000")

    def test_we_com_channel(self):
        """测试WE_COM渠道"""
        user = MagicMock()
        user.username = "wecom_user"
        user.phone = "13800138000"
        
        target = resolve_channel_target("WE_COM", user)
        self.assertEqual(target, "wecom_user")

    def test_sms_channel(self):
        """测试SMS渠道"""
        user = MagicMock()
        user.phone = "13800138000"
        
        target = resolve_channel_target("SMS", user)
        self.assertEqual(target, "13800138000")

    def test_lowercase_channel(self):
        """测试小写渠道名（应转大写）"""
        user = MagicMock()
        user.email = "test@example.com"
        
        target = resolve_channel_target("email", user)
        self.assertEqual(target, "test@example.com")

    def test_unknown_channel(self):
        """测试未知渠道（应返回None）"""
        user = MagicMock()
        
        target = resolve_channel_target("UNKNOWN", user)
        self.assertIsNone(target)

    def test_none_user(self):
        """测试None用户"""
        target = resolve_channel_target("EMAIL", None)
        self.assertIsNone(target)


class TestChannelAllowed(unittest.TestCase):
    """测试渠道允许检查"""

    def test_system_enabled(self):
        """测试SYSTEM渠道启用"""
        settings = MagicMock()
        settings.system_enabled = True
        
        self.assertTrue(channel_allowed("SYSTEM", settings))

    def test_system_disabled(self):
        """测试SYSTEM渠道禁用"""
        settings = MagicMock()
        settings.system_enabled = False
        
        self.assertFalse(channel_allowed("SYSTEM", settings))

    def test_email_enabled(self):
        """测试EMAIL渠道启用"""
        settings = MagicMock()
        settings.email_enabled = True
        
        self.assertTrue(channel_allowed("EMAIL", settings))

    def test_email_disabled(self):
        """测试EMAIL渠道禁用"""
        settings = MagicMock()
        settings.email_enabled = False
        
        self.assertFalse(channel_allowed("EMAIL", settings))

    def test_wechat_enabled(self):
        """测试WECHAT渠道启用"""
        settings = MagicMock()
        settings.wechat_enabled = True
        
        self.assertTrue(channel_allowed("WECHAT", settings))

    def test_we_com_enabled(self):
        """测试WE_COM渠道启用"""
        settings = MagicMock()
        settings.wechat_enabled = True
        
        self.assertTrue(channel_allowed("WE_COM", settings))

    def test_sms_enabled(self):
        """测试SMS渠道启用"""
        settings = MagicMock()
        settings.sms_enabled = True
        
        self.assertTrue(channel_allowed("SMS", settings))

    def test_lowercase_channel(self):
        """测试小写渠道名"""
        settings = MagicMock()
        settings.email_enabled = True
        
        self.assertTrue(channel_allowed("email", settings))

    def test_unknown_channel(self):
        """测试未知渠道（应返回True）"""
        settings = MagicMock()
        
        self.assertTrue(channel_allowed("UNKNOWN", settings))

    def test_none_settings(self):
        """测试None设置（应返回True）"""
        self.assertTrue(channel_allowed("EMAIL", None))


class TestParseTimeStr(unittest.TestCase):
    """测试时间字符串解析"""

    def test_valid_time(self):
        """测试有效时间"""
        result = parse_time_str("09:30")
        self.assertEqual(result, time(9, 30))

    def test_midnight(self):
        """测试午夜"""
        result = parse_time_str("00:00")
        self.assertEqual(result, time(0, 0))

    def test_noon(self):
        """测试正午"""
        result = parse_time_str("12:00")
        self.assertEqual(result, time(12, 0))

    def test_end_of_day(self):
        """测试一天结束"""
        result = parse_time_str("23:59")
        self.assertEqual(result, time(23, 59))

    def test_invalid_format(self):
        """测试无效格式（应返回None）"""
        result = parse_time_str("9:30am")
        self.assertIsNone(result)

    def test_invalid_hour(self):
        """测试无效小时（应返回None）"""
        result = parse_time_str("25:00")
        self.assertIsNone(result)

    def test_invalid_minute(self):
        """测试无效分钟（应返回None）"""
        result = parse_time_str("09:60")
        self.assertIsNone(result)

    def test_none_value(self):
        """测试None值"""
        result = parse_time_str(None)
        self.assertIsNone(result)

    def test_empty_string(self):
        """测试空字符串"""
        result = parse_time_str("")
        self.assertIsNone(result)

    def test_no_colon(self):
        """测试没有冒号（应返回None）"""
        result = parse_time_str("0930")
        self.assertIsNone(result)


class TestIsQuietHours(unittest.TestCase):
    """测试免打扰时段判断"""

    def test_within_quiet_hours_same_day(self):
        """测试在免打扰时段内（同一天）"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 22, 30)
        
        self.assertTrue(is_quiet_hours(settings, current_time))

    def test_before_quiet_hours(self):
        """测试在免打扰时段之前"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 21, 30)
        
        self.assertFalse(is_quiet_hours(settings, current_time))

    def test_after_quiet_hours(self):
        """测试在免打扰时段之后"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 23, 30)
        
        self.assertFalse(is_quiet_hours(settings, current_time))

    def test_quiet_hours_across_midnight(self):
        """测试跨午夜的免打扰时段"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "08:00"
        
        # 晚上11点（在时段内）
        current_time = datetime(2024, 1, 1, 23, 0)
        self.assertTrue(is_quiet_hours(settings, current_time))
        
        # 凌晨2点（在时段内）
        current_time = datetime(2024, 1, 1, 2, 0)
        self.assertTrue(is_quiet_hours(settings, current_time))
        
        # 上午9点（不在时段内）
        current_time = datetime(2024, 1, 1, 9, 0)
        self.assertFalse(is_quiet_hours(settings, current_time))

    def test_at_start_boundary(self):
        """测试在开始边界"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 22, 0)
        
        self.assertTrue(is_quiet_hours(settings, current_time))

    def test_at_end_boundary(self):
        """测试在结束边界"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 23, 0)
        
        self.assertTrue(is_quiet_hours(settings, current_time))

    def test_none_settings(self):
        """测试None设置"""
        current_time = datetime(2024, 1, 1, 22, 30)
        
        self.assertFalse(is_quiet_hours(None, current_time))

    def test_invalid_start_time(self):
        """测试无效开始时间"""
        settings = MagicMock()
        settings.quiet_hours_start = "invalid"
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 22, 30)
        
        self.assertFalse(is_quiet_hours(settings, current_time))

    def test_invalid_end_time(self):
        """测试无效结束时间"""
        settings = MagicMock()
        settings.quiet_hours_start = "22:00"
        settings.quiet_hours_end = "invalid"
        
        current_time = datetime(2024, 1, 1, 22, 30)
        
        self.assertFalse(is_quiet_hours(settings, current_time))

    def test_none_start_time(self):
        """测试None开始时间"""
        settings = MagicMock()
        settings.quiet_hours_start = None
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 22, 30)
        
        self.assertFalse(is_quiet_hours(settings, current_time))


class TestNextQuietResume(unittest.TestCase):
    """测试免打扰恢复时间计算"""

    def test_resume_same_day(self):
        """测试同一天恢复"""
        settings = MagicMock()
        settings.quiet_hours_end = "23:00"
        
        current_time = datetime(2024, 1, 1, 22, 0)
        
        resume = next_quiet_resume(settings, current_time)
        
        self.assertEqual(resume, datetime(2024, 1, 1, 23, 0))

    def test_resume_next_day(self):
        """测试次日恢复"""
        settings = MagicMock()
        settings.quiet_hours_end = "08:00"
        
        current_time = datetime(2024, 1, 1, 22, 0)
        
        resume = next_quiet_resume(settings, current_time)
        
        self.assertEqual(resume, datetime(2024, 1, 2, 8, 0))

    def test_resume_at_midnight(self):
        """测试午夜恢复"""
        settings = MagicMock()
        settings.quiet_hours_end = "00:00"
        
        current_time = datetime(2024, 1, 1, 22, 0)
        
        resume = next_quiet_resume(settings, current_time)
        
        self.assertEqual(resume, datetime(2024, 1, 2, 0, 0))

    def test_invalid_end_time(self):
        """测试无效结束时间（应返回30分钟后）"""
        settings = MagicMock()
        settings.quiet_hours_end = "invalid"
        
        current_time = datetime(2024, 1, 1, 22, 0)
        
        resume = next_quiet_resume(settings, current_time)
        
        self.assertEqual(resume, datetime(2024, 1, 1, 22, 30))

    def test_none_end_time(self):
        """测试None结束时间（应返回30分钟后）"""
        settings = MagicMock()
        settings.quiet_hours_end = None
        
        current_time = datetime(2024, 1, 1, 22, 0)
        
        resume = next_quiet_resume(settings, current_time)
        
        self.assertEqual(resume, datetime(2024, 1, 1, 22, 30))


if __name__ == "__main__":
    unittest.main()
