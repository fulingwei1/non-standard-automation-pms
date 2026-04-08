# -*- coding: utf-8 -*-
"""alert_subscription_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.alert_subscription_service import AlertSubscriptionService

class TestAlertSubscriptionServiceInit:
    def test_init(self):
        service = AlertSubscriptionService(Mock())
        assert service is not None
