# -*- coding: utf-8 -*-
"""opportunity_scoring单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.opportunity_scoring import OpportunityScoringMixin

class TestOpportunityScoringMixinInit:
    def test_init(self):
        service = OpportunityScoringMixin(Mock())
        assert service is not None
