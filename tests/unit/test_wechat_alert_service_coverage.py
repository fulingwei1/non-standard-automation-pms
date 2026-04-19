# -*- coding: utf-8 -*-
"""wechat_alert_service单元测试"""
from app.services.alert.wechat_alert_service import WeChatAlertService


class TestWeChatAlertServiceInit:
    def test_init(self):
        assert hasattr(WeChatAlertService, "send_shortage_alert")
        assert hasattr(WeChatAlertService, "batch_send_alerts")
