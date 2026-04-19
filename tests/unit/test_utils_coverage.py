# -*- coding: utf-8 -*-
"""utils单元测试"""
from app.services.approval_engine.notify.utils import NotificationUtilsMixin


class TestNotificationUtilsMixinInit:
    def test_init(self):
        assert hasattr(NotificationUtilsMixin, "_generate_dedup_key")
