# -*- coding: utf-8 -*-
"""cost_review_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_review_service import CostReviewService

class TestCostReviewServiceInit:
    def test_init(self):
        assert CostReviewService is not None
        assert hasattr(CostReviewService, 'generate_cost_review_report')
