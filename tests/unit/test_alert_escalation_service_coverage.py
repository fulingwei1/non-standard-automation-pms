# -*- coding: utf-8 -*-
"""alert_escalation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.alert_escalation_service import AlertEscalationService

class TestAlertEscalationServiceInit:
    def test_init(self):
        service = AlertEscalationService(Mock())
        assert service is not None
