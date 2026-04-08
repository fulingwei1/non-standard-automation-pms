# -*- coding: utf-8 -*-
"""plan_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.plan_service import ProductionPlanService

class TestProductionPlanServiceInit:
    def test_init(self):
        service = ProductionPlanService(Mock())
        assert service is not None
