# -*- coding: utf-8 -*-
"""
装配工艺齐套率 API
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.assembly_kit_service import AssemblyKitService

router = APIRouter()


@router.get("/stages", summary="获取装配阶段定义")
def get_assembly_stages(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取所有装配阶段定义"""
    service = AssemblyKitService(db)
    return {"stages": service.get_assembly_stages()}


@router.post("/bom/{bom_id}/auto-assign", summary="自动分配物料到工艺阶段")
def auto_assign_materials(
    bom_id: int = Path(..., description="BOM ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动分配 BOM 物料到装配工艺阶段
    
    基于物料分类映射表自动分配
    """
    service = AssemblyKitService(db)
    result = service.auto_assign_materials_to_stages(bom_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/project/{project_id}/kit-rate", summary="计算分阶段齐套率")
def calculate_kit_rate(
    project_id: int = Path(..., description="项目 ID"),
    machine_id: Optional[int] = Query(None, description="机台 ID"),
    stage_code: Optional[str] = Query(None, description="阶段编码"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算分阶段齐套率
    
    返回各阶段的：
    - 整体齐套率
    - 阻塞性齐套率
    - 综合齐套率
    """
    service = AssemblyKitService(db)
    result = service.calculate_stage_kit_rate(project_id, machine_id, stage_code)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/project/{project_id}/analyze", summary="保存齐套分析结果")
def analyze_readiness(
    project_id: int = Path(..., description="项目 ID"),
    machine_id: Optional[int] = Query(None, description="机台 ID"),
    planned_start_date: Optional[str] = Query(None, description="计划开工日期"),
    target_stage: Optional[str] = Query(None, description="目标阶段"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    保存齐套分析结果
    
    自动计算并保存各阶段齐套率
    """
    from datetime import date
    
    service = AssemblyKitService(db)
    
    # 解析日期
    start_date = None
    if planned_start_date:
        start_date = date.fromisoformat(planned_start_date)
    
    readiness = service.save_readiness_analysis(
        project_id=project_id,
        machine_id=machine_id,
        planned_start_date=start_date,
        target_stage=target_stage,
    )
    
    return {
        "readiness_id": readiness.id,
        "readiness_no": readiness.readiness_no,
        "overall_kit_rate": float(readiness.overall_kit_rate),
        "blocking_kit_rate": float(readiness.blocking_kit_rate),
        "total_items": readiness.total_items,
        "fulfilled_items": readiness.fulfilled_items,
        "shortage_items": readiness.shortage_items,
    }


@router.get("/project/{project_id}/time-based-kit-rate", summary="基于时间的齐套率预警")
def calculate_time_based_kit_rate(
    project_id: int = Path(..., description="项目 ID"),
    machine_id: Optional[int] = Query(None, description="机台 ID"),
    planned_start_date: Optional[str] = Query(None, description="计划开工日期 (YYYY-MM-DD)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    基于时间的齐套率预警
    
    考虑因素：
    1. 采购提前期（从下单到到货的天数）
    2. 生产周期（物料齐套到生产完成的天数）
    3. 计划开工日期
    
    预警级别：
    - L1: 停工预警（已延期或 3 天内开工但物料未到）
    - L2: 紧急预警（7 天内开工，风险高）
    - L3: 提前预警（需注意）
    - L4: 常规预警
    """
    from datetime import date
    
    # 解析计划开工日期
    start_date = None
    if planned_start_date:
        start_date = date.fromisoformat(planned_start_date)
    
    service = AssemblyKitService(db)
    result = service.calculate_time_based_kit_rate(
        project_id,
        machine_id,
        start_date,
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/project/{project_id}/enhanced-kit-rate", summary="增强版时间预警（含采购承诺 + 春节）")
def calculate_enhanced_kit_rate(
    project_id: int = Path(..., description="项目 ID"),
    machine_id: Optional[int] = Query(None, description="机台 ID"),
    planned_start_date: Optional[str] = Query(None, description="计划开工日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    增强版基于时间的齐套率预警
    
    考虑因素：
    1. 采购承诺交期（优先级最高，采购员根据供应商承诺填写）
    2. 相似物料历史数据（无承诺交期时，参考同分类/同供应商物料）
    3. 春节假期因素（自动检测并增加提前期）
    
    返回：
    - 各阶段齐套率
    - 预计到货时间（优先承诺交期）
    - 春节影响说明
    - 预警级别（L1-L4）
    """
    from datetime import date
    from app.services.assembly_kit_service_enhanced import AssemblyKitServiceEnhanced
    
    # 解析计划开工日期
    start_date = None
    if planned_start_date:
        start_date = date.fromisoformat(planned_start_date)
    
    service = AssemblyKitServiceEnhanced(db)
    result = service.calculate_enhanced_time_based_kit_rate(
        project_id,
        machine_id,
        start_date,
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
