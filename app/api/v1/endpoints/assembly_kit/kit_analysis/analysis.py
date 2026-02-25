# -*- coding: utf-8 -*-
"""
齐套分析 - 分析执行和详情
"""
import json
import logging
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models import (
    AssemblyStage,
    BomHeader,
    BomItem,
    Machine,
    MaterialReadiness,
    Project,
    ShortageDetail,
    User,
)
from app.schemas.assembly_kit import (
    MaterialReadinessCreate,
    MaterialReadinessDetailResponse,
    MaterialReadinessResponse,
    ShortageDetailResponse,
    StageKitRate,
)
from app.schemas.common import ResponseModel

from .utils import (
    calculate_available_qty,
    calculate_estimated_ready_date,
    generate_readiness_no,
)
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis", response_model=ResponseModel)
async def execute_kit_analysis(
    request: MaterialReadinessCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("assembly_kit:create"))
):
    """执行齐套分析"""
    from app.services.assembly_kit_service import (
        analyze_bom_item,
        calculate_stage_kit_rates,
        initialize_stage_results,
        validate_analysis_inputs,
    )

    # 验证输入参数
    project, bom, machine = validate_analysis_inputs(
        db, request.project_id, request.bom_id, request.machine_id
    )

    check_date = request.check_date or date.today()

    # 获取BOM物料及装配属性
    bom_items = db.query(BomItem).filter(BomItem.bom_id == request.bom_id).all()

    if not bom_items:
        raise HTTPException(status_code=400, detail="BOM无物料明细")

    # 获取装配阶段
    stages = db.query(AssemblyStage).filter(
        AssemblyStage.is_active
    ).order_by(AssemblyStage.stage_order).all()

    stage_map = {s.stage_code: s for s in stages}

    # 初始化阶段统计
    stage_results = initialize_stage_results(stages)

    # 缺料明细
    shortage_details = []

    # 遍历BOM物料进行分析
    for bom_item in bom_items:
        detail = analyze_bom_item(
            db, bom_item, check_date, stage_map, stage_results, calculate_available_qty
        )
        if detail:
            shortage_details.append(detail)

    # 计算各阶段齐套率和是否可开始
    stage_kit_rates_data, can_proceed, first_blocked_stage, current_workable_stage, overall_stats, all_blocking_items = calculate_stage_kit_rates(
        stages, stage_results, shortage_details
    )

    # 转换为 StageKitRate 对象
    stage_kit_rates = [
        StageKitRate(**data) for data in stage_kit_rates_data
    ]

    # 计算整体齐套率
    overall_kit_rate = Decimal(overall_stats["fulfilled"] / overall_stats["total"] * 100) if overall_stats["total"] > 0 else Decimal(100)
    blocking_kit_rate = Decimal(overall_stats["blocking_fulfilled"] / overall_stats["blocking_total"] * 100) if overall_stats["blocking_total"] > 0 else Decimal(100)

    # 计算预计完全齐套日期（基于阻塞物料的预计到货日期）
    estimated_ready_date = calculate_estimated_ready_date(db, all_blocking_items, check_date)

    # 创建齐套分析记录
    readiness = MaterialReadiness(
        readiness_no=generate_readiness_no(),
        project_id=request.project_id,
        machine_id=request.machine_id,
        bom_id=request.bom_id,
        planned_start_date=getattr(request, "planned_start_date", None) or project.planned_start_date,
        overall_kit_rate=round(overall_kit_rate, 2),
        blocking_kit_rate=round(blocking_kit_rate, 2),
        stage_kit_rates=json.dumps({s.stage_code: {"kit_rate": float(s.kit_rate), "blocking_rate": float(s.blocking_rate), "can_start": s.can_start} for s in stage_kit_rates}),
        total_items=overall_stats["total"],
        fulfilled_items=overall_stats["fulfilled"],
        shortage_items=len(shortage_details),
        blocking_total=overall_stats["blocking_total"],
        blocking_fulfilled=overall_stats["blocking_fulfilled"],
        can_start=first_blocked_stage is None,
        current_workable_stage=current_workable_stage,
        first_blocked_stage=first_blocked_stage,
        estimated_ready_date=estimated_ready_date,
        analysis_time=datetime.now(),
        analyzed_by=current_user.id
    )
    db.add(readiness)
    db.flush()

    # 创建缺料明细
    for detail in shortage_details:
        shortage = ShortageDetail(
            readiness_id=readiness.id,
            bom_item_id=detail["bom_item_id"],
            material_id=detail["material_id"],
            material_code=detail["material_code"],
            material_name=detail["material_name"],
            assembly_stage=detail["assembly_stage"],
            is_blocking=detail["is_blocking"],
            required_qty=detail["required_qty"],
            stock_qty=detail["stock_qty"],
            allocated_qty=detail["allocated_qty"],
            in_transit_qty=detail["in_transit_qty"],
            available_qty=detail["available_qty"],
            shortage_qty=detail["shortage_qty"],
            alert_level=detail["alert_level"],
            expected_arrival=detail.get("expected_arrival"),
            required_date=detail.get("required_date")
        )
        db.add(shortage)

        # 如果是L1或L2级别，发送企业微信预警
        if detail["alert_level"] in ["L1", "L2"]:
            try:
                from app.services.wechat_alert_service import WeChatAlertService
                WeChatAlertService.send_shortage_alert(
                    db, shortage, detail["alert_level"]
                )
            except Exception as e:
                # 预警发送失败不影响分析结果
                logger.error(f"发送企业微信预警失败: {e}")

    db.commit()
    db.refresh(readiness)

    # 构建响应
    response_data = MaterialReadinessResponse(
        id=readiness.id,
        readiness_no=readiness.readiness_no,
        project_id=readiness.project_id,
        machine_id=readiness.machine_id,
        bom_id=readiness.bom_id,
        check_date=check_date,
        overall_kit_rate=readiness.overall_kit_rate,
        blocking_kit_rate=readiness.blocking_kit_rate,
        can_start=readiness.can_start,
        first_blocked_stage=readiness.first_blocked_stage,
        estimated_ready_date=readiness.estimated_ready_date,
        stage_kit_rates=stage_kit_rates,
        project_no=project.project_code if project else None,
        project_name=project.project_name if project else None,
        machine_no=machine.machine_code if machine else None,
        bom_no=bom.bom_no,
        analysis_time=readiness.analysis_time,
        analyzed_by=readiness.analyzed_by,
        created_at=readiness.created_at
    )

    return ResponseModel(
        code=200,
        message="齐套分析完成",
        data=response_data
    )


