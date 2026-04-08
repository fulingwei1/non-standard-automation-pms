# -*- coding: utf-8 -*-
"""manager_evaluation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.manager_evaluation_service import ManagerEvaluationService

class TestManagerEvaluationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ManagerEvaluationService(mock_db)
        assert hasattr(service, 'db')
