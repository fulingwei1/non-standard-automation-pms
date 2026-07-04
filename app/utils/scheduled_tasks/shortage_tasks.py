# -*- coding: utf-8 -*-
"""缺料管理定时任务（APPR-04 回填：从 stub 转真实现）。

generate_shortage_alerts 接 SmartAlertEngine（PROD-02 修复后的真实扫描引擎）：
按工单/BOM 需求 vs 库存+在途 生成缺料预警，CRITICAL/URGENT 自动生成处理方案。
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def auto_trigger_urgent_purchase_from_shortage_alerts():
    """为紧急级别（CRITICAL/URGENT）缺料预警自动创建紧急采购申请（每日调度）。

    申请以 SUBMITTED 状态进入审批池并按预警去重（PROD-15 已做实），
    人工审批仍是采购动作的最终闸门——自动化的是"提单"，不是"批准"。
    """
    from app.models.base import get_session
    from app.services.urgent_purchase_from_shortage_service import (
        auto_trigger_urgent_purchase_for_alerts,
    )

    session = get_session()
    try:
        stats = auto_trigger_urgent_purchase_for_alerts(session)
        result = {
            "status": "success",
            "task": "auto_trigger_urgent_purchase_from_shortage_alerts",
            **{k: stats.get(k, 0) for k in ("checked_count", "created_count", "skipped_count", "failed_count")},
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(
            "[紧急采购触发任务] 检查 %s 条预警，新建 %s 单申请",
            result["checked_count"], result["created_count"],
        )
        return result
    except Exception as e:  # noqa: BLE001 - 返回 error 哨兵让调度监控记失败
        logger.exception("[紧急采购触发任务] 执行失败")
        try:
            session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "status": "error",
            "task": "auto_trigger_urgent_purchase_from_shortage_alerts",
            "message": str(e)[:500],
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        session.close()


def generate_shortage_alerts():
    """全量扫描并生成缺料预警（每日调度）。

    返回哨兵语义：success（含生成数量）/ error（调度监控计失败并按 SLA 重试）。
    """
    from app.models.base import get_session
    from app.services.shortage.smart_alert_engine import SmartAlertEngine

    session = get_session()
    try:
        alerts = SmartAlertEngine(session).scan_and_alert()
        result = {
            "status": "success",
            "task": "generate_shortage_alerts",
            "alerts_created": len(alerts),
            "timestamp": datetime.now().isoformat(),
        }
        logger.info("[缺料预警任务] 扫描完成，生成 %s 条预警", len(alerts))
        return result
    except Exception as e:  # noqa: BLE001 - 返回 error 哨兵让调度监控记失败
        logger.exception("[缺料预警任务] 扫描失败")
        try:
            session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "status": "error",
            "task": "generate_shortage_alerts",
            "message": str(e)[:500],
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        session.close()
