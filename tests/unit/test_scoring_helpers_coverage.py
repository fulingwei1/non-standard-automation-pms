# -*- coding: utf-8 -*-
"""scoring_helpers单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.scoring_helpers import ScoringHelpersMixin

class TestScoringHelpersMixinInit:
    def test_init(self):
        service = ScoringHelpersMixin(Mock())
        assert service is not None
