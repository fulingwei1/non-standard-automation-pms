# -*- coding: utf-8 -*-
"""第十七批 - 备份管理服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from datetime import datetime, timedelta

pytest.importorskip("app.services.backup_service")


class TestBackupService:

    def test_format_size_bytes(self):
        """_format_size 字节格式化"""
        from app.services.backup_service import BackupService
        assert BackupService._format_size(512) == "512.00 B"

    def test_format_size_kilobytes(self):
        from app.services.backup_service import BackupService
        result = BackupService._format_size(2048)
        assert "KB" in result

    def test_format_size_megabytes(self):
        from app.services.backup_service import BackupService
        result = BackupService._format_size(5 * 1024 * 1024)
        assert "MB" in result

    def test_create_backup_script_not_found(self):
        """脚本不存在时返回 error 状态"""
        from app.services.backup_service import BackupService
        with patch.object(Path, "exists", return_value=False):
            result = BackupService.create_backup("full")
        assert result["status"] == "error"
        assert "备份脚本不存在" in result["message"]

    def test_create_backup_success(self):
        """脚本执行成功返回 success"""
        from app.services.backup_service import BackupService
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Backup OK"
        with patch.object(Path, "exists", return_value=True), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.create_backup("database")
        assert result["status"] == "success"
        assert result["backup_type"] == "database"

    def test_create_backup_failure(self):
        """脚本执行失败返回 failed"""
        from app.services.backup_service import BackupService
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "pg_dump: error"
        with patch.object(Path, "exists", return_value=True), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.create_backup("database")
        assert result["status"] == "failed"

    def test_list_backups_empty_dir(self):
        """备份目录不含匹配文件时返回空列表"""
        from app.services.backup_service import BackupService
        with patch.object(Path, "glob", return_value=[]):
            result = BackupService.list_backups("database")
        assert result == []

    def test_get_latest_backup_none_when_empty(self):
        """无备份文件时 get_latest_backup 返回 None"""
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "list_backups", return_value=[]):
            result = BackupService.get_latest_backup()
        assert result is None

    def test_get_latest_backup_returns_first(self):
        """list_backups 有数据时返回第一个"""
        from app.services.backup_service import BackupService
        fake = [{"filename": "pms_20260101.sql.gz"}, {"filename": "pms_20260102.sql.gz"}]
        with patch.object(BackupService, "list_backups", return_value=fake):
            result = BackupService.get_latest_backup()
        assert result == fake[0]

    def test_delete_old_backups_no_expired(self):
        """无过期备份时 deleted_count 为 0"""
        from app.services.backup_service import BackupService
        now_str = datetime.now().isoformat()
        fake_backups = [{"path": "/tmp/x.sql.gz", "size": 100, "created_at": now_str}]
        with patch.object(BackupService, "list_backups", return_value=fake_backups):
            result = BackupService.delete_old_backups(retention_days=7)
        assert result["deleted_count"] == 0

    def test_create_backup_timeout(self):
        """备份超时返回 failed"""
        import subprocess
        from app.services.backup_service import BackupService
        with patch.object(Path, "exists", return_value=True), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="bash", timeout=3600)):
            result = BackupService.create_backup("full")
        assert result["status"] == "failed"
        assert "超时" in result["message"]
