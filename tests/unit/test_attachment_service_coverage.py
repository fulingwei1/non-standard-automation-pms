# -*- coding: utf-8 -*-
"""attachment_service单元测试"""
import pytest
from unittest.mock import Mock
from services/sales/contract/attachment_service import ContractAttachmentService

class TestContractAttachmentServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ContractAttachmentService(mock_db)
        assert hasattr(service, 'db')
