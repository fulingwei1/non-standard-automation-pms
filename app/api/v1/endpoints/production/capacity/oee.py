# -*- coding: utf-8 -*-
"""
设备OEE分析接口
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Workshop,
)

router = APIRouter()


@router.get("/oee")
async def get_oee_analysis(
    equipment_id: Optional[int] = Query(None, description="设备ID"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    workstation_id: Optional[int] = Query(None, description="工位ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    shift: Optional[str] = Query(None, description="班次"),
    min_oee: Optional[float] = Query(None, description="最小OEE过滤"),
    max_oee: Optional[float] = Query(None, description="最大OEE过滤"),
    group_by: str = Query("equipment", description="分组方式: equipment/workshop/date/shift"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    设备OEE分析
    
    OEE (Overall Equipment Effectiveness) = 可用率 × 性能率 × 合格率
    - 可用率 = 运行时间 / 计划生产时间
    - 性能率 = (理想周期时间 × 实际产量) / 运行时间
    - 合格率 = 合格数量 / 实际产量
    
    国际标准:
    - 世界级 OEE: ≥ 85%
    - 良好 OEE: 60% - 85%
    - 需改进 OEE: < 60%
    """
    # 构建查询条件
    filters = []
    
    if equipment_id:
        filters.append(EquipmentOEERecord.equipment_id == equipment_id)
    if workshop_id:
        filters.append(EquipmentOEERecord.workshop_id == workshop_id)
    if workstation_id:
        filters.append(EquipmentOEERecord.workstation_id == workstation_id)
    if start_date:
        filters.append(EquipmentOEERecord.record_date >= start_date)
    if end_date:
        filters.append(EquipmentOEERecord.record_date <= end_date)
    if shift:
        filters.append(EquipmentOEERecord.shift == shift)
    if min_oee is not None:
        filters.append(EquipmentOEERecord.oee >= min_oee)
    if max_oee is not None:
        filters.append(EquipmentOEERecord.oee <= max_oee)
    
    # 默认查询最近30天
    if not start_date and not end_date:
        filters.append(EquipmentOEERecord.record_date >= date.today() - timedelta(days=30))
    
    # 基础查询
    query = db.query(EquipmentOEERecord).filter(and_(*filters)) if filters else db.query(EquipmentOEERecord)
    
    # 总数查询
    total = query.count()
    
    # 根据分组方式聚合数据
    if group_by == "equipment":
        # 按设备分组
        grouped_data = (
            db.query(
                EquipmentOEERecord.equipment_id,
                Equipment.equipment_code,
                Equipment.equipment_name,
                func.count(EquipmentOEERecord.id).label('record_count'),
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                func.avg(EquipmentOEERecord.availability).label('avg_availability'),
                func.avg(EquipmentOEERecord.performance).label('avg_performance'),
                func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                func.min(EquipmentOEERecord.oee).label('min_oee'),
                func.max(EquipmentOEERecord.oee).label('max_oee'),
                func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                func.sum(EquipmentOEERecord.qualified_qty).label('total_qualified'),
                func.sum(EquipmentOEERecord.defect_qty).label('total_defects'),
            )
            .join(Equipment, EquipmentOEERecord.equipment_id == Equipment.id)
            .filter(and_(*filters) if filters else True)
            .group_by(EquipmentOEERecord.equipment_id, Equipment.equipment_code, Equipment.equipment_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "equipment_id": row.equipment_id,
                "equipment_code": row.equipment_code,
                "equipment_name": row.equipment_name,
                "record_count": row.record_count,
                "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                "avg_availability": float(row.avg_availability) if row.avg_availability else 0,
                "avg_performance": float(row.avg_performance) if row.avg_performance else 0,
                "avg_quality": float(row.avg_quality) if row.avg_quality else 0,
                "min_oee": float(row.min_oee) if row.min_oee else 0,
                "max_oee": float(row.max_oee) if row.max_oee else 0,
                "total_output": row.total_output or 0,
                "total_qualified": row.total_qualified or 0,
                "total_defects": row.total_defects or 0,
                "oee_level": _get_oee_level(float(row.avg_oee) if row.avg_oee else 0),
            }
            for row in grouped_data
        ]
        
    elif group_by == "workshop":
        # 按车间分组
        grouped_data = (
            db.query(
                EquipmentOEERecord.workshop_id,
                Workshop.workshop_name,
                func.count(EquipmentOEERecord.id).label('record_count'),
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                func.avg(EquipmentOEERecord.availability).label('avg_availability'),
                func.avg(EquipmentOEERecord.performance).label('avg_performance'),
                func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                func.sum(EquipmentOEERecord.actual_output).label('total_output'),
            )
            .join(Workshop, EquipmentOEERecord.workshop_id == Workshop.id)
            .filter(and_(*filters) if filters else True)
            .group_by(EquipmentOEERecord.workshop_id, Workshop.workshop_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "workshop_id": row.workshop_id,
                "workshop_name": row.workshop_name,
                "record_count": row.record_count,
                "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                "avg_availability": float(row.avg_availability) if row.avg_availability else 0,
                "avg_performance": float(row.avg_performance) if row.avg_performance else 0,
                "avg_quality": float(row.avg_quality) if row.avg_quality else 0,
                "total_output": row.total_output or 0,
                "oee_level": _get_oee_level(float(row.avg_oee) if row.avg_oee else 0),
            }
            for row in grouped_data
        ]
        
    elif group_by == "date":
        # 按日期分组
        grouped_data = (
            db.query(
                EquipmentOEERecord.record_date,
                func.count(EquipmentOEERecord.id).label('record_count'),
                func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                func.avg(EquipmentOEERecord.availability).label('avg_availability'),
                func.avg(EquipmentOEERecord.performance).label('avg_performance'),
                func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                func.sum(EquipmentOEERecord.actual_output).label('total_output'),
            )
            .filter(and_(*filters) if filters else True)
            .group_by(EquipmentOEERecord.record_date)
            .order_by(EquipmentOEERecord.record_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "record_date": row.record_date.isoformat() if row.record_date else None,
                "record_count": row.record_count,
                "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                "avg_availability": float(row.avg_availability) if row.avg_availability else 0,
                "avg_performance": float(row.avg_performance) if row.avg_performance else 0,
                "avg_quality": float(row.avg_quality) if row.avg_quality else 0,
                "total_output": row.total_output or 0,
                "oee_level": _get_oee_level(float(row.avg_oee) if row.avg_oee else 0),
            }
            for row in grouped_data
        ]
        
    else:  # 明细查询
        records = (
            query
            .order_by(EquipmentOEERecord.record_date.desc(), EquipmentOEERecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "id": record.id,
                "equipment_id": record.equipment_id,
                "workshop_id": record.workshop_id,
                "workstation_id": record.workstation_id,
                "record_date": record.record_date.isoformat() if record.record_date else None,
                "shift": record.shift,
                "oee": float(record.oee),
                "availability": float(record.availability),
                "performance": float(record.performance),
                "quality": float(record.quality),
                "actual_output": record.actual_output,
                "qualified_qty": record.qualified_qty,
                "defect_qty": record.defect_qty,
                "operating_time": record.operating_time,
                "unplanned_downtime": record.unplanned_downtime,
                "oee_level": _get_oee_level(float(record.oee)),
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
            for record in records
        ]
    
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "group_by": group_by,
        },
    }


def _get_oee_level(oee: float) -> str:
    """获取OEE等级"""
    if oee >= 85:
        return "世界级"
    elif oee >= 60:
        return "良好"
    else:
        return "需改进"
