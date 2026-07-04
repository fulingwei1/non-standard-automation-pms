# -*- coding: utf-8 -*-
"""通用审批引擎定时任务。"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def process_approval_timeouts(now=None, limit: int = 500):
    """扫描 approval_tasks.due_at 并执行节点超时动作。"""
    from app.models.base import get_session
    from app.services.approval_engine.engine import ApprovalEngineService

    session = get_session()
    try:
        result = ApprovalEngineService(session).process_approval_timeouts(
            now=now,
            limit=limit,
        )
        logger.info(
            "[审批超时任务] 检查 %s 条，处理 %s 条，失败 %s 条",
            result.get("checked_count"),
            result.get("processed_count"),
            result.get("failed_count"),
        )
        return result
    except Exception as e:  # noqa: BLE001 - 调度任务返回 error 哨兵
        logger.exception("[审批超时任务] 执行失败")
        try:
            session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "status": "error",
            "task": "process_approval_timeouts",
            "message": str(e)[:500],
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        session.close()


def process_approval_timeout_warnings(now=None, limit: int = 500):
    """扫描即将超时的审批任务并发送预警提醒。"""
    from app.models.base import get_session
    from app.services.approval_engine.engine import ApprovalEngineService

    session = get_session()
    try:
        result = ApprovalEngineService(session).process_approval_timeout_warnings(
            now=now,
            limit=limit,
        )
        logger.info(
            "[审批超时预警任务] 检查 %s 条，提醒 %s 条",
            result.get("checked_count"),
            result.get("warning_count"),
        )
        return result
    except Exception as e:  # noqa: BLE001
        logger.exception("[审批超时预警任务] 执行失败")
        try:
            session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "status": "error",
            "task": "process_approval_timeout_warnings",
            "message": str(e)[:500],
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        session.close()
