# -*- coding: utf-8 -*-
"""
物料采购管理 P3 级增强服务
- 缺料等待浪费计算
- 安全库存动态预警
- 重复采购检查
- 呆滞物料分析
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_UP
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.ecn.core import Ecn
from app.models.ecn.impact import EcnAffectedMaterial
from app.models.inventory_tracking import MaterialStock, MaterialTransaction
from app.models.material import BomHeader, BomItem, Material, MaterialShortage
from app.models.project import Project
from app.models.purchase import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)
from app.models.vendor import Vendor
from app.schemas.material_procurement_optimization import (
    DuplicatePurchaseCheckRequest,
    ShortageWasteCalculationRequest,
)


class MaterialProcurementOptimizationService:
    """物料采购管理 P3 增强服务"""

    ACTIVE_PO_STATUSES = {"DRAFT", "PENDING", "APPROVED", "ORDERED", "PARTIAL_RECEIVED"}
    ACTIVE_PR_STATUSES = {"DRAFT", "PENDING", "APPROVED"}
    CONSUMPTION_TRANSACTION_TYPES = {"ISSUE", "SCRAP"}

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _d(value: Any, default: str = "0") -> Decimal:
        if value is None:
            return Decimal(default)
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal(default)

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _safe_str(value: Any) -> str:
        return (value or "").strip()

    def calculate_shortage_waste(
        self, payload: ShortageWasteCalculationRequest
    ) -> Dict[str, Any]:
        labor_idle_cost = self._round_money(
            Decimal(payload.waiting_workers)
            * self._d(payload.labor_hourly_rate)
            * self._d(payload.waiting_hours)
        )
        machine_idle_cost = self._round_money(
            Decimal(payload.idle_machines)
            * self._d(payload.machine_hourly_rate)
            * self._d(payload.waiting_hours)
        )
        delay_penalty = self._round_money(
            self._d(payload.contract_amount)
            * Decimal(payload.delay_days)
            * self._d(payload.daily_penalty_rate)
        )
        opportunity_cost = self._round_money(
            Decimal(payload.delay_days) * self._d(payload.daily_output_value)
        )

        subtotal = labor_idle_cost + machine_idle_cost + delay_penalty + opportunity_cost
        management_buffer_cost = Decimal("0")
        if payload.include_management_buffer:
            management_buffer_cost = self._round_money(
                subtotal * self._d(payload.management_buffer_rate)
            )

        total_waste = subtotal + management_buffer_cost
        per_day_waste = self._round_money(
            total_waste / Decimal(payload.delay_days)
            if payload.delay_days > 0
            else Decimal("0")
        )
        per_hour_waste = self._round_money(
            total_waste / self._d(payload.waiting_hours)
            if self._d(payload.waiting_hours) > 0
            else Decimal("0")
        )

        project = self.db.query(Project).filter(Project.id == payload.project_id).first() if payload.project_id else None
        material = None
        if payload.material_id:
            material = self.db.query(Material).filter(Material.id == payload.material_id).first()
        elif payload.material_code:
            material = (
                self.db.query(Material)
                .filter(Material.material_code == payload.material_code)
                .first()
            )

        action_suggestions: List[str] = []
        if labor_idle_cost > 0:
            action_suggestions.append("优先锁定替代料或跨项目调拨，先把人从等待状态里捞出来")
        if machine_idle_cost > 0:
            action_suggestions.append("设备空转成本已发生，建议重排产并插入可替代工单")
        if delay_penalty > 0:
            action_suggestions.append("已存在延期罚款风险，采购需拉通供应商承诺交期并做日跟催")
        if opportunity_cost > 0:
            action_suggestions.append("机会成本偏高，建议项目经理升级为经营层关注事项")
        if not action_suggestions:
            action_suggestions.append("当前浪费金额不高，但建议保留参数模板，后续按项目复用")

        severity = "提示"
        if total_waste >= Decimal("50000"):
            severity = "紧急"
        elif total_waste >= Decimal("10000"):
            severity = "警告"

        return {
            "project": {
                "id": project.id if project else payload.project_id,
                "project_code": project.project_code if project else None,
                "project_name": project.project_name if project else None,
            },
            "material": {
                "id": material.id if material else payload.material_id,
                "material_code": material.material_code if material else payload.material_code,
                "material_name": material.material_name if material else None,
            },
            "shortage_reason": payload.shortage_reason,
            "config": {
                "labor_hourly_rate": self._d(payload.labor_hourly_rate),
                "machine_hourly_rate": self._d(payload.machine_hourly_rate),
                "daily_penalty_rate": self._d(payload.daily_penalty_rate),
                "daily_output_value": self._d(payload.daily_output_value),
                "management_buffer_rate": self._d(payload.management_buffer_rate),
                "include_management_buffer": payload.include_management_buffer,
            },
            "inputs": {
                "waiting_workers": payload.waiting_workers,
                "waiting_hours": self._d(payload.waiting_hours),
                "idle_machines": payload.idle_machines,
                "contract_amount": self._d(payload.contract_amount),
                "delay_days": payload.delay_days,
            },
            "cost_breakdown": {
                "labor_idle_cost": labor_idle_cost,
                "machine_idle_cost": machine_idle_cost,
                "delay_penalty": delay_penalty,
                "opportunity_cost": opportunity_cost,
                "management_buffer_cost": management_buffer_cost,
            },
            "total_waste_amount": self._round_money(total_waste),
            "daily_waste_amount": per_day_waste,
            "hourly_waste_amount": per_hour_waste,
            "severity": severity,
            "action_suggestions": action_suggestions,
        }

    def get_safety_stock_alerts(
        self,
        days: int = 90,
        safety_factor: Decimal = Decimal("1.5"),
        purchase_cycle_days: Optional[int] = None,
        focus_shortage_threshold: int = 2,
    ) -> Dict[str, Any]:
        cutoff_dt = datetime.now() - timedelta(days=days)
        alerts: List[Dict[str, Any]] = []

        materials = self.db.query(Material).filter(Material.is_active.is_(True)).all()
        for material in materials:
            current_stock = self._current_stock(material.id)
            consumed_qty = self._consumed_qty(material.id, cutoff_dt)
            avg_daily_usage = (
                consumed_qty / Decimal(days) if days > 0 else Decimal("0")
            )
            lead_time_days = purchase_cycle_days or (material.lead_time_days or 0) or 7
            effective_safety_factor = self._d(safety_factor)
            safety_stock = self._round_money(
                avg_daily_usage * Decimal(lead_time_days) * effective_safety_factor
            )
            shortage_frequency = self._shortage_frequency(material.id, cutoff_dt.date())
            suggested_days_cover = max(lead_time_days, 7)
            suggested_qty_base = avg_daily_usage * Decimal(suggested_days_cover)
            gap_qty = max(Decimal("0"), safety_stock + suggested_qty_base - current_stock)
            moq = self._d(material.min_order_qty, "1")
            suggested_replenishment_qty = self._round_up_to_moq(gap_qty, moq)

            alert_level = None
            if current_stock <= Decimal("0") or current_stock < safety_stock * Decimal("0.5"):
                alert_level = "紧急"
            elif current_stock < safety_stock:
                alert_level = "警告"
            elif current_stock < safety_stock * Decimal("1.2"):
                alert_level = "提示"

            is_high_frequency_shortage = shortage_frequency >= focus_shortage_threshold
            if alert_level or is_high_frequency_shortage:
                alert_level = alert_level or "提示"
                vendor_name = None
                if material.default_supplier_id:
                    vendor = self.db.query(Vendor).filter(Vendor.id == material.default_supplier_id).first()
                    vendor_name = vendor.supplier_name if vendor else None

                actions = []
                if current_stock < safety_stock:
                    actions.append("建议立即触发补货申请，并锁定采购交期")
                if suggested_replenishment_qty > 0:
                    actions.append(
                        f"建议补货 {suggested_replenishment_qty} {material.unit or '件'}，已按MOQ取整"
                    )
                if is_high_frequency_shortage:
                    actions.append("近90天缺料频繁，建议纳入重点物料周会清单")
                if avg_daily_usage == 0 and current_stock > 0:
                    actions.append("近90天几乎无消耗，补货前先确认是否为呆滞风险")

                alerts.append(
                    {
                        "material_id": material.id,
                        "material_code": material.material_code,
                        "material_name": material.material_name,
                        "specification": material.specification,
                        "unit": material.unit,
                        "current_stock": self._round_money(current_stock),
                        "avg_daily_usage": self._round_money(avg_daily_usage),
                        "purchase_cycle_days": lead_time_days,
                        "safety_factor": effective_safety_factor,
                        "calculated_safety_stock": safety_stock,
                        "suggested_replenishment_qty": suggested_replenishment_qty,
                        "moq": moq,
                        "alert_level": alert_level,
                        "shortage_frequency_90d": shortage_frequency,
                        "is_high_frequency_shortage": is_high_frequency_shortage,
                        "default_supplier_name": vendor_name,
                        "actions": actions,
                    }
                )

        alerts.sort(
            key=lambda item: (
                {"紧急": 0, "警告": 1, "提示": 2}.get(item["alert_level"], 3),
                -float(item["shortage_frequency_90d"]),
                float(item["current_stock"]),
            )
        )

        return {
            "config": {
                "consumption_days": days,
                "safety_factor": self._d(safety_factor),
                "purchase_cycle_days_override": purchase_cycle_days,
                "focus_shortage_threshold": focus_shortage_threshold,
            },
            "summary": {
                "total_alerts": len(alerts),
                "emergency_count": sum(1 for x in alerts if x["alert_level"] == "紧急"),
                "warning_count": sum(1 for x in alerts if x["alert_level"] == "警告"),
                "notice_count": sum(1 for x in alerts if x["alert_level"] == "提示"),
                "high_frequency_shortage_count": sum(
                    1 for x in alerts if x["is_high_frequency_shortage"]
                ),
            },
            "items": alerts,
        }

    def check_duplicate_purchase(
        self, payload: DuplicatePurchaseCheckRequest
    ) -> Dict[str, Any]:
        material = self._resolve_material(
            payload.material_id,
            payload.material_code,
            payload.material_name,
            payload.specification,
        )
        material_id = material.id if material else payload.material_id
        material_code = material.material_code if material else payload.material_code
        material_name = material.material_name if material else payload.material_name
        specification = material.specification if material else payload.specification

        duplicate_requests = []
        if payload.check_open_purchase_requests:
            q = (
                self.db.query(PurchaseRequest, PurchaseRequestItem)
                .join(PurchaseRequestItem, PurchaseRequest.id == PurchaseRequestItem.request_id)
                .filter(PurchaseRequest.status.in_(self.ACTIVE_PR_STATUSES))
            )
            q = self._apply_material_match_filter(
                q,
                PurchaseRequestItem.material_id,
                PurchaseRequestItem.material_code,
                PurchaseRequestItem.material_name,
                PurchaseRequestItem.specification,
                material_id,
                material_code,
                material_name,
                specification,
            )
            for req, item in q.all():
                duplicate_requests.append(
                    {
                        "request_id": req.id,
                        "request_no": req.request_no,
                        "status": req.status,
                        "project_id": req.project_id,
                        "material_id": item.material_id,
                        "material_code": item.material_code,
                        "material_name": item.material_name,
                        "specification": item.specification,
                        "quantity": self._d(item.quantity),
                        "ordered_qty": self._d(item.ordered_qty),
                    }
                )

        duplicate_orders = []
        if payload.check_open_purchase_orders:
            q = (
                self.db.query(PurchaseOrder, PurchaseOrderItem)
                .join(PurchaseOrderItem, PurchaseOrder.id == PurchaseOrderItem.order_id)
                .filter(PurchaseOrder.status.in_(self.ACTIVE_PO_STATUSES))
            )
            q = self._apply_material_match_filter(
                q,
                PurchaseOrderItem.material_id,
                PurchaseOrderItem.material_code,
                PurchaseOrderItem.material_name,
                PurchaseOrderItem.specification,
                material_id,
                material_code,
                material_name,
                specification,
            )
            for po, item in q.all():
                duplicate_orders.append(
                    {
                        "order_id": po.id,
                        "order_no": po.order_no,
                        "status": po.status,
                        "project_id": po.project_id,
                        "supplier_id": po.supplier_id,
                        "material_id": item.material_id,
                        "material_code": item.material_code,
                        "material_name": item.material_name,
                        "specification": item.specification,
                        "quantity": self._d(item.quantity),
                        "received_qty": self._d(item.received_qty),
                    }
                )

        transferable_stock = []
        if material_id:
            active_project_ids = {
                x["project_id"] for x in duplicate_orders if x.get("project_id")
            } | {x["project_id"] for x in duplicate_requests if x.get("project_id")}
            for project_id in sorted(pid for pid in active_project_ids if pid and pid != payload.project_id):
                project_stock = self._project_allocatable_stock(material_id, project_id)
                if project_stock > 0:
                    project = self.db.query(Project).filter(Project.id == project_id).first()
                    transferable_stock.append(
                        {
                            "project_id": project_id,
                            "project_code": project.project_code if project else None,
                            "project_name": project.project_name if project else None,
                            "allocatable_stock": self._round_money(project_stock),
                        }
                    )

        bom_consistency = self._bom_consistency(material_id, payload.project_id, payload.requested_bom_version)

        suggestions = []
        if duplicate_orders or duplicate_requests:
            suggestions.append("检测到已有在途采购，优先评估并单/改量，别重复下单制造库存垃圾")
        if transferable_stock:
            suggestions.append("存在其他项目可调拨库存，建议先调拨再采购")
        if bom_consistency["version_conflict"]:
            suggestions.append("BOM版本不一致，先统一版本再审批采购申请")
        if not suggestions:
            suggestions.append("未发现明显重复采购风险，可继续走采购流程")

        return {
            "request_context": {
                "project_id": payload.project_id,
                "requested_quantity": self._d(payload.requested_quantity),
                "requested_bom_version": payload.requested_bom_version,
            },
            "material": {
                "material_id": material_id,
                "material_code": material_code,
                "material_name": material_name,
                "specification": specification,
            },
            "duplicate_found": bool(duplicate_orders or duplicate_requests),
            "duplicate_purchase_requests": duplicate_requests,
            "duplicate_purchase_orders": duplicate_orders,
            "transferable_stock_options": transferable_stock,
            "bom_consistency": bom_consistency,
            "suggestions": suggestions,
        }

    def get_slow_moving_analysis(self) -> Dict[str, Any]:
        today = datetime.now()
        date_90 = today - timedelta(days=90)
        date_180 = today - timedelta(days=180)
        date_365 = today - timedelta(days=365)

        items: List[Dict[str, Any]] = []
        materials = self.db.query(Material).filter(Material.is_active.is_(True)).all()
        for material in materials:
            current_stock = self._current_stock(material.id)
            if current_stock <= 0:
                continue

            last_txn = (
                self.db.query(MaterialTransaction)
                .filter(
                    MaterialTransaction.material_id == material.id,
                    MaterialTransaction.transaction_type.in_(self.CONSUMPTION_TRANSACTION_TYPES),
                )
                .order_by(MaterialTransaction.transaction_date.desc())
                .first()
            )
            last_consumed_at = last_txn.transaction_date if last_txn else None
            days_without_consumption = (
                (today - last_consumed_at).days if last_consumed_at else 9999
            )

            category = None
            if days_without_consumption >= 365:
                category = "报废"
            elif days_without_consumption >= 180:
                category = "呆滞"
            elif days_without_consumption >= 90:
                category = "慢动"
            else:
                ecn_obsolete = self._ecn_obsolete_signal(material.id)
                if ecn_obsolete:
                    category = "报废"
                    days_without_consumption = max(days_without_consumption, 365)

            if not category:
                continue

            unit_value = self._material_unit_value(material)
            book_value = self._round_money(current_stock * unit_value)
            reason = self._analyze_slow_moving_reason(material.id, category, last_consumed_at)
            disposal = self._suggest_disposal(category, reason)
            recovery_rate = {
                "内部调拨": Decimal("1"),
                "退回供应商": Decimal("0.85"),
                "折价变卖": Decimal("0.5"),
                "拆解利用": Decimal("0.35"),
                "报废": Decimal("0.05"),
            }.get(disposal, Decimal("0.3"))
            potential_recovery_amount = self._round_money(book_value * recovery_rate)

            items.append(
                {
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "specification": material.specification,
                    "current_stock": self._round_money(current_stock),
                    "unit": material.unit,
                    "unit_value": self._round_money(unit_value),
                    "book_value": book_value,
                    "category": category,
                    "days_without_consumption": days_without_consumption,
                    "last_consumed_at": last_consumed_at.isoformat() if last_consumed_at else None,
                    "reason": reason,
                    "disposal_suggestion": disposal,
                    "potential_recovery_amount": potential_recovery_amount,
                }
            )

        items.sort(
            key=lambda item: (
                {"报废": 0, "呆滞": 1, "慢动": 2}.get(item["category"], 3),
                -float(item["book_value"]),
            )
        )

        return {
            "summary": {
                "slow_moving_count": sum(1 for x in items if x["category"] == "慢动"),
                "stagnant_count": sum(1 for x in items if x["category"] == "呆滞"),
                "scrap_count": sum(1 for x in items if x["category"] == "报废"),
                "total_book_value": self._round_money(
                    sum((self._d(x["book_value"]) for x in items), Decimal("0"))
                ),
                "total_potential_recovery_amount": self._round_money(
                    sum((self._d(x["potential_recovery_amount"]) for x in items), Decimal("0"))
                ),
            },
            "thresholds": {
                "slow_moving_days": 90,
                "stagnant_days": 180,
                "scrap_days": 365,
            },
            "items": items,
        }

    def _current_stock(self, material_id: int) -> Decimal:
        stock = (
            self.db.query(func.coalesce(func.sum(MaterialStock.available_quantity), 0))
            .filter(MaterialStock.material_id == material_id)
            .scalar()
        )
        if stock is None or self._d(stock) == 0:
            stock = self.db.query(Material.current_stock).filter(Material.id == material_id).scalar()
        return self._d(stock)

    def _consumed_qty(self, material_id: int, cutoff_dt: datetime) -> Decimal:
        qty = (
            self.db.query(func.coalesce(func.sum(MaterialTransaction.quantity), 0))
            .filter(
                MaterialTransaction.material_id == material_id,
                MaterialTransaction.transaction_type.in_(self.CONSUMPTION_TRANSACTION_TYPES),
                MaterialTransaction.transaction_date >= cutoff_dt,
            )
            .scalar()
        )
        return abs(self._d(qty))

    def _shortage_frequency(self, material_id: int, cutoff_date: date) -> int:
        return (
            self.db.query(MaterialShortage)
            .filter(
                MaterialShortage.material_id == material_id,
                MaterialShortage.created_at >= cutoff_date,
            )
            .count()
        )

    def _round_up_to_moq(self, qty: Decimal, moq: Decimal) -> Decimal:
        qty = self._d(qty)
        moq = self._d(moq, "1")
        if qty <= 0:
            return Decimal("0")
        if moq <= 0:
            return self._round_money(qty)
        multiplier = (qty / moq).quantize(Decimal("1"), rounding=ROUND_UP)
        return self._round_money(multiplier * moq)

    def _resolve_material(
        self,
        material_id: Optional[int],
        material_code: Optional[str],
        material_name: Optional[str],
        specification: Optional[str],
    ) -> Optional[Material]:
        if material_id:
            return self.db.query(Material).filter(Material.id == material_id).first()
        if material_code:
            exact = self.db.query(Material).filter(Material.material_code == material_code).first()
            if exact:
                return exact
        query = self.db.query(Material)
        if material_name:
            query = query.filter(Material.material_name == material_name)
        if specification:
            query = query.filter(Material.specification == specification)
        return query.first()

    def _apply_material_match_filter(
        self,
        query,
        material_id_col,
        material_code_col,
        material_name_col,
        specification_col,
        material_id,
        material_code,
        material_name,
        specification,
    ):
        conditions = []
        if material_id:
            conditions.append(material_id_col == material_id)
        if material_code:
            conditions.append(material_code_col == material_code)
        if material_name and specification:
            conditions.append(
                and_(material_name_col == material_name, specification_col == specification)
            )
        elif material_name:
            conditions.append(material_name_col == material_name)
        elif specification:
            conditions.append(specification_col == specification)
        if conditions:
            query = query.filter(or_(*conditions))
        return query

    def _project_allocatable_stock(self, material_id: int, project_id: int) -> Decimal:
        allocatable = (
            self.db.query(func.coalesce(func.sum(MaterialStock.available_quantity), 0))
            .filter(
                MaterialStock.material_id == material_id,
                or_(
                    MaterialStock.location.contains(f"P{project_id}"),
                    MaterialStock.location.contains(f"项目{project_id}"),
                ),
            )
            .scalar()
        )
        return self._d(allocatable)

    def _bom_consistency(
        self, material_id: Optional[int], project_id: Optional[int], requested_bom_version: Optional[str]
    ) -> Dict[str, Any]:
        if not material_id or not project_id:
            return {
                "project_id": project_id,
                "requested_bom_version": requested_bom_version,
                "active_bom_versions": [],
                "latest_bom_version": None,
                "version_conflict": False,
            }

        rows = (
            self.db.query(BomHeader.version, BomHeader.is_latest)
            .join(BomItem, BomItem.bom_id == BomHeader.id)
            .filter(BomHeader.project_id == project_id, BomItem.material_id == material_id)
            .distinct()
            .all()
        )
        active_versions = [row.version for row in rows]
        latest_version = next((row.version for row in rows if row.is_latest), None)
        version_conflict = bool(
            requested_bom_version
            and latest_version
            and requested_bom_version != latest_version
        )
        return {
            "project_id": project_id,
            "requested_bom_version": requested_bom_version,
            "active_bom_versions": active_versions,
            "latest_bom_version": latest_version,
            "version_conflict": version_conflict,
        }

    def _ecn_obsolete_signal(self, material_id: int) -> bool:
        if not material_id:
            return False
        row = (
            self.db.query(EcnAffectedMaterial)
            .join(Ecn, Ecn.id == EcnAffectedMaterial.ecn_id)
            .filter(
                EcnAffectedMaterial.material_id == material_id,
                or_(
                    EcnAffectedMaterial.is_obsolete_risk.is_(True),
                    EcnAffectedMaterial.status == "OBSOLETE",
                    Ecn.status.in_(["APPROVED", "COMPLETED", "CLOSED"]),
                ),
            )
            .order_by(EcnAffectedMaterial.created_at.desc())
            .first()
        )
        return row is not None and bool(getattr(row, "is_obsolete_risk", False))

    def _material_unit_value(self, material: Material) -> Decimal:
        return max(
            self._d(getattr(material, "last_price", None)),
            self._d(getattr(material, "standard_price", None)),
            Decimal("0"),
        )

    def _analyze_slow_moving_reason(
        self, material_id: int, category: str, last_consumed_at: Optional[datetime]
    ) -> str:
        ecn_item = (
            self.db.query(EcnAffectedMaterial)
            .filter(EcnAffectedMaterial.material_id == material_id)
            .order_by(EcnAffectedMaterial.created_at.desc())
            .first()
        )
        if ecn_item and getattr(ecn_item, "is_obsolete_risk", False):
            return "ECN变更/设计淘汰"

        cancelled_project_count = (
            self.db.query(BomHeader)
            .join(BomItem, BomItem.bom_id == BomHeader.id)
            .join(Project, Project.id == BomHeader.project_id)
            .filter(
                BomItem.material_id == material_id,
                Project.status.in_(["CANCELLED", "STOPPED", "CLOSED"]),
            )
            .count()
        )
        if cancelled_project_count > 0:
            return "项目取消或停滞"

        open_po_qty = (
            self.db.query(func.coalesce(func.sum(PurchaseOrderItem.quantity), 0))
            .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
            .filter(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.status.in_(self.ACTIVE_PO_STATUSES),
            )
            .scalar()
        )
        issue_180_qty = self._consumed_qty(material_id, datetime.now() - timedelta(days=180))
        if self._d(open_po_qty) > issue_180_qty * Decimal("1.5") and self._d(open_po_qty) > 0:
            return "采购过量"

        quality_scrap_qty = (
            self.db.query(func.coalesce(func.sum(MaterialTransaction.quantity), 0))
            .filter(
                MaterialTransaction.material_id == material_id,
                MaterialTransaction.transaction_type == "SCRAP",
            )
            .scalar()
        )
        if abs(self._d(quality_scrap_qty)) > 0:
            return "质量问题"

        if last_consumed_at is None:
            return "长期无消耗"
        return "需求下降导致慢动"

    def _suggest_disposal(self, category: str, reason: str) -> str:
        if "项目取消" in reason:
            return "内部调拨"
        if "采购过量" in reason:
            return "退回供应商"
        if "质量问题" in reason:
            return "拆解利用" if category != "报废" else "报废"
        if "ECN" in reason or category == "报废":
            return "折价变卖" if category != "报废" else "报废"
        return "内部调拨"
