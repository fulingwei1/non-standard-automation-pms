# -*- coding: utf-8 -*-
"""
销售漏斗状态机 API endpoints

提供统一状态管理、阶段门验证、状态转换和滞留时间监控接口。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales.sales_funnel import FunnelEntityTypeEnum, GateTypeEnum, StageDwellTimeConfig
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.dwell_time_monitor import DwellTimeMonitorService
from app.services.sales.funnel_state_machine import FunnelStateMachine
from app.services.sales.gate_validators import GateValidatorFactory

router = APIRouter()


def _parse_entity_type(entity_type: str) -> FunnelEntityTypeEnum:
    """兼容前端传入的小写或大写实体类型。"""
    try:
        return FunnelEntityTypeEnum(str(entity_type).upper())
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="无效的实体类型，支持: LEAD, OPPORTUNITY, QUOTE, CONTRACT",
        ) from exc


def _build_validation_payload(result: Any, gate_result: Any = None) -> Dict[str, Any]:
    """统一阶段门验证返回结构，并兼容旧字段。"""
    data = {
        "is_valid": result.passed,
        "passed": result.passed,
        "errors": result.failed_rules,
        "failed_rules": result.failed_rules,
        "warnings": result.warnings,
        "checked_items": result.passed_rules,
        "passed_rules": result.passed_rules,
        "score": result.score,
        "threshold": result.threshold,
        "details": result.details,
    }

    if gate_result:
        data["result_id"] = gate_result.id
        data["gate_type"] = gate_result.gate_type
        data["result_status"] = gate_result.result

    return data


# ==================== 请求/响应模型 ====================


class GateValidationRequest(BaseModel):
    """阶段门验证请求"""

    model_config = ConfigDict(populate_by_name=True)

    gate_type: str = Field(..., description="阶段门类型: G1/G2/G3/G4")
    entity_id: int = Field(..., description="实体ID")
    save_result: bool = Field(default=True, description="是否保存验证结果")


class TransitionRequest(BaseModel):
    """状态转换请求"""

    model_config = ConfigDict(populate_by_name=True)

    entity_type: str = Field(..., description="实体类型: LEAD/OPPORTUNITY/QUOTE/CONTRACT")
    entity_id: int = Field(..., description="实体ID")
    to_stage: str = Field(..., description="目标阶段")
    reason: Optional[str] = Field(None, description="转换原因")
    notes: Optional[str] = Field(None, description="备注")
    skip_validation: bool = Field(default=False, description="跳过阶段门验证")


class LeadToOpportunityRequest(BaseModel):
    """线索转商机请求"""

    model_config = ConfigDict(populate_by_name=True)

    lead_id: int = Field(..., description="线索ID")
    opportunity_name: Optional[str] = Field(None, description="商机名称")
    expected_amount: Optional[float] = Field(None, description="预期金额")
    expected_close_date: Optional[str] = Field(None, description="预期关闭日期")
    owner_id: Optional[int] = Field(None, description="负责人ID")


class OpportunityToQuoteRequest(BaseModel):
    """商机转报价请求"""

    model_config = ConfigDict(populate_by_name=True)

    opportunity_id: int = Field(..., description="商机ID")
    quote_title: Optional[str] = Field(None, description="报价标题")
    validity_days: int = Field(default=30, description="有效期天数")


class QuoteToContractRequest(BaseModel):
    """报价转合同请求"""

    model_config = ConfigDict(populate_by_name=True)

    quote_id: int = Field(..., description="报价ID")
    contract_title: Optional[str] = Field(None, description="合同标题")
    contract_type: str = Field(default="SALES", description="合同类型")


class AlertAcknowledgeRequest(BaseModel):
    """确认预警请求"""

    model_config = ConfigDict(populate_by_name=True)

    alert_id: int = Field(..., description="预警ID")


class AlertResolveRequest(BaseModel):
    """解决预警请求"""

    model_config = ConfigDict(populate_by_name=True)

    alert_id: int = Field(..., description="预警ID")
    resolution_note: Optional[str] = Field(None, description="解决备注")


# ==================== 阶段门验证 API ====================


@router.post("/funnel/validate-gate", response_model=ResponseModel)
def validate_gate(
    *,
    db: Session = Depends(deps.get_db),
    request: GateValidationRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证阶段门

    支持的阶段门类型:
    - G1: 线索→商机（验证客户信息、需求摘要、技术评估）
    - G2: 商机→报价（验证商机阶段、金额、评估完成）
    - G3: 报价→合同（验证审批状态、毛利率、有效期）
    - G4: 合同→项目（验证签署状态、交付物、付款条款）
    """
    try:
        gate_type = GateTypeEnum(str(request.gate_type).upper())
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"无效的阶段门类型，支持: G1, G2, G3, G4"
        )

    result, gate_result = GateValidatorFactory.validate_gate(
        gate_type=gate_type,
        entity_id=request.entity_id,
        db=db,
        validated_by=current_user.id,
        save_result=request.save_result,
    )

    return ResponseModel(
        code=200,
        message="通过验证" if result.passed else "验证失败",
        data=_build_validation_payload(result, gate_result),
    )


