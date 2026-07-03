# -*- coding: utf-8 -*-
"""
ECN 状态机管理 API 端点
提供状态查询、状态转换、状态历史等功能
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.core.state_machine.ecn import EcnStateMachine
from app.core.state_machine.ecn_status import EcnStatus
from app.models.ecn import Ecn, EcnLog
from app.models.state_machine import StateTransitionLog
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ecn/state-machine", tags=["ECN状态机"])


CURRENT_ECN_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["SUBMITTED", "CANCELLED"],
    "READY_TO_SUBMIT": ["SUBMITTED", "CANCELLED"],
    "SUBMITTED": [
        "EVALUATING",
        "EVALUATION_PENDING",
        "PENDING_APPROVAL",
        "APPROVAL_PENDING",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
    ],
    "EVALUATING": ["EVALUATED", "PENDING_APPROVAL", "APPROVED", "REJECTED", "CANCELLED"],
    "EVALUATED": ["PENDING_APPROVAL", "APPROVED", "REJECTED", "CANCELLED"],
    "EVALUATION_PENDING": [
        "EVALUATION_IN_PROGRESS",
        "APPROVAL_PENDING",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
    ],
    "EVALUATION_IN_PROGRESS": ["APPROVAL_PENDING", "APPROVED", "REJECTED", "CANCELLED"],
    "PENDING_APPROVAL": ["APPROVED", "REJECTED", "CANCELLED"],
    "APPROVAL_PENDING": ["APPROVED", "REJECTED", "CANCELLED"],
    "APPROVED": ["EXECUTING", "READY_TO_EXECUTE", "IN_PROGRESS", "IMPLEMENTED", "CANCELLED"],
    "READY_TO_EXECUTE": ["EXECUTING", "IN_PROGRESS", "CANCELLED"],
    "EXECUTING": ["PENDING_VERIFY", "COMPLETED", "EXECUTION_COMPLETED", "CANCELLED"],
    "IN_PROGRESS": ["EXECUTION_PAUSED", "EXECUTION_COMPLETED", "READY_TO_CLOSE", "CANCELLED"],
    "EXECUTION_PAUSED": ["IN_PROGRESS", "CANCELLED"],
    "PENDING_VERIFY": ["EXECUTING", "COMPLETED", "CANCELLED"],
    "EXECUTION_COMPLETED": ["READY_TO_CLOSE", "CLOSED"],
    "COMPLETED": ["CLOSED"],
    "READY_TO_CLOSE": ["CLOSED"],
    "REJECTED": ["DRAFT", "CANCELLED"],
    "CLOSED": [],
    "CANCELLED": [],
}

CURRENT_STATUS_LABELS = {
    "DRAFT": "草稿",
    "READY_TO_SUBMIT": "准备提交",
    "SUBMITTED": "已提交",
    "EVALUATING": "评估中",
    "EVALUATED": "评估完成",
    "EVALUATION_PENDING": "待评估",
    "EVALUATION_IN_PROGRESS": "评估中",
    "PENDING_APPROVAL": "待审批",
    "PENDING_REVIEW": "待审核",
    "APPROVAL_PENDING": "待审批",
    "APPROVED": "已批准",
    "READY_TO_EXECUTE": "准备执行",
    "EXECUTING": "执行中",
    "IN_PROGRESS": "执行中",
    "EXECUTION_PAUSED": "执行暂停",
    "PENDING_VERIFY": "待验证",
    "IMPLEMENTED": "已实施",
    "EXECUTION_COMPLETED": "执行完成",
    "COMPLETED": "已完成",
    "READY_TO_CLOSE": "准备关闭",
    "CLOSED": "已关闭",
    "REJECTED": "已拒绝",
    "CANCELLED": "已取消",
}

CURRENT_EDITABLE_STATES = {"DRAFT", "READY_TO_SUBMIT"}
CURRENT_SUBMITTABLE_STATES = {"DRAFT", "READY_TO_SUBMIT"}
CURRENT_CANCELLABLE_STATES = {
    "DRAFT",
    "SUBMITTED",
    "EVALUATING",
    "EVALUATED",
    "EVALUATION_PENDING",
    "EVALUATION_IN_PROGRESS",
    "PENDING_APPROVAL",
    "APPROVAL_PENDING",
    "APPROVED",
    "EXECUTING",
    "IN_PROGRESS",
    "EXECUTION_PAUSED",
    "PENDING_VERIFY",
}

CURRENT_ACTION_MAP = {
    "SUBMITTED": "SUBMIT",
    "EVALUATING": "START_EVALUATION",
    "EVALUATION_PENDING": "START_EVALUATION",
    "EVALUATED": "COMPLETE_EVALUATION",
    "PENDING_APPROVAL": "SUBMIT_APPROVAL",
    "APPROVAL_PENDING": "SUBMIT_APPROVAL",
    "APPROVED": "APPROVE",
    "REJECTED": "REJECT",
    "EXECUTING": "START_EXECUTION",
    "READY_TO_EXECUTE": "READY_TO_EXECUTE",
    "IN_PROGRESS": "START_EXECUTION",
    "PENDING_VERIFY": "SUBMIT_VERIFY",
    "IMPLEMENTED": "IMPLEMENT",
    "COMPLETED": "COMPLETE",
    "EXECUTION_COMPLETED": "COMPLETE_EXECUTION",
    "CLOSED": "CLOSE",
    "CANCELLED": "CANCEL",
    "DRAFT": "REVISE",
}


class StateInfoResponse(BaseModel):
    """状态信息响应"""

    current_state: str  # 当前状态
    display_name: str  # 显示名称
    description: str  # 状态描述
    is_editable: bool  # 是否可编辑
    allowed_transitions: Dict[str, List[str]]  # 允许的转换


class TransitionHistoryResponse(BaseModel):
    """状态转换历史响应"""

    from_state: str  # 源状态
    to_state: str  # 目标状态
    timestamp: str  # 转换时间
    actor: str  # 操作人
    kwargs: Dict[str, Any] = {}  # 额外参数


class TransitionRequest(BaseModel):
    """状态转换请求"""

    target_state: str  # 目标状态
    comment: str = ""  # 备注


# ========== 依赖注入 ==========


def get_ecn_state_machine(ecn_id: int, db: Session) -> EcnStateMachine:
    """获取 ECN 状态机实例（依赖注入）"""
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    return EcnStateMachine(ecn, db)


def _state_value(state_machine: EcnStateMachine) -> str:
    """兼容历史库空状态和字符串状态。"""
    raw_state = state_machine.current_state
    if hasattr(raw_state, "value"):
        raw_state = raw_state.value
    return str(raw_state or EcnStatus.DRAFT.value)


def _known_current_states() -> set[str]:
    known = set(CURRENT_ECN_TRANSITIONS)
    for targets in CURRENT_ECN_TRANSITIONS.values():
        known.update(targets)
    return known


def _display_name(state: str) -> str:
    try:
        return EcnStatus(state).display_name()
    except ValueError:
        return CURRENT_STATUS_LABELS.get(state, state)


def _allowed_current_transitions(current_state: str) -> List[str]:
    return CURRENT_ECN_TRANSITIONS.get(current_state, [])


def _validate_current_transition(current_state: str, target_state: str) -> None:
    known_states = _known_current_states()
    if target_state not in known_states:
        raise HTTPException(status_code=400, detail=f"无效的状态值: {target_state}")

    allowed = _allowed_current_transitions(current_state)
    if target_state not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"不允许的状态转换: 未定义从 '{current_state}' 到 '{target_state}' 的状态转换规则",
        )


def _apply_current_transition(
    *,
    state_machine: EcnStateMachine,
    target_state: str,
    comment: str,
    current_user: Any,
    db: Session,
) -> Dict[str, Any]:
    ecn = state_machine.model
    previous_state = _state_value(state_machine)
    _validate_current_transition(previous_state, target_state)

    now = datetime.now()
    ecn.status = target_state
    if target_state == "SUBMITTED":
        ecn.applied_at = ecn.applied_at or now
        ecn.current_step = "EVALUATION"
    elif target_state in {"EVALUATING", "EVALUATION_PENDING", "EVALUATION_IN_PROGRESS"}:
        ecn.current_step = "EVALUATION"
    elif target_state in {"PENDING_APPROVAL", "APPROVAL_PENDING"}:
        ecn.current_step = "APPROVAL"
    elif target_state == "APPROVED":
        ecn.approved_at = ecn.approved_at or now
        ecn.approval_result = "APPROVED"
        ecn.current_step = "EXECUTION"
    elif target_state == "REJECTED":
        ecn.approved_at = ecn.approved_at or now
        ecn.approval_result = "REJECTED"
        ecn.current_step = "REJECTED"
    elif target_state in {"EXECUTING", "IN_PROGRESS", "IMPLEMENTED"}:
        ecn.execution_start = ecn.execution_start or now
        ecn.current_step = "EXECUTION"
    elif target_state in {"COMPLETED", "EXECUTION_COMPLETED"}:
        ecn.execution_end = ecn.execution_end or now
        ecn.current_step = "COMPLETED"
    elif target_state == "CLOSED":
        ecn.closed_at = ecn.closed_at or now
        ecn.closed_by = getattr(current_user, "id", None)
        ecn.current_step = "CLOSED"
    elif target_state == "CANCELLED":
        ecn.current_step = "CANCELLED"

    action = CURRENT_ACTION_MAP.get(target_state, "STATUS_CHANGE")
    actor_name = (
        getattr(current_user, "real_name", None)
        or getattr(current_user, "username", None)
        or str(getattr(current_user, "id", ""))
    )
    db.add(
        EcnLog(
            ecn_id=ecn.id,
            log_type="STATUS_CHANGE",
            log_action=action,
            old_status=previous_state,
            new_status=target_state,
            log_content=comment
            or f"{_display_name(previous_state)} -> {_display_name(target_state)}",
            created_by=getattr(current_user, "id", None),
        )
    )
    db.add(
        StateTransitionLog(
            entity_type="ECN",
            entity_id=ecn.id,
            from_state=previous_state,
            to_state=target_state,
            operator_id=getattr(current_user, "id", None),
            operator_name=actor_name,
            action_type=action,
            comment=comment,
        )
    )
    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return {
        "previous_state": previous_state,
        "current_state": target_state,
        "timestamp": now.isoformat(),
        "actor": actor_name,
        "action": action,
    }


def _state_metadata(
    state_machine: EcnStateMachine,
) -> tuple[str, str, str, bool, Dict[str, List[str]]]:
    current_state = _state_value(state_machine)
    if current_state in CURRENT_ECN_TRANSITIONS:
        display_name = _display_name(current_state)
        return (
            current_state,
            display_name,
            display_name,
            current_state in CURRENT_EDITABLE_STATES,
            {current_state: _allowed_current_transitions(current_state)},
        )

    try:
        status = EcnStatus(current_state)
    except ValueError:
        status = None

    if status:
        display_name = status.display_name()
        description = status.description()
        is_editable = status.is_editable
    else:
        display_name = state_machine.get_status_label()
        description = display_name
        is_editable = state_machine.is_editable()

    allowed = state_machine.get_allowed_transitions()
    return current_state, display_name, description, is_editable, {current_state: allowed}


# ========== 状态查询端点 ==========


@router.get("/{ecn_id}/state", response_model=ResponseModel[StateInfoResponse])
def get_ecn_state(
    ecn_id: int = Path(..., description="ECN ID"),
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    获取 ECN 当前状态

    - 检查 ECN 是否存在
    - 获取状态机实例
    - 返回状态信息
    """
    try:
        state_machine = get_ecn_state_machine(ecn_id, db)
        current_state, display_name, description, is_editable, allowed_transitions = (
            _state_metadata(state_machine)
        )

        return ResponseModel(
            success=True,
            data=StateInfoResponse(
                current_state=current_state,
                display_name=display_name,
                description=description,
                is_editable=is_editable,
                allowed_transitions=allowed_transitions,
            ),
            message=f"ECN {ecn_id} 当前状态: {current_state}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取ECN状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 状态转换端点 ==========


@router.post("/{ecn_id}/transition")
async def transition_ecn_state(
    ecn_id: int,
    request: TransitionRequest,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    状态转换

    - 检查 ECN 是否存在
    - 获取状态机实例
    - 验证转换是否允许
    - 执行状态转换
    - 记录转换历史
    """
    try:
        state_machine = get_ecn_state_machine(ecn_id, db)
        current_state = _state_value(state_machine)

        if current_state in CURRENT_ECN_TRANSITIONS:
            payload = _apply_current_transition(
                state_machine=state_machine,
                target_state=request.target_state,
                comment=request.comment,
                current_user=current_user,
                db=db,
            )

            return ResponseModel(
                success=True,
                data=payload,
                message=f"ECN {ecn_id} 状态已从 {payload['previous_state']} 转换到 {payload['current_state']}",
            )

        # 旧库历史状态兜底仍走 legacy 状态机。
        try:
            target_status = EcnStatus(request.target_state)
            target_value = target_status.value
        except ValueError:
            target_value = request.target_state

        can_transition, reason = state_machine.can_transition_to(target_value)
        if not can_transition:
            raise HTTPException(status_code=400, detail=f"不允许的状态转换: {reason}")

        state_machine.transition_to(target_value, comment=request.comment)

        previous_state = (
            state_machine.previous_state.value
            if hasattr(state_machine.previous_state, "value")
            else state_machine.previous_state
        )
        current_state = (
            state_machine.current_state.value
            if hasattr(state_machine.current_state, "value")
            else state_machine.current_state
        )
        timestamp = (
            state_machine._transition_history[-1].get("timestamp")
            if state_machine._transition_history
            else datetime.now().isoformat()
        )

        return ResponseModel(
            success=True,
            data={
                "previous_state": previous_state,
                "current_state": current_state,
                "timestamp": timestamp,
                "actor": current_user.username,
            },
            message=f"ECN {ecn_id} 状态已从 {previous_state or 'DRAFT'} 转换到 {current_state}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ECN状态转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 状态历史端点 ==========


@router.get(
    "/{ecn_id}/transitions",
    response_model=ResponseModel[List[TransitionHistoryResponse]],
)
def get_transition_history(
    ecn_id: int,
    limit: int = Query(10, ge=1, le=100, description="返回记录数量限制"),
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    获取 ECN 状态转换历史

    - 检查 ECN 是否存在
    - 获取状态机实例
    - 获取历史记录
    """
    try:
        state_machine = get_ecn_state_machine(ecn_id, db)
        history = state_machine.get_transition_history()

        # 按时间倒序，返回最近的 N 条
        limited_history = list(reversed(history[-limit:]))

        return ResponseModel(
            success=True,
            data=[
                TransitionHistoryResponse(
                    from_state=record.get("from_state"),
                    to_state=record.get("to_state"),
                    timestamp=record.get("timestamp"),
                    actor=record.get("actor"),
                    kwargs=record.get("kwargs", {}),
                )
                for record in limited_history
            ],
            message=f"ECN {ecn_id} 状态转换历史（最近 {len(limited_history)} 条）",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取转换历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 允许的转换查询端点 ==========


@router.get("/{ecn_id}/allowed-transitions", response_model=ResponseModel[StateInfoResponse])
def get_allowed_transitions(
    ecn_id: int,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    获取当前状态允许的所有转换目标状态

    - 检查 ECN 是否存在
    - 获取状态机实例
    - 获取允许的转换列表
    """
    try:
        state_machine = get_ecn_state_machine(ecn_id, db)
        current_state, display_name, description, is_editable, allowed = _state_metadata(
            state_machine
        )

        return ResponseModel(
            success=True,
            data=StateInfoResponse(
                current_state=current_state,
                display_name=display_name,
                description=description,
                is_editable=is_editable,
                allowed_transitions=allowed,
            ),
            message=f"ECN {ecn_id} 允许 {len(allowed.get(current_state, []))} 个转换",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取允许转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 批量操作端点 ==========


@router.post("/{ecn_id}/batch-transition")
async def batch_transition_ecns(
    ecn_id: int,
    ecn_ids: List[int],
    target_state: str,
    comment: str = "",
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    批量状态转换

    支持批量操作多个 ECN 的状态
    """
    results = []

    for item_id in ecn_ids:
        try:
            state_machine = get_ecn_state_machine(item_id, db)
            current_state = _state_value(state_machine)

            if current_state in CURRENT_ECN_TRANSITIONS:
                payload = _apply_current_transition(
                    state_machine=state_machine,
                    target_state=target_state,
                    comment=comment,
                    current_user=current_user,
                    db=db,
                )
                results.append(
                    {
                        "ecn_id": item_id,
                        "success": True,
                        "previous_state": payload["previous_state"],
                        "current_state": payload["current_state"],
                    }
                )
                continue

            try:
                target_status = EcnStatus(target_state)
                target_value = target_status.value
            except ValueError:
                target_value = target_state

            can_transition, reason = state_machine.can_transition_to(target_value)

            if not can_transition:
                results.append(
                    {
                        "ecn_id": item_id,
                        "success": False,
                        "error": reason,
                    }
                )
                continue

            # 执行转换
            state_machine.transition_to(target_value, comment=comment)

            previous_state = (
                state_machine.previous_state.value
                if hasattr(state_machine.previous_state, "value")
                else state_machine.previous_state
            )
            current_state = (
                state_machine.current_state.value
                if hasattr(state_machine.current_state, "value")
                else state_machine.current_state
            )

            results.append(
                {
                    "ecn_id": item_id,
                    "success": True,
                    "previous_state": previous_state,
                    "current_state": current_state,
                }
            )
        except Exception as e:
            results.append(
                {
                    "ecn_id": item_id,
                    "success": False,
                    "error": str(e),
                }
            )

    successful = sum(1 for r in results if r.get("success", False))

    return ResponseModel(
        success=successful,
        data=results,
        message=f"批量转换完成：{successful}/{len(ecn_ids)} 成功",
    )


# ========== 健康检查端点 ==========


@router.get("/{ecn_id}/health", response_model=ResponseModel[Dict[str, Any]])
def get_ecn_state_health(
    ecn_id: int,
    current_user: Any = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    获取 ECN 状态健康度

    检查：
    - 当前状态是否正常
    - 是否处于卡住状态
    - 最近转换是否成功
    """
    try:
        state_machine = get_ecn_state_machine(ecn_id, db)
        current_state = _state_value(state_machine)

        if current_state in CURRENT_ECN_TRANSITIONS:
            if current_state in {"CANCELLED", "CLOSED"}:
                health_status = "terminated"
            elif current_state in {"DRAFT", "READY_TO_SUBMIT"}:
                health_status = "draft"
            elif current_state in {
                "EVALUATING",
                "EVALUATION_PENDING",
                "EVALUATION_IN_PROGRESS",
                "PENDING_APPROVAL",
                "APPROVAL_PENDING",
            }:
                health_status = "at_risk"
            elif current_state in {"EXECUTION_PAUSED", "PENDING_VERIFY"}:
                health_status = "paused"
            elif current_state in {"COMPLETED", "EXECUTION_COMPLETED", "APPROVED"}:
                health_status = "completed"
            elif current_state in {"READY_TO_CLOSE"}:
                health_status = "nearly_closed"
            else:
                health_status = "healthy"

            return ResponseModel(
                success=True,
                data={
                    "ecn_id": ecn_id,
                    "current_state": current_state,
                    "health_status": health_status,
                    "can_edit": current_state in CURRENT_EDITABLE_STATES,
                    "can_submit": current_state in CURRENT_SUBMITTABLE_STATES,
                    "is_cancellable": current_state in CURRENT_CANCELLABLE_STATES,
                },
                message=f"ECN {ecn_id} 健康度: {health_status}",
            )

        # 简化的历史状态健康度判断
        health_status = "healthy"

        if current_state in [EcnStatus.DRAFT.value, EcnStatus.READY_TO_SUBMIT.value]:
            health_status = "draft"
        elif current_state == EcnStatus.CANCELLED.value:
            health_status = "terminated"
        elif current_state in [
            EcnStatus.EVALUATION_PENDING.value,
            EcnStatus.EVALUATION_IN_PROGRESS.value,
        ]:
            health_status = "at_risk"
        elif current_state in [EcnStatus.IN_PROGRESS.value, EcnStatus.EXECUTION_PAUSED.value]:
            health_status = "paused"
        elif current_state in [EcnStatus.APPROVED.value, EcnStatus.EXECUTION_COMPLETED.value]:
            health_status = "completed"
        elif current_state in [EcnStatus.READY_TO_CLOSE.value]:
            health_status = "nearly_closed"
        else:
            health_status = "unknown"

        try:
            status = EcnStatus(current_state)
        except ValueError:
            status = None

        return ResponseModel(
            success=True,
            data={
                "ecn_id": ecn_id,
                "current_state": current_state,
                "health_status": health_status,
                "can_edit": status.is_editable if status else state_machine.is_editable(),
                "can_submit": status.is_submittable if status else False,
                "is_cancellable": status.is_cancellable if status else state_machine.is_cancellable(),
            },
            message=f"ECN {ecn_id} 健康度: {health_status}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取ECN健康度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
