"""
备份管理服务
提供备份、恢复、列表、验证等功能的Python API
"""

import gzip
import hashlib
import logging
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BackupService:
    """备份管理服务"""

    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/var/backups/pms"))
    SCRIPT_DIR = Path(__file__).parent.parent.parent / "scripts"

    @classmethod
    def create_backup(cls, backup_type: str = "full") -> Dict:
        """
        创建备份

        Args:
            backup_type: 备份类型
                - full: 完整备份（数据库+文件）
                - database: 仅数据库
                - files: 仅文件

        Returns:
            备份结果字典
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if backup_type == "database":
                from app.models.base import get_database_url

                database_url = get_database_url()
                if database_url.startswith("sqlite:///"):
                    sqlite_path = cls._sqlite_path_from_url(database_url)
                    if sqlite_path is not None:
                        return cls._create_sqlite_database_backup(sqlite_path, timestamp)

            # 根据类型选择脚本
            script_map = {
                "full": "backup_full.sh",
                "database": "backup_database.sh",
                "files": "backup_files.sh",
            }

            script_name = script_map.get(backup_type, "backup_full.sh")
            script_path = cls.SCRIPT_DIR / script_name

            if not script_path.exists():
                return {"status": "error", "message": f"备份脚本不存在: {script_path}"}

            # 执行备份脚本
            logger.info(f"执行备份: {backup_type}")
            result = subprocess.run(
                ["bash", str(script_path)],
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
            )

            if result.returncode == 0:
                logger.info(f"备份成功: {backup_type}")
                return {
                    "status": "success",
                    "timestamp": timestamp,
                    "backup_type": backup_type,
                    "message": "备份成功",
                    "output": result.stdout,
                }
            else:
                logger.error(f"备份失败: {result.stderr}")
                return {
                    "status": "failed",
                    "backup_type": backup_type,
                    "error": result.stderr,
                    "message": "备份失败",
                }

        except subprocess.TimeoutExpired:
            logger.error("备份超时")
            return {"status": "failed", "message": "备份超时（超过1小时）"}
        except Exception as e:
            logger.error(f"备份异常: {str(e)}")
            return {"status": "error", "message": f"备份异常: {str(e)}"}

    @classmethod
    def _create_sqlite_database_backup(cls, db_path: Path, timestamp: str) -> Dict:
        """Create a compressed SQL dump for the active SQLite database."""
        if not db_path.exists():
            return {
                "status": "error",
                "backup_type": "database",
                "message": f"SQLite 数据库不存在: {db_path}",
            }

        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_file = cls.BACKUP_DIR / f"pms_{timestamp}.sql.gz"

        try:
            source = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            try:
                with gzip.open(backup_file, "wt", encoding="utf-8") as fh:
                    for line in source.iterdump():
                        fh.write(f"{line}\n")
            finally:
                source.close()

            digest = hashlib.md5(backup_file.read_bytes()).hexdigest()
            Path(str(backup_file) + ".md5").write_text(digest, encoding="utf-8")
            size = backup_file.stat().st_size

            retention_days = int(os.getenv("RETENTION_DAYS", "7"))
            cls.delete_old_backups(retention_days=retention_days, backup_type="database")

            return {
                "status": "success",
                "timestamp": timestamp,
                "backup_type": "database",
                "message": "SQLite 数据库备份成功",
                "backup_file": str(backup_file),
                "size": size,
                "size_human": cls._format_size(size),
                "md5": digest,
            }
        except Exception as exc:
            logger.error(f"SQLite 数据库备份失败: {exc}")
            return {"status": "failed", "backup_type": "database", "message": str(exc)}

    @staticmethod
    def _sqlite_path_from_url(database_url: str) -> Optional[Path]:
        raw_path = database_url.replace("sqlite:///", "", 1)
        if raw_path in {":memory:", ""} or raw_path.startswith("file:"):
            return None
        return Path(raw_path)

    @classmethod
    def _resolve_backup_file(cls, backup_file: str) -> Path:
        """Resolve a backup filename or path under BACKUP_DIR."""
        file_path = Path(backup_file)
        if not file_path.is_absolute():
            file_path = cls.BACKUP_DIR / file_path

        resolved = file_path.resolve()
        backup_root = cls.BACKUP_DIR.resolve()
        if resolved != backup_root and backup_root not in resolved.parents:
            raise ValueError(f"备份文件必须位于备份目录内: {backup_root}")
        return resolved

    @classmethod
    def _verify_sqlite_backup_file(cls, file_path: Path) -> Dict:
        """Validate checksum, gzip format, SQL loadability, and SQLite integrity."""
        if not file_path.exists():
            return {"status": "error", "message": f"备份文件不存在: {file_path}"}
        if file_path.stat().st_size <= 0:
            return {"status": "invalid", "message": "备份文件无效或已损坏"}

        md5_file = Path(str(file_path) + ".md5")
        if md5_file.exists():
            expected = md5_file.read_text(encoding="utf-8").strip()
            actual = hashlib.md5(file_path.read_bytes()).hexdigest()
            if expected and expected != actual:
                return {"status": "failed", "message": "备份文件MD5校验失败"}

        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as fh:
                sql_dump = fh.read()
        except Exception as exc:
            return {"status": "failed", "message": f"GZIP或SQL读取失败: {exc}"}

        temp_conn = sqlite3.connect(":memory:")
        try:
            temp_conn.executescript(sql_dump)
            integrity = temp_conn.execute("PRAGMA integrity_check").fetchone()[0]
            table_count = temp_conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
        except sqlite3.Error as exc:
            return {"status": "failed", "message": f"SQLite恢复校验失败: {exc}"}
        finally:
            temp_conn.close()

        if integrity != "ok":
            return {"status": "failed", "message": f"SQLite完整性校验失败: {integrity}"}

        return {
            "status": "success",
            "message": "SQLite 备份验证通过",
            "backup_file": str(file_path),
            "table_count": table_count,
        }

    @classmethod
    def list_backups(cls, backup_type: str = "database") -> List[Dict]:
        """
        列出所有备份文件

        Args:
            backup_type: 备份类型 (database/uploads/configs/logs/full)

        Returns:
            备份文件列表
        """
        backups = []

        # 根据类型设置文件模式
        pattern_map = {
            "database": "pms_*.sql.gz",
            "uploads": "uploads_*.tar.gz",
            "configs": "configs_*.tar.gz",
            "logs": "logs_*.tar.gz",
            "full": "pms_full_*.tar.gz",
        }

        pattern = pattern_map.get(backup_type, "pms_*.sql.gz")

        try:
            for file in cls.BACKUP_DIR.glob(pattern):
                if not file.is_file():
                    continue

                stat = file.stat()
                md5_file = Path(str(file) + ".md5")

                # 读取MD5
                md5_hash = None
                if md5_file.exists():
                    try:
                        md5_hash = md5_file.read_text().strip()
                    except Exception:
                        pass

                backups.append(
                    {
                        "filename": file.name,
                        "path": str(file),
                        "size": stat.st_size,
                        "size_human": cls._format_size(stat.st_size),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "has_checksum": md5_file.exists(),
                        "md5": md5_hash,
                        "type": backup_type,
                    }
                )

            # 按时间倒序排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"列出备份失败: {str(e)}")

        return backups

    @classmethod
    def get_latest_backup(cls, backup_type: str = "database") -> Optional[Dict]:
        """获取最新的备份"""
        backups = cls.list_backups(backup_type)
        return backups[0] if backups else None

    @classmethod
    def verify_backup(cls, backup_file: str) -> Dict:
        """
        验证备份文件完整性

        Args:
            backup_file: 备份文件路径或文件名

        Returns:
            验证结果
        """
        try:
            file_path = cls._resolve_backup_file(backup_file)

            if not file_path.exists():
                return {"status": "error", "message": f"备份文件不存在: {file_path}"}

            try:
                if file_path.stat().st_size <= 0:
                    return {"status": "invalid", "message": "备份文件无效或已损坏"}
            except OSError as exc:
                logger.warning(f"读取备份文件信息失败，改为继续执行脚本校验: {exc}")

            # 执行验证脚本
            script_path = cls.SCRIPT_DIR / "verify_backup.sh"

            result = subprocess.run(
                ["bash", str(script_path), str(file_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
            )

            if result.returncode == 0:
                return {"status": "success", "message": "备份验证通过", "output": result.stdout}
            else:
                return {"status": "failed", "message": "备份验证失败", "error": result.stderr}

        except Exception as e:
            logger.error(f"验证失败: {str(e)}")
            return {"status": "error", "message": f"验证异常: {str(e)}"}

    @classmethod
    def restore_backup(
        cls,
        backup_file: str,
        database_url: Optional[str] = None,
        confirm: bool = False,
    ) -> Dict:
        """
        Restore a SQLite database from a compressed SQL dump.

        The restore path is intentionally explicit and requires confirm=True
        because it replaces the target database file.
        """
        if not confirm:
            return {"status": "error", "message": "恢复数据库需要显式确认 confirm=True"}

        try:
            from app.models.base import get_database_url

            active_database_url = database_url or get_database_url()
            sqlite_path = cls._sqlite_path_from_url(active_database_url)
            if sqlite_path is None:
                return {"status": "error", "message": "当前恢复功能仅支持 SQLite 数据库"}

            file_path = cls._resolve_backup_file(backup_file)
            verification = cls._verify_sqlite_backup_file(file_path)
            if verification.get("status") != "success":
                return verification

            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = None

            if sqlite_path.exists() and sqlite_path.stat().st_size > 0:
                current_backup = cls._create_sqlite_database_backup(
                    sqlite_path,
                    f"before_restore_{timestamp}",
                )
                if current_backup.get("status") != "success":
                    return {
                        "status": "failed",
                        "message": "恢复前备份当前数据库失败",
                        "pre_restore_error": current_backup,
                    }
                pre_restore_backup = current_backup.get("backup_file")

            restore_tmp = sqlite_path.with_name(f".{sqlite_path.name}.restore-{timestamp}.tmp")
            if restore_tmp.exists():
                restore_tmp.unlink()

            try:
                with gzip.open(file_path, "rt", encoding="utf-8") as fh:
                    sql_dump = fh.read()

                target = sqlite3.connect(restore_tmp)
                try:
                    target.executescript(sql_dump)
                    integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
                finally:
                    target.close()

                if integrity != "ok":
                    return {
                        "status": "failed",
                        "message": f"恢复后SQLite完整性校验失败: {integrity}",
                    }

                for sidecar_name in (f"{sqlite_path}-wal", f"{sqlite_path}-shm"):
                    sidecar = Path(sidecar_name)
                    if sidecar.exists():
                        sidecar.unlink()

                if sqlite_path.exists():
                    shutil.copystat(sqlite_path, restore_tmp, follow_symlinks=True)
                os.replace(restore_tmp, sqlite_path)
            finally:
                if restore_tmp.exists():
                    restore_tmp.unlink()

            try:
                from app.models.base import reset_engine

                reset_engine()
            except Exception:
                logger.debug("恢复后重置数据库引擎失败，已忽略", exc_info=True)

            return {
                "status": "success",
                "message": "SQLite 数据库恢复成功",
                "backup_file": str(file_path),
                "database_file": str(sqlite_path),
                "pre_restore_backup": pre_restore_backup,
                "table_count": verification.get("table_count"),
            }
        except Exception as e:
            logger.error(f"恢复失败: {str(e)}")
            return {"status": "error", "message": f"恢复异常: {str(e)}"}

    @classmethod
    def delete_old_backups(cls, retention_days: int = 7, backup_type: str = "database") -> Dict:
        """
        删除过期备份

        Args:
            retention_days: 保留天数
            backup_type: 备份类型

        Returns:
            删除结果
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            deleted_size = 0

            backups = cls.list_backups(backup_type)

            for backup in backups:
                created_at = datetime.fromisoformat(backup["created_at"])

                if created_at < cutoff_date:
                    file_path = Path(backup["path"])

                    # 删除备份文件
                    if file_path.exists():
                        deleted_size += backup["size"]
                        file_path.unlink()
                        deleted_count += 1

                    # 删除MD5文件
                    md5_file = Path(str(file_path) + ".md5")
                    if md5_file.exists():
                        md5_file.unlink()

            logger.info(
                f"清理完成: 删除{deleted_count}个文件, 释放{cls._format_size(deleted_size)}"
            )

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "freed_space": deleted_size,
                "freed_space_human": cls._format_size(deleted_size),
            }

        except Exception as e:
            logger.error(f"清理失败: {str(e)}")
            return {"status": "error", "message": f"清理异常: {str(e)}"}

    @classmethod
    def get_backup_stats(cls) -> Dict:
        """获取备份统计信息"""
        try:
            stats = {
                "database": {"count": 0, "total_size": 0, "latest": None},
                "uploads": {"count": 0, "total_size": 0, "latest": None},
                "configs": {"count": 0, "total_size": 0, "latest": None},
                "full": {"count": 0, "total_size": 0, "latest": None},
            }

            for backup_type in stats.keys():
                backups = cls.list_backups(backup_type)

                stats[backup_type]["count"] = len(backups)
                stats[backup_type]["total_size"] = sum(b["size"] for b in backups)
                stats[backup_type]["total_size_human"] = cls._format_size(
                    stats[backup_type]["total_size"]
                )

                if backups:
                    stats[backup_type]["latest"] = backups[0]

            # 磁盘空间
            if cls.BACKUP_DIR.exists():
                disk_usage = os.statvfs(cls.BACKUP_DIR)
                stats["disk"] = {
                    "total": disk_usage.f_frsize * disk_usage.f_blocks,
                    "used": disk_usage.f_frsize * (disk_usage.f_blocks - disk_usage.f_bfree),
                    "free": disk_usage.f_frsize * disk_usage.f_bavail,
                    "percent": round((1 - disk_usage.f_bavail / disk_usage.f_blocks) * 100, 2),
                }
                stats["disk"]["total_human"] = cls._format_size(stats["disk"]["total"])
                stats["disk"]["used_human"] = cls._format_size(stats["disk"]["used"])
                stats["disk"]["free_human"] = cls._format_size(stats["disk"]["free"])

            return stats

        except Exception as e:
            logger.error(f"获取统计失败: {str(e)}")
            return {}

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
