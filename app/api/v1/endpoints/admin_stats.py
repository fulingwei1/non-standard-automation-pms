# -*- coding: utf-8 -*-
"""Admin statistics routes and runtime collector."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.models.login_attempt import LoginAttempt
from app.models.user import (
    ApiPermission,
    PermissionAudit,
    Role,
    RoleApiPermission,
    User,
    UserRole,
)
from app.services.backup_service import BackupService

router = APIRouter()
_PROCESS_STARTED_AT = datetime.now()


def _safe_count(query) -> int:
    try:
        return int(query.count())
    except Exception:
        return 0


def _database_file_size() -> int:
    try:
        from app.models.base import get_database_url

        database_url = get_database_url()
        if not database_url.startswith("sqlite:///"):
            return 0
        raw_path = database_url.replace("sqlite:///", "", 1)
        if raw_path in {"", ":memory:"} or raw_path.startswith("file:"):
            return 0
        db_path = Path(raw_path)
        return db_path.stat().st_size if db_path.exists() else 0
    except Exception:
        return 0


def _directory_size(path: Path) -> int:
    try:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
    except OSError:
        return 0

    total = 0
    try:
        for root, _, files in os.walk(path):
            for filename in files:
                file_path = Path(root) / filename
                try:
                    total += file_path.stat().st_size
                except OSError:
                    continue
    except OSError:
        return total
    return total


def _storage_used(paths: Iterable[Path] | None = None) -> int:
    if paths is None:
        paths = [
            Path(getattr(settings, "UPLOAD_DIR", "uploads")),
            BackupService.BACKUP_DIR,
        ]
    return sum(_directory_size(Path(path)) for path in paths)


def _process_uptime_percent() -> float:
    now = datetime.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    observed_seconds = max((now - day_start).total_seconds(), 1)
    process_seconds = max((now - _PROCESS_STARTED_AT).total_seconds(), 0)
    return round(min(process_seconds / observed_seconds * 100, 100), 2)


def _latest_backup_info() -> Dict[str, Any]:
    latest = BackupService.get_latest_backup("database")
    if not latest:
        return {"lastBackup": None, "lastBackupFile": None, "lastBackupSize": 0}
    return {
        "lastBackup": latest.get("created_at"),
        "lastBackupFile": latest.get("filename"),
        "lastBackupSize": latest.get("size", 0),
    }


def _api_response_time_ms(db: Session) -> float:
    try:
        from sqlalchemy import text

        started = time.perf_counter()
        db.execute(text("SELECT 1"))
        return round((time.perf_counter() - started) * 1000, 2)
    except Exception:
        return 0.0


def collect_admin_stats(db: Session) -> Dict[str, Any]:
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_users = _safe_count(db.query(User))
    active_users = _safe_count(db.query(User).filter(User.is_active.is_(True)))
    total_roles = _safe_count(db.query(Role))
    active_roles = _safe_count(db.query(Role).filter(Role.is_active.is_(True)))
    total_permissions = _safe_count(db.query(ApiPermission))
    assigned_permissions = _safe_count(db.query(RoleApiPermission.permission_id).distinct())
    users_with_roles = _safe_count(db.query(UserRole.user_id).distinct())
    login_today = _safe_count(
        db.query(LoginAttempt).filter(
            LoginAttempt.success.is_(True),
            LoginAttempt.created_at >= today_start,
        )
    )
    login_week = _safe_count(
        db.query(LoginAttempt).filter(
            LoginAttempt.success.is_(True),
            LoginAttempt.created_at >= week_start,
        )
    )
    login_total_week = _safe_count(db.query(LoginAttempt).filter(LoginAttempt.created_at >= week_start))
    login_failed_week = _safe_count(
        db.query(LoginAttempt).filter(
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= week_start,
        )
    )
    error_rate = round(login_failed_week / login_total_week * 100, 2) if login_total_week else 0

    data = {
        "totalUsers": total_users,
        "activeUsers": active_users,
        "inactiveUsers": max(total_users - active_users, 0),
        "newUsersThisMonth": _safe_count(db.query(User).filter(User.created_at >= month_start)),
        "usersWithRoles": users_with_roles,
        "usersWithoutRoles": max(total_users - users_with_roles, 0),
        "totalRoles": total_roles,
        "systemRoles": _safe_count(db.query(Role).filter(Role.is_system.is_(True))),
        "customRoles": _safe_count(db.query(Role).filter(Role.is_system.is_(False))),
        "activeRoles": active_roles,
        "inactiveRoles": max(total_roles - active_roles, 0),
        "totalPermissions": total_permissions,
        "assignedPermissions": assigned_permissions,
        "unassignedPermissions": max(total_permissions - assigned_permissions, 0),
        "systemUptime": _process_uptime_percent(),
        "databaseSize": _database_file_size(),
        "storageUsed": _storage_used(),
        "apiResponseTime": _api_response_time_ms(db),
        "errorRate": error_rate,
        "loginCountToday": login_today,
        "loginCountThisWeek": login_week,
        "auditLogsToday": _safe_count(db.query(PermissionAudit).filter(PermissionAudit.created_at >= today_start)),
        "auditLogsThisWeek": _safe_count(db.query(PermissionAudit).filter(PermissionAudit.created_at >= week_start)),
    }
    data.update(_latest_backup_info())
    return data


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    return {"code": 200, "message": "success", "data": collect_admin_stats(db)}


__all__ = ["router", "collect_admin_stats"]
