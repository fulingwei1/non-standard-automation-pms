# -*- coding: utf-8 -*-
"""
商机管理 - CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.crud import SalesQueryBuilder, SalesQueryConfig
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.project import Customer
from app.models.sales import Opportunity, OpportunityRequirement
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    OpportunityCreate,
    OpportunityRequirementResponse,
    OpportunityResponse,
    OpportunityUpdate,
)
from app.utils.db_helpers import get_or_404

from .utils import (
    generate_opportunity_code,
    get_entity_creator_id,
)


def apply_keyword_filter(query, keyword: Optional[str]) -> Any:
    """
    应用关键词过滤到查询
    支持按商机编码、商机名称、客户名称搜索
    """
    if not keyword:
        return query
    
    from sqlalchemy import or_
    from app.models.project import Customer
    
    return query.filter(
        or_(
            Opportunity.opp_code.contains(keyword),
            Opportunity.opp_name.contains(keyword),
            Opportunity.customer.has(Customer.customer_name.contains(keyword)),
        )
    )


# 商机查询配置
OPPORTUNITY_QUERY_CONFIG = SalesQueryConfig(
    keyword_fields=["opp_code", "opp_name"],
    default_sort_field="priority_score",
    default_sort_desc=True,
    owner_field="owner_id",
)

router = APIRouter()


@router.get("/opportunities", response_model=PaginatedResponse[OpportunityResponse])
def read_opportunities(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机列表
    Issue 7.1: 已集成数据权限过滤

    使用 SalesQueryBuilder 统一处理查询逻辑
    """

    def transform_opportunity(opp: Opportunity) -> OpportunityResponse:
        """将 Opportunity 模型转换为响应对象"""
        # 获取第一个 requirement（如果存在）
        req = opp.requirements[0] if opp.requirements else None
        opp_dict = {
            **{c.name: getattr(opp, c.name) for c in opp.__table__.columns},
            "customer_name": opp.customer.customer_name if opp.customer else None,
            "owner_name": opp.owner.real_name if opp.owner else None,
            "updated_by_name": opp.updater.real_name if opp.updater else None,
            "requirement": None,
        }
        if req:
            opp_dict["requirement"] = OpportunityRequirementResponse(
                **{c.name: getattr(req, c.name) for c in req.__table__.columns}
            )
        return OpportunityResponse(**opp_dict)

    # 使用 SalesQueryBuilder 链式构建查询
    result = (
        SalesQueryBuilder(db, Opportunity, OPPORTUNITY_QUERY_CONFIG)
        .with_options(
            joinedload(Opportunity.customer),
            joinedload(Opportunity.owner),
            joinedload(Opportunity.updater),
            joinedload(Opportunity.requirements),
        )
        .with_scope_filter(current_user)
        .with_keyword(keyword)
        .with_status(stage, field_name="stage")
        .with_customer(customer_id)
        .with_owner(owner_id)
        .with_sort(nulls_last=True)
        .with_secondary_sort("created_at", is_desc=True)
        .with_pagination(pagination)
        .execute_with_transform(transform_opportunity)
    )

    return pagination.to_response(result.items, result.total)


@router.post("/opportunities", response_model=OpportunityResponse, status_code=201)
def create_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_in: OpportunityCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建商机
    """
    opp_data = opp_in.model_dump(exclude={"requirement"})

    # 如果没有提供编码，自动生成
    if not opp_data.get("opp_code"):
        opp_data["opp_code"] = generate_opportunity_code(db)
    else:
        # 检查编码是否已存在
        existing = (
            db.query(Opportunity).filter(Opportunity.opp_code == opp_data["opp_code"]).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="商机编码已存在")

    # 如果没有指定负责人，默认使用当前用户
    if not opp_data.get("owner_id"):
        opp_data["owner_id"] = current_user.id

    customer = db.query(Customer).filter(Customer.id == opp_data["customer_id"]).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    opportunity = Opportunity(**opp_data)
    opportunity.updated_by = current_user.id
    db.add(opportunity)
    db.flush()

    # 创建需求信息
    if opp_in.requirement:
        valid_req_fields = {c.name for c in OpportunityRequirement.__table__.columns}
        req_data = opp_in.requirement.model_dump(exclude_unset=True)
        req_data = {k: v for k, v in req_data.items() if k in valid_req_fields}
        req_data["opportunity_id"] = opportunity.id
        requirement = OpportunityRequirement(**req_data)
        db.add(requirement)

    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": customer.customer_name,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
def read_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取商机详情
    """
    opportunity = (
        db.query(Opportunity)
        .options(
            joinedload(Opportunity.customer),
            joinedload(Opportunity.owner),
            joinedload(Opportunity.updater),
            joinedload(Opportunity.requirements),
        )
        .filter(Opportunity.id == opp_id)
        .first()
    )

    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    if not security.check_sales_data_permission(opportunity, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该商机")

    req = opportunity.requirements[0] if opportunity.requirements else None
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)


@router.put("/opportunities/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    opp_id: int,
    opp_in: OpportunityUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新商机
    Issue 7.2: 已集成操作权限检查
    """
    opportunity = get_or_404(db, Opportunity, opp_id, detail="商机不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(opportunity),
        opportunity.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此商机")

    update_data = opp_in.model_dump(exclude_unset=True, exclude={"requirement"})
    for field, value in update_data.items():
        setattr(opportunity, field, value)
    opportunity.updated_by = current_user.id

    if opp_in.requirement is not None:
        valid_req_fields = {c.name for c in OpportunityRequirement.__table__.columns}
        req_data = opp_in.requirement.model_dump(exclude_unset=True)
        req_data = {k: v for k, v in req_data.items() if k in valid_req_fields}
        if req_data:
            req = (
                db.query(OpportunityRequirement)
                .filter(OpportunityRequirement.opportunity_id == opportunity.id)
                .first()
            )
            if req:
                for field, value in req_data.items():
                    setattr(req, field, value)
            else:
                req_data["opportunity_id"] = opportunity.id
                requirement = OpportunityRequirement(**req_data)
                db.add(requirement)

    db.commit()
    db.refresh(opportunity)

    req = (
        db.query(OpportunityRequirement)
        .filter(OpportunityRequirement.opportunity_id == opportunity.id)
        .first()
    )
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(
            **{c.name: getattr(req, c.name) for c in req.__table__.columns}
        )

    return OpportunityResponse(**opp_dict)
