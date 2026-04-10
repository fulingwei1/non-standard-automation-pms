# -*- coding: utf-8 -*-
"""quote_approval_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.quote_approval.quote_approval_service import QuoteApprovalService

class TestQuoteApprovalServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = QuoteApprovalService(mock_db)
        assert hasattr(service, 'db')
