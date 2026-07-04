# -*- coding: utf-8 -*-
"""设备保养提醒服务。"""
import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.production import Equipment, Workshop
from app.utils.scheduled_tasks.base import send_notification_for_alert

logger = logging.getLogger(__name__)

MAINTENANCE_RULE_CODE = "EQUIPMENT_MAINTENANCE_DUE"
MAINTENANCE_TARGET_TYPE = "EQUIPMENT_MAINTENANCE"
OPEN_ALERT_STATUSES = ("PENDING", "OPEN", "PROCESSING", "IN_PROGRESS")


class EquipmentMaintenanceService:
    """设备保养提醒业务服务。"""

    def __init__(self, db: Session):
        self.db = db

    def check_maintenance_reminders(
        self,
        *,
        current_date: Optional[date] = None,
        days_ahead: int = 7,
        dispatch_notifications: bool = True,
    ) -> dict[str, Any]:
        """扫描即将到期/已逾期设备并创建去重预警。"""
        if current_date is None:
            current_date = date.today()

        window_end = current_date + timedelta(days=max(days_ahead, 0))
        candidates = (
            self.db.query(Equipment)
            .filter(
                Equipment.is_active.is_(True),
                Equipment.next_maintenance_date.isnot(None),
            )
            .all()
        )
        due_equipment = [
            equipment
            for equipment in candidates
            if equipment.next_maintenance_date and equipment.next_maintenance_date <= window_end
        ]

        rule = self._get_or_create_rule()
        alerts_created = 0
        skipped_existing = 0
        overdue_count = 0
        now = datetime.now()

        for equipment in due_equipment:
            if self._has_open_alert(equipment.id):
                skipped_existing += 1
                continue

            days_until = (equipment.next_maintenance_date - current_date).days
            if days_until < 0:
                overdue_count += 1

            alert = self._build_alert(
                rule=rule,
                equipment=equipment,
                current_date=current_date,
                days_until=days_until,
                now=now,
            )
            self.db.add(alert)
            self.db.flush()
            alerts_created += 1

            if dispatch_notifications:
                send_notification_for_alert(self.db, alert, logger_instance=logger)

        return {
            "checked_count": len(candidates),
            "due_count": len(due_equipment),
            "overdue_count": overdue_count,
            "alerts_created": alerts_created,
            "skipped_existing": skipped_existing,
            "window_end": window_end.isoformat(),
        }

    def _get_or_create_rule(self) -> AlertRule:
        rule = self.db.query(AlertRule).filter(AlertRule.rule_code == MAINTENANCE_RULE_CODE).first()
        if rule:
            return rule

        rule = AlertRule(
            rule_code=MAINTENANCE_RULE_CODE,
            rule_name="设备保养到期提醒",
            rule_type="EQUIPMENT",
            target_type=MAINTENANCE_TARGET_TYPE,
            target_field="next_maintenance_date",
            condition_type="CUSTOM",
            condition_expr="next_maintenance_date <= current_date + days_ahead",
            alert_level="WARNING",
            notify_channels=["SYSTEM"],
            enforcement_mode="WARN",
            check_frequency="DAILY",
            is_enabled=True,
            is_system=True,
            is_active=True,
            description="扫描设备下次保养日期，提醒车间主管及时安排保养。",
        )
        self.db.add(rule)
        self.db.flush()
        return rule

    def _has_open_alert(self, equipment_id: int) -> bool:
        return (
            self.db.query(AlertRecord)
            .filter(
                AlertRecord.target_type == MAINTENANCE_TARGET_TYPE,
                AlertRecord.target_id == equipment_id,
                AlertRecord.status.in_(OPEN_ALERT_STATUSES),
            )
            .first()
            is not None
        )

    def _resolve_handler_id(self, equipment: Equipment) -> Optional[int]:
        if not equipment.workshop_id:
            return None
        workshop = self.db.query(Workshop).filter(Workshop.id == equipment.workshop_id).first()
        return workshop.manager_id if workshop else None

    def _build_alert(
        self,
        *,
        rule: AlertRule,
        equipment: Equipment,
        current_date: date,
        days_until: int,
        now: datetime,
    ) -> AlertRecord:
        is_overdue = days_until < 0
        alert_level = "CRITICAL" if is_overdue else "WARNING"
        title = "设备保养已逾期" if is_overdue else "设备保养即将到期"
        if is_overdue:
            content = (
                f"设备 {equipment.equipment_code}（{equipment.equipment_name}）"
                f"保养日期已逾期 {-days_until} 天，请立即安排。"
            )
        else:
            content = (
                f"设备 {equipment.equipment_code}（{equipment.equipment_name}）"
                f"将在 {days_until} 天后到达保养日期，请提前安排。"
            )

        return AlertRecord(
            alert_no=f"ALT-EQM-{equipment.id}-{now.strftime('%Y%m%d%H%M%S%f')}",
            rule_id=rule.id,
            target_type=MAINTENANCE_TARGET_TYPE,
            target_id=equipment.id,
            target_no=equipment.equipment_code,
            target_name=equipment.equipment_name,
            alert_level=alert_level,
            severity=alert_level,
            alert_title=title,
            alert_content=content,
            alert_data={
                "equipment_id": equipment.id,
                "equipment_code": equipment.equipment_code,
                "next_maintenance_date": equipment.next_maintenance_date.isoformat(),
                "current_date": current_date.isoformat(),
                "days_until": days_until,
                "is_overdue": is_overdue,
            },
            triggered_at=now,
            trigger_value=equipment.next_maintenance_date.isoformat(),
            threshold_value=current_date.isoformat(),
            status="PENDING",
            handler_id=self._resolve_handler_id(equipment),
        )
