# -*- coding: utf-8 -*-
"""
ECN执行流程 API endpoints

包含：开始执行、验证、关闭
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnLog, EcnTask
from app.models.user import User
from app.schemas.ecn import EcnClose, EcnResponse, EcnStartExecution, EcnVerify
from app.utils.db_helpers import get_or_404

from .utils import build_ecn_response

router = APIRouter()


@router.put("/ecns/{ecn_id}/start-execution", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def start_ecn_execution(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    execution_in: EcnStartExecution,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始执行ECN
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    if ecn.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能开始执行已审批的ECN")

    ecn.status = "EXECUTING"
    ecn.execution_start = datetime.now()
    ecn.current_step = "EXECUTION"

    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="STATUS_CHANGE",
        log_action="START_EXECUTION",
        old_status="APPROVED",
        new_status="EXECUTING",
        log_content=execution_in.remark or "开始执行ECN",
        created_by=current_user.id
    )
    db.add(log)
    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)


@router.put("/ecns/{ecn_id}/verify", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def verify_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    verify_in: EcnVerify,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证ECN执行结果
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    if ecn.status != "EXECUTING":
        raise HTTPException(status_code=400, detail="只能验证执行中的ECN")

    # 检查是否所有任务都已完成
    pending_tasks = db.query(EcnTask).filter(
        EcnTask.ecn_id == ecn_id,
        EcnTask.status != "COMPLETED"
    ).count()

    if pending_tasks > 0:
        raise HTTPException(status_code=400, detail="还有未完成的任务，无法验证")

    old_status = ecn.status
    if verify_in.verify_result == "PASS":
        ecn.status = "COMPLETED"
        ecn.current_step = "COMPLETED"
        ecn.execution_end = datetime.now()
    else:
        ecn.status = "PENDING_VERIFY"
        ecn.current_step = "VERIFICATION_FAILED"

    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="VERIFICATION",
        log_action="VERIFY",
        old_status=old_status,
        new_status=ecn.status,
        log_content=verify_in.verify_note or f"验证结果: {verify_in.verify_result}",
        created_by=current_user.id
    )
    db.add(log)
    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)


@router.put("/ecns/{ecn_id}/close", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def close_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    close_in: EcnClose,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭ECN
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    if ecn.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只能关闭已完成的ECN")

    ecn.status = "CLOSED"
    ecn.closed_at = datetime.now()
    ecn.closed_by = current_user.id
    ecn.current_step = "CLOSED"

    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="STATUS_CHANGE",
        log_action="CLOSE",
        old_status="COMPLETED",
        new_status="CLOSED",
        log_content=close_in.close_note or "ECN已关闭",
        created_by=current_user.id
    )
    db.add(log)
    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)
