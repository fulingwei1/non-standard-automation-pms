# -*- coding: utf-8 -*-
"""utils单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.utils import NotificationUtilsMixin

class TestNotificationUtilsMixinInit:
    def test_init(self):
        service = NotificationUtilsMixin(Mock())
        assert service is not None
