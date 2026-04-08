# -*- coding: utf-8 -*-
"""matching单元测试"""
import pytest
from unittest.mock import Mock
from app.services.staff_matching.matching import MatchingEngine

class TestMatchingEngineInit:
    def test_init(self):
        service = MatchingEngine(Mock())
        assert service is not None
