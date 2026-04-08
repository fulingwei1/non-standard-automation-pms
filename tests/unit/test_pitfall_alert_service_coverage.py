# -*- coding: utf-8 -*-
"""pitfall_alert_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.knowledge.pitfall_alert_service import PitfallAlertService

class TestPitfallAlertServiceInit:
    def test_init(self):
        service = PitfallAlertService(Mock())
        assert service is not None
