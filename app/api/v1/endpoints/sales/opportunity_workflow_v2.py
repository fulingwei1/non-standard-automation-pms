# -*- coding: utf-8 -*-
"""
商机工作流操作（基于统一状态机框架）

包含：阶段推进、评分、赢单、输单
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.opportunity import OpportunityStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from app.models.sales import Opportunity, OpportunityRequirement
from app.models.user import User
from app.schemas.sales import OpportunityResponse, OpportunityRequirementResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.put("/opportunities/{opp_id}/stage/v2", response_model=OpportunityResponse)
def update_opportunity_stage_v2(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    new_stage: str,
    comment: Optional[str] = None,
    current_user: User = Depends(security.require_permission("opportunity:update")),
) -> Any:
    """
    更新商机阶段（使用状态机框架）

    状态转换:
    - DISCOVERY → QUALIFIED
    - QUALIFIED → PROPOSAL
    - PROPOSAL → NEGOTIATION
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    state_machine = OpportunityStateMachine(opportunity, db)

    try:
        state_machine.transition_to(
            new_stage,
            current_user=current_user,
            comment=comment or f"阶段推进到 {new_stage}",
        )

        db.commit()
        db.refresh(opportunity)

        return _build_opportunity_response(db, opportunity)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/opportunities/{opp_id}/win/v2", response_model=OpportunityResponse)
def win_opportunity_v2(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    comment: Optional[str] = None,
    current_user: User = Depends(security.require_permission("opportunity:win")),
) -> Any:
    """
    赢单（使用状态机框架）

    状态转换: 任意阶段 → WON
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # 只能从 NEGOTIATION 阶段赢单
    if opportunity.stage != "NEGOTIATION":
        raise HTTPException(status_code=400, detail="只能从谈判阶段赢单")

    state_machine = OpportunityStateMachine(opportunity, db)

    try:
        state_machine.transition_to(
            "WON",
            current_user=current_user,
            comment=comment or "商机赢单",
        )

        db.commit()
        db.refresh(opportunity)

        return _build_opportunity_response(db, opportunity)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/opportunities/{opp_id}/lose/v2", response_model=OpportunityResponse)
def lose_opportunity_v2(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    lose_reason: Optional[str] = None,
    comment: Optional[str] = None,
    current_user: User = Depends(security.require_permission("opportunity:update")),
) -> Any:
    """
    输单（使用状态机框架）

    状态转换: 任意阶段 → LOST
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    state_machine = OpportunityStateMachine(opportunity, db)

    try:
        state_machine.transition_to(
            "LOST",
            current_user=current_user,
            comment=comment or f"商机输单: {lose_reason or '未填写原因'}",
            lose_reason=lose_reason,
        )

        db.commit()
        db.refresh(opportunity)

        return _build_opportunity_response(db, opportunity)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _build_opportunity_response(db: Session, opportunity: Opportunity) -> OpportunityResponse:
    """构建商机响应"""
    req = db.query(OpportunityRequirement).filter(
        OpportunityRequirement.opportunity_id == opportunity.id
    ).first()

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
