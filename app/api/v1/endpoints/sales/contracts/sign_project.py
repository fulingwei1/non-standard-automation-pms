# -*- coding: utf-8 -*-
"""
合同签订与项目生成 API endpoints
包括：合同签订、项目生成、收款计划自动生成
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Customer, Project
from app.models.sales import Contract, ContractDeliverable
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import ContractProjectCreateRequest, ContractSignRequest

from ..utils import validate_g4_contract_to_project

from app.utils.db_helpers import get_or_404
router = APIRouter()


def _generate_payment_plans_from_contract(db: Session, contract: Contract) -> List:
    """
    根据合同自动生成收款计划

    使用重构后的PaymentPlanService，将原来157行的复杂函数拆分为多个小函数
    """
    from app.services.sales.payment_plan_service import PaymentPlanService

    payment_service = PaymentPlanService(db)
    return payment_service.generate_payment_plans_from_contract(contract)


@router.post("/contracts/{contract_id}/sign", response_model=ResponseModel)
def sign_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    sign_request: ContractSignRequest,
    auto_generate_payment_plans: bool = Query(True, description="自动生成收款计划"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同签订（自动生成收款计划）
    """
    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    contract.signing_date = sign_request.signed_date
    contract.status = "SIGNED"

    # Sprint 2.1 + Issue 1.2: 合同签订自动创建项目并触发阶段流转
    auto_create_project = getattr(sign_request, 'auto_create_project', True) if hasattr(sign_request, 'auto_create_project') else True
    created_project = None

    if auto_create_project:
        try:
            from app.services.status_transition_service import StatusTransitionService
            transition_service = StatusTransitionService(db)
            created_project = transition_service.handle_contract_signed(contract_id, auto_create_project=True)

            if created_project:
                # 更新合同关联的项目ID（如果之前没有）
                if not contract.project_id:
                    contract.project_id = created_project.id

                # Issue 1.2: 合同签订后自动触发阶段流转检查（S3→S4）
                try:
                    auto_transition_result = transition_service.check_auto_stage_transition(
                        created_project.id,
                        auto_advance=True  # 自动推进
                    )
                    if auto_transition_result.get("auto_advanced"):
                        logger.info(f"合同签订后自动推进项目 {created_project.id} 至 {auto_transition_result.get('target_stage')} 阶段")
                except Exception as e:
                    # 自动流转失败不影响合同签订，记录日志
                    logger.warning(f"合同签订后自动阶段流转失败：{str(e)}", exc_info=True)
        except Exception as e:
            # 自动创建项目失败不影响合同签订，记录日志
            logger.warning(f"合同签订自动创建项目失败：{str(e)}", exc_info=True)

    # 自动生成收款计划
    if auto_generate_payment_plans and contract.project_id:
        _generate_payment_plans_from_contract(db, contract)

    db.commit()

    # 发送合同签订通知
    try:
        from app.services.sales_reminder import notify_contract_signed
        notify_contract_signed(db, contract.id)
        db.commit()
    except Exception as e:
        # 通知失败不影响主流程
        logger.warning(f"合同签订通知发送失败，不影响主流程: {e}", exc_info=True)

    response_data = {"contract_id": contract.id}
    if created_project:
        response_data["project_id"] = created_project.id
        response_data["project_code"] = created_project.project_code
        return ResponseModel(code=200, message="合同签订成功，项目已自动创建", data=response_data)

    return ResponseModel(code=200, message="合同签订成功", data=response_data)


@router.post("/contracts/{contract_id}/project", response_model=ResponseModel)
def create_contract_project(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    project_request: ContractProjectCreateRequest,
    skip_g4_validation: bool = Query(False, description="跳过G4验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同生成项目（G4阶段门验证）
    """
    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    # 获取交付物清单
    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()

    # G4验证
    if not skip_g4_validation:
        is_valid, errors = validate_g4_contract_to_project(contract, deliverables, db)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"G4阶段门验证失败: {', '.join(errors)}"
            )

    # 检查项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == project_request.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    # 获取线索ID（通过商机关联）
    lead_id = None
    if contract.opportunity_id:
        from app.models.sales import Opportunity
        opportunity = db.query(Opportunity).filter(Opportunity.id == contract.opportunity_id).first()
        if opportunity and hasattr(opportunity, "lead_id"):
            lead_id = opportunity.lead_id

    # 创建项目
    project = Project(
        project_code=project_request.project_code,
        project_name=project_request.project_name,
        customer_id=contract.customer_id,
        contract_no=contract.contract_code,
        customer_contract_no=getattr(contract, "customer_contract_no", None),
        contract_amount=contract.contract_amount,
        contract_date=contract.signing_date,
        pm_id=project_request.pm_id,
        planned_start_date=project_request.planned_start_date,
        planned_end_date=project_request.planned_end_date,
        lead_id=lead_id,
        opportunity_id=contract.opportunity_id,
        contract_id=contract.id,
    )

    # 填充客户信息
    customer = db.query(Customer).filter(Customer.id == contract.customer_id).first()
    if customer:
        project.customer_name = customer.customer_name
        project.customer_contact = customer.contact_person
        project.customer_phone = customer.contact_phone

    db.add(project)
    db.flush()

    # 关联合同和项目
    contract.project_id = project.id
    db.commit()

    return ResponseModel(code=200, message="项目创建成功", data={"project_id": project.id})
