# -*- coding: utf-8 -*-
"""
产能分析看板接口
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
)

router = APIRouter()


@router.get("/dashboard")
async def get_capacity_dashboard(
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
):
    """
    产能分析看板
    
    综合展示:
    - OEE整体情况
    - 工人效率情况
    - 产能瓶颈
    - 趋势分析
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # 构建过滤条件
    oee_filters = [
        EquipmentOEERecord.record_date >= start_date,
        EquipmentOEERecord.record_date <= end_date,
    ]
    
    efficiency_filters = [
        WorkerEfficiencyRecord.record_date >= start_date,
        WorkerEfficiencyRecord.record_date <= end_date,
    ]
    
    if workshop_id:
        oee_filters.append(EquipmentOEERecord.workshop_id == workshop_id)
        efficiency_filters.append(WorkerEfficiencyRecord.workshop_id == workshop_id)
    
    # 1. OEE概览
    oee_summary = (
        db.query(
            func.count(EquipmentOEERecord.id).label('total_records'),
            func.avg(EquipmentOEERecord.oee).label('avg_oee'),
            func.avg(EquipmentOEERecord.availability).label('avg_availability'),
            func.avg(EquipmentOEERecord.performance).label('avg_performance'),
            func.avg(EquipmentOEERecord.quality).label('avg_quality'),
            func.sum(EquipmentOEERecord.actual_output).label('total_output'),
            func.sum(EquipmentOEERecord.qualified_qty).label('total_qualified'),
            func.sum(EquipmentOEERecord.defect_qty).label('total_defects'),
            func.sum(EquipmentOEERecord.unplanned_downtime).label('total_downtime'),
        )
        .filter(and_(*oee_filters))
        .first()
    )
    
    # 2. 工人效率概览
    efficiency_summary = (
        db.query(
            func.count(WorkerEfficiencyRecord.id).label('total_records'),
            func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
            func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
            func.avg(WorkerEfficiencyRecord.utilization_rate).label('avg_utilization'),
            func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
            func.sum(WorkerEfficiencyRecord.actual_hours).label('total_hours'),
        )
        .filter(and_(*efficiency_filters))
        .first()
    )
    
    # 3. OEE分布
    oee_distribution = (
        db.query(
            func.count(EquipmentOEERecord.id).label('count'),
            func.sum(func.if_(EquipmentOEERecord.oee >= 85, 1, 0)).label('world_class'),
            func.sum(func.if_(and_(EquipmentOEERecord.oee >= 60, EquipmentOEERecord.oee < 85), 1, 0)).label('good'),
            func.sum(func.if_(EquipmentOEERecord.oee < 60, 1, 0)).label('needs_improvement'),
        )
        .filter(and_(*oee_filters))
        .first()
    )
    
    # 4. Top 5 最佳设备
    top_equipment = (
        db.query(
            Equipment.id,
            Equipment.equipment_code,
            Equipment.equipment_name,
            func.avg(EquipmentOEERecord.oee).label('avg_oee'),
            func.sum(EquipmentOEERecord.actual_output).label('total_output'),
        )
        .join(Equipment, EquipmentOEERecord.equipment_id == Equipment.id)
        .filter(and_(*oee_filters))
        .group_by(Equipment.id, Equipment.equipment_code, Equipment.equipment_name)
        .order_by(func.avg(EquipmentOEERecord.oee).desc())
        .limit(5)
        .all()
    )
    
    # 5. Top 5 最佳工人
    top_workers = (
        db.query(
            Worker.id,
            Worker.worker_code,
            Worker.worker_name,
            func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
            func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
        )
        .join(Worker, WorkerEfficiencyRecord.worker_id == Worker.id)
        .filter(and_(*efficiency_filters))
        .group_by(Worker.id, Worker.worker_code, Worker.worker_name)
        .order_by(func.avg(WorkerEfficiencyRecord.efficiency).desc())
        .limit(5)
        .all()
    )
    
    # 6. 瓶颈设备(OEE最低的5个)
    bottleneck_equipment = (
        db.query(
            Equipment.id,
            Equipment.equipment_code,
            Equipment.equipment_name,
            func.avg(EquipmentOEERecord.oee).label('avg_oee'),
            func.sum(EquipmentOEERecord.unplanned_downtime).label('total_downtime'),
        )
        .join(Equipment, EquipmentOEERecord.equipment_id == Equipment.id)
        .filter(and_(*oee_filters))
        .group_by(Equipment.id, Equipment.equipment_code, Equipment.equipment_name)
        .order_by(func.avg(EquipmentOEERecord.oee).asc())
        .limit(5)
        .all()
    )
    
    # 7. 最近7天趋势
    recent_trend = (
        db.query(
            EquipmentOEERecord.record_date,
            func.avg(EquipmentOEERecord.oee).label('avg_oee'),
            func.sum(EquipmentOEERecord.actual_output).label('total_output'),
        )
        .filter(
            EquipmentOEERecord.record_date >= end_date - timedelta(days=7),
            EquipmentOEERecord.record_date <= end_date,
        )
        .group_by(EquipmentOEERecord.record_date)
        .order_by(EquipmentOEERecord.record_date)
        .all()
    )
    
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
            "oee_overview": {
                "total_records": oee_summary.total_records or 0,
                "avg_oee": float(oee_summary.avg_oee) if oee_summary.avg_oee else 0,
                "avg_availability": float(oee_summary.avg_availability) if oee_summary.avg_availability else 0,
                "avg_performance": float(oee_summary.avg_performance) if oee_summary.avg_performance else 0,
                "avg_quality": float(oee_summary.avg_quality) if oee_summary.avg_quality else 0,
                "total_output": oee_summary.total_output or 0,
                "total_qualified": oee_summary.total_qualified or 0,
                "total_defects": oee_summary.total_defects or 0,
                "total_downtime": oee_summary.total_downtime or 0,
                "quality_rate": round((oee_summary.total_qualified / oee_summary.total_output * 100) if oee_summary.total_output else 0, 2),
            },
            "efficiency_overview": {
                "total_records": efficiency_summary.total_records or 0,
                "avg_efficiency": float(efficiency_summary.avg_efficiency) if efficiency_summary.avg_efficiency else 0,
                "avg_quality_rate": float(efficiency_summary.avg_quality_rate) if efficiency_summary.avg_quality_rate else 0,
                "avg_utilization": float(efficiency_summary.avg_utilization) if efficiency_summary.avg_utilization else 0,
                "total_completed": efficiency_summary.total_completed or 0,
                "total_hours": float(efficiency_summary.total_hours) if efficiency_summary.total_hours else 0,
            },
            "oee_distribution": {
                "total": oee_distribution.count or 0,
                "world_class": oee_distribution.world_class or 0,
                "good": oee_distribution.good or 0,
                "needs_improvement": oee_distribution.needs_improvement or 0,
            },
            "top_equipment": [
                {
                    "id": row.id,
                    "code": row.equipment_code,
                    "name": row.equipment_name,
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "total_output": row.total_output or 0,
                }
                for row in top_equipment
            ],
            "top_workers": [
                {
                    "id": row.id,
                    "code": row.worker_code,
                    "name": row.worker_name,
                    "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                    "total_completed": row.total_completed or 0,
                }
                for row in top_workers
            ],
            "bottleneck_equipment": [
                {
                    "id": row.id,
                    "code": row.equipment_code,
                    "name": row.equipment_name,
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "total_downtime": row.total_downtime or 0,
                }
                for row in bottleneck_equipment
            ],
            "recent_trend": [
                {
                    "date": row.record_date.isoformat(),
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "total_output": row.total_output or 0,
                }
                for row in recent_trend
            ],
        },
    }
