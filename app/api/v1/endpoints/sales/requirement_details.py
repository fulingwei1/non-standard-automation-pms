# -*- coding: utf-8 -*-
"""
需求管理 - 需求详情管理

包含线索需求详情的CRUD操作
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Lead, LeadRequirementDetail
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.sales import (
    LeadRequirementDetailCreate,
    LeadRequirementDetailResponse,
    LeadRequirementDetailUpdate,
)
from app.services.sales.lead_operation_audit import log_lead_operation
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _requirement_detail_audit_value(detail: LeadRequirementDetail) -> dict[str, Any]:
    fields = [
        "id",
        "lead_id",
        "customer_factory_location",
        "target_object_type",
        "application_scenario",
        "delivery_mode",
        "expected_delivery_date",
        "requirement_source",
        "requirement_maturity",
        "has_sow",
        "has_interface_doc",
        "has_drawing_doc",
        "cycle_time_seconds",
        "workstation_count",
        "acceptance_method",
        "acceptance_basis",
        "requirement_items",
        "technical_spec",
        "delivery_requirements",
        "special_notes",
        "requirement_version",
        "is_frozen",
        "frozen_at",
        "frozen_by",
    ]
    return {field: _audit_scalar(getattr(detail, field, None)) for field in fields}


@router.get("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse)
def get_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索需求详情
    """
    get_or_404(db, Lead, lead_id, detail="线索不存在")

    detail = (
        db.query(LeadRequirementDetail).filter(LeadRequirementDetail.lead_id == lead_id).first()
    )

    if not detail:
        return LeadRequirementDetailResponse(
            id=0,
            lead_id=lead_id,
            requirement_maturity=3,
            has_sow=False,
            has_interface_doc=False,
            has_drawing_doc=False,
            requirement_version="DRAFT",
            is_frozen=False,
        )

    # 获取冻结人姓名
    frozen_by_name = None
    if detail.frozen_by:
        user = db.query(User).filter(User.id == detail.frozen_by).first()
        frozen_by_name = user.real_name if user else None

    # 构建响应，包含 frozen_by_name
    response_data = LeadRequirementDetailResponse.model_validate(detail)
    if hasattr(response_data, "frozen_by_name"):
        response_data.frozen_by_name = frozen_by_name

    return response_data


@router.post(
    "/leads/{lead_id}/requirement-detail",
    response_model=LeadRequirementDetailResponse,
    status_code=201,
)
def create_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    detail_in: LeadRequirementDetailCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建线索需求详情
    """
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")

    # 检查是否已存在
    existing = (
        db.query(LeadRequirementDetail).filter(LeadRequirementDetail.lead_id == lead_id).first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="该线索已存在需求详情，请使用更新接口")

    detail = LeadRequirementDetail(lead_id=lead_id, **detail_in.model_dump(exclude_none=True))
    db.add(detail)
    db.flush()
    log_lead_operation(
        db,
        lead,
        SalesOperationType.UPDATE,
        current_user,
        old_value={"requirement_detail": None},
        new_value={"requirement_detail": _requirement_detail_audit_value(detail)},
        operation_desc="创建线索需求详情",
    )
    db.commit()
    db.refresh(detail)

    return LeadRequirementDetailResponse.model_validate(detail)


@router.put("/leads/{lead_id}/requirement-detail", response_model=LeadRequirementDetailResponse)
def update_lead_requirement_detail(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    detail_in: LeadRequirementDetailUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新线索需求详情
    """
    lead = get_or_404(db, Lead, lead_id, detail="线索不存在")

    detail = (
        db.query(LeadRequirementDetail).filter(LeadRequirementDetail.lead_id == lead_id).first()
    )

    if not detail:
        raise HTTPException(status_code=404, detail="需求详情不存在")

    # 更新字段
    old_value = _requirement_detail_audit_value(detail)
    update_data = detail_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(detail, field, value)
    db.add(detail)
    db.flush()
    log_lead_operation(
        db,
        lead,
        SalesOperationType.UPDATE,
        current_user,
        old_value={"requirement_detail": old_value},
        new_value={"requirement_detail": _requirement_detail_audit_value(detail)},
        operation_desc="更新线索需求详情",
    )
    db.commit()
    db.refresh(detail)

    return LeadRequirementDetailResponse.model_validate(detail)
