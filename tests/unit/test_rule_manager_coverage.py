# -*- coding: utf-8 -*-
"""rule_manager单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.rule_engine.rule_manager import RuleManager

class TestRuleManagerInit:
    def test_init(self):
        service = RuleManager(Mock())
        assert service is not None
