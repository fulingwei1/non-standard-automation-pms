# -*- coding: utf-8 -*-
"""alert_upgrader单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.rule_engine.alert_upgrader import AlertUpgrader

class TestAlertUpgraderInit:
    def test_init(self):
        service = AlertUpgrader(Mock())
        assert service is not None
