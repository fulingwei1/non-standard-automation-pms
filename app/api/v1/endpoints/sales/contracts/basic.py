# -*- coding: utf-8 -*-
"""
合同基础操作 API endpoints
包括：合同列表、创建、详情、更新
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.crud import SalesQueryBuilder, SalesQueryConfig
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.project import Customer
from app.models.sales import Contract, ContractDeliverable, Opportunity, Quote, QuoteItem, QuoteVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    ContractCreate,
    ContractDeliverableResponse,
    ContractResponse,
    ContractUpdate,
)
from app.utils.db_helpers import get_or_404

from ..utils import (
    generate_contract_code,
    get_entity_creator_id,
    validate_g3_quote_to_contract,
)


# 合同查询配置
CONTRACT_QUERY_CONFIG = SalesQueryConfig(
    keyword_fields=["contract_code"],
    default_sort_field="created_at",
    default_sort_desc=True,
    owner_field="sales_owner_id",  # 合同使用 sales_owner_id 作为负责人字段
)

router = APIRouter()


def _map_contract_payload_to_model(payload: dict, *, is_create: bool = False) -> dict:
    """将 Contract schema 字段映射为 Contract ORM 字段。"""

    field_map = {
        "contract_code": "contract_code",
        "customer_contract_no": "customer_contract_no",
        "opportunity_id": "opportunity_id",
        "quote_version_id": "quote_id",
        "customer_id": "customer_id",
        "project_id": "project_id",
        "contract_amount": "total_amount",
        "signed_date": "signing_date",
        "status": "status",
        "payment_terms_summary": "payment_terms",
        "acceptance_summary": "contract_subject",
        "owner_id": "sales_owner_id",
    }

    mapped: dict = {}
    for src_field, dst_field in field_map.items():
        if src_field in payload:
            mapped[dst_field] = payload.get(src_field)

    if is_create:
        mapped.setdefault("contract_type", "sales")
        if not mapped.get("status"):
            mapped["status"] = "draft"
        if mapped.get("total_amount") is None:
            mapped["total_amount"] = 0

    return mapped


def _build_contract_response_dict(contract: Contract, deliverables: list[ContractDeliverable]) -> dict:
    """构建 ContractResponse 所需字段（兼容 schema 命名）。"""

    contract_dict = {
        **{c.name: getattr(contract, c.name) for c in contract.__table__.columns},
        "quote_version_id": contract.quote_id,
        "contract_amount": contract.total_amount,
        "signed_date": contract.signing_date,
        "payment_terms_summary": contract.payment_terms,
        "acceptance_summary": contract.contract_subject,
        "owner_id": contract.sales_owner_id,
        "opportunity_code": contract.opportunity.opp_code if contract.opportunity else None,
        "customer_name": contract.customer.customer_name if contract.customer else None,
        "project_code": contract.project.project_code if contract.project else None,
        "owner_name": contract.sales_owner.real_name if contract.sales_owner else None,
        "deliverables": [
            ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns})
            for d in deliverables
        ],
    }
    return contract_dict


@router.get("/contracts", response_model=PaginatedResponse[ContractResponse])
def read_contracts(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.require_permission("contract:view")),
) -> Any:
    """
    获取合同列表
    Issue 7.1: 已集成数据权限过滤

    使用 SalesQueryBuilder 统一处理查询逻辑
    """

    def transform_contract(contract: Contract) -> ContractResponse:
        """将 Contract 模型转换为响应对象"""
        # 加载交付物（由于不能在 transform 中修改查询，需要额外查询）
        deliverables = (
            db.query(ContractDeliverable)
            .filter(ContractDeliverable.contract_id == contract.id)
            .all()
        )
        return ContractResponse(**_build_contract_response_dict(contract, deliverables))

    # 使用 SalesQueryBuilder 链式构建查询
    result = (
        SalesQueryBuilder(db, Contract, CONTRACT_QUERY_CONFIG)
        .with_options(
            joinedload(Contract.customer),
            joinedload(Contract.project),
            joinedload(Contract.opportunity),
            joinedload(Contract.sales_owner),
            joinedload(Contract.contract_manager),
        )
        .with_scope_filter(current_user)
        .with_keyword(keyword)
        .with_status(status)
        .with_customer(customer_id)
        .with_sort()
        .with_pagination(pagination)
        .execute_with_transform(transform_contract)
    )

    return PaginatedResponse(
        items=result.items,
        total=result.total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(result.total),
    )


@router.post("/contracts", response_model=ContractResponse, status_code=201)
def create_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_in: ContractCreate,
    skip_g3_validation: bool = Query(False, description="跳过G3验证"),
    current_user: User = Depends(security.require_permission("contract:create")),
) -> Any:
    """
    创建合同（G3阶段门验证）
    """
    contract_payload = contract_in.model_dump(exclude={"deliverables"})
    contract_data = _map_contract_payload_to_model(contract_payload, is_create=True)

    # 检查报价是否存在（如果提供了 quote_id）
    quote = None
    version = None
    items: List[QuoteItem] = []
    if contract_data.get("quote_id"):
        version = (
            db.query(QuoteVersion)
            .filter(QuoteVersion.id == contract_data["quote_id"])
            .first()
        )
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
                    status_code=400, detail=f"G3阶段门验证失败: {', '.join(errors)}"
                )
            if warning:
                # 警告信息可以通过响应返回，但不阻止创建
                pass

    # 如果没有提供编码，自动生成
    if not contract_data.get("contract_code"):
        contract_data["contract_code"] = generate_contract_code(db)
    else:
        existing = (
            db.query(Contract)
            .filter(Contract.contract_code == contract_data["contract_code"])
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="合同编码已存在")

    # 如果没有指定负责人，默认使用当前用户
    if not contract_data.get("sales_owner_id"):
        contract_data["sales_owner_id"] = current_user.id

    # 兼容旧 schema：如果未提供合同名称，自动生成
    if not contract_data.get("contract_name"):
        contract_data["contract_name"] = (
            contract_data.get("customer_contract_no")
            or contract_data.get("contract_code")
            or f"销售合同-{current_user.id}"
        )

    opportunity = (
        db.query(Opportunity).filter(Opportunity.id == contract_data["opportunity_id"]).first()
    )
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
            deliverable = ContractDeliverable(
                contract_id=contract.id, **deliverable_data.model_dump()
            )
            db.add(deliverable)

    db.commit()
    db.refresh(contract)

    deliverables = (
        db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    )
    return ContractResponse(**_build_contract_response_dict(contract, deliverables))


class ContractFromQuoteRequest(BaseModel):
    """从报价创建合同请求"""

    quote_id: int = Field(..., description="报价ID")
    quote_version_id: Optional[int] = Field(
        default=None, description="报价版本ID（留空使用当前版本）"
    )
    contract_code: Optional[str] = Field(default=None, description="合同编码（留空自动生成）")
    contract_name: Optional[str] = Field(default=None, description="合同名称")
    payment_terms: Optional[str] = Field(default=None, description="付款条款")
    remark: Optional[str] = Field(default=None, description="备注")


@router.post("/contracts/from-quote", response_model=ContractResponse, status_code=201)
def create_contract_from_quote(
    *,
    db: Session = Depends(deps.get_db),
    request: ContractFromQuoteRequest,
    skip_g3_validation: bool = Query(False, description="跳过G3验证"),
    current_user: User = Depends(security.require_permission("contract:create")),
) -> Any:
    """
    从报价创建合同

    自动从报价中提取客户、商机、金额等信息创建合同。
    执行 G3 阶段门验证（可跳过）。
    """
    # 查找报价
    quote = db.query(Quote).filter(Quote.id == request.quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 验证报价状态
    if quote.status not in ("APPROVED", "ACCEPTED"):
        raise HTTPException(
            status_code=400,
            detail=f"报价状态为 {quote.status}，只有已审批通过(APPROVED)或已接受(ACCEPTED)的报价才能创建合同",
        )

    # 确定版本
    if request.quote_version_id:
        version = (
            db.query(QuoteVersion)
            .filter(QuoteVersion.id == request.quote_version_id)
            .first()
        )
        if not version:
            raise HTTPException(status_code=404, detail="报价版本不存在")
    elif quote.current_version_id:
        version = (
            db.query(QuoteVersion)
            .filter(QuoteVersion.id == quote.current_version_id)
            .first()
        )
        if not version:
            raise HTTPException(status_code=404, detail="报价当前版本不存在")
    else:
        # 取最新版本
        version = (
            db.query(QuoteVersion)
            .filter(QuoteVersion.quote_id == quote.id)
            .order_by(QuoteVersion.created_at.desc())
            .first()
        )
        if not version:
            raise HTTPException(status_code=404, detail="报价无任何版本")

    # G3 验证
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    if not skip_g3_validation:
        is_valid, errors, warning = validate_g3_quote_to_contract(quote, version, items, db)
        if not is_valid:
            raise HTTPException(
                status_code=400, detail=f"G3阶段门验证失败: {', '.join(errors)}"
            )

    # 检查商机
    if not quote.opportunity_id:
        raise HTTPException(status_code=400, detail="报价未关联商机")

    opportunity = db.query(Opportunity).filter(Opportunity.id == quote.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="关联的商机不存在")

    # 检查客户
    customer = db.query(Customer).filter(Customer.id == quote.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="关联的客户不存在")

    # 生成合同编码
    if request.contract_code:
        existing = (
            db.query(Contract)
            .filter(Contract.contract_code == request.contract_code)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="合同编码已存在")
        contract_code = request.contract_code
    else:
        contract_code = generate_contract_code(db)

    # 创建合同
    contract_name = (
        request.contract_name
        or f"{customer.customer_name}-{quote.quote_code}"
    )

    contract = Contract(
        contract_code=contract_code,
        contract_name=contract_name,
        contract_type="sales",
        opportunity_id=quote.opportunity_id,
        quote_id=version.id,
        customer_id=quote.customer_id,
        total_amount=version.total_price or 0,
        status="draft",
        sales_owner_id=quote.owner_id or current_user.id,
        payment_terms=request.payment_terms,
    )
    db.add(contract)
    db.flush()

    db.commit()
    db.refresh(contract)

    logger.info(
        f"从报价 {quote.quote_code} 创建合同 {contract_code}, 操作人: {current_user.id}"
    )

    deliverables = (
        db.query(ContractDeliverable)
        .filter(ContractDeliverable.contract_id == contract.id)
        .all()
    )
    return ContractResponse(**_build_contract_response_dict(contract, deliverables))


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def read_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.require_permission("contract:view")),
) -> Any:
    """
    获取合同详情
    """
    contract = (
        db.query(Contract)
        .options(
            joinedload(Contract.customer),
            joinedload(Contract.project),
            joinedload(Contract.opportunity),
            joinedload(Contract.sales_owner),
        )
        .filter(Contract.id == contract_id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 数据权限检查
    if not security.check_sales_data_permission(contract, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该合同")

    deliverables = (
        db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    )
    return ContractResponse(**_build_contract_response_dict(contract, deliverables))


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
def update_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    contract_in: ContractUpdate,
    current_user: User = Depends(security.require_permission("contract:update")),
) -> Any:
    """
    更新合同
    Issue 7.2: 已集成操作权限检查
    """
    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(contract),
        contract.sales_owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此合同")

    update_payload = contract_in.model_dump(exclude_unset=True)
    update_data = _map_contract_payload_to_model(update_payload)

    # 记录需要同步的字段
    need_sync = any(
        field in update_data for field in ["total_amount", "signing_date", "delivery_deadline"]
    )

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

    deliverables = (
        db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract.id).all()
    )
    return ContractResponse(**_build_contract_response_dict(contract, deliverables))
