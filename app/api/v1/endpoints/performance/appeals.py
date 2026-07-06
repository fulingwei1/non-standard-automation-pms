# -*- coding: utf-8 -*-
"""绩效申诉 API."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.performance import (
    PerformanceAdjustmentHistory,
    PerformanceAppeal,
    PerformanceResult,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/performance/appeals", tags=["performance-appeals"])

VALID_HANDLE_STATUSES = {"ACCEPTED", "REJECTED", "CLOSED"}


class PerformanceAppealCreate(BaseModel):
    """绩效申诉提交参数."""

    result_id: int = Field(..., description="绩效结果ID")
    appeal_reason: str = Field(..., min_length=1, description="申诉理由")
    expected_score: Optional[Decimal] = Field(None, description="期望得分")
    supporting_evidence: Optional[str] = Field(None, description="支撑证据")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件")


class PerformanceAppealHandle(BaseModel):
    """绩效申诉处理参数."""

    status: str = Field(..., description="处理状态: ACCEPTED/REJECTED/CLOSED")
    handle_result: str = Field(..., min_length=1, description="处理结果")
    new_score: Optional[Decimal] = Field(None, description="调整后得分")
    new_level: Optional[str] = Field(None, description="调整后等级")


def _display_name(user: User) -> str:
    return user.real_name or user.username


def _decimal_to_float(value: Optional[Decimal]) -> Optional[float]:
    return float(value) if value is not None else None


def _datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _get_roles(user: User) -> List[Any]:
    roles = getattr(user, "roles", []) or []
    if hasattr(roles, "all"):
        try:
            return list(roles.all())
        except Exception:
            return []
    return list(roles)


def _can_manage_performance(user: User) -> bool:
    if getattr(user, "is_superuser", False):
        return True

    manage_codes = {
        "admin",
        "super_admin",
        "hr",
        "hr_manager",
        "performance_manager",
        "performance_admin",
    }
    manage_names = {"管理员", "超级管理员", "人事", "人力资源", "绩效管理员", "HR"}
    for user_role in _get_roles(user):
        role = getattr(user_role, "role", None)
        role_code = (getattr(role, "role_code", "") or "").lower()
        role_name = getattr(role, "role_name", "") or ""
        if role_code in manage_codes or role_name in manage_names:
            return True
    return False


def _get_result_or_404(db: Session, result_id: int) -> PerformanceResult:
    result = db.query(PerformanceResult).filter(PerformanceResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="绩效结果不存在")
    return result


def _get_appeal_or_404(db: Session, appeal_id: int) -> PerformanceAppeal:
    appeal = db.query(PerformanceAppeal).filter(PerformanceAppeal.id == appeal_id).first()
    if not appeal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="绩效申诉不存在")
    return appeal


def _calculate_level(score: Decimal) -> str:
    if score >= Decimal("85"):
        return "S"
    if score >= Decimal("70"):
        return "A"
    if score >= Decimal("60"):
        return "B"
    if score >= Decimal("40"):
        return "C"
    return "D"


def _appeal_to_dict(appeal: PerformanceAppeal) -> Dict[str, Any]:
    return {
        "id": appeal.id,
        "result_id": appeal.result_id,
        "appellant_id": appeal.appellant_id,
        "appellant_name": appeal.appellant_name,
        "appeal_reason": appeal.appeal_reason,
        "expected_score": _decimal_to_float(appeal.expected_score),
        "supporting_evidence": appeal.supporting_evidence,
        "attachments": appeal.attachments or [],
        "appeal_time": _datetime_to_iso(appeal.appeal_time),
        "status": appeal.status,
        "handler_id": appeal.handler_id,
        "handler_name": appeal.handler_name,
        "handle_time": _datetime_to_iso(appeal.handle_time),
        "handle_result": appeal.handle_result,
        "new_score": _decimal_to_float(appeal.new_score),
        "new_level": appeal.new_level,
    }


@router.post("", response_model=ResponseModel)
def submit_performance_appeal(
    payload: PerformanceAppealCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """提交绩效申诉."""
    result = _get_result_or_404(db, payload.result_id)
    if result.user_id != current_user.id and not _can_manage_performance(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能申诉自己的绩效结果")

    appeal = PerformanceAppeal(
        result_id=result.id,
        appellant_id=current_user.id,
        appellant_name=_display_name(current_user),
        appeal_reason=payload.appeal_reason.strip(),
        expected_score=payload.expected_score,
        supporting_evidence=payload.supporting_evidence,
        attachments=payload.attachments or [],
        status="PENDING",
        appeal_time=datetime.now(),
    )
    result.status = "APPEALING"

    db.add(appeal)
    db.commit()
    db.refresh(appeal)
    return ResponseModel(code=200, message="申诉提交成功", data=_appeal_to_dict(appeal))


@router.get("", response_model=ResponseModel)
def list_performance_appeals(
    result_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """查询绩效申诉列表."""
    query = db.query(PerformanceAppeal)
    if not _can_manage_performance(current_user):
        query = query.filter(PerformanceAppeal.appellant_id == current_user.id)
    if result_id is not None:
        query = query.filter(PerformanceAppeal.result_id == result_id)
    if status_filter:
        query = query.filter(PerformanceAppeal.status == status_filter)

    total = query.count()
    appeals = (
        query.order_by(desc(PerformanceAppeal.appeal_time))
        .offset(max(skip, 0))
        .limit(max(min(limit, 1000), 1))
        .all()
    )
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [_appeal_to_dict(appeal) for appeal in appeals],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    )


@router.put("/{appeal_id}/handle", response_model=ResponseModel)
def handle_performance_appeal(
    appeal_id: int,
    payload: PerformanceAppealHandle,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """处理绩效申诉."""
    if not _can_manage_performance(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限处理绩效申诉")

    handle_status = payload.status.upper()
    if handle_status not in VALID_HANDLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="申诉处理状态无效")

    appeal = _get_appeal_or_404(db, appeal_id)
    result = _get_result_or_404(db, appeal.result_id)

    appeal.status = handle_status
    appeal.handler_id = current_user.id
    appeal.handler_name = _display_name(current_user)
    appeal.handle_time = datetime.now()
    appeal.handle_result = payload.handle_result.strip()
    appeal.new_score = payload.new_score
    appeal.new_level = payload.new_level

    if handle_status == "ACCEPTED":
        new_score = payload.new_score if payload.new_score is not None else result.total_score
        new_level = payload.new_level or (result.level if new_score is None else _calculate_level(new_score))
        if not result.is_adjusted:
            result.original_total_score = result.total_score
            result.original_dept_rank = result.dept_rank
            result.original_company_rank = result.company_rank

        history = PerformanceAdjustmentHistory(
            result_id=result.id,
            original_total_score=result.total_score,
            original_dept_rank=result.dept_rank,
            original_company_rank=result.company_rank,
            original_level=result.level,
            adjusted_total_score=new_score,
            adjusted_dept_rank=result.dept_rank,
            adjusted_company_rank=result.company_rank,
            adjusted_level=new_level,
            adjustment_reason=f"绩效申诉处理：{appeal.handle_result}",
            adjusted_by=current_user.id,
            adjusted_by_name=_display_name(current_user),
            adjusted_at=appeal.handle_time,
        )
        db.add(history)

        result.total_score = new_score
        result.adjusted_total_score = new_score
        result.level = new_level
        result.adjustment_reason = history.adjustment_reason
        result.adjusted_by = current_user.id
        result.adjusted_at = appeal.handle_time
        result.is_adjusted = True
        result.status = "APPEAL_ACCEPTED"
    elif handle_status == "REJECTED":
        result.status = "APPEAL_REJECTED"
    else:
        result.status = "APPEAL_CLOSED"

    db.commit()
    db.refresh(appeal)
    return ResponseModel(code=200, message="申诉处理成功", data=_appeal_to_dict(appeal))
