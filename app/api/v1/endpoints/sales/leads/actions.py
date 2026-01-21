# -*- coding: utf-8 -*-
"""
线索特殊操作
包含：转商机、标记无效、导出
"""

import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import LeadStatusEnum
from app.models.sales import Lead, LeadFollowUp
from app.models.user import User
from app.schemas.common import ResponseModel

from ..utils import (
    generate_opportunity_code,
    validate_g1_lead_to_opportunity,
)

router = APIRouter()


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
    from app.schemas.sales import OpportunityRequirementResponse, OpportunityResponse

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
    from app.services.excel_export_service import (
        ExcelExportService,
        create_excel_response,
    )

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
