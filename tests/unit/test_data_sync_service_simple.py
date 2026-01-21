# -*- coding: utf-8 -*-
"""
Tests for data_sync_service service (Simplified)
Covers: app/services/data_sync_service.py
Coverage Target: 0% → 60%+
Batch: P3 - 扩展服务模块测试
"""

import pytest


class TestDataSyncService:
    """Test suite for DataSyncService class."""

    def test_import_data_sync_service(self):
        """Test importing data sync service module."""
        try:
            from app.services.data_sync_service import DataSyncService
            assert DataSyncService is not None
        except ImportError as e:
            pytest.fail(f"Cannot import DataSyncService: {e}")

    def test_module_has_class(self):
        """Test that module has DataSyncService class."""
        from app.services.data_sync_service import DataSyncService
        
        assert DataSyncService is not None
        assert hasattr(DataSyncService, '__init__')

    def test_module_has_methods(self):
        """Test that module has expected methods."""
        from app.services.data_sync_service import DataSyncService
        
        # Check that methods exist
        assert hasattr(DataSyncService, 'sync_contract_to_project')
        assert hasattr(DataSyncService, 'sync_payment_plan_to_project')

    def test_init_requires_db(self):
        """Test that __init__ requires db parameter."""
        from app.services.data_sync_service import DataSyncService
        from unittest.mock import MagicMock
        
        # Create mock db
        mock_db = MagicMock()
        service = DataSyncService(mock_db)
        
        assert service.db == mock_db
