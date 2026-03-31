# -*- coding: utf-8 -*-
"""
物料预警子服务
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.production.material_tracking import (
    MaterialAlert,
    MaterialAlertRule,
    MaterialConsumption,
)
from app.utils.db_helpers import save_obj


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def list_alerts(
        self,
        alert_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        status: str = "ACTIVE",
        material_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """物料预警列表"""
        from app.common.query_filters import apply_pagination

        query = self.db.query(MaterialAlert)

        if alert_type:
            query = query.filter(MaterialAlert.alert_type == alert_type)
        if alert_level:
            query = query.filter(MaterialAlert.alert_level == alert_level)
        if status:
            query = query.filter(MaterialAlert.status == status)
        if material_id:
            query = query.filter(MaterialAlert.material_id == material_id)

        query = query.order_by(desc(MaterialAlert.alert_date))

        total = query.count()
        offset = (page - 1) * page_size
        alerts = apply_pagination(query, offset, page_size).all()

        alert_data = [
            {
                "id": a.id,
                "alert_no": a.alert_no,
                "material_code": a.material_code,
                "material_name": a.material_name,
                "alert_type": a.alert_type,
                "alert_level": a.alert_level,
                "alert_date": a.alert_date.isoformat() if a.alert_date else None,
                "current_stock": float(a.current_stock) if a.current_stock else 0,
                "safety_stock": float(a.safety_stock) if a.safety_stock else 0,
                "shortage_qty": float(a.shortage_qty) if a.shortage_qty else 0,
                "days_to_stockout": a.days_to_stockout,
                "alert_message": a.alert_message,
                "recommendation": a.recommendation,
                "status": a.status,
                "assigned_to_id": a.assigned_to_id,
            }
            for a in alerts
        ]

        return {
            "items": alert_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def create_alert_rule(
        self,
        rule_data: Dict[str, Any],
        current_user_id: int,
    ) -> Dict[str, Any]:
        """配置物料预警规则"""
        rule = MaterialAlertRule(
            rule_name=rule_data["rule_name"],
            material_id=rule_data.get("material_id"),
            category_id=rule_data.get("category_id"),
            alert_type=rule_data["alert_type"],
            alert_level=rule_data.get("alert_level", "WARNING"),
            threshold_type=rule_data.get("threshold_type", "PERCENTAGE"),
            threshold_value=rule_data["threshold_value"],
            safety_days=rule_data.get("safety_days", 7),
            lead_time_days=rule_data.get("lead_time_days", 0),
            buffer_ratio=rule_data.get("buffer_ratio", 1.2),
            notify_users=rule_data.get("notify_users"),
            notify_roles=rule_data.get("notify_roles"),
            is_active=rule_data.get("is_active", True),
            priority=rule_data.get("priority", 0),
            description=rule_data.get("description"),
            created_by=current_user_id,
        )

        save_obj(self.db, rule)

        return {"id": rule.id, "rule_name": rule.rule_name}

    def check_and_create_alerts(self, material: Material):
        """检查并创建物料预警"""
        # 查询适用的预警规则
        rules = (
            self.db.query(MaterialAlertRule)
            .filter(
                MaterialAlertRule.is_active == True,
                or_(
                    MaterialAlertRule.material_id == material.id,
                    MaterialAlertRule.material_id == None,  # 全局规则
                ),
            )
            .all()
        )

        for rule in rules:
            should_alert = False
            alert_message = ""
            shortage_qty = 0

            # 低库存预警
            if rule.alert_type == "LOW_STOCK":
                if rule.threshold_type == "PERCENTAGE":
                    threshold = float(material.safety_stock or 0) * (
                        float(rule.threshold_value) / 100
                    )
                    if float(material.current_stock or 0) < threshold:
                        should_alert = True
                        shortage_qty = threshold - float(material.current_stock or 0)
                        alert_message = (
                            f"{material.material_name} 库存低于安全库存的{rule.threshold_value}%"
                        )
                elif rule.threshold_type == "FIXED":
                    if float(material.current_stock or 0) < float(rule.threshold_value):
                        should_alert = True
                        shortage_qty = float(rule.threshold_value) - float(
                            material.current_stock or 0
                        )
                        alert_message = f"{material.material_name} 库存低于{rule.threshold_value}"

            # 缺料预警
            elif rule.alert_type == "SHORTAGE":
                if float(material.current_stock or 0) <= 0:
                    should_alert = True
                    alert_message = f"{material.material_name} 已缺料"

            if should_alert:
                # 检查是否已存在活动预警
                existing = (
                    self.db.query(MaterialAlert)
                    .filter(
                        MaterialAlert.material_id == material.id,
                        MaterialAlert.alert_type == rule.alert_type,
                        MaterialAlert.status == "ACTIVE",
                    )
                    .first()
                )

                if not existing:
                    # 创建新预警
                    alert_no = (
                        f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{material.material_code}"
                    )

                    # 计算消耗速率和缺货天数
                    avg_daily_consumption = self._calculate_avg_daily_consumption(
                        material.id, days=30
                    )
                    days_to_stockout = 0
                    if avg_daily_consumption > 0:
                        days_to_stockout = int(
                            float(material.current_stock or 0) / avg_daily_consumption
                        )

                    alert = MaterialAlert(
                        alert_no=alert_no,
                        material_id=material.id,
                        material_code=material.material_code,
                        material_name=material.material_name,
                        alert_date=datetime.now(),
                        alert_type=rule.alert_type,
                        alert_level=rule.alert_level,
                        current_stock=material.current_stock,
                        safety_stock=material.safety_stock,
                        shortage_qty=shortage_qty,
                        avg_daily_consumption=avg_daily_consumption,
                        days_to_stockout=days_to_stockout,
                        alert_message=alert_message,
                        recommendation=f"建议采购数量: {shortage_qty + float(material.safety_stock or 0)}",
                        status="ACTIVE",
                    )

                    self.db.add(alert)
                    self.db.commit()

    def _calculate_avg_daily_consumption(self, material_id: int, days: int = 30) -> float:
        """计算平均日消耗 (内部辅助方法)"""
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

        consumptions = (
            self.db.query(MaterialConsumption)
            .filter(
                MaterialConsumption.material_id == material_id,
                MaterialConsumption.consumption_date >= start_dt,
                MaterialConsumption.consumption_date <= end_dt,
            )
            .all()
        )

        total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])

        return total_consumption / days if days > 0 else 0
