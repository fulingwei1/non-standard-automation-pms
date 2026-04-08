# -*- coding: utf-8 -*-
"""schedule_prediction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.schedule_prediction_service import SchedulePredictionService

class TestSchedulePredictionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SchedulePredictionService(mock_db)
        assert hasattr(service, 'db')
