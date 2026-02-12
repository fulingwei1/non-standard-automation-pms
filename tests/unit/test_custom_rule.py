# -*- coding: utf-8 -*-
"""Tests for data_scope/custom_rule.py"""

from unittest.mock import MagicMock

import pytest


class TestCustomRuleService:
    def test_validate_scope_config_not_dict(self):
        from app.services.data_scope.custom_rule import CustomRuleService
        errors = CustomRuleService.validate_scope_config("invalid")
        assert len(errors) > 0
        assert "字典" in errors[0]

    def test_validate_scope_config_invalid_conditions(self):
        from app.services.data_scope.custom_rule import CustomRuleService
        errors = CustomRuleService.validate_scope_config({"conditions": "bad"})
        assert len(errors) > 0

    def test_validate_scope_config_empty_valid(self):
        from app.services.data_scope.custom_rule import CustomRuleService
        errors = CustomRuleService.validate_scope_config({"conditions": []})
        assert len(errors) == 0

    def test_validate_scope_config_valid_condition(self):
        from app.services.data_scope.custom_rule import CustomRuleService
        config = {
            "conditions": [
                {"type": "user_ids", "values": [1, 2, 3]}
            ]
        }
        errors = CustomRuleService.validate_scope_config(config)
        assert len(errors) == 0

    def test_validate_scope_config_invalid_type(self):
        from app.services.data_scope.custom_rule import CustomRuleService
        config = {
            "conditions": [
                {"type": "invalid_type", "values": [1]}
            ]
        }
        errors = CustomRuleService.validate_scope_config(config)
        assert len(errors) > 0

    def test_validate_scope_config_missing_type(self):
        from app.services.data_scope.custom_rule import CustomRuleService
        config = {"conditions": [{"values": [1]}]}
        errors = CustomRuleService.validate_scope_config(config)
        assert len(errors) > 0
