# -*- coding: utf-8 -*-
"""
产能分析服务

封装所有产能分析相关的业务逻辑，包括:
- 瓶颈识别与利用率分析
- OEE计算与分析
- 工人效率计算与分析
- 多维度对比分析
- 趋势分析
- 产能预测
- 看板数据
- 报告生成
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func, case
from sqlalchemy.orm import Session

from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
    Workstation,
    WorkOrder,
)


class CapacityAnalysisService:
    """产能分析服务"""

    def __init__(self, db: Session):
        self.db = db

    # --- 瓶颈分析 ---

    def identify_bottlenecks(
        self,
        workshop_id: Optional[int],
        start_date: Optional[date],
        end_date: Optional[date],
        threshold: float,
        limit: int,
    ) -> dict:
        """产能瓶颈识别"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        filters = [
            EquipmentOEERecord.record_date >= start_date,
            EquipmentOEERecord.record_date <= end_date,
        ]
        if workshop_id:
            filters.append(EquipmentOEERecord.workshop_id == workshop_id)

        # 1. 设备瓶颈分析
        equipment_bottlenecks = (
            self.db.query(
                Equipment.id.label("equipment_id"),
                Equipment.equipment_code,
                Equipment.equipment_name,
                Workshop.workshop_name,
                func.count(EquipmentOEERecord.id).label("record_count"),
                func.avg(EquipmentOEERecord.oee).label("avg_oee"),
                func.sum(EquipmentOEERecord.operating_time).label("total_operating_time"),
                func.sum(EquipmentOEERecord.planned_production_time).label("total_planned_time"),
                func.sum(EquipmentOEERecord.unplanned_downtime).label("total_downtime"),
                func.sum(EquipmentOEERecord.actual_output).label("total_output"),
                (func.sum(EquipmentOEERecord.operating_time) * 100.0 /
                 func.sum(EquipmentOEERecord.planned_production_time)).label("utilization_rate"),
            )
            .join(Equipment, EquipmentOEERecord.equipment_id == Equipment.id)
            .join(Workshop, Equipment.workshop_id == Workshop.id)
            .filter(and_(*filters))
            .group_by(Equipment.id, Equipment.equipment_code, Equipment.equipment_name, Workshop.workshop_name)
            .having(func.sum(EquipmentOEERecord.operating_time) * 100.0 /
                    func.sum(EquipmentOEERecord.planned_production_time) >= threshold)
            .order_by((func.sum(EquipmentOEERecord.operating_time) * 100.0 /
                       func.sum(EquipmentOEERecord.planned_production_time)).desc())
            .limit(limit)
            .all()
        )

        # 2. 工位瓶颈分析
        workstation_bottlenecks = (
            self.db.query(
                Workstation.id.label("workstation_id"),
                Workstation.workstation_code,
                Workstation.workstation_name,
                Workshop.workshop_name,
                func.count(WorkOrder.id).label("work_order_count"),
                func.sum(WorkOrder.actual_hours).label("total_hours"),
                func.sum(WorkOrder.completed_qty).label("total_completed"),
                func.avg(
                    case(
                        [(WorkOrder.actual_hours > 0,
                          WorkOrder.standard_hours * 100.0 / WorkOrder.actual_hours)],
                        else_=0
                    )
                ).label("avg_efficiency"),
            )
            .join(Workshop, Workstation.workshop_id == Workshop.id)
            .join(WorkOrder, Workstation.id == WorkOrder.workstation_id, isouter=True)
            .filter(WorkOrder.actual_start_time >= start_date)
            .filter(WorkOrder.actual_start_time <= end_date)
            .group_by(Workstation.id, Workstation.workstation_code, Workstation.workstation_name, Workshop.workshop_name)
            .having(func.count(WorkOrder.id) > 0)
            .order_by(func.sum(WorkOrder.actual_hours).desc())
            .limit(limit)
            .all()
        )

        # 3. 工人瓶颈分析(效率低的工人)
        worker_filter = [
            WorkerEfficiencyRecord.record_date >= start_date,
            WorkerEfficiencyRecord.record_date <= end_date,
        ]

        low_efficiency_workers = (
            self.db.query(
                Worker.id.label("worker_id"),
                Worker.worker_no,
                Worker.worker_name,
                func.count(WorkerEfficiencyRecord.id).label("record_count"),
                func.avg(WorkerEfficiencyRecord.efficiency).label("avg_efficiency"),
                func.sum(WorkerEfficiencyRecord.actual_hours).label("total_hours"),
                func.sum(WorkerEfficiencyRecord.completed_qty).label("total_completed"),
            )
            .join(Worker, WorkerEfficiencyRecord.worker_id == Worker.id)
            .filter(and_(*worker_filter))
            .group_by(Worker.id, Worker.worker_no, Worker.worker_name)
            .having(func.avg(WorkerEfficiencyRecord.efficiency) < 80)
            .order_by(func.avg(WorkerEfficiencyRecord.efficiency).asc())
            .limit(limit)
            .all()
        )

        return {
            "equipment_bottlenecks": [
                {
                    "type": "设备",
                    "equipment_id": row.equipment_id,
                    "equipment_code": row.equipment_code,
                    "equipment_name": row.equipment_name,
                    "workshop_name": row.workshop_name,
                    "utilization_rate": float(row.utilization_rate) if row.utilization_rate else 0,
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "total_output": row.total_output or 0,
                    "total_downtime": row.total_downtime or 0,
                    "impact_level": "高" if row.utilization_rate >= 90 else "中",
                    "suggestion": self._get_equipment_suggestion(row),
                }
                for row in equipment_bottlenecks
            ],
            "workstation_bottlenecks": [
                {
                    "type": "工位",
                    "workstation_id": row.workstation_id,
                    "workstation_code": row.workstation_code,
                    "workstation_name": row.workstation_name,
                    "workshop_name": row.workshop_name,
                    "work_order_count": row.work_order_count,
                    "total_hours": float(row.total_hours) if row.total_hours else 0,
                    "total_completed": row.total_completed or 0,
                    "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                    "suggestion": "考虑增加工位或优化工序",
                }
                for row in workstation_bottlenecks
            ],
            "low_efficiency_workers": [
                {
                    "type": "工人",
                    "worker_id": row.worker_id,
                    "worker_code": row.worker_no,
                    "worker_name": row.worker_name,
                    "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                    "total_hours": float(row.total_hours) if row.total_hours else 0,
                    "total_completed": row.total_completed or 0,
                    "suggestion": "建议提供培训或调整工作安排",
                }
                for row in low_efficiency_workers
            ],
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "threshold": threshold,
            },
        }
