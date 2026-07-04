# -*- coding: utf-8 -*-
"""Scheduled backup tasks."""

import logging
from typing import Any, Dict

from app.services.backup_service import BackupService

logger = logging.getLogger(__name__)


def daily_database_backup_task() -> Dict[str, Any]:
    """Create the daily database backup through the scheduler."""
    result = BackupService.create_backup("database")
    if result.get("status") != "success":
        logger.error("每日数据库备份失败: %s", result)
    return result
