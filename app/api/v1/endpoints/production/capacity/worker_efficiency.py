# -*- coding: utf-8 -*-
"""
工人效率分析接口
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    Worker,
    WorkerEfficiencyRecord,
    Workshop,
)

router = APIRouter()


@router.get("/worker-efficiency")
async def get_worker_efficiency_analysis(
    worker_id: Optional[int] = Query(None, description="工人ID"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    workstation_id: Optional[int] = Query(None, description="工位ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    shift: Optional[str] = Query(None, description="班次"),
    min_efficiency: Optional[float] = Query(None, description="最小效率过滤"),
    max_efficiency: Optional[float] = Query(None, description="最大效率过滤"),
    skill_level: Optional[str] = Query(None, description="技能等级"),
    group_by: str = Query("worker", description="分组方式: worker/workshop/date/skill"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    工人效率分析
    
    工人效率 = 标准工时 / 实际工时 × 100%
    
    效率等级:
    - 优秀: ≥ 120%
    - 良好: 100% - 120%
    - 正常: 80% - 100%
    - 偏低: < 80%
    """
    # 构建查询条件
    filters = []
    
    if worker_id:
        filters.append(WorkerEfficiencyRecord.worker_id == worker_id)
    if workshop_id:
        filters.append(WorkerEfficiencyRecord.workshop_id == workshop_id)
    if workstation_id:
        filters.append(WorkerEfficiencyRecord.workstation_id == workstation_id)
    if start_date:
        filters.append(WorkerEfficiencyRecord.record_date >= start_date)
    if end_date:
        filters.append(WorkerEfficiencyRecord.record_date <= end_date)
    if shift:
        filters.append(WorkerEfficiencyRecord.shift == shift)
    if min_efficiency is not None:
        filters.append(WorkerEfficiencyRecord.efficiency >= min_efficiency)
    if max_efficiency is not None:
        filters.append(WorkerEfficiencyRecord.efficiency <= max_efficiency)
    if skill_level:
        filters.append(WorkerEfficiencyRecord.skill_level == skill_level)
    
    # 默认查询最近30天
    if not start_date and not end_date:
        filters.append(WorkerEfficiencyRecord.record_date >= date.today() - timedelta(days=30))
    
    # 基础查询
    query = db.query(WorkerEfficiencyRecord).filter(and_(*filters)) if filters else db.query(WorkerEfficiencyRecord)
    
    # 总数查询
    total = query.count()
    
    # 根据分组方式聚合数据
    if group_by == "worker":
        # 按工人分组
        grouped_data = (
            db.query(
                WorkerEfficiencyRecord.worker_id,
                Worker.worker_no,
                Worker.worker_name,
                func.count(WorkerEfficiencyRecord.id).label('record_count'),
                func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
                func.avg(WorkerEfficiencyRecord.utilization_rate).label('avg_utilization'),
                func.avg(WorkerEfficiencyRecord.overall_efficiency).label('avg_overall'),
                func.sum(WorkerEfficiencyRecord.standard_hours).label('total_standard_hours'),
                func.sum(WorkerEfficiencyRecord.actual_hours).label('total_actual_hours'),
                func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
                func.sum(WorkerEfficiencyRecord.qualified_qty).label('total_qualified'),
                func.sum(WorkerEfficiencyRecord.defect_qty).label('total_defects'),
            )
            .join(Worker, WorkerEfficiencyRecord.worker_id == Worker.id)
            .filter(and_(*filters) if filters else True)
            .group_by(WorkerEfficiencyRecord.worker_id, Worker.worker_no, Worker.worker_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "worker_id": row.worker_id,
                "worker_code": row.worker_no,
                "worker_name": row.worker_name,
                "record_count": row.record_count,
                "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                "avg_quality_rate": float(row.avg_quality_rate) if row.avg_quality_rate else 0,
                "avg_utilization": float(row.avg_utilization) if row.avg_utilization else 0,
                "avg_overall": float(row.avg_overall) if row.avg_overall else 0,
                "total_standard_hours": float(row.total_standard_hours) if row.total_standard_hours else 0,
                "total_actual_hours": float(row.total_actual_hours) if row.total_actual_hours else 0,
                "total_completed": row.total_completed or 0,
                "total_qualified": row.total_qualified or 0,
                "total_defects": row.total_defects or 0,
                "efficiency_level": _get_efficiency_level(float(row.avg_efficiency) if row.avg_efficiency else 0),
            }
            for row in grouped_data
        ]
        
    elif group_by == "workshop":
        # 按车间分组
        grouped_data = (
            db.query(
                WorkerEfficiencyRecord.workshop_id,
                Workshop.workshop_name,
                func.count(WorkerEfficiencyRecord.id).label('record_count'),
                func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
                func.avg(WorkerEfficiencyRecord.overall_efficiency).label('avg_overall'),
                func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
            )
            .join(Workshop, WorkerEfficiencyRecord.workshop_id == Workshop.id)
            .filter(and_(*filters) if filters else True)
            .group_by(WorkerEfficiencyRecord.workshop_id, Workshop.workshop_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "workshop_id": row.workshop_id,
                "workshop_name": row.workshop_name,
                "record_count": row.record_count,
                "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                "avg_quality_rate": float(row.avg_quality_rate) if row.avg_quality_rate else 0,
                "avg_overall": float(row.avg_overall) if row.avg_overall else 0,
                "total_completed": row.total_completed or 0,
                "efficiency_level": _get_efficiency_level(float(row.avg_efficiency) if row.avg_efficiency else 0),
            }
            for row in grouped_data
        ]
        
    elif group_by == "date":
        # 按日期分组
        grouped_data = (
            db.query(
                WorkerEfficiencyRecord.record_date,
                func.count(WorkerEfficiencyRecord.id).label('record_count'),
                func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
                func.avg(WorkerEfficiencyRecord.overall_efficiency).label('avg_overall'),
                func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
            )
            .filter(and_(*filters) if filters else True)
            .group_by(WorkerEfficiencyRecord.record_date)
            .order_by(WorkerEfficiencyRecord.record_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "record_date": row.record_date.isoformat() if row.record_date else None,
                "record_count": row.record_count,
                "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                "avg_quality_rate": float(row.avg_quality_rate) if row.avg_quality_rate else 0,
                "avg_overall": float(row.avg_overall) if row.avg_overall else 0,
                "total_completed": row.total_completed or 0,
                "efficiency_level": _get_efficiency_level(float(row.avg_efficiency) if row.avg_efficiency else 0),
            }
            for row in grouped_data
        ]
        
    elif group_by == "skill":
        # 按技能等级分组
        grouped_data = (
            db.query(
                WorkerEfficiencyRecord.skill_level,
                func.count(WorkerEfficiencyRecord.id).label('record_count'),
                func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
                func.avg(WorkerEfficiencyRecord.overall_efficiency).label('avg_overall'),
            )
            .filter(and_(*filters) if filters else True)
            .filter(WorkerEfficiencyRecord.skill_level.isnot(None))
            .group_by(WorkerEfficiencyRecord.skill_level)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "skill_level": row.skill_level,
                "record_count": row.record_count,
                "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                "avg_quality_rate": float(row.avg_quality_rate) if row.avg_quality_rate else 0,
                "avg_overall": float(row.avg_overall) if row.avg_overall else 0,
                "efficiency_level": _get_efficiency_level(float(row.avg_efficiency) if row.avg_efficiency else 0),
            }
            for row in grouped_data
        ]
        
    else:  # 明细查询
        records = (
            query
            .order_by(WorkerEfficiencyRecord.record_date.desc(), WorkerEfficiencyRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        items = [
            {
                "id": record.id,
                "worker_id": record.worker_id,
                "workshop_id": record.workshop_id,
                "workstation_id": record.workstation_id,
                "record_date": record.record_date.isoformat() if record.record_date else None,
                "shift": record.shift,
                "efficiency": float(record.efficiency),
                "quality_rate": float(record.quality_rate),
                "utilization_rate": float(record.utilization_rate),
                "overall_efficiency": float(record.overall_efficiency),
                "standard_hours": float(record.standard_hours),
                "actual_hours": float(record.actual_hours),
                "completed_qty": record.completed_qty,
                "qualified_qty": record.qualified_qty,
                "defect_qty": record.defect_qty,
                "skill_level": record.skill_level,
                "efficiency_level": _get_efficiency_level(float(record.efficiency)),
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


def _get_efficiency_level(efficiency: float) -> str:
    """获取效率等级"""
    if efficiency >= 120:
        return "优秀"
    elif efficiency >= 100:
        return "良好"
    elif efficiency >= 80:
        return "正常"
    else:
        return "偏低"
