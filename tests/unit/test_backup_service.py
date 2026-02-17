# -*- coding: utf-8 -*-
"""
I2组 - 备份管理服务 单元测试
覆盖: app/services/backup_service.py
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import subprocess

import pytest


# ─── _format_size ─────────────────────────────────────────────────────────────

class TestFormatSize:
    def setup_method(self):
        from app.services.backup_service import BackupService
        self.svc = BackupService

    def test_bytes(self):
        assert "B" in self.svc._format_size(512)

    def test_kilobytes(self):
        result = self.svc._format_size(2048)
        assert "KB" in result

    def test_megabytes(self):
        result = self.svc._format_size(1024 * 1024 * 5)
        assert "MB" in result

    def test_gigabytes(self):
        result = self.svc._format_size(1024 ** 3 * 2)
        assert "GB" in result

    def test_zero(self):
        result = self.svc._format_size(0)
        assert "0.00 B" in result

    def test_format_precision(self):
        result = self.svc._format_size(1536)  # 1.5 KB
        assert "1.50 KB" in result


# ─── list_backups ─────────────────────────────────────────────────────────────

class TestListBackups:
    def test_returns_empty_when_dir_empty(self, tmp_path):
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.list_backups("database")
        assert result == []

    def test_lists_matching_files(self, tmp_path):
        from app.services.backup_service import BackupService

        # 创建测试备份文件
        backup_file = tmp_path / "pms_20240115_120000.sql.gz"
        backup_file.write_bytes(b"fake backup content")

        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.list_backups("database")

        assert len(result) == 1
        assert result[0]["filename"] == "pms_20240115_120000.sql.gz"
        assert "size" in result[0]
        assert "created_at" in result[0]

    def test_reads_md5_file(self, tmp_path):
        from app.services.backup_service import BackupService

        backup_file = tmp_path / "pms_20240115_120000.sql.gz"
        backup_file.write_bytes(b"content")
        md5_file = tmp_path / "pms_20240115_120000.sql.gz.md5"
        md5_file.write_text("abc123def456")

        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.list_backups("database")

        assert result[0]["has_checksum"] is True
        assert result[0]["md5"] == "abc123def456"

    def test_sorted_by_time_desc(self, tmp_path):
        from app.services.backup_service import BackupService
        import time

        f1 = tmp_path / "pms_20240110_120000.sql.gz"
        f1.write_bytes(b"old")
        time.sleep(0.01)
        f2 = tmp_path / "pms_20240115_120000.sql.gz"
        f2.write_bytes(b"new")

        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.list_backups("database")

        # 最新的在前
        assert result[0]["filename"] > result[1]["filename"] or \
               result[0]["created_at"] >= result[1]["created_at"]

    def test_unknown_type_uses_default_pattern(self, tmp_path):
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.list_backups("unknown_type")
        assert result == []

    def test_handles_exception_gracefully(self):
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "BACKUP_DIR", Path("/nonexistent/path/abc")):
            result = BackupService.list_backups("database")
        assert result == []


# ─── get_latest_backup ───────────────────────────────────────────────────────

class TestGetLatestBackup:
    def test_returns_none_when_empty(self, tmp_path):
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.get_latest_backup()
        assert result is None

    def test_returns_first_backup(self, tmp_path):
        from app.services.backup_service import BackupService

        f = tmp_path / "pms_20240115_120000.sql.gz"
        f.write_bytes(b"content")

        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.get_latest_backup()

        assert result is not None
        assert result["filename"] == "pms_20240115_120000.sql.gz"


# ─── create_backup ────────────────────────────────────────────────────────────

class TestCreateBackup:
    def test_script_not_exist(self, tmp_path):
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "SCRIPT_DIR", tmp_path):
            result = BackupService.create_backup("full")

        assert result["status"] == "error"
        assert "不存在" in result["message"]

    def test_success(self, tmp_path):
        from app.services.backup_service import BackupService

        script = tmp_path / "backup_full.sh"
        script.write_text("#!/bin/bash\necho 'backup done'")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "backup done\n"

        with patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.create_backup("full")

        assert result["status"] == "success"
        assert result["backup_type"] == "full"

    def test_failure(self, tmp_path):
        from app.services.backup_service import BackupService

        script = tmp_path / "backup_database.sh"
        script.write_text("#!/bin/bash\nexit 1")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error occurred"

        with patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.create_backup("database")

        assert result["status"] == "failed"

    def test_timeout(self, tmp_path):
        from app.services.backup_service import BackupService

        script = tmp_path / "backup_full.sh"
        script.write_text("#!/bin/bash\nsleep 999")

        with patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("bash", 3600)):
            result = BackupService.create_backup("full")

        assert result["status"] == "failed"
        assert "超时" in result["message"]

    def test_exception(self, tmp_path):
        from app.services.backup_service import BackupService

        script = tmp_path / "backup_files.sh"
        script.write_text("#!/bin/bash\necho ok")

        with patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", side_effect=Exception("unexpected")):
            result = BackupService.create_backup("files")

        assert result["status"] == "error"

    def test_unknown_type_defaults_to_full(self, tmp_path):
        from app.services.backup_service import BackupService

        script = tmp_path / "backup_full.sh"
        script.write_text("#!/bin/bash\necho ok")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"

        with patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.create_backup("unknown")

        assert result["status"] == "success"


# ─── verify_backup ────────────────────────────────────────────────────────────

class TestVerifyBackup:
    def test_file_not_exist(self, tmp_path):
        from app.services.backup_service import BackupService
        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.verify_backup("nonexistent.sql.gz")
        assert result["status"] == "error"

    def test_success(self, tmp_path):
        from app.services.backup_service import BackupService

        backup = tmp_path / "pms_20240115.sql.gz"
        backup.write_bytes(b"content")
        script = tmp_path / "verify_backup.sh"
        script.write_text("#!/bin/bash\necho 'OK'")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "验证通过"

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.verify_backup(str(backup))

        assert result["status"] == "success"

    def test_failure(self, tmp_path):
        from app.services.backup_service import BackupService

        backup = tmp_path / "pms_20240115.sql.gz"
        backup.write_bytes(b"corrupt")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "checksum mismatch"

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch.object(BackupService, "SCRIPT_DIR", tmp_path), \
             patch("subprocess.run", return_value=mock_result):
            result = BackupService.verify_backup(str(backup))

        assert result["status"] == "failed"

    def test_exception(self, tmp_path):
        from app.services.backup_service import BackupService

        backup = tmp_path / "pms_20240115.sql.gz"
        backup.write_bytes(b"content")

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch("subprocess.run", side_effect=Exception("error")):
            result = BackupService.verify_backup(str(backup))

        assert result["status"] == "error"


# ─── delete_old_backups ───────────────────────────────────────────────────────

class TestDeleteOldBackups:
    def test_no_old_backups(self, tmp_path):
        from app.services.backup_service import BackupService

        # 创建新文件（今天）
        f = tmp_path / "pms_20240115_120000.sql.gz"
        f.write_bytes(b"content")

        with patch.object(BackupService, "BACKUP_DIR", tmp_path):
            result = BackupService.delete_old_backups(retention_days=7)

        assert result["status"] == "success"
        assert result["deleted_count"] == 0

    def test_deletes_old_files(self, tmp_path):
        from app.services.backup_service import BackupService

        # 创建"旧"备份文件（手动设置列表）
        old_backup_path = tmp_path / "pms_old.sql.gz"
        old_backup_path.write_bytes(b"old content")

        old_time = (datetime.now() - timedelta(days=10)).isoformat()

        old_backup_info = {
            "filename": "pms_old.sql.gz",
            "path": str(old_backup_path),
            "size": 11,
            "size_human": "11.00 B",
            "created_at": old_time,
            "has_checksum": False,
            "md5": None,
            "type": "database"
        }

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch.object(BackupService, "list_backups", return_value=[old_backup_info]):
            result = BackupService.delete_old_backups(retention_days=7, backup_type="database")

        assert result["status"] == "success"
        assert result["deleted_count"] == 1
        assert not old_backup_path.exists()

    def test_exception_returns_error(self):
        from app.services.backup_service import BackupService

        with patch.object(BackupService, "list_backups", side_effect=Exception("disk error")):
            result = BackupService.delete_old_backups()

        assert result["status"] == "error"


# ─── get_backup_stats ─────────────────────────────────────────────────────────

class TestGetBackupStats:
    def test_returns_stats_structure(self, tmp_path):
        from app.services.backup_service import BackupService

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch.object(BackupService, "list_backups", return_value=[]):
            result = BackupService.get_backup_stats()

        assert "database" in result
        assert "uploads" in result
        assert "configs" in result

    def test_counts_backups(self, tmp_path):
        from app.services.backup_service import BackupService

        fake_backup = {
            "filename": "pms_test.sql.gz",
            "size": 1024,
        }

        def mock_list(backup_type):
            if backup_type == "database":
                return [fake_backup, fake_backup]
            return []

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch.object(BackupService, "list_backups", side_effect=mock_list):
            result = BackupService.get_backup_stats()

        assert result["database"]["count"] == 2

    def test_exception_returns_empty(self):
        from app.services.backup_service import BackupService

        with patch.object(BackupService, "list_backups", side_effect=Exception("error")):
            result = BackupService.get_backup_stats()

        assert result == {}

    def test_disk_stats_when_dir_exists(self, tmp_path):
        from app.services.backup_service import BackupService

        with patch.object(BackupService, "BACKUP_DIR", tmp_path), \
             patch.object(BackupService, "list_backups", return_value=[]):
            result = BackupService.get_backup_stats()

        # tmp_path 存在，应有 disk 统计
        assert "disk" in result
        assert "total" in result["disk"]
