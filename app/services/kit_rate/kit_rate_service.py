# -*- coding: utf-8 -*-
"""
Kit rate service for procurement readiness.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.assembly_kit import KitRateSnapshot
from app.models.material import BomHeader, BomItem
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrderItem


class KitRateService:
    """Centralized kit-rate business logic."""

    def __init__(self, db: Session):
        self.db = db

    def _get_project(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return project

    def _get_machine(self, machine_id: int) -> Machine:
        machine = self.db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
        return machine

    def _get_latest_bom(self, machine_id: int) -> Optional[BomHeader]:
        return (
            self.db.query(BomHeader)
            .filter(BomHeader.machine_id == machine_id)
            .filter(BomHeader.is_latest)
            .first()
        )

    def list_bom_items_for_machine(self, machine_id: int) -> List[BomItem]:
        self._get_machine(machine_id)
        bom = self._get_latest_bom(machine_id)
        if not bom:
            return []
        return bom.items.all()

    def list_bom_items_for_project(self, project_id: int) -> List[BomItem]:
        self._get_project(project_id)
        machines = self.db.query(Machine).filter(Machine.project_id == project_id).all()
        all_items: List[BomItem] = []
        for machine in machines:
            bom = self._get_latest_bom(machine.id)
            if not bom:
                continue
            all_items.extend(bom.items.all())
        return all_items

    def _get_in_transit_qty(self, material_id: Optional[int]) -> Decimal:
        if not material_id:
            return Decimal(0)
        in_transit_qty = Decimal(0)
        po_items = (
            self.db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == material_id)
            .filter(
                PurchaseOrderItem.status.in_(
                    ["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]
                )
            )
            .all()
        )
        for po_item in po_items:
            in_transit_qty += (po_item.quantity or 0) - (po_item.received_qty or 0)
        return in_transit_qty

    def calculate_kit_rate(
        self,
        bom_items: List[BomItem],
        calculate_by: str = "quantity",
    ) -> Dict[str, Any]:
        if calculate_by not in ["quantity", "amount"]:
            raise HTTPException(
                status_code=400, detail="calculate_by 必须是 quantity 或 amount"
            )

        total_items = len(bom_items)
        if total_items == 0:
            return {
                "total_items": 0,
                "fulfilled_items": 0,
                "shortage_items": 0,
                "in_transit_items": 0,
                "kit_rate": 0.0,
                "kit_status": "complete",
            }

        fulfilled_items = 0
        shortage_items = 0
        in_transit_items = 0
        total_quantity = Decimal(0)
        total_amount = Decimal(0)
        fulfilled_quantity = Decimal(0)
        fulfilled_amount = Decimal(0)

        for item in bom_items:
            material = item.material
            available_qty = (material.current_stock or 0) + (item.received_qty or 0)
            in_transit_qty = self._get_in_transit_qty(item.material_id)
            total_available = available_qty + in_transit_qty

            required_qty = item.quantity or 0
            item_amount = required_qty * (item.unit_price or 0)
            total_amount += item_amount

            if calculate_by == "quantity":
                total_quantity += required_qty
                if total_available >= required_qty:
                    fulfilled_items += 1
                    fulfilled_quantity += required_qty
                elif total_available > 0:
                    in_transit_items += 1
                else:
                    shortage_items += 1
            else:
                total_quantity += required_qty
                if total_available >= required_qty:
                    fulfilled_items += 1
                    fulfilled_quantity += required_qty
                    fulfilled_amount += item_amount
                elif total_available > 0:
                    in_transit_items += 1
                else:
                    shortage_items += 1

        if calculate_by == "quantity":
            kit_rate = float((fulfilled_quantity / total_quantity) * 100) if total_quantity > 0 else 0.0
        else:
            kit_rate = float((fulfilled_amount / total_amount) * 100) if total_amount > 0 else 0.0

        if kit_rate >= 100:
            kit_status = "complete"
        elif kit_rate >= 80:
            kit_status = "partial"
        else:
            kit_status = "shortage"

        return {
            "total_items": total_items,
            "fulfilled_items": fulfilled_items,
            "shortage_items": shortage_items,
            "in_transit_items": in_transit_items,
            "kit_rate": round(kit_rate, 2),
            "kit_status": kit_status,
            "total_quantity": float(total_quantity),
            "fulfilled_quantity": float(fulfilled_quantity),
            "total_amount": float(total_amount),
            "fulfilled_amount": float(fulfilled_amount),
            "calculate_by": calculate_by,
        }

    def get_machine_kit_rate(self, machine_id: int, calculate_by: str) -> Dict[str, Any]:
        machine = self._get_machine(machine_id)
        bom = self._get_latest_bom(machine_id)
        if not bom:
            raise HTTPException(status_code=404, detail="机台没有BOM")
        kit_rate = self.calculate_kit_rate(bom.items.all(), calculate_by)
        return {
            "machine_id": machine_id,
            "machine_no": machine.machine_no,
            "machine_name": machine.machine_name,
            "bom_id": bom.id,
            "bom_no": bom.bom_no,
            "bom_name": bom.bom_name,
            **kit_rate,
        }

    def get_project_kit_rate(self, project_id: int, calculate_by: str) -> Dict[str, Any]:
        project = self._get_project(project_id)
        machines = self.db.query(Machine).filter(Machine.project_id == project_id).all()

        all_bom_items: List[BomItem] = []
        machine_stats: List[Dict[str, Any]] = []

        for machine in machines:
            bom = self._get_latest_bom(machine.id)
            if not bom:
                continue
            bom_items = bom.items.all()
            all_bom_items.extend(bom_items)
            machine_kit_rate = self.calculate_kit_rate(bom_items, calculate_by)
            machine_stats.append(
                {
                    "machine_id": machine.id,
                    "machine_no": machine.machine_no,
                    "machine_name": machine.machine_name,
                    **machine_kit_rate,
                }
            )

        project_kit_rate = self.calculate_kit_rate(all_bom_items, calculate_by)
        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            **project_kit_rate,
            "machines": machine_stats,
        }

    def get_machine_material_status(self, machine_id: int) -> Dict[str, Any]:
        machine = self._get_machine(machine_id)
        bom = self._get_latest_bom(machine_id)
        if not bom:
            raise HTTPException(status_code=404, detail="机台没有BOM")

        material_status_list = []
        for item in bom.items.all():
            material = item.material
            required_qty = item.quantity or 0
            current_stock = material.current_stock or 0 if material else 0
            received_qty = item.received_qty or 0
            available_qty = current_stock + received_qty
            in_transit_qty = self._get_in_transit_qty(item.material_id)
            total_available = available_qty + in_transit_qty
            shortage_qty = max(0, required_qty - total_available)

            if total_available >= required_qty:
                status = "fulfilled"
            elif total_available > 0:
                status = "partial"
            else:
                status = "shortage"

            material_status_list.append(
                {
                    "bom_item_id": item.id,
                    "item_no": item.item_no,
                    "material_id": item.material_id,
                    "material_code": item.material_code,
                    "material_name": item.material_name,
                    "specification": item.specification,
                    "unit": item.unit,
                    "required_qty": float(required_qty),
                    "current_stock": float(current_stock),
                    "received_qty": float(received_qty),
                    "available_qty": float(available_qty),
                    "in_transit_qty": float(in_transit_qty),
                    "total_available": float(total_available),
                    "shortage_qty": float(shortage_qty),
                    "status": status,
                    "is_key_item": item.is_key_item,
                    "required_date": item.required_date.isoformat() if item.required_date else None,
                }
            )

        return {
            "machine_id": machine_id,
            "machine_no": machine.machine_no,
            "machine_name": machine.machine_name,
            "bom_id": bom.id,
            "bom_no": bom.bom_no,
            "items": material_status_list,
        }

    def get_project_material_status(self, project_id: int) -> Dict[str, Any]:
        project = self._get_project(project_id)
        machines = self.db.query(Machine).filter(Machine.project_id == project_id).all()

        material_summary: Dict[str, Dict[str, Any]] = {}

        for machine in machines:
            bom = self._get_latest_bom(machine.id)
            if not bom:
                continue
            for item in bom.items.all():
                material_code = item.material_code
                if material_code not in material_summary:
                    material = item.material
                    material_summary[material_code] = {
                        "material_id": item.material_id,
                        "material_code": material_code,
                        "material_name": item.material_name,
                        "specification": item.specification,
                        "unit": item.unit,
                        "total_required_qty": Decimal(0),
                        "current_stock": float(material.current_stock or 0)
                        if material
                        else 0,
                        "total_received_qty": Decimal(0),
                        "total_in_transit_qty": Decimal(0),
                        "is_key_material": item.is_key_item,
                        "machines": [],
                    }

                summary = material_summary[material_code]
                summary["total_required_qty"] += item.quantity or 0
                summary["total_received_qty"] += item.received_qty or 0
                summary["total_in_transit_qty"] += self._get_in_transit_qty(
                    item.material_id
                )

                summary["machines"].append(
                    {
                        "machine_id": machine.id,
                        "machine_no": machine.machine_no,
                        "required_qty": float(item.quantity or 0),
                    }
                )

        material_list = []
        total_required = Decimal(0)
        total_available = Decimal(0)
        total_shortage = Decimal(0)

        for _, summary in material_summary.items():
            total_available_qty = (
                summary["current_stock"]
                + float(summary["total_received_qty"])
                + float(summary["total_in_transit_qty"])
            )
            shortage_qty = max(0, float(summary["total_required_qty"]) - total_available_qty)

            total_required += summary["total_required_qty"]
            total_available += Decimal(total_available_qty)
            total_shortage += Decimal(shortage_qty)

            material_list.append(
                {
                    **summary,
                    "total_required_qty": float(summary["total_required_qty"]),
                    "total_received_qty": float(summary["total_received_qty"]),
                    "total_in_transit_qty": float(summary["total_in_transit_qty"]),
                    "total_available_qty": total_available_qty,
                    "shortage_qty": shortage_qty,
                    "status": "fulfilled"
                    if shortage_qty == 0
                    else ("partial" if total_available_qty > 0 else "shortage"),
                }
            )

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "summary": {
                "total_materials": len(material_list),
                "total_required_qty": float(total_required),
                "total_available_qty": float(total_available),
                "total_shortage_qty": float(total_shortage),
            },
            "materials": material_list,
        }

    def get_dashboard(self, project_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        if project_ids:
            projects = self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        else:
            from sqlalchemy import true

            projects = self.db.query(Project).filter(Project.is_active == true()).all()

        dashboard_data = []
        total_projects = 0
        complete_projects = 0
        partial_projects = 0
        shortage_projects = 0

        for project in projects:
            kit_rate_data = self.get_project_kit_rate(
                project_id=project.id, calculate_by="quantity"
            )

            dashboard_data.append(
                {
                    "project_id": project.id,
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "planned_end_date": project.planned_end_date.isoformat()
                    if project.planned_end_date
                    else None,
                    "kit_rate": kit_rate_data["kit_rate"],
                    "kit_status": kit_rate_data["kit_status"],
                    "total_items": kit_rate_data["total_items"],
                    "fulfilled_items": kit_rate_data["fulfilled_items"],
                    "shortage_items": kit_rate_data["shortage_items"],
                    "in_transit_items": kit_rate_data.get("in_transit_items", 0),
                }
            )

            total_projects += 1
            if kit_rate_data["kit_status"] == "complete":
                complete_projects += 1
            elif kit_rate_data["kit_status"] == "partial":
                partial_projects += 1
            else:
                shortage_projects += 1

        return {
            "summary": {
                "total_projects": total_projects,
                "complete_projects": complete_projects,
                "partial_projects": partial_projects,
                "shortage_projects": shortage_projects,
            },
            "projects": dashboard_data,
        }

    def _ensure_snapshot_table(self) -> None:
        inspector = inspect(self.db.get_bind())
        if not inspector.has_table(KitRateSnapshot.__tablename__):
            raise HTTPException(
                status_code=500,
                detail=(
                    f"齐套率快照表({KitRateSnapshot.__tablename__})不存在，"
                    "请先执行数据库迁移"
                ),
            )

    def get_trend(
        self,
        start_date: date,
        end_date: date,
        group_by: str,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._ensure_snapshot_table()

        query = self.db.query(KitRateSnapshot).filter(
            KitRateSnapshot.snapshot_date >= start_date,
            KitRateSnapshot.snapshot_date <= end_date,
        )
        if project_id:
            query = query.filter(KitRateSnapshot.project_id == project_id)

        snapshots = query.order_by(KitRateSnapshot.snapshot_date).all()

        if not snapshots:
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by,
                "trend_data": [],
                "summary": {
                    "avg_kit_rate": 0.0,
                    "max_kit_rate": 0.0,
                    "min_kit_rate": 0.0,
                    "data_points": 0,
                },
                "note": "暂无快照数据。定时任务会在每日凌晨自动生成快照。",
            }

        trend_data = []
        if group_by == "day":
            daily_data: Dict[str, Dict[str, Any]] = {}
            for snapshot in snapshots:
                day_key = snapshot.snapshot_date.isoformat()
                if day_key not in daily_data:
                    daily_data[day_key] = {
                        "rates": [],
                        "total_items": 0,
                        "fulfilled_items": 0,
                        "shortage_items": 0,
                    }
                daily_data[day_key]["rates"].append(float(snapshot.kit_rate))
                daily_data[day_key]["total_items"] += snapshot.total_items or 0
                daily_data[day_key]["fulfilled_items"] += snapshot.fulfilled_items or 0
                daily_data[day_key]["shortage_items"] += snapshot.shortage_items or 0

            for day_key in sorted(daily_data.keys()):
                data = daily_data[day_key]
                avg_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0.0
                trend_data.append(
                    {
                        "date": day_key,
                        "kit_rate": round(avg_rate, 2),
                        "project_count": len(data["rates"]),
                        "total_items": data["total_items"],
                        "fulfilled_items": data["fulfilled_items"],
                        "shortage_items": data["shortage_items"],
                    }
                )
        else:
            monthly_data: Dict[str, Dict[str, Any]] = {}
            for snapshot in snapshots:
                month_key = snapshot.snapshot_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "rates": [],
                        "total_items": 0,
                        "fulfilled_items": 0,
                        "shortage_items": 0,
                    }
                monthly_data[month_key]["rates"].append(float(snapshot.kit_rate))
                monthly_data[month_key]["total_items"] += snapshot.total_items or 0
                monthly_data[month_key]["fulfilled_items"] += snapshot.fulfilled_items or 0
                monthly_data[month_key]["shortage_items"] += snapshot.shortage_items or 0

            for month_key in sorted(monthly_data.keys()):
                data = monthly_data[month_key]
                avg_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0.0
                trend_data.append(
                    {
                        "date": month_key,
                        "kit_rate": round(avg_rate, 2),
                        "project_count": len(data["rates"]),
                        "total_items": data["total_items"],
                        "fulfilled_items": data["fulfilled_items"],
                        "shortage_items": data["shortage_items"],
                    }
                )

        if trend_data:
            all_rates = [d["kit_rate"] for d in trend_data]
            avg_rate = sum(all_rates) / len(all_rates)
            max_rate = max(all_rates)
            min_rate = min(all_rates)
        else:
            avg_rate = 0.0
            max_rate = 0.0
            min_rate = 0.0

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by,
            "trend_data": trend_data,
            "summary": {
                "avg_kit_rate": round(avg_rate, 2),
                "max_kit_rate": round(max_rate, 2),
                "min_kit_rate": round(min_rate, 2),
                "data_points": len(trend_data),
            },
        }

    def get_snapshots(
        self,
        project_id: int,
        start_date: date,
        end_date: date,
        snapshot_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_snapshot_table()

        query = self.db.query(KitRateSnapshot).filter(
            KitRateSnapshot.project_id == project_id,
            KitRateSnapshot.snapshot_date >= start_date,
            KitRateSnapshot.snapshot_date <= end_date,
        )

        if snapshot_type:
            query = query.filter(KitRateSnapshot.snapshot_type == snapshot_type)

        snapshots = query.order_by(KitRateSnapshot.snapshot_time.desc()).all()

        project = self._get_project(project_id)
        snapshot_list = []
        for snapshot in snapshots:
            snapshot_list.append(
                {
                    "id": snapshot.id,
                    "snapshot_date": snapshot.snapshot_date.isoformat(),
                    "snapshot_time": snapshot.snapshot_time.isoformat()
                    if snapshot.snapshot_time
                    else None,
                    "snapshot_type": snapshot.snapshot_type,
                    "trigger_event": snapshot.trigger_event,
                    "kit_rate": float(snapshot.kit_rate) if snapshot.kit_rate else 0.0,
                    "kit_status": snapshot.kit_status,
                    "total_items": snapshot.total_items,
                    "fulfilled_items": snapshot.fulfilled_items,
                    "shortage_items": snapshot.shortage_items,
                    "in_transit_items": snapshot.in_transit_items,
                    "blocking_kit_rate": float(snapshot.blocking_kit_rate)
                    if snapshot.blocking_kit_rate
                    else 0.0,
                    "project_stage": snapshot.project_stage,
                    "project_health": snapshot.project_health,
                }
            )

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_snapshots": len(snapshot_list),
            "snapshots": snapshot_list,
        }
