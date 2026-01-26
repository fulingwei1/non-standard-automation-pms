# -*- coding: utf-8 -*-
"""
ECN 状态机管理 API 端点
提供状态查询、状态转换、状态历史等功能
"""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.core.state_machine.ecn_status import EcnStatus
from app.core.state_machine.ecn import EcnStateMachine
from app.models.ecn import Ecn
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ecn/state-machine", tags=["ECN状态机"])


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
        current_state = state_machine.current_state.value

        return ResponseModel(
            success=True,
            data=StateInfoResponse(
                current_state=current_state,
                display_name=state_machine.get_status_display(),
                description=state_machine.current_state.description,
                is_editable=state_machine.current_state.is_editable,
                allowed_transitions=state_machine.get_allowed_transitions(),
            ),
            message=f"ECN {ecn_id} 当前状态: {current_state}",
        )
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

        # 验证目标状态
        try:
            target_status = EcnStatus(request.target_state)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"无效的状态值: {request.target_state}"
            )

        # 检查是否可以转换
        can_transition, reason = state_machine.can_transition_to(target_status.value)
        if not can_transition:
            raise HTTPException(status_code=400, detail=f"不允许的状态转换: {reason}")

        # 执行转换
        state_machine.transition_to(
            request.target_status.value, comment=request.comment
        )

        return ResponseModel(
            success=True,
            data={
                "previous_state": state_machine.previous_state.value
                if state_machine.previous_state
                else None,
                "current_state": state_machine.current_state.value,
                "timestamp": state_machine._transition_history[-1].get("timestamp"),
                "actor": current_user.username,
            },
            message=f"ECN {ecn_id} 状态已从 {state_machine.previous_state.value if state_machine.previous_state else 'DRAFT'} 转换到 {state_machine.current_state.value}",
        )
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
    except Exception as e:
        logger.error(f"获取转换历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 允许的转换查询端点 ==========


@router.get(
    "/{ecn_id}/allowed-transitions", response_model=ResponseModel[StateInfoResponse]
)
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
        allowed = state_machine.get_allowed_transitions()

        return ResponseModel(
            success=True,
            data=StateInfoResponse(
                current_state=state_machine.current_state.value,
                display_name=state_machine.get_status_display(),
                description=state_machine.current_state.description,
                is_editable=state_machine.current_state.is_editable,
                allowed_transitions=allowed,
            ),
            message=f"ECN {ecn_id} 允许 {len(allowed.get(current_state.display_name(), []))} 个转换",
        )
    except Exception as e:
        logger.error(f"获取允许转换失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 批量操作端点 ==========


@router.post("/{ecn_id}/batch-transition")
async def batch_transition_ecns(
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

    for ecn_id in ecn_ids:
        try:
            state_machine = get_ecn_state_machine(ecn_id, db)

            # 验证目标状态
            target_status = EcnStatus(target_state)
            if not isinstance(target_status, EcnStatus):
                raise HTTPException(
                    status_code=400, detail=f"无效的状态值: {target_state}"
                )

            # 检查是否可以转换
            can_transition, reason = state_machine.can_transition_to(
                target_status.value
            )

            if not can_transition:
                results.append(
                    {
                        "ecn_id": ecn_id,
                        "success": False,
                        "error": reason,
                    }
                )
                continue

            # 执行转换
            state_machine.transition_to(target_status.value, comment=comment)

            results.append(
                {
                    "ecn_id": ecn_id,
                    "success": True,
                    "previous_state": state_machine.previous_state.value
                    if state_machine.previous_state
                    else None,
                    "current_state": state_machine.current_state.value,
                }
            )
        except Exception as e:
            results.append(
                {
                    "ecn_id": ecn_id,
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
        current_state = state_machine.current_state.value

        # 简化的健康度判断
        health_status = "healthy"

        if current_state in [
            EcnStatus.DRAFT,
            EcnStatus.READY_TO_SUBMIT,
            EcnStatus.CANCELLED,
        ]:
            health_status = "terminated"
        elif current_state in [
            EcnStatus.EVALUATION_PENDING,
            EcnStatus.EVALUATION_IN_PROGRESS,
        ]:
            health_status = "at_risk"
        elif current_state in [EcnStatus.IN_PROGRESS, EcnStatus.EXECUTION_PAUSED]:
            health_status = "paused"
        elif current_state in [EcnStatus.APPROVED, EcnStatus.EXECUTION_COMPLETED]:
            health_status = "completed"
        elif current_state in [EcnStatus.READY_TO_CLOSE]:
            health_status = "nearly_closed"
        else:
            health_status = "unknown"

        return ResponseModel(
            success=True,
            data={
                "ecn_id": ecn_id,
                "current_state": current_state,
                "health_status": health_status,
                "can_edit": state_machine.current_state.is_editable,
                "can_submit": state_machine.current_state.is_submittable,
                is_cancellable: state_machine.current_state.is_cancellable,
            },
            message=f"ECN {ecn_id} 健康度: {health_status}",
        )
    except Exception as e:
        logger.error(f"获取ECN健康度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
