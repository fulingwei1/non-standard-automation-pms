# -*- coding: utf-8 -*-
"""
商机管理 - 工作流操作（阶段门、阶段、评分、赢单、输单）
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import can_set_opportunity_gate
from app.models.enums import OpportunityStageEnum
from app.models.sales import Opportunity, OpportunityRequirement
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import OpportunityRequirementResponse, OpportunityResponse
from app.utils.db_helpers import get_or_404

from .utils import validate_g2_opportunity_to_quote

logger = logging.getLogger(__name__)

router = APIRouter()


class OpportunityGateSubmitRequest(BaseModel):
    """商机阶段门提交请求（轻量版，用于 gate_status 更新）"""

    model_config = ConfigDict(populate_by_name=True)

    gate_status: str = Field(..., description="阶段门状态：PASS/REJECT")


@router.post("/opportunities/{opp_id}/gate", response_model=ResponseModel)
def submit_opportunity_gate(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    gate_request: OpportunityGateSubmitRequest,
    gate_type: str = Query("G2", description="阶段门类型: G1, G2, G3, G4"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交商机阶段门（带自动验证）
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not can_set_opportunity_gate(db, current_user, opportunity):
        raise HTTPException(status_code=403, detail="无权限设置商机阶段门")

    # 根据阶段门类型进行验证
    validation_errors = []
    if gate_type == "G2":
        is_valid, errors = validate_g2_opportunity_to_quote(opportunity)
        if not is_valid:
            validation_errors = errors

    if validation_errors and gate_request.gate_status == "PASS":
        raise HTTPException(
            status_code=400, detail=f"{gate_type}阶段门验证失败: {', '.join(validation_errors)}"
        )

    opportunity.gate_status = gate_request.gate_status
    if gate_request.gate_status == "PASS":
        opportunity.gate_passed_at = datetime.now()
    opportunity.updated_by = current_user.id

    db.commit()

    return ResponseModel(
        code=200,
        message=f"{gate_type}阶段门{'通过' if gate_request.gate_status == 'PASS' else '拒绝'}",
        data={"validation_errors": validation_errors} if validation_errors else None,
    )


@router.put("/opportunities/{opp_id}/stage", response_model=OpportunityResponse)
def update_opportunity_stage(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    stage: str = Query(..., description="新阶段"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新商机阶段
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    valid_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    if stage not in valid_stages:
        raise HTTPException(
            status_code=400, detail=f"无效的阶段，必须是: {', '.join(valid_stages)}"
        )

    opportunity.stage = stage
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/score", response_model=OpportunityResponse)
def update_opportunity_score(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    score: int = Query(..., ge=0, le=100, description="评分"),
    score_remark: Optional[str] = Query(None, description="评分说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商机评分（准入评估）
    评分范围：0-100分
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    opportunity.score = score

    # 根据评分自动更新风险等级
    if score >= 80:
        opportunity.risk_level = "LOW"
    elif score >= 60:
        opportunity.risk_level = "MEDIUM"
    else:
        opportunity.risk_level = "HIGH"
    opportunity.updated_by = current_user.id

    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/win", response_model=OpportunityResponse)
def win_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    赢单
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    opportunity.stage = "WON"
    opportunity.gate_status = "PASS"
    opportunity.gate_passed_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}/lose", response_model=OpportunityResponse)
def lose_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    lose_reason: Optional[str] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    输单
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    opportunity.stage = "LOST"
    if lose_reason:
        opportunity.lose_reason = lose_reason
    opportunity.lost_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    return _build_opportunity_response(db, opportunity)


# ==================== 新增高频 API ====================

# 阶段推进顺序
STAGE_ORDER = [
    OpportunityStageEnum.DISCOVERY.value,
    OpportunityStageEnum.QUALIFICATION.value,
    OpportunityStageEnum.PROPOSAL.value,
    OpportunityStageEnum.NEGOTIATION.value,
    OpportunityStageEnum.CLOSING.value,
]


class OpportunityAdvanceRequest(BaseModel):
    """商机阶段推进请求"""

    model_config = ConfigDict(populate_by_name=True)

    target_stage: Optional[str] = Field(
        default=None, description="目标阶段（留空自动推进到下一阶段）"
    )
    remark: Optional[str] = Field(default=None, description="推进备注")


class OpportunityLossRequest(BaseModel):
    """商机输单请求"""

    model_config = ConfigDict(populate_by_name=True)

    loss_reason: str = Field(..., min_length=1, description="输单原因（必填）")
    competitor: Optional[str] = Field(default=None, description="竞争对手")
    remark: Optional[str] = Field(default=None, description="备注")


def _build_opportunity_response(db: Session, opportunity: Opportunity) -> OpportunityResponse:
    """构建商机响应对象"""
    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )
    return OpportunityResponse(**opp_dict)


@router.post("/opportunities/{opp_id}/advance", response_model=ResponseModel)
def advance_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: OpportunityAdvanceRequest = Body(default=OpportunityAdvanceRequest()),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    推进商机阶段

    自动推进到下一阶段，或指定目标阶段。
    不能从 WON/LOST 推进，也不能跳过阶段倒退。
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    # 数据权限检查
    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    current_stage = opportunity.stage
    if current_stage in ("WON", "LOST"):
        raise HTTPException(status_code=400, detail=f"商机已{('赢单' if current_stage == 'WON' else '输单')}，无法继续推进")

    if request.target_stage:
        target = request.target_stage
        # 验证目标阶段有效
        valid_targets = STAGE_ORDER + ["WON"]
        if target not in valid_targets:
            raise HTTPException(
                status_code=400, detail=f"无效的目标阶段，可选: {', '.join(valid_targets)}"
            )
        # 不能倒退
        if current_stage in STAGE_ORDER and target in STAGE_ORDER:
            if STAGE_ORDER.index(target) <= STAGE_ORDER.index(current_stage):
                raise HTTPException(status_code=400, detail="不能倒退阶段")
    else:
        # 自动推进到下一阶段
        if current_stage not in STAGE_ORDER:
            raise HTTPException(
                status_code=400, detail=f"当前阶段 {current_stage} 不支持自动推进"
            )
        idx = STAGE_ORDER.index(current_stage)
        if idx >= len(STAGE_ORDER) - 1:
            # CLOSING 之后需要明确 win 或 loss
            raise HTTPException(
                status_code=400,
                detail="已在最后阶段(CLOSING)，请使用赢单或输单接口",
            )
        target = STAGE_ORDER[idx + 1]

    old_stage = opportunity.stage
    opportunity.stage = target
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    logger.info(f"商机 {opp_id} 阶段推进: {old_stage} → {target}, 操作人: {current_user.id}")

    return ResponseModel(
        code=200,
        message=f"商机阶段已从 {old_stage} 推进到 {target}",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": target,
        },
    )


@router.post("/opportunities/{opp_id}/win", response_model=ResponseModel)
def win_opportunity_post(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    remark: Optional[str] = Body(default=None, embed=True),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记赢单
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    if opportunity.stage == "WON":
        raise HTTPException(status_code=400, detail="商机已是赢单状态")
    if opportunity.stage == "LOST":
        raise HTTPException(status_code=400, detail="商机已输单，无法标记赢单")

    old_stage = opportunity.stage
    opportunity.stage = "WON"
    opportunity.gate_status = "PASS"
    opportunity.gate_passed_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    logger.info(f"商机 {opp_id} 赢单: {old_stage} → WON, 操作人: {current_user.id}")

    return ResponseModel(
        code=200,
        message="商机已标记为赢单",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": "WON",
        },
    )


@router.post("/opportunities/{opp_id}/loss", response_model=ResponseModel)
def loss_opportunity_post(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: OpportunityLossRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记输单（需填写原因）
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权操作该商机")

    if opportunity.stage == "LOST":
        raise HTTPException(status_code=400, detail="商机已是输单状态")
    if opportunity.stage == "WON":
        raise HTTPException(status_code=400, detail="商机已赢单，无法标记输单")

    old_stage = opportunity.stage
    opportunity.stage = "LOST"
    opportunity.lose_reason = request.loss_reason
    opportunity.lost_at = datetime.now()
    opportunity.updated_by = current_user.id
    db.commit()
    db.refresh(opportunity)

    logger.info(
        f"商机 {opp_id} 输单: {old_stage} → LOST, 原因: {request.loss_reason}, 操作人: {current_user.id}"
    )

    return ResponseModel(
        code=200,
        message="商机已标记为输单",
        data={
            "opportunity_id": opp_id,
            "old_stage": old_stage,
            "new_stage": "LOST",
            "loss_reason": request.loss_reason,
        },
    )
