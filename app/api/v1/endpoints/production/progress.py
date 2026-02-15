# -*- coding: utf-8 -*-
"""
生产进度实时跟踪系统 - API接口
实现8个核心接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import check_permissions
from app.models.user import User
from app.schemas.production_progress import (
    BottleneckWorkstation,
    ProductionProgressLogCreate,
    ProductionProgressLogResponse,
    ProgressAlertDismiss,
    ProgressAlertResponse,
    ProgressDeviation,
    RealtimeProgressOverview,
    WorkOrderProgressTimeline,
    WorkstationStatusResponse,
)
from app.services.production_progress_service import ProductionProgressService

router = APIRouter()


@router.get(
    "/realtime",
    response_model=RealtimeProgressOverview,
    summary="实时进度总览",
    description="获取生产进度实时总览数据，包含工单数量、工位状态、预警统计等",
)
async def get_realtime_progress(
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    workstation_id: Optional[int] = Query(None, description="工位ID筛选"),
    status: Optional[str] = Query(None, description="工单状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **GET /production/progress/realtime**
    
    获取实时进度总览：
    - 工单统计（总数、进行中、今日完成、延期）
    - 工位统计（活跃、空闲、瓶颈）
    - 预警统计（总数、严重预警）
    - 整体指标（进度、产能利用率、效率）
    
    **权限要求**: production:read
    """
    check_permissions(current_user, ["production:read"])
    
    service = ProductionProgressService(db)
    overview = service.get_realtime_overview(workshop_id=workshop_id)
    
    return overview


@router.get(
    "/work-orders/{work_order_id}/timeline",
    response_model=WorkOrderProgressTimeline,
    summary="工单进度时间线",
    description="获取指定工单的完整进度时间线和预警历史",
)
async def get_work_order_timeline(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **GET /production/progress/work-orders/{id}/timeline**
    
    获取工单进度时间线：
    - 工单基本信息
    - 进度变化历史
    - 预警记录
    - 计划 vs 实际对比
    
    **权限要求**: production:read
    """
    check_permissions(current_user, ["production:read"])
    
    service = ProductionProgressService(db)
    timeline = service.get_work_order_timeline(work_order_id)
    
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工单 {work_order_id} 不存在"
        )
    
    return timeline


@router.get(
    "/workstations/{workstation_id}/realtime",
    response_model=WorkstationStatusResponse,
    summary="工位实时状态",
    description="获取指定工位的实时运行状态和产能信息",
)
async def get_workstation_realtime(
    workstation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **GET /production/progress/workstations/{id}/realtime**
    
    获取工位实时状态：
    - 当前状态（空闲/忙碌/暂停/维护/离线）
    - 当前工单和操作工
    - 今日产量和目标
    - 产能利用率
    - 效率和质量指标
    - 瓶颈状态
    
    **权限要求**: production:read
    """
    check_permissions(current_user, ["production:read"])
    
    service = ProductionProgressService(db)
    ws_status = service.get_workstation_realtime(workstation_id)
    
    if not ws_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工位 {workstation_id} 状态不存在"
        )
    
    return ws_status


