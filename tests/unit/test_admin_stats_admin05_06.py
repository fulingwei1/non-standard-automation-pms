# -*- coding: utf-8 -*-
"""ADMIN-05/06: admin stats must be real routes and non-constant metrics."""

from datetime import datetime
from pathlib import Path


class _FakeQuery:
    def __init__(self, count_value):
        self.count_value = count_value

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def count(self):
        return self.count_value


class _FakeSession:
    def __init__(self):
        self.counts = {
            "User": 9,
            "Role": 4,
            "ApiPermission": 13,
            "LoginAttempt": 7,
            "PermissionAudit": 5,
            "user_roles": 6,
            "role_permissions": 11,
        }

    def query(self, target, *args):
        key = getattr(target, "__name__", None)
        table = getattr(getattr(target, "table", None), "name", None)
        column_name = getattr(target, "name", None)
        if table == "user_roles":
            key = "user_roles"
        elif table == "role_api_permissions":
            key = "role_permissions"
        elif column_name == "permission_id":
            key = "role_permissions"
        return _FakeQuery(self.counts.get(key, 0))


def test_admin_stats_router_exposes_stats_route_not_placeholder():
    from app.api.v1.endpoints.admin_stats import router

    route_paths = {route.path for route in router.routes}

    assert "/stats" in route_paths
    assert "/" not in route_paths


def test_collect_admin_stats_uses_runtime_counts_and_backup_metadata(monkeypatch, tmp_path):
    from app.api.v1.endpoints import admin_stats

    backup_file = tmp_path / "pms_20260704_010203.sql.gz"
    backup_file.write_bytes(b"real-backup")

    monkeypatch.setattr(
        admin_stats.BackupService,
        "get_latest_backup",
        lambda backup_type="database": {
            "filename": backup_file.name,
            "path": str(backup_file),
            "created_at": datetime(2026, 7, 4, 1, 2, 3).isoformat(),
            "size": backup_file.stat().st_size,
        },
    )
    monkeypatch.setattr(admin_stats, "_database_file_size", lambda: 4096)
    monkeypatch.setattr(admin_stats, "_storage_used", lambda paths=None: 8192)
    monkeypatch.setattr(admin_stats, "_process_uptime_percent", lambda: 88.8)

    data = admin_stats.collect_admin_stats(_FakeSession())

    assert data["totalUsers"] == 9
    assert data["usersWithRoles"] == 6
    assert data["totalRoles"] == 4
    assert data["assignedPermissions"] == 11
    assert data["systemUptime"] == 88.8
    assert data["databaseSize"] == 4096
    assert data["storageUsed"] == 8192
    assert data["lastBackup"] == "2026-07-04T01:02:03"
    assert data["lastBackupFile"] == backup_file.name
    assert data["auditLogsToday"] == 5


def test_admin_compat_stats_delegates_to_same_runtime_collector(monkeypatch):
    from app.api.v1.endpoints import admin_compat

    called = {}

    def fake_collect(db):
        called["db"] = db
        return {"totalUsers": 3, "systemUptime": 77.7, "lastBackup": "x"}

    monkeypatch.setattr(admin_compat, "collect_admin_stats", fake_collect)
    response = admin_compat.get_admin_stats(db="db-session", _current_user=object())

    assert called["db"] == "db-session"
    assert response["data"]["systemUptime"] == 77.7
