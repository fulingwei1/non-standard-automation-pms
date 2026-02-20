# -*- coding: utf-8 -*-
"""
物料跟踪系统 API
Team 5: 物料全流程追溯
"""
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.schemas.response import (
    create_pagination_response,
    create_success_response,
)
from app.models.user import User
from app.services.production.material_tracking.material_tracking_service import (
    MaterialTrackingService,
)

router = APIRouter()


# ================== 1. 实时库存查询 ==================
@router.get("/realtime-stock", summary="实时库存查询")
def get_realtime_stock(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    material_id: Optional[int] = Query(None, description="物料ID"),
    material_code: Optional[str] = Query(None, description="物料编码"),
    category_id: Optional[int] = Query(None, description="物料分类ID"),
    warehouse_location: Optional[str] = Query(None, description="仓库位置"),
    status: Optional[str] = Query(None, description="批次状态"),
    low_stock_only: bool = Query(False, description="仅显示低库存"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """
    实时库存查询 - 支持多维度筛选

    - 按物料、分类、仓库位置筛选
    - 显示每个物料的批次明细
    - 支持低库存预警
    """
    service = MaterialTrackingService(db)
    result = service.get_realtime_stock(
        material_id=material_id,
        material_code=material_code,
        category_id=category_id,
        warehouse_location=warehouse_location,
        status=status,
        low_stock_only=low_stock_only,
        page=page,
        page_size=page_size,
    )
    return create_pagination_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# ================== 2. 记录物料消耗 ==================
@router.post("/consumption", summary="记录物料消耗")
def create_consumption(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    consumption_data: Dict[str, Any],
) -> Any:
    """
    记录物料消耗

    必填字段:
    - material_id: 物料ID
    - consumption_qty: 消耗数量
    - consumption_type: 消耗类型 (PRODUCTION/TESTING/WASTE/REWORK/OTHER)

    可选字段:
    - batch_id: 批次ID
    - work_order_id: 工单ID
    - project_id: 项目ID
    - standard_qty: 标准消耗数量 (用于浪费识别)
    - barcode: 扫描条码
    """
    service = MaterialTrackingService(db)
    data = service.create_consumption(consumption_data, current_user.id)
    return create_success_response(data=data, message="物料消耗记录成功")


# ================== 3. 消耗分析 ==================
@router.get("/consumption-analysis", summary="物料消耗分析")
def get_consumption_analysis(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    material_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    work_order_id: Optional[int] = Query(None),
    consumption_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: str = Query("day", description="分组方式: day/week/month/material/project"),
) -> Any:
    """
    物料消耗分析

    - 支持按时间、物料、项目、工单分析
    - 支持按日/周/月聚合
    - 包含浪费统计
    """
    service = MaterialTrackingService(db)
    data = service.get_consumption_analysis(
        material_id=material_id,
        project_id=project_id,
        work_order_id=work_order_id,
        consumption_type=consumption_type,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
    )
    return create_success_response(data=data)


# ================== 4. 缺料预警列表 ==================
@router.get("/alerts", summary="物料预警列表")
def get_material_alerts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    alert_type: Optional[str] = Query(None),
    alert_level: Optional[str] = Query(None),
    status: str = Query("ACTIVE", description="状态筛选"),
    material_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """
    物料预警列表

    预警类型:
    - SHORTAGE: 缺料
    - LOW_STOCK: 低库存
    - EXPIRED: 过期
    - SLOW_MOVING: 呆滞
    - HIGH_WASTE: 高浪费

    预警级别:
    - INFO: 提示
    - WARNING: 警告
    - CRITICAL: 严重
    - URGENT: 紧急
    """
    service = MaterialTrackingService(db)
    result = service.list_alerts(
        alert_type=alert_type,
        alert_level=alert_level,
        status=status,
        material_id=material_id,
        page=page,
        page_size=page_size,
    )
    return create_pagination_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# ================== 5. 配置预警规则 ==================
@router.post("/alert-rules", summary="配置物料预警规则")
def create_alert_rule(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    rule_data: Dict[str, Any],
) -> Any:
    """
    配置物料预警规则

    示例:
    {
        "rule_name": "低库存预警",
        "material_id": 1,  # 可选,NULL表示全局规则
        "alert_type": "LOW_STOCK",
        "alert_level": "WARNING",
        "threshold_type": "PERCENTAGE",  # PERCENTAGE/FIXED/DAYS
        "threshold_value": 20,  # 低于20%触发
        "safety_days": 7,
        "lead_time_days": 3,
        "buffer_ratio": 1.2
    }
    """
    service = MaterialTrackingService(db)
    data = service.create_alert_rule(rule_data, current_user.id)
    return create_success_response(data=data, message="预警规则创建成功")


# ================== 6. 物料浪费追溯 ==================
@router.get("/waste-tracing", summary="物料浪费追溯")
def get_waste_tracing(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    material_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_variance_rate: float = Query(10, description="最小差异率(%)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    """
    物料浪费追溯

    - 识别实际消耗 > 标准消耗的记录
    - 分析浪费原因
    - 支持按物料、项目、时间段查询
    """
    service = MaterialTrackingService(db)
    result = service.get_waste_records(
        material_id=material_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        min_variance_rate=min_variance_rate,
        page=page,
        page_size=page_size,
    )
    return create_pagination_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        extra_data={
            "summary": result["summary"]
        }
    )


# ================== 7. 批次追溯 ==================
@router.get("/batch-tracing", summary="物料批次追溯")
def get_batch_tracing(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    batch_no: Optional[str] = Query(None, description="批次号"),
    batch_id: Optional[int] = Query(None, description="批次ID"),
    barcode: Optional[str] = Query(None, description="条码扫描"),
    trace_direction: str = Query("forward", description="追溯方向: forward-正向, backward-反向"),
) -> Any:
    """
    批次追溯 - 支持正向和反向查询

    正向追溯: 从批次 → 消耗记录 → 产品/项目
    反向追溯: 从产品/项目 → 消耗记录 → 批次

    支持条码/二维码扫描
    """
    service = MaterialTrackingService(db)
    data = service.trace_batch(
        batch_no=batch_no,
        batch_id=batch_id,
        barcode=barcode,
        trace_direction=trace_direction,
    )
    return create_success_response(data=data)


# ================== 8. 物料成本分析 ==================
@router.get("/cost-analysis", summary="物料成本分析")
def get_cost_analysis(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    project_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    top_n: int = Query(10, description="Top N 物料"),
) -> Any:
    """
    物料成本分析

    - 按物料统计成本
    - Top N 成本物料
    - 成本趋势分析
    """
    service = MaterialTrackingService(db)
    data = service.get_cost_analysis(
        start_date=start_date,
        end_date=end_date,
        project_id=project_id,
        category_id=category_id,
        top_n=top_n,
    )
    return create_success_response(data=data)


# ================== 9. 库存周转率 ==================
@router.get("/inventory-turnover", summary="库存周转率分析")
def get_inventory_turnover(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    material_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    days: int = Query(30, description="统计天数"),
) -> Any:
    """
    库存周转率分析

    周转率 = 消耗数量 / 平均库存
    周转天数 = 天数 / 周转率
    """
    service = MaterialTrackingService(db)
    data = service.get_turnover_analysis(
        material_id=material_id,
        category_id=category_id,
        days=days,
    )
    return create_success_response(data=data)
