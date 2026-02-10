# -*- coding: utf-8 -*-
"""
商机管理 - CRUD操作
"""

from datetime import date, datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.common.pagination import get_pagination_query, PaginationParams
from app.models.enums import OpportunityStageEnum
from app.models.project import Customer
from app.models.sales import Opportunity, OpportunityRequirement
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sales import (
    OpportunityCreate,
    OpportunityRequirementResponse,
    OpportunityResponse,
    OpportunityUpdate,
)

from .utils import (
    generate_opportunity_code,
    get_entity_creator_id,
    validate_g2_opportunity_to_quote,
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
    """
    query = db.query(Opportunity).options(joinedload(Opportunity.customer))

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Opportunity, 'owner_id')

    if keyword:
        query = query.filter(
            or_(
                Opportunity.opp_code.contains(keyword),
                Opportunity.opp_name.contains(keyword),
            )
        )

    if stage:
        query = query.filter(Opportunity.stage == stage)

    if customer_id:
        query = query.filter(Opportunity.customer_id == customer_id)

    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)

    total = query.count()
    # 使用 eager loading 避免 N+1 查询
    # 默认按优先级排序，如果没有优先级则按创建时间排序
    opportunities = query.options(
        joinedload(Opportunity.customer),
        joinedload(Opportunity.owner),
        joinedload(Opportunity.updater),
        joinedload(Opportunity.requirements)
    ).order_by(
        desc(Opportunity.priority_score).nullslast(),
        desc(Opportunity.created_at)
    ).offset(pagination.offset).limit(pagination.limit).all()

    opp_responses = []
    for opp in opportunities:
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
            opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})
        opp_responses.append(OpportunityResponse(**opp_dict))

    return pagination.to_response(opp_responses, total)


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
        existing = db.query(Opportunity).filter(Opportunity.opp_code == opp_data["opp_code"]).first()
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

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": customer.customer_name,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

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
    opportunity = db.query(Opportunity).options(
        joinedload(Opportunity.customer),
        joinedload(Opportunity.owner),
        joinedload(Opportunity.updater),
        joinedload(Opportunity.requirements)
    ).filter(Opportunity.id == opp_id).first()

    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    req = opportunity.requirements[0] if opportunity.requirements else None
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

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
    opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

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
            req = db.query(OpportunityRequirement).filter(
                OpportunityRequirement.opportunity_id == opportunity.id
            ).first()
            if req:
                for field, value in req_data.items():
                    setattr(req, field, value)
            else:
                req_data["opportunity_id"] = opportunity.id
                requirement = OpportunityRequirement(**req_data)
                db.add(requirement)

    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": opportunity.customer.customer_name if opportunity.customer else None,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "updated_by_name": opportunity.updater.real_name if opportunity.updater else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})

    return OpportunityResponse(**opp_dict)
