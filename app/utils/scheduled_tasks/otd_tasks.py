# -*- coding: utf-8 -*-
"""
定时任务 - OTD 项目交付智能体每日扫描

每天 07:00 执行（排在 06:00 项目风险计算之后，拿到当日最新风险/健康度数据）。
扫描执行中项目（生命周期 S2~S8）的 10 维 OTD 风险，
对 HIGH/CRITICAL 产出 AlertRecord 并推送站内+邮件给项目经理。
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.dependencies import get_db_session

logger = logging.getLogger(__name__)


def daily_otd_scan() -> Dict[str, Any]:
    """
    OTD 每日交付风险扫描。

    Returns:
        执行结果统计。注意：失败时返回 {"status": "error", ...}，
        scheduler.py 的 _is_failed_task_result 会据此判定任务失败。
    """
    try:
        with get_db_session() as db:
            from app.services.otd import OTDScanService

            result = OTDScanService(db).batch_scan(
                active_only=True, create_alerts=True, create_snapshot=True
            )

            logger.info(
                "[OTD 每日扫描] 扫描 %s 个项目，有风险 %s 个，"
                "HIGH/CRITICAL %s 个，新建预警 %s 条，新建快照 %s 条",
                result["scanned"],
                result["with_risk"],
                result["high_or_critical"],
                result["alerts_created"],
                result.get("snapshots_created", 0),
            )

            return {
                "status": "success",
                "scanned": result["scanned"],
                "with_risk": result["with_risk"],
                "high_or_critical": result["high_or_critical"],
                "alerts_created": result["alerts_created"],
                "snapshots_created": result.get("snapshots_created", 0),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error("[OTD 每日扫描] 失败: %s", e, exc_info=True)
        return {"status": "error", "message": str(e)}
