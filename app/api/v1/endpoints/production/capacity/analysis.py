# -*- coding: utf-8 -*-
"""
产能分析接口 - 瓶颈识别和利用率
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, case
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
    Workstation,
    WorkOrder,
)

router = APIRouter()


@router.get("/bottlenecks")
async def identify_bottlenecks(
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    threshold: float = Query(80.0, description="瓶颈阈值(%),利用率超过此值视为瓶颈"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    产能瓶颈识别
    
    瓶颈识别标准:
    1. 产能利用率最高(超过阈值)
    2. 影响整体产出
    3. 持续时间长
    
    返回瓶颈工位、设备和工人信息
    """
    # 默认查询最近30天
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
        db.query(
            Equipment.id.label('equipment_id'),
            Equipment.equipment_code,
            Equipment.equipment_name,
            Workshop.workshop_name,
            func.count(EquipmentOEERecord.id).label('record_count'),
            func.avg(EquipmentOEERecord.oee).label('avg_oee'),
            func.sum(EquipmentOEERecord.operating_time).label('total_operating_time'),
            func.sum(EquipmentOEERecord.planned_production_time).label('total_planned_time'),
            func.sum(EquipmentOEERecord.unplanned_downtime).label('total_downtime'),
            func.sum(EquipmentOEERecord.actual_output).label('total_output'),
            (func.sum(EquipmentOEERecord.operating_time) * 100.0 / 
             func.sum(EquipmentOEERecord.planned_production_time)).label('utilization_rate'),
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
        db.query(
            Workstation.id.label('workstation_id'),
            Workstation.workstation_code,
            Workstation.workstation_name,
            Workshop.workshop_name,
            func.count(WorkOrder.id).label('work_order_count'),
            func.sum(WorkOrder.actual_hours).label('total_hours'),
            func.sum(WorkOrder.completed_qty).label('total_completed'),
            func.avg(
                case(
                    [(WorkOrder.actual_hours > 0, 
                      WorkOrder.standard_hours * 100.0 / WorkOrder.actual_hours)],
                    else_=0
                )
            ).label('avg_efficiency'),
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
        db.query(
            Worker.id.label('worker_id'),
            Worker.worker_code,
            Worker.worker_name,
            func.count(WorkerEfficiencyRecord.id).label('record_count'),
            func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
            func.sum(WorkerEfficiencyRecord.actual_hours).label('total_hours'),
            func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
        )
        .join(Worker, WorkerEfficiencyRecord.worker_id == Worker.id)
        .filter(and_(*worker_filter))
        .group_by(Worker.id, Worker.worker_code, Worker.worker_name)
        .having(func.avg(WorkerEfficiencyRecord.efficiency) < 80)
        .order_by(func.avg(WorkerEfficiencyRecord.efficiency).asc())
        .limit(limit)
        .all()
    )
    
    return {
        "code": 200,
        "message": "瓶颈识别成功",
        "data": {
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
                    "suggestion": _get_equipment_suggestion(row),
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
                    "worker_code": row.worker_code,
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
        },
    }


@router.get("/utilization")
async def get_capacity_utilization(
    type: str = Query("equipment", description="类型: equipment/workstation/worker"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    产能利用率分析
    
    利用率 = 实际使用时间 / 可用时间 × 100%
    """
    # 默认查询最近30天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    if type == "equipment":
        filters = [
            EquipmentOEERecord.record_date >= start_date,
            EquipmentOEERecord.record_date <= end_date,
        ]
        if workshop_id:
            filters.append(EquipmentOEERecord.workshop_id == workshop_id)
        
        # 设备利用率
        query = (
            db.query(
                Equipment.id,
                Equipment.equipment_code,
                Equipment.equipment_name,
                func.sum(EquipmentOEERecord.operating_time).label('total_operating'),
                func.sum(EquipmentOEERecord.planned_production_time).label('total_planned'),
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                (func.sum(EquipmentOEERecord.operating_time) * 100.0 / 
                 func.sum(EquipmentOEERecord.planned_production_time)).label('utilization_rate'),
            )
            .join(Equipment, EquipmentOEERecord.equipment_id == Equipment.id)
            .filter(and_(*filters))
            .group_by(Equipment.id, Equipment.equipment_code, Equipment.equipment_name)
        )
        
        total = query.count()
        results = query.offset((page - 1) * page_size).limit(page_size).all()
        
        items = [
            {
                "id": row.id,
                "code": row.equipment_code,
                "name": row.equipment_name,
                "utilization_rate": float(row.utilization_rate) if row.utilization_rate else 0,
                "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                "total_operating": row.total_operating or 0,
                "total_planned": row.total_planned or 0,
                "status": _get_utilization_status(float(row.utilization_rate) if row.utilization_rate else 0),
            }
            for row in results
        ]
        
    elif type == "worker":
        filters = [
            WorkerEfficiencyRecord.record_date >= start_date,
            WorkerEfficiencyRecord.record_date <= end_date,
        ]
        if workshop_id:
            filters.append(WorkerEfficiencyRecord.workshop_id == workshop_id)
        
        # 工人利用率
        query = (
            db.query(
                Worker.id,
                Worker.worker_code,
                Worker.worker_name,
                func.avg(WorkerEfficiencyRecord.utilization_rate).label('avg_utilization'),
                func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                func.sum(WorkerEfficiencyRecord.actual_hours).label('total_hours'),
                func.sum(WorkerEfficiencyRecord.idle_hours).label('total_idle'),
            )
            .join(Worker, WorkerEfficiencyRecord.worker_id == Worker.id)
            .filter(and_(*filters))
            .group_by(Worker.id, Worker.worker_code, Worker.worker_name)
        )
        
        total = query.count()
        results = query.offset((page - 1) * page_size).limit(page_size).all()
        
        items = [
            {
                "id": row.id,
                "code": row.worker_code,
                "name": row.worker_name,
                "utilization_rate": float(row.avg_utilization) if row.avg_utilization else 0,
                "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                "total_hours": float(row.total_hours) if row.total_hours else 0,
                "total_idle": float(row.total_idle) if row.total_idle else 0,
                "status": _get_utilization_status(float(row.avg_utilization) if row.avg_utilization else 0),
            }
            for row in results
        ]
    else:
        return {
            "code": 400,
            "message": "不支持的类型",
            "data": None,
        }
    
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "type": type,
        },
    }


def _get_equipment_suggestion(row) -> str:
    """获取设备改进建议"""
    if row.utilization_rate >= 95:
        return "严重瓶颈,建议增加设备或优化排程"
    elif row.utilization_rate >= 85:
        return "需要关注,考虑增加备用设备"
    elif row.avg_oee < 60:
        return "OEE偏低,建议检查设备状态和维护计划"
    else:
        return "正常运行,持续监控"


def _get_utilization_status(rate: float) -> str:
    """获取利用率状态"""
    if rate >= 90:
        return "饱和"
    elif rate >= 70:
        return "良好"
    elif rate >= 50:
        return "正常"
    else:
        return "偏低"
