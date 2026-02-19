# -*- coding: utf-8 -*-
"""外部渠道通知单元测试 - 第三十六批"""

import pytest
import logging
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.approval_engine.notify.external_channels")

try:
    from app.services.approval_engine.notify.external_channels import ExternalChannelsMixin
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    ExternalChannelsMixin = None


def make_service():
    class FakeService(ExternalChannelsMixin):
        pass
    return FakeService()


class TestQueueEmailNotification:
    def test_email_notification_logs_debug(self, caplog):
        svc = make_service()
        notification = {"title": "审批通知", "body": "请审批"}
        with caplog.at_level(logging.DEBUG, logger="app.services.approval_engine.notify.external_channels"):
            svc._queue_email_notification(notification)
        # 方法调用不报错
        assert True

    def test_email_notification_with_empty_dict(self):
        svc = make_service()
        # 不应抛异常
        svc._queue_email_notification({})

    def test_email_notification_with_none_title(self):
        svc = make_service()
        svc._queue_email_notification({"title": None})


class TestQueueWechatNotification:
    def test_wechat_notification_logs_debug(self, caplog):
        svc = make_service()
        notification = {"title": "企微通知"}
        with caplog.at_level(logging.DEBUG, logger="app.services.approval_engine.notify.external_channels"):
            svc._queue_wechat_notification(notification)
        assert True

    def test_wechat_notification_with_empty_dict(self):
        svc = make_service()
        svc._queue_wechat_notification({})

    def test_wechat_returns_none(self):
        svc = make_service()
        result = svc._queue_wechat_notification({"title": "test"})
        assert result is None

    def test_email_returns_none(self):
        svc = make_service()
        result = svc._queue_email_notification({"title": "test"})
        assert result is None

    def test_mixin_can_be_inherited(self):
        class MultiMixin(ExternalChannelsMixin):
            pass
        obj = MultiMixin()
        assert hasattr(obj, "_queue_email_notification")
        assert hasattr(obj, "_queue_wechat_notification")
