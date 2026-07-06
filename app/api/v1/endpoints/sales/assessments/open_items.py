# -*- coding: utf-8 -*-
"""
待办事项管理 API endpoints

包含待办事项的查询、创建、更新、关闭等端点
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.enums import AssessmentSourceTypeEnum, OpenItemStatusEnum
from app.models.sales import Lead, OpenItem, Opportunity
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sales import OpenItemCreate, OpenItemResponse
from app.services.sales.lead_operation_audit import log_lead_operation
from app.services.sales.opportunity_operation_audit import log_opportunity_operation
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _open_item_audit_value(open_item: OpenItem) -> dict[str, Any]:
    fields = [
        "id",
        "source_type",
        "source_id",
        "item_code",
        "item_type",
        "description",
        "responsible_party",
        "responsible_person_id",
        "due_date",
        "status",
        "close_evidence",
        "blocks_quotation",
        "closed_at",
    ]
    return {field: _audit_scalar(getattr(open_item, field, None)) for field in fields}


def _generate_open_item_code(db: Session, source_type: str, source_id: int) -> str:
    today = datetime.now().strftime("%y%m%d")
    source_prefix = "L" if source_type == AssessmentSourceTypeEnum.LEAD.value else "O"
    code_prefix = f"OI-{source_prefix}-{today}-{source_id:03d}"
    sequence = (
        db.query(OpenItem).filter(OpenItem.item_code.like(f"{code_prefix}-%")).count()
    ) + 1
    return f"{code_prefix}-{sequence:02d}"


def _log_open_item_source_operation(
    db: Session,
    open_item: OpenItem,
    operation_type: str,
    current_user: User,
    *,
    old_open_item: dict[str, Any] | None,
    new_open_item: dict[str, Any] | None,
    operation_desc: str,
    remark: str | None = None,
) -> None:
    old_value = {"open_item": old_open_item}
    new_value = {"open_item": new_open_item}
    if open_item.source_type == AssessmentSourceTypeEnum.LEAD.value:
        lead = get_or_404(db, Lead, open_item.source_id, detail="线索不存在")
        log_lead_operation(
            db,
            lead,
            operation_type,
            current_user,
            old_value=old_value,
            new_value=new_value,
            operation_desc=operation_desc,
            remark=remark,
        )
        return

    if open_item.source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value:
        opportunity = get_or_404(db, Opportunity, open_item.source_id, detail="商机不存在")
        log_opportunity_operation(
            db,
            opportunity,
            operation_type,
            current_user,
            old_value=old_value,
            new_value=new_value,
            operation_desc=operation_desc,
            remark=remark,
        )


@router.get("/open-items", response_model=PaginatedResponse[OpenItemResponse])
def list_open_items(
    *,
    db: Session = Depends(deps.get_db),
    source_type: Optional[str] = Query(None, description="来源类型"),
    source_id: Optional[int] = Query(None, description="来源ID"),
    status: Optional[str] = Query(None, description="状态"),
    blocks_quotation: Optional[bool] = Query(None, description="是否阻塞报价"),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取未决事项列表"""
    query = db.query(OpenItem)

    if source_type:
        query = query.filter(OpenItem.source_type == source_type)
    if source_id:
        query = query.filter(OpenItem.source_id == source_id)
    if status:
        query = query.filter(OpenItem.status == status)
    if blocks_quotation is not None:
        query = query.filter(OpenItem.blocks_quotation == blocks_quotation)

    total = query.count()
    items = apply_pagination(
        query.order_by(desc(OpenItem.created_at)), pagination.offset, pagination.limit
    ).all()

    result = []
    for item in items:
        responsible_person_name = None
        if item.responsible_person_id:
            person = db.query(User).filter(User.id == item.responsible_person_id).first()
            responsible_person_name = person.real_name if person else None

        result.append(
            OpenItemResponse(
                id=item.id,
                source_type=item.source_type,
                source_id=item.source_id,
                item_code=item.item_code,
                item_type=item.item_type,
                description=item.description,
                responsible_party=item.responsible_party,
                responsible_person_id=item.responsible_person_id,
                due_date=item.due_date,
                status=item.status,
                close_evidence=item.close_evidence,
                blocks_quotation=item.blocks_quotation,
                closed_at=item.closed_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
                responsible_person_name=responsible_person_name,
            )
        )

    return PaginatedResponse(
        items=result, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.post("/leads/{lead_id}/open-items", response_model=OpenItemResponse, status_code=201)
def create_open_item(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    request: OpenItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建未决事项（线索）"""
    get_or_404(db, Lead, lead_id, detail="线索不存在")

    item_code = _generate_open_item_code(db, AssessmentSourceTypeEnum.LEAD.value, lead_id)

    open_item = OpenItem(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=lead_id,
        item_code=item_code,
        item_type=request.item_type,
        description=request.description,
        responsible_party=request.responsible_party,
        responsible_person_id=request.responsible_person_id,
        due_date=request.due_date,
        blocks_quotation=request.blocks_quotation,
    )

    db.add(open_item)
    db.flush()
    _log_open_item_source_operation(
        db,
        open_item,
        SalesOperationType.UPDATE,
        current_user,
        old_open_item=None,
        new_open_item=_open_item_audit_value(open_item),
        operation_desc="创建线索未决事项",
        remark=request.description,
    )
    db.commit()
    db.refresh(open_item)

    responsible_person_name = None
    if open_item.responsible_person_id:
        person = db.query(User).filter(User.id == open_item.responsible_person_id).first()
        responsible_person_name = person.real_name if person else None

    return OpenItemResponse(
        id=open_item.id,
        source_type=open_item.source_type,
        source_id=open_item.source_id,
        item_code=open_item.item_code,
        item_type=open_item.item_type,
        description=open_item.description,
        responsible_party=open_item.responsible_party,
        responsible_person_id=open_item.responsible_person_id,
        due_date=open_item.due_date,
        status=open_item.status,
        close_evidence=open_item.close_evidence,
        blocks_quotation=open_item.blocks_quotation,
        closed_at=open_item.closed_at,
        created_at=open_item.created_at,
        updated_at=open_item.updated_at,
        responsible_person_name=responsible_person_name,
    )


@router.post("/opportunities/{opp_id}/open-items", response_model=OpenItemResponse, status_code=201)
def create_open_item_for_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    request: OpenItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建未决事项（商机）"""
    get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    item_code = _generate_open_item_code(
        db, AssessmentSourceTypeEnum.OPPORTUNITY.value, opp_id
    )

    open_item = OpenItem(
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=opp_id,
        item_code=item_code,
        item_type=request.item_type,
        description=request.description,
        responsible_party=request.responsible_party,
        responsible_person_id=request.responsible_person_id,
        due_date=request.due_date,
        blocks_quotation=request.blocks_quotation,
    )

    db.add(open_item)
    db.flush()
    _log_open_item_source_operation(
        db,
        open_item,
        SalesOperationType.UPDATE,
        current_user,
        old_open_item=None,
        new_open_item=_open_item_audit_value(open_item),
        operation_desc="创建商机未决事项",
        remark=request.description,
    )
    db.commit()
    db.refresh(open_item)

    responsible_person_name = None
    if open_item.responsible_person_id:
        person = db.query(User).filter(User.id == open_item.responsible_person_id).first()
        responsible_person_name = person.real_name if person else None

    return OpenItemResponse(
        id=open_item.id,
        source_type=open_item.source_type,
        source_id=open_item.source_id,
        item_code=open_item.item_code,
        item_type=open_item.item_type,
        description=open_item.description,
        responsible_party=open_item.responsible_party,
        responsible_person_id=open_item.responsible_person_id,
        due_date=open_item.due_date,
        status=open_item.status,
        close_evidence=open_item.close_evidence,
        blocks_quotation=open_item.blocks_quotation,
        closed_at=open_item.closed_at,
        created_at=open_item.created_at,
        updated_at=open_item.updated_at,
        responsible_person_name=responsible_person_name,
    )


@router.put("/open-items/{item_id}", response_model=OpenItemResponse)
def update_open_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    request: OpenItemCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新未决事项"""
    open_item = get_or_404(db, OpenItem, item_id, detail="未决事项不存在")
    old_open_item = _open_item_audit_value(open_item)

    open_item.item_type = request.item_type
    open_item.description = request.description
    open_item.responsible_party = request.responsible_party
    open_item.responsible_person_id = request.responsible_person_id
    open_item.due_date = request.due_date
    open_item.blocks_quotation = request.blocks_quotation

    db.flush()
    _log_open_item_source_operation(
        db,
        open_item,
        SalesOperationType.UPDATE,
        current_user,
        old_open_item=old_open_item,
        new_open_item=_open_item_audit_value(open_item),
        operation_desc="更新未决事项",
        remark=request.description,
    )
    db.commit()
    db.refresh(open_item)

    responsible_person_name = None
    if open_item.responsible_person_id:
        person = db.query(User).filter(User.id == open_item.responsible_person_id).first()
        responsible_person_name = person.real_name if person else None

    return OpenItemResponse(
        id=open_item.id,
        source_type=open_item.source_type,
        source_id=open_item.source_id,
        item_code=open_item.item_code,
        item_type=open_item.item_type,
        description=open_item.description,
        responsible_party=open_item.responsible_party,
        responsible_person_id=open_item.responsible_person_id,
        due_date=open_item.due_date,
        status=open_item.status,
        close_evidence=open_item.close_evidence,
        blocks_quotation=open_item.blocks_quotation,
        closed_at=open_item.closed_at,
        created_at=open_item.created_at,
        updated_at=open_item.updated_at,
        responsible_person_name=responsible_person_name,
    )


@router.post("/open-items/{item_id}/close", response_model=ResponseModel)
def close_open_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    close_evidence: Optional[str] = Query(None, description="关闭证据"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """关闭未决事项"""
    open_item = get_or_404(db, OpenItem, item_id, detail="未决事项不存在")
    old_open_item = _open_item_audit_value(open_item)

    open_item.status = OpenItemStatusEnum.CLOSED.value
    open_item.close_evidence = close_evidence
    open_item.closed_at = datetime.now()

    db.flush()
    _log_open_item_source_operation(
        db,
        open_item,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_open_item=old_open_item,
        new_open_item=_open_item_audit_value(open_item),
        operation_desc="关闭未决事项",
        remark=close_evidence,
    )
    db.commit()

    return ResponseModel(message="未决事项已关闭")
