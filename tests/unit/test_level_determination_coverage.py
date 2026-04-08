# -*- coding: utf-8 -*-
"""level_determination单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.level_determination import LevelDeterminationMixin

class TestLevelDeterminationMixinInit:
    def test_init(self):
        service = LevelDeterminationMixin(Mock())
        assert service is not None
