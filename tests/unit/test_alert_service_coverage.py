# -*- coding: utf-8 -*-
"""alert_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.material_tracking.alert_service import AlertService

class TestAlertServiceInit:
    def test_init(self):
        service = AlertService(Mock())
        assert service is not None
