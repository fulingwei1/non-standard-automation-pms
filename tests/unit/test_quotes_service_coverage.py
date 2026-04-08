# -*- coding: utf-8 -*-
"""quotes_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/quotes_service import QuotesService

class TestQuotesServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = QuotesService(mock_db)
        assert hasattr(service, 'db')
