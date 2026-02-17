# -*- coding: utf-8 -*-
"""
产能计算接口
"""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.production import (
    Equipment,
    EquipmentOEERecord,
    Worker,
    WorkerEfficiencyRecord,
)
from app.utils.db_helpers import save_obj

router = APIRouter()


class OEECalculateRequest(BaseModel):
    """OEE计算请求"""
    equipment_id: int
    record_date: date
    shift: Optional[str] = None
    planned_production_time: int  # 分钟
    planned_downtime: int = 0  # 分钟
    unplanned_downtime: int = 0  # 分钟
    ideal_cycle_time: float  # 分钟/件
    actual_output: int  # 件
    target_output: int  # 件
    qualified_qty: int  # 件
    defect_qty: int = 0  # 件
    rework_qty: int = 0  # 件
    operator_id: Optional[int] = None
    work_order_id: Optional[int] = None
    downtime_reason: Optional[str] = None
    remark: Optional[str] = None


class WorkerEfficiencyCalculateRequest(BaseModel):
    """工人效率计算请求"""
    worker_id: int
    record_date: date
    shift: Optional[str] = None
    standard_hours: float  # 小时
    actual_hours: float  # 小时
    completed_qty: int  # 件
    qualified_qty: int  # 件
    defect_qty: int = 0  # 件
    idle_hours: float = 0  # 小时
    break_hours: float = 0  # 小时
    work_order_id: Optional[int] = None
    remark: Optional[str] = None


@router.post("/oee/calculate")
async def calculate_oee(
    request: OEECalculateRequest,
    db: Session = Depends(get_db),
):
    """
    触发OEE计算
    
    OEE计算公式(严格遵循国际标准):
    1. 可用率(Availability) = 运行时间 / 计划生产时间
    2. 性能率(Performance) = (理想周期时间 × 实际产量) / 运行时间
    3. 合格率(Quality) = 合格数量 / 实际产量
    4. OEE = 可用率 × 性能率 × 合格率
    """
    # 验证设备存在
    equipment = db.query(Equipment).filter(Equipment.id == request.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 计算运行时间
    operating_time = request.planned_production_time - request.planned_downtime - request.unplanned_downtime
    
    if operating_time <= 0:
        raise HTTPException(status_code=400, detail="运行时间必须大于0")
    
    if request.actual_output <= 0:
        raise HTTPException(status_code=400, detail="实际产量必须大于0")
    
    # 1. 计算可用率
    availability = (operating_time / request.planned_production_time) * 100
    
    # 2. 计算性能率
    ideal_production_time = request.ideal_cycle_time * request.actual_output
    performance = (ideal_production_time / operating_time) * 100
    
    # 限制性能率不超过100%(如果超过,说明实际比理想更快,可能是数据错误)
    if performance > 100:
        performance = 100
    
    # 3. 计算合格率
    quality = (request.qualified_qty / request.actual_output) * 100
    
    # 4. 计算OEE
    oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
    
    # 5. 计算损失
    availability_loss = request.planned_downtime + request.unplanned_downtime
    performance_loss = operating_time - int(ideal_production_time)
    quality_loss = int((request.defect_qty + request.rework_qty) * request.ideal_cycle_time)
    
    # 创建OEE记录
    oee_record = EquipmentOEERecord(
        equipment_id=request.equipment_id,
        workshop_id=equipment.workshop_id,
        record_date=request.record_date,
        shift=request.shift,
        planned_production_time=request.planned_production_time,
        planned_downtime=request.planned_downtime,
        unplanned_downtime=request.unplanned_downtime,
        operating_time=operating_time,
        ideal_cycle_time=request.ideal_cycle_time,
        actual_output=request.actual_output,
        target_output=request.target_output,
        qualified_qty=request.qualified_qty,
        defect_qty=request.defect_qty,
        rework_qty=request.rework_qty,
        availability=round(availability, 2),
        performance=round(performance, 2),
        quality=round(quality, 2),
        oee=round(oee, 2),
        availability_loss=availability_loss,
        performance_loss=performance_loss,
        quality_loss=quality_loss,
        operator_id=request.operator_id,
        work_order_id=request.work_order_id,
        downtime_reason=request.downtime_reason,
        remark=request.remark,
        is_auto_calculated=True,
        calculated_at=datetime.now(),
    )
    
    save_obj(db, oee_record)
    
    return {
        "code": 200,
        "message": "OEE计算成功",
        "data": {
            "id": oee_record.id,
            "oee": float(oee_record.oee),
            "availability": float(oee_record.availability),
            "performance": float(oee_record.performance),
            "quality": float(oee_record.quality),
            "oee_level": _get_oee_level(float(oee_record.oee)),
            "losses": {
                "availability_loss": availability_loss,
                "performance_loss": performance_loss,
                "quality_loss": quality_loss,
                "total_loss": availability_loss + performance_loss + quality_loss,
            },
        },
    }


@router.post("/worker-efficiency/calculate")
async def calculate_worker_efficiency(
    request: WorkerEfficiencyCalculateRequest,
    db: Session = Depends(get_db),
):
    """
    计算工人效率
    
    工人效率 = 标准工时 / 实际工时 × 100%
    """
    # 验证工人存在
    worker = db.query(Worker).filter(Worker.id == request.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="工人不存在")
    
    if request.actual_hours <= 0:
        raise HTTPException(status_code=400, detail="实际工时必须大于0")
    
    if request.completed_qty <= 0:
        raise HTTPException(status_code=400, detail="完成数量必须大于0")
    
    # 1. 计算工作效率
    efficiency = (request.standard_hours / request.actual_hours) * 100
    
    # 2. 计算合格率
    quality_rate = (request.qualified_qty / request.completed_qty) * 100
    
    # 3. 计算利用率
    effective_hours = request.actual_hours - request.idle_hours - request.break_hours
    utilization_rate = (effective_hours / request.actual_hours) * 100
    
    # 4. 计算综合效率
    overall_efficiency = (efficiency / 100) * (quality_rate / 100) * (utilization_rate / 100) * 100
    
    # 创建效率记录
    efficiency_record = WorkerEfficiencyRecord(
        worker_id=request.worker_id,
        record_date=request.record_date,
        shift=request.shift,
        standard_hours=request.standard_hours,
        actual_hours=request.actual_hours,
        idle_hours=request.idle_hours,
        break_hours=request.break_hours,
        completed_qty=request.completed_qty,
        qualified_qty=request.qualified_qty,
        defect_qty=request.defect_qty,
        efficiency=round(efficiency, 2),
        quality_rate=round(quality_rate, 2),
        utilization_rate=round(utilization_rate, 2),
        overall_efficiency=round(overall_efficiency, 2),
        work_order_id=request.work_order_id,
        remark=request.remark,
        is_auto_calculated=True,
        calculated_at=datetime.now(),
    )
    
    save_obj(db, efficiency_record)
    
    return {
        "code": 200,
        "message": "工人效率计算成功",
        "data": {
            "id": efficiency_record.id,
            "efficiency": float(efficiency_record.efficiency),
            "quality_rate": float(efficiency_record.quality_rate),
            "utilization_rate": float(efficiency_record.utilization_rate),
            "overall_efficiency": float(efficiency_record.overall_efficiency),
            "efficiency_level": _get_efficiency_level(float(efficiency_record.efficiency)),
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
