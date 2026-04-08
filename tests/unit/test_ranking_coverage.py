# -*- coding: utf-8 -*-
"""ranking单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.ranking import RankingMixin

class TestRankingMixinInit:
    def test_init(self):
        service = RankingMixin(Mock())
        assert service is not None
