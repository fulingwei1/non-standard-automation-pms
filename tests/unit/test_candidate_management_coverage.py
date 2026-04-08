# -*- coding: utf-8 -*-
"""candidate_management单元测试"""
import pytest
from unittest.mock import Mock
from app.services.staff_matching.candidate_management import CandidateManager

class TestCandidateManagerInit:
    def test_init(self):
        service = CandidateManager(Mock())
        assert service is not None
