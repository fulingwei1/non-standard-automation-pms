# -*- coding: utf-8 -*-
"""
线索转项目端点
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import EvaluationDecisionEnum
from app.models.project import Customer, Machine, Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.presales import LeadConversionRequest, LeadConversionResponse
from app.utils.number_generator import generate_customer_code

from .utils import convert_lead_code_to_project_code

router = APIRouter()

APPROVED_DECISIONS = {
    EvaluationDecisionEnum.GO.value,
    EvaluationDecisionEnum.GO_WITH_CONDITIONS.value,
    "APPROVED",
    "approved",
}


@router.post("/from-lead", response_model=ResponseModel[LeadConversionResponse])
async def create_project_from_lead(
    lead_data: LeadConversionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("presale_analytics:create")),
) -> Any:
    """从评估通过的销售线索创建项目

    由 presales-evaluation-system 在评估通过后调用
    """
    # 验证评估决策
    if lead_data.decision not in APPROVED_DECISIONS:
        return ResponseModel(
            code=400,
            message=f"线索评估未通过，当前决策: {lead_data.decision}",
            data=LeadConversionResponse(
                success=False,
                lead_id=lead_data.lead_id,
                message=f"评估未通过: {lead_data.decision}",
            ),
        )

    # 生成项目编号
    project_code = convert_lead_code_to_project_code(lead_data.lead_id)

    # 检查是否已存在该项目
    existing_project = db.query(Project).filter(Project.project_code == project_code).first()
    if existing_project:
        return ResponseModel(
            code=400,
            message=f"项目 {project_code} 已存在",
            data=LeadConversionResponse(
                success=False,
                project_id=existing_project.id,
                project_code=project_code,
                lead_id=lead_data.lead_id,
                message=f"项目已存在，ID: {existing_project.id}",
            ),
        )

    # 查找或创建客户
    customer = db.query(Customer).filter(Customer.customer_name == lead_data.customer_name).first()
    if not customer:
        customer = Customer(
            customer_code=generate_customer_code(db),
            customer_name=lead_data.customer_name,
            industry=lead_data.customer_industry,
            contact_person=lead_data.customer_contact,
            contact_phone=lead_data.customer_phone,
            status="ACTIVE",
            created_at=datetime.now(timezone.utc),
            created_by=current_user.id,
        )
        db.add(customer)
        db.flush()

    # 创建项目。当前项目模型以 S1 作为售前/需求进入的起点。
    project = Project(
        project_code=project_code,
        project_name=lead_data.lead_name,
        customer_id=customer.id,
        customer_name=customer.customer_name,
        customer_contact=lead_data.customer_contact,
        customer_phone=lead_data.customer_phone,
        salesperson_id=lead_data.salesperson_id,
        stage="S1",
        status="ST01",
        health="H1",
        contract_amount=lead_data.estimated_amount,
        contract_date=lead_data.expected_contract_date,
        planned_end_date=lead_data.expected_delivery_date,
        description=lead_data.requirement_summary,
        requirements=lead_data.requirement_summary,
        industry=lead_data.customer_industry,
        project_category="SALES",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        created_by=current_user.id,
        evaluation_score=lead_data.evaluation_score,
        predicted_win_rate=lead_data.predicted_win_rate,
        source_lead_id=lead_data.lead_id,
    )

    db.add(project)
    db.flush()

    # 如果有设备数量，创建设备记录
    for i in range(lead_data.machine_count):
        machine = Machine(
            project_id=project.id,
            machine_code=f"{project_code}-PN{i + 1:03d}",
            machine_name=f"{lead_data.lead_name}-设备{i+1}",
            machine_no=i + 1,
            stage="S1",
            status="ST01",
            health="H1",
            created_at=datetime.now(timezone.utc),
        )
        db.add(machine)

    db.commit()

    return ResponseModel(
        code=200,
        message="项目创建成功",
        data=LeadConversionResponse(
            success=True,
            project_id=project.id,
            project_code=project_code,
            lead_id=lead_data.lead_id,
            message=f"已从线索 {lead_data.lead_id} 创建项目 {project_code}",
        ),
    )
