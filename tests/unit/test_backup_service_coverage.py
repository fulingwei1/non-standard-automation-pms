# -*- coding: utf-8 -*-
"""backup_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.backup_service import BackupService

class TestBackupServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BackupService(mock_db)
        assert hasattr(service, 'db')
