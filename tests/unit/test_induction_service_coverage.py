# -*- coding: utf-8 -*-
"""induction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.knowledge.induction_service import BestPracticeInductionService

class TestBestPracticeInductionServiceInit:
    def test_init(self):
        service = BestPracticeInductionService(Mock())
        assert service is not None
