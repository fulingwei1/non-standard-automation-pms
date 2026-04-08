# -*- coding: utf-8 -*-
"""condition_parser单元测试"""
import pytest
from unittest.mock import Mock
from app.services.approval_engine.condition_parser import ConditionParseError

class TestConditionParseErrorInit:
    def test_init(self):
        service = ConditionParseError(Mock())
        assert service is not None
