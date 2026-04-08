# -*- coding: utf-8 -*-
"""alert_creator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.rule_engine.alert_creator import AlertCreator

class TestAlertCreatorInit:
    def test_init(self):
        service = AlertCreator(Mock())
        assert service is not None