@router.get("/funnel/gate-configs", response_model=ResponseModel)
def get_gate_configs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取所有阶段门配置"""
    from app.models.sales.sales_funnel import StageGateConfig

    configs = db.query(StageGateConfig).filter(StageGateConfig.is_active == True).all()

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": c.id,
                    "gate_type": c.gate_type,
                    "gate_name": c.gate_name,
                    "description": c.description,
                    "validation_rules": c.validation_rules,
                    "required_fields": c.required_fields,
                    "requires_approval": c.requires_approval,
                }
                for c in configs
            ],
            "total": len(configs),
        },
    )


# ==================== 状态转换 API ====================


@router.post("/funnel/transition", response_model=ResponseModel)
def perform_transition(
    *,
    db: Session = Depends(deps.get_db),
    request: TransitionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行状态转换

    通用的状态转换接口，支持所有实体类型的阶段推进。
    """
    state_machine = FunnelStateMachine(db)
    entity_type = _parse_entity_type(request.entity_type)
    extra_data = {"notes": request.notes} if request.notes else None
    transition_reason = request.reason or request.notes

    success, log, errors = state_machine.transition(
        entity_type=entity_type,
        entity_id=request.entity_id,
        to_stage=request.to_stage,
        reason=transition_reason,
        validate_gate=not request.skip_validation,
        transitioned_by=current_user.id,
        extra_data=extra_data,
    )

    if not success:
        raise HTTPException(status_code=400, detail=f"转换失败: {', '.join(errors)}")

    return ResponseModel(
        code=200,
        message="转换成功",
        data={
            "log_id": log.id if log else None,
            "from_stage": log.from_stage if log else None,
            "to_stage": log.to_stage if log else None,
            "transitioned_at": log.transitioned_at.isoformat() if log and log.transitioned_at else None,
        },
    )


