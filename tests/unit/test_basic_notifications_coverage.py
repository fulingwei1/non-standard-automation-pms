# -*- coding: utf-8 -*-
"""basic_notifications单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.basic_notifications import BasicNotificationsMixin

class TestBasicNotificationsMixinInit:
    def test_init(self):
        service = BasicNotificationsMixin(Mock())
        assert service is not None
