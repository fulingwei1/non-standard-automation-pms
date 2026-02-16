# -*- coding: utf-8 -*-
"""
多维度对比分析接口
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
)

router = APIRouter()


@router.get("/comparison")
async def multi_dimensional_comparison(
    dimension: str = Query(..., description="对比维度: workshop/equipment/worker/time"),
    metric: str = Query("oee", description="对比指标: oee/efficiency/output/quality"),
    workshop_ids: Optional[str] = Query(None, description="车间ID列表,逗号分隔"),
    equipment_ids: Optional[str] = Query(None, description="设备ID列表,逗号分隔"),
    worker_ids: Optional[str] = Query(None, description="工人ID列表,逗号分隔"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    compare_periods: bool = Query(False, description="是否对比时间段(当前期vs上一期)"),
    db: Session = Depends(get_db),
):
    """
    多维度对比分析
    
    支持对比维度:
    - workshop: 车间对比
    - equipment: 设备对比
    - worker: 工人对比
    - time: 时间段对比
    
    支持对比指标:
    - oee: 设备综合效率
    - efficiency: 工人效率
    - output: 产量
    - quality: 质量合格率
    """
    # 默认查询最近30天
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    if dimension == "workshop":
        # 车间对比
        filters = [
            EquipmentOEERecord.record_date >= start_date,
            EquipmentOEERecord.record_date <= end_date,
        ]
        
        if workshop_ids:
            ids = [int(id.strip()) for id in workshop_ids.split(',')]
            filters.append(EquipmentOEERecord.workshop_id.in_(ids))
        
        results = (
            db.query(
                Workshop.id.label('workshop_id'),
                Workshop.workshop_name,
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                func.count(EquipmentOEERecord.id).label('record_count'),
            )
            .join(Workshop, EquipmentOEERecord.workshop_id == Workshop.id)
            .filter(and_(*filters))
            .group_by(Workshop.id, Workshop.workshop_name)
            .all()
        )
        
        items = [
            {
                "id": row.workshop_id,
                "name": row.workshop_name,
                "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                "total_output": row.total_output or 0,
                "avg_quality": float(row.avg_quality) if row.avg_quality else 0,
                "record_count": row.record_count,
                "rank": idx + 1,
            }
            for idx, row in enumerate(sorted(results, key=lambda x: float(x.avg_oee) if x.avg_oee else 0, reverse=True))
        ]
        
    elif dimension == "equipment":
        # 设备对比
        filters = [
            EquipmentOEERecord.record_date >= start_date,
            EquipmentOEERecord.record_date <= end_date,
        ]
        
        if equipment_ids:
            ids = [int(id.strip()) for id in equipment_ids.split(',')]
            filters.append(EquipmentOEERecord.equipment_id.in_(ids))
        
        results = (
            db.query(
                Equipment.id.label('equipment_id'),
                Equipment.equipment_code,
                Equipment.equipment_name,
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                func.avg(EquipmentOEERecord.availability).label('avg_availability'),
                func.avg(EquipmentOEERecord.performance).label('avg_performance'),
                func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                func.sum(EquipmentOEERecord.actual_output).label('total_output'),
            )
            .join(Equipment, EquipmentOEERecord.equipment_id == Equipment.id)
            .filter(and_(*filters))
            .group_by(Equipment.id, Equipment.equipment_code, Equipment.equipment_name)
            .all()
        )
        
        items = [
            {
                "id": row.equipment_id,
                "code": row.equipment_code,
                "name": row.equipment_name,
                "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                "avg_availability": float(row.avg_availability) if row.avg_availability else 0,
                "avg_performance": float(row.avg_performance) if row.avg_performance else 0,
                "avg_quality": float(row.avg_quality) if row.avg_quality else 0,
                "total_output": row.total_output or 0,
                "rank": idx + 1,
            }
            for idx, row in enumerate(sorted(results, key=lambda x: float(x.avg_oee) if x.avg_oee else 0, reverse=True))
        ]
        
    elif dimension == "worker":
        # 工人对比
        filters = [
            WorkerEfficiencyRecord.record_date >= start_date,
            WorkerEfficiencyRecord.record_date <= end_date,
        ]
        
        if worker_ids:
            ids = [int(id.strip()) for id in worker_ids.split(',')]
            filters.append(WorkerEfficiencyRecord.worker_id.in_(ids))
        
        results = (
            db.query(
                Worker.id.label('worker_id'),
                Worker.worker_code,
                Worker.worker_name,
                func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
                func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
                func.sum(WorkerEfficiencyRecord.actual_hours).label('total_hours'),
            )
            .join(Worker, WorkerEfficiencyRecord.worker_id == Worker.id)
            .filter(and_(*filters))
            .group_by(Worker.id, Worker.worker_code, Worker.worker_name)
            .all()
        )
        
        items = [
            {
                "id": row.worker_id,
                "code": row.worker_code,
                "name": row.worker_name,
                "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                "avg_quality_rate": float(row.avg_quality_rate) if row.avg_quality_rate else 0,
                "total_completed": row.total_completed or 0,
                "total_hours": float(row.total_hours) if row.total_hours else 0,
                "rank": idx + 1,
            }
            for idx, row in enumerate(sorted(results, key=lambda x: float(x.avg_efficiency) if x.avg_efficiency else 0, reverse=True))
        ]
        
    elif dimension == "time":
        # 时间段对比
        if compare_periods:
            # 对比当前期和上一期
            period_length = (end_date - start_date).days
            prev_start = start_date - timedelta(days=period_length)
            prev_end = start_date - timedelta(days=1)
            
            # 当前期
            current_data = (
                db.query(
                    func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                    func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                    func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                )
                .filter(
                    EquipmentOEERecord.record_date >= start_date,
                    EquipmentOEERecord.record_date <= end_date,
                )
                .first()
            )
            
            # 上一期
            prev_data = (
                db.query(
                    func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                    func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                    func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                )
                .filter(
                    EquipmentOEERecord.record_date >= prev_start,
                    EquipmentOEERecord.record_date <= prev_end,
                )
                .first()
            )
            
            current_oee = float(current_data.avg_oee) if current_data.avg_oee else 0
            prev_oee = float(prev_data.avg_oee) if prev_data.avg_oee else 0
            
            items = [
                {
                    "period": "当前期",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "avg_oee": current_oee,
                    "total_output": current_data.total_output or 0,
                    "avg_quality": float(current_data.avg_quality) if current_data.avg_quality else 0,
                },
                {
                    "period": "上一期",
                    "start_date": prev_start.isoformat(),
                    "end_date": prev_end.isoformat(),
                    "avg_oee": prev_oee,
                    "total_output": prev_data.total_output or 0,
                    "avg_quality": float(prev_data.avg_quality) if prev_data.avg_quality else 0,
                },
            ]
            
            # 计算变化
            oee_change = ((current_oee - prev_oee) / prev_oee * 100) if prev_oee > 0 else 0
            output_change = ((current_data.total_output - prev_data.total_output) / prev_data.total_output * 100) if prev_data.total_output > 0 else 0
            
            comparison_summary = {
                "oee_change_percent": round(oee_change, 2),
                "output_change_percent": round(output_change, 2),
                "trend": "上升" if oee_change > 5 else ("下降" if oee_change < -5 else "平稳"),
            }
        else:
            # 按月对比
            results = (
                db.query(
                    func.date_format(EquipmentOEERecord.record_date, '%Y-%m').label('month'),
                    func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                    func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                )
                .filter(
                    EquipmentOEERecord.record_date >= start_date,
                    EquipmentOEERecord.record_date <= end_date,
                )
                .group_by(func.date_format(EquipmentOEERecord.record_date, '%Y-%m'))
                .order_by(func.date_format(EquipmentOEERecord.record_date, '%Y-%m'))
                .all()
            )
            
            items = [
                {
                    "period": row.month,
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "total_output": row.total_output or 0,
                }
                for row in results
            ]
            
            comparison_summary = {}
    else:
        return {
            "code": 400,
            "message": "不支持的对比维度",
            "data": None,
        }
    
    return {
        "code": 200,
        "message": "对比成功",
        "data": {
            "dimension": dimension,
            "metric": metric,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "items": items,
            "comparison_summary": comparison_summary if 'comparison_summary' in locals() else {},
        },
    }