@router.get("/funnel/can-transition", response_model=ResponseModel)
def check_can_transition(
    *,
    db: Session = Depends(deps.get_db),
    entity_type: str = Query(..., description="实体类型"),
    entity_id: int = Query(..., description="实体ID"),
    to_stage: str = Query(..., description="目标阶段"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """检查是否可以转换状态"""
    state_machine = FunnelStateMachine(db)
    can_do, errors = state_machine.can_transition(
        _parse_entity_type(entity_type), entity_id, to_stage
    )

    return ResponseModel(
        code=200,
        message="可以转换" if can_do else "不满足转换条件",
        data={"can_transition": can_do, "errors": errors},
    )


# ==================== 跨实体转换 API ====================


@router.post("/funnel/lead-to-opportunity", response_model=ResponseModel)
def convert_lead_to_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    request: LeadToOpportunityRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    线索转商机（G1 阶段门）

    将合格的线索转化为商机，自动执行 G1 验证。
    """
    state_machine = FunnelStateMachine(db)

    opportunity_data = {
        "opp_name": request.opportunity_name,
        "est_amount": request.expected_amount,
        "expected_close_date": request.expected_close_date,
        "owner_id": request.owner_id or current_user.id,
    }

    success, opportunity, errors = state_machine.lead_to_opportunity(
        lead_id=request.lead_id,
        opportunity_data=opportunity_data,
        transitioned_by=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=f"转换失败: {', '.join(errors)}")

    return ResponseModel(
        code=200,
        message="线索已转化为商机",
        data={
            "opportunity_id": opportunity.id if opportunity else None,
            "opportunity_name": opportunity.opp_name if opportunity else None,
        },
    )


@router.post("/funnel/opportunity-to-quote", response_model=ResponseModel)
def convert_opportunity_to_quote(
    *,
    db: Session = Depends(deps.get_db),
    request: OpportunityToQuoteRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商机转报价（G2 阶段门）

    为合格的商机创建报价，自动执行 G2 验证。
    """
    state_machine = FunnelStateMachine(db)

    quote_data = {
        "quote_name": request.quote_title,
        "validity_days": request.validity_days,
    }

    success, quote, errors = state_machine.opportunity_to_quote(
        opportunity_id=request.opportunity_id,
        quote_data=quote_data,
        transitioned_by=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=f"转换失败: {', '.join(errors)}")

    return ResponseModel(
        code=200,
        message="商机已转化为报价",
        data={
            "quote_id": quote.id if quote else None,
            "quote_code": quote.quote_code if hasattr(quote, "quote_code") and quote else None,
        },
    )


@router.post("/funnel/quote-to-contract", response_model=ResponseModel)
def convert_quote_to_contract(
    *,
    db: Session = Depends(deps.get_db),
    request: QuoteToContractRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价转合同（G3 阶段门）

    为已审批的报价创建合同，自动执行 G3 验证。
    """
    state_machine = FunnelStateMachine(db)

    contract_data = {
        "contract_name": request.contract_title,
        "contract_type": request.contract_type.lower(),
    }

    success, contract, errors = state_machine.quote_to_contract(
        quote_id=request.quote_id,
        contract_data=contract_data,
        transitioned_by=current_user.id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=f"转换失败: {', '.join(errors)}")

    return ResponseModel(
        code=200,
        message="报价已转化为合同",
        data={
            "contract_id": contract.id if contract else None,
            "contract_code": contract.contract_code if contract else None,
        },
    )


# ==================== 漏斗状态查询 API ====================


@router.get("/funnel/stages", response_model=ResponseModel)
def get_funnel_stages(
    *,
    db: Session = Depends(deps.get_db),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取漏斗阶段配置"""
    from app.models.sales.sales_funnel import SalesFunnelStage

    query = db.query(SalesFunnelStage).filter(SalesFunnelStage.is_active == True)

    entity_type_enum = _parse_entity_type(entity_type) if entity_type else None
    if entity_type_enum:
        query = query.filter(SalesFunnelStage.entity_type == entity_type_enum.value)

    stages = query.order_by(SalesFunnelStage.sequence).all()
    dwell_configs = (
        db.query(StageDwellTimeConfig)
        .filter(StageDwellTimeConfig.stage_id.in_([stage.id for stage in stages]))
        .all()
        if stages
        else []
    )
    config_by_stage_id = {config.stage_id: config for config in dwell_configs}

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": s.id,
                    "stage_code": s.stage_code,
                    "stage_name": s.stage_name,
                    "entity_type": s.entity_type,
                    "sequence": s.sequence,
                    "required_gate": s.required_gate,
                    "expected_hours": config_by_stage_id.get(s.id).expected_hours
                    if config_by_stage_id.get(s.id)
                    else None,
                    "expected_duration_days": round(
                        config_by_stage_id[s.id].expected_hours / 24, 1
                    )
                    if config_by_stage_id.get(s.id)
                    else None,
                }
                for s in stages
            ],
            "total": len(stages),
        },
    )


