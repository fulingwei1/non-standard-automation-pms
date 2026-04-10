# -*- coding: utf-8 -*-
"""resource_plan_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.resource_plan_service import ResourcePlanService

class TestResourcePlanServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ResourcePlanService(mock_db)
        assert hasattr(service, 'db')
