# -*- coding: utf-8 -*-
"""qualification_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.qualification_service import QualificationService

class TestQualificationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = QualificationService(mock_db)
        assert hasattr(service, 'db')
