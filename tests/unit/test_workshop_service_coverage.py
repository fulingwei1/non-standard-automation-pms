# -*- coding: utf-8 -*-
"""workshop_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.production.workshop_service import WorkshopService

class TestWorkshopServiceInit:
    def test_init(self):
        service = WorkshopService(Mock())
        assert service is not None
