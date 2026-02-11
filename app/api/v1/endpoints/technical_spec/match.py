# -*- coding: utf-8 -*-
"""
规格匹配检查
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomItem
from app.models.technical_spec import SpecMatchRecord
from app.models.user import User
from app.schemas.technical_spec import (
    SpecMatchCheckRequest,
    SpecMatchCheckResponse,
    SpecMatchRecordListResponse,
    SpecMatchRecordResponse,
    TechnicalSpecRequirementResponse,
)
from app.utils.spec_matcher import SpecMatcher
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


def get_match_target_name(db: Session, match_type: str, match_target_id: int) -> Optional[str]:
    """根据匹配类型获取目标名称"""
    if not match_target_id:
        return None

    if match_type == 'BOM':
        bom_item = db.query(BomItem).filter(BomItem.id == match_target_id).first()
        if bom_item:
            return bom_item.material_name or bom_item.material_code
    elif match_type == 'PURCHASE_ORDER':
        from app.models.purchase import PurchaseOrderItem
        po_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == match_target_id).first()
        if po_item:
            return po_item.material_name or po_item.material_code

    return None


@router.post("/match/check", response_model=SpecMatchCheckResponse)
def check_spec_match(
    check_request: SpecMatchCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
) -> Any:
    """手动触发规格匹配检查"""
    from app.models.purchase import PurchaseOrderItem
    from app.services.spec_match_service import (
        calculate_match_statistics,
        check_all_bom_items,
        check_all_po_items,
        check_bom_item_match,
        check_po_item_match,
        get_project_requirements,
    )

    # 获取项目的所有规格要求
    requirements = get_project_requirements(db, check_request.project_id)

    if not requirements:
        return SpecMatchCheckResponse(
            total_checked=0,
            matched_count=0,
            mismatched_count=0,
            unknown_count=0,
            results=[]
        )

    matcher = SpecMatcher()
    results = []

    if check_request.match_type == 'PURCHASE_ORDER':
        # 检查采购订单
        if check_request.match_target_id:
            # 检查特定订单行
            po_item = db.query(PurchaseOrderItem).filter(
                PurchaseOrderItem.id == check_request.match_target_id
            ).first()

            if not po_item:
                raise HTTPException(status_code=404, detail="采购订单行不存在")

            results = check_po_item_match(
                db, po_item, requirements, check_request.project_id, matcher
            )
        else:
            # 检查所有采购订单
            results = check_all_po_items(
                db, check_request.project_id, requirements, matcher
            )

    elif check_request.match_type == 'BOM':
        # 检查BOM
        if check_request.match_target_id:
            # 检查特定BOM行
            bom_item = db.query(BomItem).filter(
                BomItem.id == check_request.match_target_id
            ).first()

            if not bom_item:
                raise HTTPException(status_code=404, detail="BOM行不存在")

            results = check_bom_item_match(
                db, bom_item, requirements, check_request.project_id, matcher
            )
        else:
            # 检查所有BOM行
            results = check_all_bom_items(
                db, check_request.project_id, requirements, matcher
            )

    db.commit()

    # 计算统计
    stats = calculate_match_statistics(results)

    return SpecMatchCheckResponse(
        total_checked=stats['total'],
        matched_count=stats['matched'],
        mismatched_count=stats['mismatched'],
        unknown_count=stats['unknown'],
        results=results
    )


@router.get("/match/records", response_model=SpecMatchRecordListResponse)
def list_match_records(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("technical_spec:read")),
    project_id: Optional[int] = Query(None, description="项目ID"),
    match_type: Optional[str] = Query(None, description="匹配类型"),
    match_status: Optional[str] = Query(None, description="匹配状态"),
    pagination: PaginationParams = Depends(get_pagination_query),
) -> Any:
    """获取规格匹配记录列表"""

    query = db.query(SpecMatchRecord)

    if project_id:
        query = query.filter(SpecMatchRecord.project_id == project_id)
    if match_type:
        query = query.filter(SpecMatchRecord.match_type == match_type)
    if match_status:
        query = query.filter(SpecMatchRecord.match_status == match_status)

    total = query.count()
    records = apply_pagination(query.order_by(desc(SpecMatchRecord.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for record in records:
        items.append(SpecMatchRecordResponse(
            id=record.id,
            project_id=record.project_id,
            spec_requirement_id=record.spec_requirement_id,
            match_type=record.match_type,
            match_target_id=record.match_target_id,
            match_status=record.match_status,
            match_score=record.match_score,
            differences=record.differences,
            alert_id=record.alert_id,
            spec_requirement=TechnicalSpecRequirementResponse(
                id=record.spec_requirement.id,
                project_id=record.spec_requirement.project_id,
                document_id=record.spec_requirement.document_id,
                material_code=record.spec_requirement.material_code,
                material_name=record.spec_requirement.material_name,
                specification=record.spec_requirement.specification,
                brand=record.spec_requirement.brand,
                model=record.spec_requirement.model,
                key_parameters=record.spec_requirement.key_parameters,
                requirement_level=record.spec_requirement.requirement_level,
                remark=record.spec_requirement.remark,
                extracted_by=record.spec_requirement.extracted_by,
                extracted_by_name=record.spec_requirement.extractor.name if record.spec_requirement.extractor else None,
                created_at=record.spec_requirement.created_at,
                updated_at=record.spec_requirement.updated_at,
            ) if record.spec_requirement else None,
            match_target_name=get_match_target_name(db, record.match_type, record.match_target_id),
            created_at=record.created_at,
            updated_at=record.updated_at,
        ))

    return SpecMatchRecordListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )
