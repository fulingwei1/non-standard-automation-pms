# -*- coding: utf-8 -*-
"""alert_generator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.rule_engine.alert_generator import AlertGenerator

class TestAlertGeneratorInit:
    def test_init(self):
        service = AlertGenerator(Mock())
        assert service is not None
