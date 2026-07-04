# -*- coding: utf-8 -*-
"""ADMIN-01/02/03: backup API, restore, and SQLite shell scripts."""

import os
import gzip
import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.services.backup_service import BackupService


def _create_sqlite_db(path: Path, table: str = "admin_backup_probe", value: str = "ok") -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute(f"INSERT INTO {table} (name) VALUES (?)", (value,))
        conn.commit()
    finally:
        conn.close()


def _table_values(path: Path, table: str = "admin_backup_probe") -> list[str]:
    conn = sqlite3.connect(path)
    try:
        return [row[0] for row in conn.execute(f"SELECT name FROM {table} ORDER BY id")]
    finally:
        conn.close()


def test_backup_router_exposes_real_operations_not_placeholder():
    from app.api.v1.endpoints.backup import router

    route_paths = {route.path for route in router.routes}

    assert "/stats" in route_paths
    assert "/database" in route_paths
    assert "/restore" in route_paths
    assert "/verify" in route_paths
    assert not (
        route_paths == {"/"}
        and router.routes[0].endpoint().__getitem__("message") == "backup module placeholder"
    )


def test_restore_backup_replaces_sqlite_database_and_keeps_pre_restore_copy(tmp_path):
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"
    backup_dir = tmp_path / "backups"
    _create_sqlite_db(source_db, value="restored")
    _create_sqlite_db(target_db, table="stale_table", value="old")

    with patch.object(BackupService, "BACKUP_DIR", backup_dir):
        backup = BackupService._create_sqlite_database_backup(source_db, "20260704_120000")
        result = BackupService.restore_backup(
            backup["backup_file"],
            database_url=f"sqlite:///{target_db}",
            confirm=True,
        )

    assert result["status"] == "success"
    assert Path(result["pre_restore_backup"]).exists()
    assert _table_values(target_db) == ["restored"]

    conn = sqlite3.connect(target_db)
    try:
        stale_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stale_table'"
        ).fetchone()
    finally:
        conn.close()
    assert stale_table is None


def test_database_backup_scripts_use_sqlite_backup_verify_and_restore(tmp_path):
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"
    backup_dir = tmp_path / "script_backups"
    _create_sqlite_db(source_db, value="from-script")

    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{source_db}",
        "BACKUP_DIR": str(backup_dir),
        "OSS_BUCKET": "",
    }
    backup = subprocess.run(
        ["bash", "scripts/backup_database.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert backup.returncode == 0, backup.stdout + backup.stderr
    backup_files = sorted(backup_dir.glob("pms_*.sql.gz"))
    assert len(backup_files) == 1

    verify = subprocess.run(
        ["bash", "scripts/verify_backup.sh", str(backup_files[0])],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert "SQLite" in verify.stdout

    restore_env = {
        **env,
        "DATABASE_URL": f"sqlite:///{target_db}",
        "CONFIRM_RESTORE": "yes",
    }
    restore = subprocess.run(
        ["bash", "scripts/restore_database.sh", str(backup_files[0])],
        cwd=Path(__file__).resolve().parents[2],
        env=restore_env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert restore.returncode == 0, restore.stdout + restore.stderr
    assert _table_values(target_db) == ["from-script"]


def test_verify_backup_requires_checksum_sidecar(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    backup_file = backup_dir / "pms_no_checksum.sql.gz"
    with gzip.open(backup_file, "wt", encoding="utf-8") as fh:
        fh.write("CREATE TABLE checksum_probe (id INTEGER PRIMARY KEY, name TEXT);")

    verify = subprocess.run(
        ["bash", "scripts/verify_backup.sh", str(backup_file)],
        cwd=Path(__file__).resolve().parents[2],
        env={**os.environ, "BACKUP_DIR": str(backup_dir)},
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert verify.returncode != 0
    assert "Missing checksum file" in (verify.stdout + verify.stderr)
