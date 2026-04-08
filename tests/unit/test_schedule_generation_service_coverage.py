# -*- coding: utf-8 -*-
"""schedule_generation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.schedule_generation_service import ScheduleGenerationService

class TestScheduleGenerationServiceInit:
    def test_init(self):
        service = ScheduleGenerationService(Mock())
        assert service is not None