@router.get("/analysis/{readiness_id}", response_model=ResponseModel)
async def get_analysis_detail(
    readiness_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取齐套分析详情"""
    readiness = get_or_404(db, MaterialReadiness, readiness_id, "齐套分析记录不存在")

    # 获取关联信息
    project = db.query(Project).filter(Project.id == readiness.project_id).first()
    machine = db.query(Machine).filter(Machine.id == readiness.machine_id).first() if readiness.machine_id else None
    bom = db.query(BomHeader).filter(BomHeader.id == readiness.bom_id).first()

    # 获取阶段信息构建stage_kit_rates
    stages = db.query(AssemblyStage).filter(AssemblyStage.is_active).order_by(AssemblyStage.stage_order).all()
    stage_rates_data = readiness.stage_kit_rates or {}

    stage_kit_rates = []
    for stage in stages:
        rate_data = stage_rates_data.get(stage.stage_code, {})
        stage_kit_rates.append(StageKitRate(
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            stage_order=stage.stage_order,
            total_items=0,
            fulfilled_items=0,
            kit_rate=Decimal(rate_data.get("kit_rate", 0)),
            blocking_total=0,
            blocking_fulfilled=0,
            blocking_rate=Decimal(rate_data.get("blocking_rate", 0)),
            can_start=rate_data.get("can_start", False),
            color_code=stage.color_code
        ))

    # 获取缺料明细
    shortage_details = db.query(ShortageDetail).filter(
        ShortageDetail.readiness_id == readiness_id
    ).all()

    shortage_responses = [ShortageDetailResponse.model_validate(s) for s in shortage_details]

    # 获取优化建议（可选）
    optimization_suggestions = None
    try:
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        optimization_suggestions = AssemblyKitOptimizer.generate_optimization_suggestions(db, readiness)
    except Exception:
        logger.debug("生成齐套分析优化建议失败，已忽略", exc_info=True)

    response_data = MaterialReadinessDetailResponse(
        id=readiness.id,
        readiness_no=readiness.readiness_no,
        project_id=readiness.project_id,
        machine_id=readiness.machine_id,
        bom_id=readiness.bom_id,
        check_date=readiness.planned_start_date or date.today(),
        overall_kit_rate=readiness.overall_kit_rate,
        blocking_kit_rate=readiness.blocking_kit_rate,
        can_start=readiness.can_start,
        first_blocked_stage=readiness.first_blocked_stage,
        estimated_ready_date=readiness.estimated_ready_date,
        stage_kit_rates=stage_kit_rates,
        project_no=project.project_code if project else None,
        project_name=project.project_name if project else None,
        machine_no=machine.machine_code if machine else None,
        bom_no=bom.bom_no if bom else None,
        analysis_time=readiness.analysis_time,
        analyzed_by=readiness.analyzed_by,
        created_at=readiness.created_at,
        shortage_details=shortage_responses
    )

    # 将优化建议添加到响应数据中
    if optimization_suggestions:
        # 使用dict方式返回，包含优化建议
        return ResponseModel(
            code=200,
            message="success",
            data={
                **response_data.model_dump(),
                'optimization_suggestions': optimization_suggestions
            }
        )

    return ResponseModel(code=200, message="success", data=response_data)
