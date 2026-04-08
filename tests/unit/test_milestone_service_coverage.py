# -*- coding: utf-8 -*-
"""milestone_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.milestone_service import MilestoneService

class TestMilestoneServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = MilestoneService(mock_db)
        assert hasattr(service, 'db')
