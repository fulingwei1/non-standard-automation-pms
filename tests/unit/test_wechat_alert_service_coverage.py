# -*- coding: utf-8 -*-
"""wechat_alert_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.wechat_alert_service import WeChatAlertService

class TestWeChatAlertServiceInit:
    def test_init(self):
        service = WeChatAlertService(Mock())
        assert service is not None
