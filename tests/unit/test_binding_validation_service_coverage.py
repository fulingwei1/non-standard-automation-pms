# -*- coding: utf-8 -*-
"""binding_validation_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/binding_validation_service import BindingIssueLevel

class TestBindingIssueLevelInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BindingIssueLevel(mock_db)
        assert hasattr(service, 'db')
