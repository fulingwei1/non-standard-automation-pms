# -*- coding: utf-8 -*-
"""设备保养提醒定时任务。"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def check_equipment_maintenance_reminder(current_date=None, days_ahead: int = 7):
    """扫描设备下次保养日期并创建保养提醒预警。"""
    from app.models.base import get_session
    from app.services.equipment_maintenance_service import EquipmentMaintenanceService

    session = get_session()
    try:
        stats = EquipmentMaintenanceService(session).check_maintenance_reminders(
            current_date=current_date,
            days_ahead=days_ahead,
        )
        session.commit()
        result = {
            "status": "success",
            "task": "check_equipment_maintenance_reminder",
            **stats,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(
            "[设备保养提醒任务] 检查 %s 台设备，创建 %s 条提醒",
            result["checked_count"],
            result["alerts_created"],
        )
        return result
    except Exception as e:  # noqa: BLE001 - 返回 error 哨兵让调度监控记失败
        logger.exception("[设备保养提醒任务] 执行失败")
        try:
            session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {
            "status": "error",
            "task": "check_equipment_maintenance_reminder",
            "message": str(e)[:500],
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        session.close()
