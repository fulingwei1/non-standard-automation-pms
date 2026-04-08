# -*- coding: utf-8 -*-
"""condition_evaluator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.rule_engine.condition_evaluator import ConditionEvaluator

class TestConditionEvaluatorInit:
    def test_init(self):
        service = ConditionEvaluator(Mock())
        assert service is not None
