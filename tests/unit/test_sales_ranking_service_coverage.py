# -*- coding: utf-8 -*-
"""sales_ranking_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales_ranking_service import SalesRankingService

class TestSalesRankingServiceInit:
    def test_init(self):
        service = SalesRankingService(Mock())
        assert service is not None
