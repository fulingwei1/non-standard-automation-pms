# -*- coding: utf-8 -*-
"""data_sync_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.data_sync_service import DataSyncService

class TestDataSyncServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DataSyncService(mock_db)
        assert hasattr(service, 'db')
