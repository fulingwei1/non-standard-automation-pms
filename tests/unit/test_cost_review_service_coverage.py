# -*- coding: utf-8 -*-
"""cost_review_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_review_service import CostReviewService

class TestCostReviewServiceInit:
    def test_init(self):
        service = CostReviewService(Mock())
        assert service is not None
