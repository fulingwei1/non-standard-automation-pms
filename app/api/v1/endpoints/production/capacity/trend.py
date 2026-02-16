# -*- coding: utf-8 -*-
"""
产能趋势分析接口
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    EquipmentOEERecord,
    WorkerEfficiencyRecord,
)

router = APIRouter()


@router.get("/trend")
async def get_capacity_trend(
    type: str = Query("oee", description="类型: oee/efficiency"),
    equipment_id: Optional[int] = Query(None, description="设备ID"),
    worker_id: Optional[int] = Query(None, description="工人ID"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    granularity: str = Query("day", description="粒度: day/week/month"),
    db: Session = Depends(get_db),
):
    """
    产能趋势分析
    
    分析产能随时间的变化趋势
    """
    # 默认查询最近90天
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()
    
    if type == "oee":
        # OEE趋势
        filters = [
            EquipmentOEERecord.record_date >= start_date,
            EquipmentOEERecord.record_date <= end_date,
        ]
        
        if equipment_id:
            filters.append(EquipmentOEERecord.equipment_id == equipment_id)
        if workshop_id:
            filters.append(EquipmentOEERecord.workshop_id == workshop_id)
        
        if granularity == "day":
            # 按天
            results = (
                db.query(
                    EquipmentOEERecord.record_date,
                    func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                    func.avg(EquipmentOEERecord.availability).label('avg_availability'),
                    func.avg(EquipmentOEERecord.performance).label('avg_performance'),
                    func.avg(EquipmentOEERecord.quality).label('avg_quality'),
                    func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                )
                .filter(and_(*filters))
                .group_by(EquipmentOEERecord.record_date)
                .order_by(EquipmentOEERecord.record_date)
                .all()
            )
            
            items = [
                {
                    "date": row.record_date.isoformat(),
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "avg_availability": float(row.avg_availability) if row.avg_availability else 0,
                    "avg_performance": float(row.avg_performance) if row.avg_performance else 0,
                    "avg_quality": float(row.avg_quality) if row.avg_quality else 0,
                    "total_output": row.total_output or 0,
                }
                for row in results
            ]
            
        elif granularity == "week":
            # 按周
            results = (
                db.query(
                    func.date_format(EquipmentOEERecord.record_date, '%Y-%u').label('week'),
                    func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                    func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                )
                .filter(and_(*filters))
                .group_by(func.date_format(EquipmentOEERecord.record_date, '%Y-%u'))
                .order_by(func.date_format(EquipmentOEERecord.record_date, '%Y-%u'))
                .all()
            )
            
            items = [
                {
                    "period": row.week,
                    "avg_oee": float(row.avg_oee) if row.avg_oee else 0,
                    "total_output": row.total_output or 0,
                }
                for row in results
            ]
            
        else:  # month
            # 按月
            results = (
                db.query(
                    func.date_format(EquipmentOEERecord.record_date, '%Y-%m').label('month'),
                    func.avg(EquipmentOEERecord.oee).label('avg_oee'),
                    func.sum(EquipmentOEERecord.actual_output).label('total_output'),
                )
                .filter(and_(*filters))
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
            
    elif type == "efficiency":
        # 工人效率趋势
        filters = [
            WorkerEfficiencyRecord.record_date >= start_date,
            WorkerEfficiencyRecord.record_date <= end_date,
        ]
        
        if worker_id:
            filters.append(WorkerEfficiencyRecord.worker_id == worker_id)
        if workshop_id:
            filters.append(WorkerEfficiencyRecord.workshop_id == workshop_id)
        
        if granularity == "day":
            results = (
                db.query(
                    WorkerEfficiencyRecord.record_date,
                    func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                    func.avg(WorkerEfficiencyRecord.quality_rate).label('avg_quality_rate'),
                    func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
                )
                .filter(and_(*filters))
                .group_by(WorkerEfficiencyRecord.record_date)
                .order_by(WorkerEfficiencyRecord.record_date)
                .all()
            )
            
            items = [
                {
                    "date": row.record_date.isoformat(),
                    "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                    "avg_quality_rate": float(row.avg_quality_rate) if row.avg_quality_rate else 0,
                    "total_completed": row.total_completed or 0,
                }
                for row in results
            ]
        else:
            # 按周或月
            date_format = '%Y-%u' if granularity == 'week' else '%Y-%m'
            results = (
                db.query(
                    func.date_format(WorkerEfficiencyRecord.record_date, date_format).label('period'),
                    func.avg(WorkerEfficiencyRecord.efficiency).label('avg_efficiency'),
                    func.sum(WorkerEfficiencyRecord.completed_qty).label('total_completed'),
                )
                .filter(and_(*filters))
                .group_by(func.date_format(WorkerEfficiencyRecord.record_date, date_format))
                .order_by(func.date_format(WorkerEfficiencyRecord.record_date, date_format))
                .all()
            )
            
            items = [
                {
                    "period": row.period,
                    "avg_efficiency": float(row.avg_efficiency) if row.avg_efficiency else 0,
                    "total_completed": row.total_completed or 0,
                }
                for row in results
            ]
    else:
        return {
            "code": 400,
            "message": "不支持的类型",
            "data": None,
        }
    
    # 计算趋势统计
    if items and len(items) >= 2:
        values = [item.get('avg_oee', item.get('avg_efficiency', 0)) for item in items]
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        
        trend = "上升" if avg_second > avg_first * 1.05 else ("下降" if avg_second < avg_first * 0.95 else "平稳")
        change_percent = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
    else:
        trend = "数据不足"
        change_percent = 0
    
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "type": type,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": granularity,
            },
            "items": items,
            "trend_analysis": {
                "trend": trend,
                "change_percent": round(change_percent, 2),
            },
        },
    }
