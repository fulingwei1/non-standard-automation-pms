# -*- coding: utf-8 -*-
"""
定时任务 - 毛利率每日快照

每天 07:30 执行（排在 OTD 07:00 之后）。
为活跃项目落毛利率快照，用于 Dashboard 趋势分析。
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.dependencies import get_db_session

logger = logging.getLogger(__name__)


def daily_margin_snapshot() -> Dict[str, Any]:
    """毛利率每日快照。失败时返回 status=error，scheduler 会真正标失败。"""
    try:
        with get_db_session() as db:
            from app.services.dashboard.margin_trend_service import MarginTrendService

            result = MarginTrendService(db).batch_create_snapshots()
            logger.info(
                "[毛利率快照] 扫描 %s 个项目，新建快照 %s 条",
                result["total"],
                result["created"],
            )
            return {"status": "success", **result}
    except Exception as e:
        logger.error("[毛利率快照] 失败: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}