@router.post(
    "/log",
    response_model=ProductionProgressLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="记录进度日志",
    description="记录工单的进度变化，自动计算偏差并触发预警规则",
)
async def create_progress_log(
    log_data: ProductionProgressLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **POST /production/progress/log**
    
    记录进度日志：
    - 自动计算进度偏差（实际 vs 计划）
    - 更新工单进度和状态
    - 更新工位状态
    - 触发预警规则评估
    
    **权限要求**: production:write
    """
    check_permissions(current_user, ["production:write"])
    
    service = ProductionProgressService(db)
    
    try:
        progress_log = service.create_progress_log(log_data, current_user.id)
        return progress_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/bottlenecks",
    response_model=List[BottleneckWorkstation],
    summary="瓶颈工位识别",
    description="基于产能利用率识别瓶颈工位，支持分级预警",
)
async def get_bottleneck_workstations(
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    min_level: int = Query(1, ge=1, le=3, description="最小瓶颈等级（1-轻度，2-中度，3-严重）"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **GET /production/progress/bottlenecks**
    
    识别瓶颈工位：
    - 基于产能利用率算法
    - 分级识别（轻度/中度/严重）
    - 提供瓶颈原因分析
    - 显示排队工单数量
    
    **瓶颈判断规则**:
    - 轻度(level=1): 产能利用率 > 90%
    - 中度(level=2): 产能利用率 > 95% 且有排队工单
    - 严重(level=3): 产能利用率 > 98% 且排队工单 > 3
    
    **权限要求**: production:read
    """
    check_permissions(current_user, ["production:read"])
    
    service = ProductionProgressService(db)
    bottlenecks = service.identify_bottlenecks(
        workshop_id=workshop_id,
        min_level=min_level
    )
    
    return bottlenecks[:limit]


@router.get(
    "/alerts",
    response_model=List[ProgressAlertResponse],
    summary="进度预警列表",
    description="获取进度预警列表，支持多维度筛选",
)
async def get_progress_alerts(
    work_order_id: Optional[int] = Query(None, description="工单ID"),
    workstation_id: Optional[int] = Query(None, description="工位ID"),
    alert_type: Optional[str] = Query(None, description="预警类型：DELAY/BOTTLENECK/QUALITY/EFFICIENCY"),
    alert_level: Optional[str] = Query(None, description="预警级别：INFO/WARNING/CRITICAL/URGENT"),
    status: Optional[str] = Query(None, description="状态：ACTIVE/ACKNOWLEDGED/RESOLVED/DISMISSED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **GET /production/progress/alerts**
    
    获取进度预警列表：
    - 延期预警（进度偏差）
    - 瓶颈预警（产能利用率）
    - 质量预警（合格率）
    - 效率预警（生产效率）
    
    **预警规则**:
    - DELAY: 进度偏差 < -10%（WARNING）或 < -20%（CRITICAL）
    - BOTTLENECK: 工位瓶颈等级 ≥ 1
    - QUALITY: 合格率 < 95%
    - EFFICIENCY: 生产效率 < 80%
    
    **权限要求**: production:read
    """
    check_permissions(current_user, ["production:read"])
    
    service = ProductionProgressService(db)
    alerts = service.get_alerts(
        work_order_id=work_order_id,
        workstation_id=workstation_id,
        alert_type=alert_type,
        alert_level=alert_level,
        status=status
    )
    
    return alerts


@router.post(
    "/alerts/{alert_id}/dismiss",
    status_code=status.HTTP_200_OK,
    summary="关闭预警",
    description="关闭指定的进度预警，可添加处理说明",
)
async def dismiss_progress_alert(
    alert_id: int,
    dismiss_data: ProgressAlertDismiss,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **POST /production/progress/alerts/{id}/dismiss**
    
    关闭预警：
    - 更新预警状态为 DISMISSED
    - 记录关闭时间和操作人
    - 可添加处理说明
    
    **权限要求**: production:write
    """
    check_permissions(current_user, ["production:write"])
    
    service = ProductionProgressService(db)
    success = service.dismiss_alert(
        alert_id=alert_id,
        user_id=current_user.id,
        note=dismiss_data.resolution_note
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"预警 {alert_id} 不存在"
        )
    
    return {"message": "预警已关闭", "alert_id": alert_id}


@router.get(
    "/deviation",
    response_model=List[ProgressDeviation],
    summary="进度偏差分析",
    description="分析工单进度偏差，识别延期风险",
)
async def get_progress_deviation(
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    min_deviation: int = Query(10, ge=0, description="最小偏差(%)"),
    only_delayed: bool = Query(True, description="只显示延期工单"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **GET /production/progress/deviation**
    
    进度偏差分析：
    - 计划进度 vs 实际进度
    - 偏差百分比
    - 延期风险评估（LOW/MEDIUM/HIGH/CRITICAL）
    - 预计完成日期
    - 延期天数
    
    **偏差计算**:
    - 基于计划开始/结束日期线性插值
    - 偏差 = 实际进度 - 计划进度
    - 偏差 < -5% 认为延期
    
    **权限要求**: production:read
    """
    check_permissions(current_user, ["production:read"])
    
    service = ProductionProgressService(db)
    deviations = service.get_progress_deviations(
        workshop_id=workshop_id,
        min_deviation=min_deviation,
        only_delayed=only_delayed
    )
    
    return deviations
