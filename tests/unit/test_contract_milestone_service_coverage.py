# -*- coding: utf-8 -*-
"""contract_milestone_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.contract_milestone_service import MilestoneType

class TestMilestoneTypeInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MilestoneType(mock_db)
        assert hasattr(service, 'db')