@router.get("/funnel/transition-logs", response_model=ResponseModel)
def get_transition_logs(
    *,
    db: Session = Depends(deps.get_db),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    entity_id: Optional[int] = Query(None, description="实体ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取状态转换日志"""
    from app.models.sales.sales_funnel import FunnelTransitionLog

    query = db.query(FunnelTransitionLog)

    if entity_type:
        query = query.filter(FunnelTransitionLog.entity_type == _parse_entity_type(entity_type).value)
    if entity_id:
        query = query.filter(FunnelTransitionLog.entity_id == entity_id)

    total = query.count()
    logs = (
        query.order_by(FunnelTransitionLog.transitioned_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": log.id,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "from_stage": log.from_stage,
                    "to_stage": log.to_stage,
                    "reason": log.transition_reason,
                    "transition_reason": log.transition_reason,
                    "extra_data": log.extra_data,
                    "transitioned_at": log.transitioned_at.isoformat()
                    if log.transitioned_at
                    else None,
                }
                for log in logs
            ],
            "total": total,
        },
    )


# ==================== 滞留时间监控 API ====================


@router.post("/funnel/dwell-time/check", response_model=ResponseModel)
def check_dwell_time(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查所有实体的滞留时间

    扫描所有实体，对超时的创建预警。通常由定时任务调用。
    """
    service = DwellTimeMonitorService(db)
    alerts = service.check_all_entities()

    return ResponseModel(
        code=200,
        message=f"检查完成，新增 {len(alerts)} 条预警",
        data={
            "new_alerts_count": len(alerts),
            "alert_ids": [a.id for a in alerts],
        },
    )


@router.get("/funnel/dwell-time/alerts", response_model=ResponseModel)
def get_dwell_time_alerts(
    *,
    db: Session = Depends(deps.get_db),
    entity_type: Optional[str] = Query(None, description="实体类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    status: Optional[str] = Query(None, description="状态"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取滞留时间预警列表"""
    service = DwellTimeMonitorService(db)
    alerts, total = service.get_alerts(
        entity_type=_parse_entity_type(entity_type).value if entity_type else None,
        severity=severity,
        status=status,
        skip=skip,
        limit=limit,
    )

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [
                {
                    "id": a.id,
                    "entity_type": a.entity_type,
                    "entity_id": a.entity_id,
                    "stage": a.stage.stage_name if a.stage else None,
                    "severity": a.severity,
                    "status": a.status,
                    "dwell_hours": a.dwell_hours,
                    "threshold_hours": a.threshold_hours,
                    "owner_id": a.owner_id,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts
            ],
            "total": total,
        },
    )


@router.post("/funnel/dwell-time/alerts/{alert_id}/acknowledge", response_model=ResponseModel)
def acknowledge_dwell_time_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """确认滞留预警"""
    service = DwellTimeMonitorService(db)
    alert = service.acknowledge_alert(alert_id, acknowledged_by=current_user.id)

    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    return ResponseModel(
        code=200,
        message="预警已确认",
        data={"id": alert.id, "status": alert.status},
    )


@router.post("/funnel/dwell-time/alerts/{alert_id}/resolve", response_model=ResponseModel)
def resolve_dwell_time_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_id: int,
    resolution_note: Optional[str] = Query(None, description="解决备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """解决滞留预警"""
    service = DwellTimeMonitorService(db)
    alert = service.resolve_alert(alert_id, resolution_note=resolution_note)

    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    return ResponseModel(
        code=200,
        message="预警已解决",
        data={"id": alert.id, "status": alert.status},
    )


@router.get("/funnel/dwell-time/statistics", response_model=ResponseModel)
def get_dwell_time_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取滞留时间统计"""
    service = DwellTimeMonitorService(db)
    stats = service.get_alert_statistics()

    return ResponseModel(code=200, message="统计成功", data=stats)
