# -*- coding: utf-8 -*-
"""
质量管理 API 路由
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.production import DefectAnalysis
from app.schemas.production.quality import (
    BatchTracingResponse,
    CorrectiveActionCreate,
    DefectAnalysisCreate,
    DefectAnalysisResponse,
    ParetoAnalysisResponse,
    QualityAlertListResponse,
    QualityAlertRuleCreate,
    QualityAlertRuleResponse,
    QualityInspectionCreate,
    QualityInspectionListResponse,
    QualityInspectionResponse,
    QualityStatisticsResponse,
    QualityTrendResponse,
    ReworkOrderCompleteRequest,
    ReworkOrderCreate,
    ReworkOrderListResponse,
    ReworkOrderResponse,
    SPCDataResponse,
)
from app.services.production.quality_service import ProductionQualityService
from app.services.quality_service import QualityService
from app.utils.db_helpers import get_or_404

router = APIRouter()


# ==================== 质检记录 ====================

@router.post("/inspection", response_model=QualityInspectionResponse, summary="创建质检记录")
def create_quality_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_data: QualityInspectionCreate,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    创建质检记录

    - **work_order_id**: 工单ID (可选)
    - **material_id**: 物料ID (可选)
    - **inspection_type**: 检验类型 (IQC/IPQC/FQC/OQC)
    - **inspection_qty**: 检验数量
    - **qualified_qty**: 合格数量
    - **defect_qty**: 不良数量
    - **measured_value**: 测量值 (用于SPC分析)
    """
    try:
        inspection = QualityService.create_inspection(
            db=db,
            inspection_data=inspection_data,
            current_user_id=current_user["id"]
        )
        return inspection
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inspection", response_model=QualityInspectionListResponse, summary="质检记录列表")
def list_quality_inspections(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    material_id: Optional[int] = None,
    inspection_type: Optional[str] = None,
    inspection_result: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    查询质检记录列表

    支持按物料、检验类型、检验结果、日期范围筛选
    """
    service = ProductionQualityService(db)
    return service.list_inspections(
        skip=skip,
        limit=limit,
        material_id=material_id,
        inspection_type=inspection_type,
        inspection_result=inspection_result,
        start_date=start_date,
        end_date=end_date,
    )


# ==================== 质量趋势分析 ====================

@router.get("/trend", response_model=QualityTrendResponse, summary="质量趋势分析")
def get_quality_trend(
    *,
    db: Session = Depends(deps.get_db),
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    inspection_type: Optional[str] = Query(None, description="检验类型筛选"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="聚合维度"),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    质量趋势分析

    - 按日/周/月聚合质检数据
    - 计算不良率趋势
    - 提供移动平均预测
    """
    try:
        result = QualityService.get_quality_trend(
            db=db,
            start_date=start_date,
            end_date=end_date,
            material_id=material_id,
            inspection_type=inspection_type,
            group_by=group_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 不良品根因分析 ====================

@router.post("/defect-analysis", response_model=DefectAnalysisResponse, summary="创建不良品根因分析")
def create_defect_analysis(
    *,
    db: Session = Depends(deps.get_db),
    analysis_data: DefectAnalysisCreate,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    创建不良品根因分析

    基于5M1E方法:
    - Man (人)
    - Machine (机)
    - Material (料)
    - Method (法)
    - Measurement (测)
    - Environment (环)
    """
    try:
        analysis = QualityService.create_defect_analysis(
            db=db,
            analysis_data=analysis_data,
            current_user_id=current_user["id"]
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/defect-analysis/{analysis_id}", response_model=DefectAnalysisResponse, summary="获取不良品分析详情")
def get_defect_analysis(
    *,
    db: Session = Depends(deps.get_db),
    analysis_id: int,
    current_user: dict = Depends(deps.get_current_user)
):
    """获取不良品分析详情"""
    analysis = get_or_404(db, DefectAnalysis, analysis_id, detail="不良品分析记录不存在")
    return analysis


# ==================== 质量预警 ====================

@router.get("/alerts", response_model=QualityAlertListResponse, summary="质量预警列表")
def list_quality_alerts(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    alert_level: Optional[str] = None,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    质量预警列表

    显示最近触发的质量预警
    """
    service = ProductionQualityService(db)
    return service.list_alerts(skip=skip, limit=limit, alert_level=alert_level)


@router.post("/alert-rules", response_model=QualityAlertRuleResponse, summary="创建质量预警规则")
def create_quality_alert_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_data: QualityAlertRuleCreate,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    创建质量预警规则

    支持的预警类型:
    - DEFECT_RATE: 不良率预警
    - SPC_UCL: SPC控制上限预警
    - SPC_LCL: SPC控制下限预警
    - TREND: 趋势预警
    """
    service = ProductionQualityService(db)
    return service.create_alert_rule(rule_data, current_user_id=current_user["id"])


@router.get("/alert-rules", response_model=list, summary="质量预警规则列表")
def list_quality_alert_rules(
    db: Session = Depends(deps.get_db),
    enabled: Optional[int] = None,
    current_user: dict = Depends(deps.get_current_user)
):
    """查询质量预警规则列表"""
    service = ProductionQualityService(db)
    return service.list_alert_rules(enabled=enabled)


# ==================== SPC控制图 ====================

@router.get("/spc", response_model=SPCDataResponse, summary="SPC控制图数据")
def get_spc_data(
    *,
    db: Session = Depends(deps.get_db),
    material_id: int = Query(..., description="物料ID"),
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    inspection_type: Optional[str] = Query(None, description="检验类型"),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    获取SPC控制图数据

    - 计算3σ控制限 (UCL, CL, LCL)
    - 识别失控点
    - 计算过程能力指数Cpk
    """
    try:
        result = QualityService.calculate_spc_control_limits(
            db=db,
            material_id=material_id,
            start_date=start_date,
            end_date=end_date,
            inspection_type=inspection_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 返工管理 ====================

@router.post("/rework", response_model=ReworkOrderResponse, summary="创建返工单")
def create_rework_order(
    *,
    db: Session = Depends(deps.get_db),
    rework_data: ReworkOrderCreate,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    创建返工单

    - 关联原工单和质检记录
    - 支持派工和进度跟踪
    - 记录返工成本
    """
    try:
        rework_order = QualityService.create_rework_order(
            db=db,
            rework_data=rework_data.model_dump(),
            current_user_id=current_user["id"]
        )
        return rework_order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/rework/{id}/complete", response_model=ReworkOrderResponse, summary="完成返工")
def complete_rework_order(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    completion_data: ReworkOrderCompleteRequest,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    完成返工单

    - 记录完成数量、合格数量、报废数量
    - 记录实际工时和返工成本
    """
    try:
        rework_order = QualityService.complete_rework_order(
            db=db,
            rework_order_id=id,
            completion_data=completion_data.model_dump()
        )
        return rework_order
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rework", response_model=ReworkOrderListResponse, summary="返工单列表")
def list_rework_orders(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: dict = Depends(deps.get_current_user)
):
    """查询返工单列表"""
    service = ProductionQualityService(db)
    return service.list_rework_orders(skip=skip, limit=limit, status=status)


# ==================== 帕累托分析 ====================

@router.get("/pareto", response_model=ParetoAnalysisResponse, summary="帕累托分析")
def get_pareto_analysis(
    *,
    db: Session = Depends(deps.get_db),
    start_date: datetime = Query(..., description="开始日期"),
    end_date: datetime = Query(..., description="结束日期"),
    material_id: Optional[int] = Query(None, description="物料ID筛选"),
    top_n: int = Query(10, ge=1, le=50, description="显示Top N不良"),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    帕累托分析 (80/20原则)

    - 识别主要不良类型
    - 累计百分比分析
    - 找出占80%不良的关键类型
    """
    try:
        result = QualityService.pareto_analysis(
            db=db,
            start_date=start_date,
            end_date=end_date,
            material_id=material_id,
            top_n=top_n
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 质量统计看板 ====================

@router.get("/statistics", response_model=QualityStatisticsResponse, summary="质量统计看板")
def get_quality_statistics(
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    质量统计看板

    - 总体质量指标
    - Top不良类型
    - 最近7天趋势
    - 返工统计
    - 预警统计
    """
    try:
        result = QualityService.get_quality_statistics(db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 批次质量追溯 ====================

@router.get("/batch-tracing", response_model=BatchTracingResponse, summary="批次质量追溯")
def get_batch_tracing(
    *,
    db: Session = Depends(deps.get_db),
    batch_no: str = Query(..., description="批次号"),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    批次质量追溯

    - 查询批次所有质检记录
    - 关联的不良品分析
    - 关联的返工单
    - 批次质量统计
    """
    try:
        result = QualityService.batch_tracing(db=db, batch_no=batch_no)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 纠正措施 ====================

@router.post("/corrective-action", response_model=dict, summary="创建纠正措施")
def create_corrective_action(
    *,
    db: Session = Depends(deps.get_db),
    action_data: CorrectiveActionCreate,
    current_user: dict = Depends(deps.get_current_user)
):
    """
    创建纠正措施记录

    - 关联不良品分析
    - 指定责任人和完成期限
    - 跟踪措施执行和验证
    """
    service = ProductionQualityService(db)
    return service.create_corrective_action(action_data)
