# -*- coding: utf-8 -*-
"""milestone_alert_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.milestone_alert_service import MilestoneAlertService

class TestMilestoneAlertServiceInit:
    def test_init(self):
        service = MilestoneAlertService(Mock())
        assert service is not None
