# -*- coding: utf-8 -*-
"""
ECN成本影响跟踪 API

端点：
  POST  /ecns/{ecn_id}/cost-impact-analysis  — 成本影响分析
  GET   /ecns/{ecn_id}/cost-tracking          — 成本执行跟踪
  POST  /ecns/{ecn_id}/cost-records           — 新增成本记录
  GET   /ecns/{ecn_id}/cost-records           — 查询成本记录列表
  POST  /ecns/cost-records/{record_id}/approve — 审批成本记录
  POST  /ecns/{ecn_id}/cost-alerts            — 成本预警检查
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.ecn_cost_impact import (
    CostAlertCreate,
    CostAlertResponse,
    CostImpactAnalysisResponse,
    CostTrackingResponse,
    EcnCostRecordCreate,
    EcnCostRecordResponse,
)
from app.services import ecn_cost_impact_service as service

router = APIRouter()


# ─────────────────────────────────────────────────
#  1. 成本影响分析
# ─────────────────────────────────────────────────


@router.post(
    "/ecns/{ecn_id}/cost-impact-analysis",
    response_model=CostImpactAnalysisResponse,
    summary="ECN成本影响分析",
    description="分析ECN导致的直接成本（报废/返工/新购）和间接成本（延期/索赔/管理），按类型分类统计",
)
def analyze_cost_impact(
    ecn_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        result = service.cost_impact_analysis(db, ecn_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ─────────────────────────────────────────────────
#  2. 成本执行跟踪
# ─────────────────────────────────────────────────


@router.get(
    "/ecns/{ecn_id}/cost-tracking",
    response_model=CostTrackingResponse,
    summary="ECN成本执行跟踪",
    description="预算vs实际对比、成本趋势、预计最终成本",
)
def get_cost_tracking(
    ecn_id: int,
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        result = service.get_cost_tracking(db, ecn_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ─────────────────────────────────────────────────
#  3. 成本记录
# ─────────────────────────────────────────────────


@router.post(
    "/ecns/{ecn_id}/cost-records",
    response_model=EcnCostRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新增ECN成本记录",
    description="记录实际发生的成本，关联凭证，进入审批流程",
)
def create_cost_record(
    ecn_id: int,
    *,
    db: Session = Depends(deps.get_db),
    req: EcnCostRecordCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    if req.ecn_id != ecn_id:
        raise HTTPException(status_code=400, detail="路径ecn_id与请求体不一致")
    try:
        record = service.create_cost_record(
            db,
            current_user_id=current_user.id,
            ecn_id=ecn_id,
            cost_type=req.cost_type,
            project_id=req.project_id,
            machine_id=req.machine_id,
            cost_category=req.cost_category,
            estimated_amount=req.estimated_amount,
            actual_amount=req.actual_amount,
            currency=req.currency,
            cost_date=req.cost_date,
            material_id=req.material_id,
            material_code=req.material_code,
            material_name=req.material_name,
            quantity=req.quantity,
            unit_price=req.unit_price,
            rework_hours=req.rework_hours,
            hourly_rate=req.hourly_rate,
            voucher_type=req.voucher_type,
            voucher_no=req.voucher_no,
            voucher_attachment_id=req.voucher_attachment_id,
            vendor_id=req.vendor_id,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return record


@router.get(
    "/ecns/{ecn_id}/cost-records",
    response_model=List[EcnCostRecordResponse],
    summary="查询ECN成本记录",
)
def list_cost_records(
    ecn_id: int,
    *,
    db: Session = Depends(deps.get_db),
    cost_type: Optional[str] = Query(None, description="按成本类型过滤"),
    approval_status: Optional[str] = Query(None, description="按审批状态过滤"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    return service.list_cost_records(
        db, ecn_id, cost_type=cost_type, approval_status=approval_status
    )


@router.post(
    "/ecns/cost-records/{record_id}/approve",
    response_model=EcnCostRecordResponse,
    summary="审批成本记录",
)
def approve_cost_record(
    record_id: int,
    *,
    db: Session = Depends(deps.get_db),
    approved: bool = Query(..., description="是否批准"),
    note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        return service.approve_cost_record(
            db, record_id, current_user.id, approved=approved, note=note
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─────────────────────────────────────────────────
#  4. 成本预警
# ─────────────────────────────────────────────────


@router.post(
    "/ecns/{ecn_id}/cost-alerts",
    response_model=CostAlertResponse,
    summary="ECN成本预警检查",
    description="检查成本超预算、大额待审批、趋势异常等预警",
)
def check_cost_alerts(
    ecn_id: int,
    *,
    db: Session = Depends(deps.get_db),
    req: CostAlertCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    if req.ecn_id != ecn_id:
        raise HTTPException(status_code=400, detail="路径ecn_id与请求体不一致")
    try:
        return service.check_cost_alerts(
            db,
            ecn_id,
            budget_threshold=req.budget_threshold,
            large_amount_threshold=req.large_amount_threshold,
            trend_check=req.trend_check,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
