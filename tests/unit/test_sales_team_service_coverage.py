# -*- coding: utf-8 -*-
"""sales_team_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales_team_service import SalesTeamService

class TestSalesTeamServiceInit:
    def test_init(self):
        service = SalesTeamService(Mock())
        assert service is not None
