# -*- coding: utf-8 -*-
"""
BackupService 单元测试
使用 mock 来模拟文件系统操作和子进程执行
"""

import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest


class TestBackupService:
    """BackupService 测试类"""

    @pytest.fixture
    def temp_backup_dir(self, tmp_path):
        """创建临时备份目录"""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        return backup_dir

    @pytest.fixture
    def mock_script_dir(self, tmp_path):
        """创建临时脚本目录"""
        script_dir = tmp_path / "scripts"
        script_dir.mkdir()
        # 创建备份脚本
        (script_dir / "backup_full.sh").write_text("#!/bin/bash\necho 'backup done'")
        (script_dir / "backup_database.sh").write_text("#!/bin/bash\necho 'db backup done'")
        (script_dir / "backup_files.sh").write_text("#!/bin/bash\necho 'files backup done'")
        (script_dir / "verify_backup.sh").write_text("#!/bin/bash\necho 'verified'")
        return script_dir

    def test_create_backup_full_success(self, temp_backup_dir, mock_script_dir):
        """测试：创建完整备份成功"""
        with patch.object(
            BackupService, "BACKUP_DIR", temp_backup_dir
        ), patch.object(
            BackupService, "SCRIPT_DIR", mock_script_dir
        ), patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Backup completed", stderr="")

            result = BackupService.create_backup(backup_type="full")

            assert result["status"] == "success"
            assert result["backup_type"] == "full"
            assert "timestamp" in result
            mock_run.assert_called_once()

    def test_create_backup_database_success(self, temp_backup_dir, mock_script_dir):
        """测试：创建数据库备份成功"""
        with patch.object(
            BackupService, "BACKUP_DIR", temp_backup_dir
        ), patch.object(
            BackupService, "SCRIPT_DIR", mock_script_dir
        ), patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="DB backup done", stderr="")

            result = BackupService.create_backup(backup_type="database")

            assert result["status"] == "success"
            assert result["backup_type"] == "database"
            mock_run.assert_called_once()

    def test_create_backup_script_not_found(self, temp_backup_dir, tmp_path):
        """测试：备份脚本不存在"""
        with patch.object(
            BackupService, "BACKUP_DIR", temp_backup_dir
        ), patch.object(
            BackupService, "SCRIPT_DIR", tmp_path  # 空目录，没有脚本
        ):
            result = BackupService.create_backup(backup_type="full")

            assert result["status"] == "error"
            assert "不存在" in result["message"]

    def test_create_backup_subprocess_failed(self, temp_backup_dir, mock_script_dir):
        """测试：备份脚本执行失败"""
        with patch.object(
            BackupService, "BACKUP_DIR", temp_backup_dir
        ), patch.object(
            BackupService, "SCRIPT_DIR", mock_script_dir
        ), patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="Backup failed")

            result = BackupService.create_backup(backup_type="full")

            assert result["status"] == "failed"
            assert "Backup failed" in result["error"]

    def test_list_backups_empty(self, temp_backup_dir):
        """测试：列出备份（空目录）"""
        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.list_backups(backup_type="database")

            assert isinstance(result, list)
            assert len(result) == 0

    def test_list_backups_with_files(self, temp_backup_dir):
        """测试：列出备份（包含文件）"""
        # 创建模拟备份文件
        backup_file = temp_backup_dir / "pms_20240101_120000.sql.gz"
        backup_file.write_bytes(b"fake backup data")
        
        # 创建 MD5 文件
        md5_file = temp_backup_dir / "pms_20240101_120000.sql.gz.md5"
        md5_file.write_text("abc123")

        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.list_backups(backup_type="database")

            assert len(result) == 1
            assert result[0]["filename"] == "pms_20240101_120000.sql.gz"
            assert result[0]["has_checksum"] is True
            assert result[0]["md5"] == "abc123"

    def test_list_backups_sorted_by_time(self, temp_backup_dir):
        """测试：列出备份按时间倒序"""
        # 创建多个备份文件
        older = temp_backup_dir / "pms_20240101_100000.sql.gz"
        older.write_bytes(b"old")
        
        newer = temp_backup_dir / "pms_20240102_100000.sql.gz"
        newer.write_bytes(b"new")

        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.list_backups(backup_type="database")

            assert len(result) == 2
            # 最新的应该在前面
            assert result[0]["filename"] == "pms_20240102_100000.sql.gz"

    def test_get_latest_backup_exists(self, temp_backup_dir):
        """测试：获取最新备份（存在）"""
        backup_file = temp_backup_dir / "pms_20240101_120000.sql.gz"
        backup_file.write_bytes(b"backup")

        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.get_latest_backup(backup_type="database")

            assert result is not None
            assert result["filename"] == "pms_20240101_120000.sql.gz"

    def test_get_latest_backup_not_exists(self, temp_backup_dir):
        """测试：获取最新备份（不存在）"""
        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.get_latest_backup(backup_type="database")

            assert result is None

    def test_verify_backup_success(self, temp_backup_dir, mock_script_dir):
        """测试：验证备份成功"""
        backup_file = temp_backup_dir / "test_backup.tar.gz"
        backup_file.write_bytes(b"data")

        with patch.object(
            BackupService, "BACKUP_DIR", temp_backup_dir
        ), patch.object(
            BackupService, "SCRIPT_DIR", mock_script_dir
        ), patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Verification OK", stderr="")

            result = BackupService.verify_backup("test_backup.tar.gz")

            assert result["status"] == "success"
            assert "验证通过" in result["message"]

    def test_verify_backup_not_found(self, temp_backup_dir):
        """测试：验证备份（文件不存在）"""
        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.verify_backup("nonexistent.tar.gz")

            assert result["status"] == "error"
            assert "不存在" in result["message"]

    def test_delete_old_backups(self, temp_backup_dir):
        """测试：删除过期备份"""
        # 创建旧备份文件（10天前）
        old_backup = temp_backup_dir / "pms_old.sql.gz"
        old_backup.write_bytes(b"old data")
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_backup, (old_time, old_time))
        
        # 创建 MD5 文件
        old_md5 = temp_backup_dir / "pms_old.sql.gz.md5"
        old_md5.write_text("md5hash")

        # 创建新备份文件（1天前）
        new_backup = temp_backup_dir / "pms_new.sql.gz"
        new_backup.write_bytes(b"new data")

        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.delete_old_backups(retention_days=7, backup_type="database")

            assert result["status"] == "success"
            # 只计算备份文件数量，MD5 文件不计入 deleted_count
            assert result["deleted_count"] == 1

    def test_delete_old_backups_none_to_delete(self, temp_backup_dir):
        """测试：删除过期备份（没有需要删除的）"""
        # 创建新备份文件
        new_backup = temp_backup_dir / "pms_new.sql.gz"
        new_backup.write_bytes(b"new data")

        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.delete_old_backups(retention_days=7, backup_type="database")

            assert result["status"] == "success"
            assert result["deleted_count"] == 0

    def test_get_backup_stats_empty(self, temp_backup_dir):
        """测试：获取备份统计（空）"""
        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.get_backup_stats()

            assert "database" in result
            assert result["database"]["count"] == 0

    def test_get_backup_stats_with_data(self, temp_backup_dir):
        """测试：获取备份统计（有数据）"""
        # 创建备份文件
        db_backup = temp_backup_dir / "pms_20240101.sql.gz"
        db_backup.write_bytes(b"x" * 1024)  # 1KB

        with patch.object(BackupService, "BACKUP_DIR", temp_backup_dir):
            result = BackupService.get_backup_stats()

            assert result["database"]["count"] == 1
            assert result["database"]["total_size"] == 1024

    def test_format_size(self):
        """测试：文件大小格式化"""
        assert "1.00 KB" in BackupService._format_size(1024)
        assert "1.00 MB" in BackupService._format_size(1024 * 1024)
        assert "1.00 GB" in BackupService._format_size(1024 * 1024 * 1024)


# 导入被测试的类
from app.services.backup_service import BackupService