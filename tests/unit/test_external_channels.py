# -*- coding: utf-8 -*-
"""外部渠道通知单元测试"""
import pytest
from app.services.approval_engine.notify.external_channels import ExternalChannelsMixin


class TestExternalChannelsMixin:
    def setup_method(self):
        self.mixin = ExternalChannelsMixin()

    def test_queue_email_notification(self):
        # Should not raise, just logs
        self.mixin._queue_email_notification({"title": "测试"})

    def test_queue_wechat_notification(self):
        # Should not raise, just logs
        self.mixin._queue_wechat_notification({"title": "测试"})
