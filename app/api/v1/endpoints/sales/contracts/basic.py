# -*- coding: utf-8 -*-
"""
合同基础操作 API endpoints
包括：合同列表、创建、详情、更新
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer
from app.models.sales import Contract, ContractDeliverable, Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    ContractCreate,
    ContractDeliverableResponse,
    ContractResponse,
    ContractUpdate,
)

from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from ..utils import (
    generate_contract_code,
    get_entity_creator_id,
    validate_g3_quote_to_contract,
)

router = APIRouter()


@router.get("/contracts", response_model=PaginatedResponse[ContractResponse])
def read_contracts(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同列表
    Issue 7.1: 已集成数据权限过滤
    """
    query = db.query(Contract).options(
        joinedload(Contract.customer),
        joinedload(Contract.project),
        joinedload(Contract.opportunity),
        joinedload(Contract.owner)
    )

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Contract, 'owner_id')

    query = apply_keyword_filter(query, Contract, keyword, "contract_code")

    if status:
        query = query.filter(Contract.status == status)

    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)

    total = query.count()
    contracts = apply_pagination(query.order_by(desc(Contract.created_at)), pagination.offset, pagination.limit).all()

    contract_responses = []
    for contract in contracts:
        deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
        contract_dict = {
            **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
            "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
            "customer_name": contract.customer.customer_name if contract.customer else None,
            "project_code": contract.project.project_code if contract.project else None,
            "owner_name": contract.owner.real_name if contract.owner else None,
            "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
        }
        contract_responses.append(ContractResponse(**contract_dict))

    return PaginatedResponse(
        items=contract_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/contracts", response_model=ContractResponse, status_code=201)
def create_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_in: ContractCreate,
    skip_g3_validation: bool = Query(False, description="跳过G3验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建合同（G3阶段门验证）
    """
    from app.models.sales import Quote, QuoteItem, QuoteVersion

    contract_data = contract_in.model_dump(exclude={"deliverables"})

    # 检查报价是否存在（如果提供了quote_version_id）
    quote = None
    version = None
    items: List[QuoteItem] = []
    if contract_data.get("quote_version_id"):
        version = db.query(QuoteVersion).filter(QuoteVersion.id == contract_data["quote_version_id"]).first()
        if not version:
            raise HTTPException(status_code=404, detail="报价版本不存在")

        quote = db.query(Quote).filter(Quote.id == version.quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价不存在")

        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()

        # G3验证
        if not skip_g3_validation:
            is_valid, errors, warning = validate_g3_quote_to_contract(quote, version, items, db)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"G3阶段门验证失败: {', '.join(errors)}"
                )
            if warning:
                # 警告信息可以通过响应返回，但不阻止创建
                pass

    # 如果没有提供编码，自动生成
    if not contract_data.get("contract_code"):
        contract_data["contract_code"] = generate_contract_code(db)
    else:
        existing = db.query(Contract).filter(Contract.contract_code == contract_data["contract_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="合同编码已存在")

    # 如果没有指定负责人，默认使用当前用户
    if not contract_data.get("owner_id"):
        contract_data["owner_id"] = current_user.id

    opportunity = db.query(Opportunity).filter(Opportunity.id == contract_data["opportunity_id"]).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    customer = db.query(Customer).filter(Customer.id == contract_data["customer_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    contract = Contract(**contract_data)
    db.add(contract)
    db.flush()

    # 创建交付物清单
    if contract_in.deliverables:
        for deliverable_data in contract_in.deliverables:
            deliverable = ContractDeliverable(contract_id=contract.id, **deliverable_data.model_dump())
            db.add(deliverable)

    db.commit()
    db.refresh(contract)

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "opportunity_code": opportunity.opp_code,
        "customer_name": customer.customer_name,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.owner.real_name if contract.owner else None,
        "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
    }
    return ContractResponse(**contract_dict)


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def read_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同详情
    """
    contract = db.query(Contract).options(
        joinedload(Contract.customer),
        joinedload(Contract.project),
        joinedload(Contract.opportunity),
        joinedload(Contract.owner)
    ).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
        "customer_name": contract.customer.customer_name if contract.customer else None,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.owner.real_name if contract.owner else None,
        "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
    }
    return ContractResponse(**contract_dict)


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
def update_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    contract_in: ContractUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新合同
    Issue 7.2: 已集成操作权限检查
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(contract),
        contract.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此合同")

    update_data = contract_in.model_dump(exclude_unset=True)

    # 记录需要同步的字段
    need_sync = any(field in update_data for field in ["contract_amount", "signed_date", "delivery_deadline"])

    for field, value in update_data.items():
        setattr(contract, field, value)

    # Sprint 2.4: 合同变更时自动同步到项目
    if need_sync and contract.project_id:
        try:
            from app.services.data_sync_service import DataSyncService
            sync_service = DataSyncService(db)
            sync_result = sync_service.sync_contract_to_project(contract_id)
            if sync_result.get("success"):
                logger.info(f"合同变更已同步到项目：{sync_result.get('message')}")
        except Exception as e:
            # 同步失败不影响合同更新，记录日志
            logger.warning(f"合同变更同步到项目失败：{str(e)}", exc_info=True)

    db.commit()
    db.refresh(contract)

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
        "customer_name": contract.customer.customer_name if contract.customer else None,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.owner.real_name if contract.owner else None,
        "deliverables": [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables],
    }
    return ContractResponse(**contract_dict)
