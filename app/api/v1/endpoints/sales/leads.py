# -*- coding: utf-8 -*-
"""
线索管理 API endpoints
"""

from typing import Any, List, Optional
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import Lead, LeadFollowUp
from app.models.advantage_product import AdvantageProduct
from app.models.enums import LeadStatusEnum
from app.schemas.sales import (
    LeadCreate, LeadUpdate, LeadResponse,
    LeadFollowUpResponse, LeadFollowUpCreate
)
from app.schemas.common import PaginatedResponse, ResponseModel
from .utils import (
    get_entity_creator_id,
    generate_lead_code,
    validate_g1_lead_to_opportunity
)

router = APIRouter()


@router.get("/leads", response_model=PaginatedResponse[LeadResponse])
def read_leads(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索列表
    Issue 7.1: 已集成数据权限过滤
    """
    query = db.query(Lead)

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Lead, 'owner_id')

    if keyword:
        query = query.filter(
            or_(
                Lead.lead_code.contains(keyword),
                Lead.customer_name.contains(keyword),
                Lead.contact_name.contains(keyword),
            )
        )

    if status:
        query = query.filter(Lead.status == status)

    if owner_id:
        query = query.filter(Lead.owner_id == owner_id)

    total = query.count()
    offset = (page - 1) * page_size
    # 默认按优先级排序，如果没有优先级则按创建时间排序
    leads = query.order_by(
        desc(Lead.priority_score).nullslast(),
        desc(Lead.created_at)
    ).offset(offset).limit(page_size).all()

    # 填充负责人名称和优势产品信息
    lead_responses = []
    for lead in leads:
        lead_dict = {
            **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
            "owner_name": lead.owner.real_name if lead.owner else None,
        }

        # 获取优势产品详情（简化版，只在列表中显示产品数量）
        if lead.selected_advantage_products:
            try:
                product_ids = json.loads(lead.selected_advantage_products)
                products = db.query(AdvantageProduct).filter(
                    AdvantageProduct.id.in_(product_ids)
                ).all()
                lead_dict["advantage_products"] = [
                    {
                        "id": p.id,
                        "product_code": p.product_code,
                        "product_name": p.product_name,
                        "category_id": p.category_id,
                    }
                    for p in products
                ]
            except (json.JSONDecodeError, Exception):
                lead_dict["advantage_products"] = []

        lead_responses.append(LeadResponse(**lead_dict))

    return PaginatedResponse(
        items=lead_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/leads", response_model=LeadResponse, status_code=201)
def create_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_in: LeadCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建线索
    """
    # 如果没有提供编码，自动生成
    lead_data = lead_in.model_dump()
    if not lead_data.get("lead_code"):
        lead_data["lead_code"] = generate_lead_code(db)
    else:
        # 检查编码是否已存在
        existing = db.query(Lead).filter(Lead.lead_code == lead_data["lead_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="线索编码已存在")

    # 如果没有指定负责人，默认使用当前用户
    if not lead_data.get("owner_id"):
        lead_data["owner_id"] = current_user.id

    # 处理优势产品选择
    selected_products = lead_data.pop("selected_advantage_products", None)
    if selected_products and len(selected_products) > 0:
        # 验证产品ID是否存在
        products = db.query(AdvantageProduct).filter(
            AdvantageProduct.id.in_(selected_products),
            AdvantageProduct.is_active == True
        ).all()

        if len(products) != len(selected_products):
            raise HTTPException(status_code=400, detail="部分优势产品ID不存在或已禁用")

        # 存储为JSON数组
        lead_data["selected_advantage_products"] = json.dumps(selected_products)
        lead_data["is_advantage_product"] = True
        lead_data["product_match_type"] = "ADVANTAGE"
    else:
        # 如果没有选择优势产品，设置为未知
        lead_data["selected_advantage_products"] = None
        lead_data["is_advantage_product"] = False
        lead_data["product_match_type"] = "UNKNOWN"

    lead = Lead(**lead_data)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # 构造响应，包含优势产品详情
    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }

    # 获取优势产品详情
    if lead.selected_advantage_products:
        try:
            product_ids = json.loads(lead.selected_advantage_products)
            products = db.query(AdvantageProduct).filter(
                AdvantageProduct.id.in_(product_ids)
            ).all()
            lead_dict["advantage_products"] = [
                {
                    "id": p.id,
                    "product_code": p.product_code,
                    "product_name": p.product_name,
                    "category_id": p.category_id,
                }
                for p in products
            ]
        except (json.JSONDecodeError, Exception):
            lead_dict["advantage_products"] = []

    return LeadResponse(**lead_dict)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def read_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索详情
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }

    # 获取优势产品详情
    if lead.selected_advantage_products:
        try:
            product_ids = json.loads(lead.selected_advantage_products)
            products = db.query(AdvantageProduct).filter(
                AdvantageProduct.id.in_(product_ids)
            ).all()
            lead_dict["advantage_products"] = [
                {
                    "id": p.id,
                    "product_code": p.product_code,
                    "product_name": p.product_name,
                    "category_id": p.category_id,
                }
                for p in products
            ]
        except (json.JSONDecodeError, Exception):
            lead_dict["advantage_products"] = []

    return LeadResponse(**lead_dict)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
def update_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    lead_in: LeadUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新线索
    Issue 7.2: 已集成操作权限检查
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(lead),
        lead.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此线索")

    update_data = lead_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    lead_dict = {
        **{c.name: getattr(lead, c.name) for c in lead.__table__.columns},
        "owner_name": lead.owner.real_name if lead.owner else None,
    }
    return LeadResponse(**lead_dict)


@router.delete("/leads/{lead_id}", response_model=ResponseModel)
def delete_lead(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除线索
    Issue 7.2: 已集成操作权限检查（仅创建人、销售总监、管理员可以删除）
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    # Issue 7.2: 检查删除权限
    if not security.check_sales_delete_permission(
        current_user,
        db,
        get_entity_creator_id(lead),
    ):
        raise HTTPException(status_code=403, detail="您没有权限删除此线索")

    db.delete(lead)
    db.commit()

    return ResponseModel(code=200, message="线索已删除")


@router.get("/leads/{lead_id}/follow-ups", response_model=List[LeadFollowUpResponse])
def get_lead_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取线索跟进记录列表
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    follow_ups = db.query(LeadFollowUp).filter(
        LeadFollowUp.lead_id == lead_id
    ).order_by(desc(LeadFollowUp.created_at)).all()

    result = []
    for follow_up in follow_ups:
        result.append({
            "id": follow_up.id,
            "lead_id": follow_up.lead_id,
            "follow_up_type": follow_up.follow_up_type,
            "content": follow_up.content,
            "next_action": follow_up.next_action,
            "next_action_at": follow_up.next_action_at,
            "created_by": follow_up.created_by,
            "attachments": follow_up.attachments,
            "created_at": follow_up.created_at,
            "updated_at": follow_up.updated_at,
            "creator_name": follow_up.creator.real_name if follow_up.creator else None,
        })

    return result


@router.post("/leads/{lead_id}/follow-ups", response_model=LeadFollowUpResponse, status_code=201)
def create_lead_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    follow_up_in: LeadFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加线索跟进记录
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    follow_up = LeadFollowUp(
        lead_id=lead_id,
        follow_up_type=follow_up_in.follow_up_type,
        content=follow_up_in.content,
        next_action=follow_up_in.next_action,
        next_action_at=follow_up_in.next_action_at,
        created_by=current_user.id,
        attachments=follow_up_in.attachments,
    )

    db.add(follow_up)
    
    # 如果设置了下次行动时间，更新线索的next_action_at
    if follow_up_in.next_action_at:
        lead.next_action_at = follow_up_in.next_action_at
    
    db.commit()
    db.refresh(follow_up)

    return {
        "id": follow_up.id,
        "lead_id": follow_up.lead_id,
        "follow_up_type": follow_up.follow_up_type,
        "content": follow_up.content,
        "next_action": follow_up.next_action,
        "next_action_at": follow_up.next_action_at,
        "created_by": follow_up.created_by,
        "attachments": follow_up.attachments,
        "created_at": follow_up.created_at,
        "updated_at": follow_up.updated_at,
        "creator_name": follow_up.creator.real_name if follow_up.creator else None,
    }


@router.post("/leads/{lead_id}/convert", response_model=Any, status_code=201)
def convert_lead_to_opportunity(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    customer_id: int = Query(..., description="客户ID"),
    requirement_data: Optional[dict] = None,
    skip_validation: bool = Query(False, description="跳过G1验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    线索转商机（G1阶段门验证）
    """
    from app.models.project import Customer
    from app.models.sales import Opportunity, OpportunityRequirement
    from app.schemas.sales import OpportunityResponse, OpportunityRequirementResponse
    from .utils import generate_opportunity_code
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # G1验证
    requirement = None
    if requirement_data:
        requirement = OpportunityRequirement(**requirement_data)
    
    if not skip_validation:
        is_valid, messages = validate_g1_lead_to_opportunity(lead, requirement, db)
        errors = [msg for msg in messages if not msg.startswith("技术评估") and not msg.startswith("存在")]
        warnings = [msg for msg in messages if msg.startswith("技术评估") or msg.startswith("存在")]
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"G1阶段门验证失败: {', '.join(errors)}"
            )

    # 生成商机编码
    opp_code = generate_opportunity_code(db)

    opportunity = Opportunity(
        opp_code=opp_code,
        lead_id=lead_id,
        customer_id=customer_id,
        opp_name=f"{lead.customer_name} - {lead.demand_summary[:50] if lead.demand_summary else '商机'}",
        owner_id=lead.owner_id,
        stage="DISCOVERY",
        gate_status="PASS" if not skip_validation else "PENDING",
        gate_passed_at=datetime.now() if not skip_validation else None
    )

    db.add(opportunity)
    db.flush()

    # 创建需求信息
    if requirement:
        requirement.opportunity_id = opportunity.id
        db.add(requirement)

    # 更新线索状态
    lead.status = LeadStatusEnum.CONVERTED

    db.commit()
    db.refresh(opportunity)

    req = db.query(OpportunityRequirement).filter(OpportunityRequirement.opportunity_id == opportunity.id).first()
    opp_dict = {
        **{c.name: getattr(opportunity, c.name) for c in opportunity.__table__.columns},
        "customer_name": customer.customer_name,
        "owner_name": opportunity.owner.real_name if opportunity.owner else None,
        "requirement": None,
    }
    if req:
        opp_dict["requirement"] = OpportunityRequirementResponse(**{c.name: getattr(req, c.name) for c in req.__table__.columns})
    
    return OpportunityResponse(**opp_dict)


@router.put("/leads/{lead_id}/invalid", response_model=ResponseModel)
def mark_lead_invalid(
    *,
    db: Session = Depends(deps.get_db),
    lead_id: int,
    reason: Optional[str] = Query(None, description="无效原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记线索无效
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="线索不存在")

    if lead.status == LeadStatusEnum.CONVERTED:
        raise HTTPException(status_code=400, detail="已转商机的线索不能标记为无效")

    lead.status = LeadStatusEnum.INVALID
    db.commit()

    # 可选：记录一条跟进记录说明无效原因
    if reason:
        follow_up = LeadFollowUp(
            lead_id=lead_id,
            follow_up_type="OTHER",
            content=f"标记为无效：{reason}",
            created_by=current_user.id,
        )
        db.add(follow_up)
        db.commit()

    return ResponseModel(code=200, message="线索已标记为无效")


@router.get("/leads/export")
def export_leads(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.2: 导出线索列表（Excel）
    """
    from app.services.excel_export_service import ExcelExportService, create_excel_response

    query = db.query(Lead)
    if keyword:
        query = query.filter(or_(Lead.lead_code.contains(keyword), Lead.customer_name.contains(keyword), Lead.contact_name.contains(keyword)))
    if status:
        query = query.filter(Lead.status == status)
    if owner_id:
        query = query.filter(Lead.owner_id == owner_id)

    leads = query.order_by(Lead.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "lead_code", "label": "线索编码", "width": 15},
        {"key": "source", "label": "来源", "width": 15},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "industry", "label": "行业", "width": 15},
        {"key": "contact_name", "label": "联系人", "width": 15},
        {"key": "contact_phone", "label": "联系电话", "width": 15},
        {"key": "status", "label": "状态", "width": 12},
        {"key": "owner_name", "label": "负责人", "width": 12},
        {"key": "next_action_at", "label": "下次行动时间", "width": 18, "format": export_service.format_date},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = [{
        "lead_code": lead.lead_code,
        "source": lead.source or '',
        "customer_name": lead.customer_name or '',
        "industry": lead.industry or '',
        "contact_name": lead.contact_name or '',
        "contact_phone": lead.contact_phone or '',
        "status": lead.status,
        "owner_name": lead.owner.real_name if lead.owner else '',
        "next_action_at": lead.next_action_at,
        "created_at": lead.created_at,
    } for lead in leads]

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="线索列表", title="线索列表")
    filename = f"线索列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)
