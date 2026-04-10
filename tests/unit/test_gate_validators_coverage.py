# -*- coding: utf-8 -*-
"""gate_validators单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.gate_validators import ValidationResult

class TestValidationResultInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ValidationResult(mock_db)
        assert hasattr(service, 'db')
