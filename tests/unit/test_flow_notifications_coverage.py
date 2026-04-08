# -*- coding: utf-8 -*-
"""flow_notifications单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.notify.flow_notifications import FlowNotificationsMixin

class TestFlowNotificationsMixinInit:
    def test_init(self):
        service = FlowNotificationsMixin(Mock())
        assert service is not None
