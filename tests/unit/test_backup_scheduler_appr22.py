# -*- coding: utf-8 -*-
"""APPR-22: database backups must run through the scheduler and work on SQLite."""

import gzip
import sqlite3
from pathlib import Path
from unittest.mock import patch

from app.services.backup_service import BackupService


def _create_sqlite_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE audit_backup_probe (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO audit_backup_probe (name) VALUES ('ok')")
        conn.commit()
    finally:
        conn.close()


def test_sqlite_database_backup_creates_dump_and_checksum(tmp_path, monkeypatch):
    db_path = tmp_path / "app.db"
    backup_dir = tmp_path / "backups"
    _create_sqlite_db(db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    with patch.object(BackupService, "BACKUP_DIR", backup_dir):
        result = BackupService.create_backup("database")

    assert result["status"] == "success"
    backup_file = Path(result["backup_file"])
    checksum_file = Path(str(backup_file) + ".md5")
    assert backup_file.exists()
    assert backup_file.name.startswith("pms_")
    assert backup_file.name.endswith(".sql.gz")
    assert checksum_file.exists()

    with gzip.open(backup_file, "rt", encoding="utf-8") as fh:
        dump = fh.read()
    assert "CREATE TABLE audit_backup_probe" in dump
    assert "INSERT INTO \"audit_backup_probe\"" in dump


def test_daily_database_backup_task_is_registered_and_calls_backup_service():
    from app.utils.scheduled_tasks import SCHEDULED_TASKS, daily_database_backup_task
    from app.utils.scheduler import _resolve_callable
    from app.utils.scheduler_config import SCHEDULER_TASKS

    task = next(task for task in SCHEDULER_TASKS if task["id"] == "daily_database_backup")

    assert task["enabled"] is True
    assert _resolve_callable(task) is daily_database_backup_task
    assert SCHEDULED_TASKS["daily_database_backup_task"] is daily_database_backup_task

    with patch(
        "app.utils.scheduled_tasks.backup_tasks.BackupService.create_backup",
        return_value={"status": "success", "backup_type": "database", "backup_file": "x"},
    ) as mock_create:
        result = daily_database_backup_task()

    assert result["status"] == "success"
    assert result["backup_type"] == "database"
    mock_create.assert_called_once_with("database")
