# -*- coding: utf-8 -*-
"""lead_scoring单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.lead_scoring import LeadScoringMixin

class TestLeadScoringMixinInit:
    def test_init(self):
        service = LeadScoringMixin(Mock())
        assert service is not None
