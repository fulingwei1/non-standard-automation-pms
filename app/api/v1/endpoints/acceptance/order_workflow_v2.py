# -*- coding: utf-8 -*-
"""
验收单工作流操作（基于统一状态机框架）

包含：提交、开始、完成验收等流程控制
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.acceptance import AcceptanceStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from app.models.acceptance import AcceptanceOrder
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceOrderComplete,
    AcceptanceOrderResponse,
    AcceptanceOrderStart,
)

from .order_crud import read_acceptance_order

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/acceptance-orders/{order_id}/submit/v2",
    response_model=AcceptanceOrderResponse,
    status_code=status.HTTP_200_OK,
)
def submit_acceptance_order_v2(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_permission("acceptance:submit")),
) -> Any:
    """
    提交验收单（使用状态机框架）

    状态转换: DRAFT → PENDING
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    state_machine = AcceptanceStateMachine(order, db)

    try:
        state_machine.transition_to(
            "PENDING",
            current_user=current_user,
            comment="提交验收单",
        )

        db.commit()
        db.refresh(order)

        return read_acceptance_order(order_id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/acceptance-orders/{order_id}/start/v2",
    response_model=AcceptanceOrderResponse,
    status_code=status.HTTP_200_OK,
)
def start_acceptance_v2(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: AcceptanceOrderStart,
    current_user: User = Depends(security.require_permission("acceptance:start")),
) -> Any:
    """
    开始验收（使用状态机框架）

    状态转换:
    - DRAFT → IN_PROGRESS
    - PENDING → IN_PROGRESS
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    state_machine = AcceptanceStateMachine(order, db)

    try:
        state_machine.transition_to(
            "IN_PROGRESS",
            current_user=current_user,
            comment="开始验收",
            location=start_in.location,
        )

        db.commit()
        db.refresh(order)

        return read_acceptance_order(order_id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/acceptance-orders/{order_id}/complete/v2",
    response_model=AcceptanceOrderResponse,
    status_code=status.HTTP_200_OK,
)
def complete_acceptance_v2(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    complete_in: AcceptanceOrderComplete,
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    current_user: User = Depends(security.require_permission("acceptance:complete")),
) -> Any:
    """
    完成验收（使用状态机框架）

    状态转换:
    - IN_PROGRESS → PASSED (验收通过)
    - IN_PROGRESS → FAILED (验收失败)

    自动触发：收款计划开票、阶段流转、质保期、奖金计算
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    state_machine = AcceptanceStateMachine(order, db)

    # 根据验收结果选择目标状态
    if complete_in.overall_result == "PASSED":
        target_state = "PASSED"
    else:
        target_state = "FAILED"

    try:
        state_machine.transition_to(
            target_state,
            current_user=current_user,
            comment=f"完成验收: {complete_in.overall_result}",
            overall_result=complete_in.overall_result,
            conclusion=complete_in.conclusion,
            conditions=complete_in.conditions,
            auto_trigger_invoice=auto_trigger_invoice,
        )

        db.commit()
        db.refresh(order)

        return read_acceptance_order(order_id, db, current_user)

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
