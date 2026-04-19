# -*- coding: utf-8 -*-
"""backup_service单元测试"""
import pytest
from app.services.backup_service import BackupService


class TestBackupServiceInit:
    def test_init_with_db(self):
        assert BackupService is not None
        assert hasattr(BackupService, 'create_backup')
        assert hasattr(BackupService, 'list_backups')
