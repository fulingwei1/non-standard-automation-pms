# -*- coding: utf-8 -*-
"""level_determiner单元测试"""
import pytest
from unittest.mock import Mock
from app.services.alert.rule_engine.level_determiner import LevelDeterminer

class TestLevelDeterminerInit:
    def test_init(self):
        service = LevelDeterminer(Mock())
        assert service is not None
