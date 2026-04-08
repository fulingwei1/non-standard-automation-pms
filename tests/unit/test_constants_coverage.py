# -*- coding: utf-8 -*-
"""constants单元测试"""
import pytest
from unittest.mock import Mock
from app.services.lead_priority_scoring.constants import ScoringConstants

class TestScoringConstantsInit:
    def test_init(self):
        service = ScoringConstants(Mock())
        assert service is not None
