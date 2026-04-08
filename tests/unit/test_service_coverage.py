# -*- coding: utf-8 -*-
"""service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.shortage_alerts.service import ShortageAlertService

class TestShortageAlertServiceInit:
    def test_init(self):
        service = ShortageAlertService(Mock())
        assert service is not None
