# -*- coding: utf-8 -*-
"""custom_rule单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_scope.custom_rule import CustomRuleService

class TestCustomRuleServiceInit:
    def test_init(self):
        assert CustomRuleService is not None
        assert hasattr(CustomRuleService, 'get_custom_rule')
        assert hasattr(CustomRuleService, 'apply_custom_filter')
