# -*- coding: utf-8 -*-
"""rule_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.work_log_ai.rule_engine import RuleEngineMixin

class TestRuleEngineMixinInit:
    def test_init(self):
        service = RuleEngineMixin(Mock())
        assert service is not None
