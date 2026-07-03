# -*- coding: utf-8 -*-
"""
合同签订与项目生成 API endpoints
包括：合同签订、项目生成、收款计划自动生成
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import check_sales_data_permission
from app.models.project import Customer, Project
from app.models.sales import Contract, ContractDeliverable, Opportunity, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import ContractProjectCreateRequest, ContractSignRequest
from app.services.status_handlers.contract_handler import bind_presale_context_to_project
from app.utils.db_helpers import get_or_404

from ..utils import validate_g4_contract_to_project

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
    current_user: User = Depends(security.require_permission("contract:sign")),
) -> Any:
    """
    合同签订（自动生成收款计划）
    """
    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    # 数据权限：校验当前用户是否有权操作该合同
    if not check_sales_data_permission(contract, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权签订该合同")

    # F2: 签署前置——合同须已审批通过（approval_status/status 任一为 approved）
    _appr = str(getattr(contract, "approval_status", "") or "").lower()
    _st = str(getattr(contract, "status", "") or "").lower()
    if _appr != "approved" and _st not in ("approved", "signed", "executing", "completed"):
        raise HTTPException(status_code=400, detail="合同未审批通过，不能签署")

    contract.signing_date = sign_request.signed_date
    contract.status = "SIGNED"

    # Sprint 2.1 + Issue 1.2: 合同签订自动创建项目并触发阶段流转
    auto_create_project = (
        getattr(sign_request, "auto_create_project", True)
        if hasattr(sign_request, "auto_create_project")
        else True
    )
    created_project = None

    if auto_create_project:
        try:
            from app.services.status_transition_service import StatusTransitionService

            transition_service = StatusTransitionService(db)
            created_project = transition_service.handle_contract_signed(
                contract_id, auto_create_project=True
            )

            if created_project:
                # 更新合同关联的项目ID（如果之前没有）
                if not contract.project_id:
                    contract.project_id = created_project.id

                # Issue 1.2: 合同签订后自动触发阶段流转检查（S3→S4）
                try:
                    auto_transition_result = transition_service.check_auto_stage_transition(
                        created_project.id, auto_advance=True  # 自动推进
                    )
                    if auto_transition_result.get("auto_advanced"):
                        logger.info(
                            f"合同签订后自动推进项目 {created_project.id} 至 {auto_transition_result.get('target_stage')} 阶段"
                        )
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
    current_user: User = Depends(security.require_permission("contract:create")),
) -> Any:
    """
    合同生成项目（G4阶段门验证）
    """
    if project_request.contract_id and project_request.contract_id != contract_id:
        raise HTTPException(status_code=400, detail="请求体合同ID与路径合同ID不一致")

    contract = get_or_404(db, Contract, contract_id, detail="合同不存在")

    # 数据权限：校验当前用户是否有权操作该合同
    if not check_sales_data_permission(contract, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权为该合同创建项目")

    # P0-3: 验证合同状态必须为已签订
    if contract.status != "SIGNED":
        raise HTTPException(
            status_code=400,
            detail=f"合同状态必须为已签订才能创建项目，当前状态: {contract.status}",
        )

    customer = db.query(Customer).filter(Customer.id == contract.customer_id).first()
    quote_version = None
    if contract.quote_id:
        quote_version = db.query(QuoteVersion).filter(QuoteVersion.id == contract.quote_id).first()

    opportunity = None
    if contract.opportunity_id:
        opportunity = db.query(Opportunity).filter(Opportunity.id == contract.opportunity_id).first()

    lead_id = opportunity.lead_id if opportunity and hasattr(opportunity, "lead_id") else None
    salesperson_id = contract.sales_owner_id or (opportunity.owner_id if opportunity else None)

    # 检查是否已关联项目
    if contract.project_id:
        raise HTTPException(
            status_code=400,
            detail=f"合同已关联项目（ID: {contract.project_id}），不能重复创建",
        )

    if project_request.project_id:
        project = get_or_404(db, Project, project_request.project_id, detail="项目不存在")
        if project.contract_id and project.contract_id != contract.id:
            raise HTTPException(status_code=400, detail="项目已关联其他合同")

        project.contract_id = contract.id
        project.customer_id = project.customer_id or contract.customer_id
        project.contract_no = project.contract_no or contract.contract_code
        project.customer_contract_no = (
            project.customer_contract_no or getattr(contract, "customer_contract_no", None)
        )
        project.contract_amount = project.contract_amount or contract.contract_amount
        project.contract_date = project.contract_date or contract.signing_date
        project.budget_amount = (
            project.budget_amount
            or (quote_version.cost_total if quote_version and quote_version.cost_total is not None else None)
            or 0
        )
        project.lead_id = project.lead_id or lead_id
        project.opportunity_id = project.opportunity_id or contract.opportunity_id
        project.project_type = project.project_type or (opportunity.project_type if opportunity else None)
        project.product_category = project.product_category or (
            opportunity.equipment_type if opportunity else None
        )
        project.industry = project.industry or (customer.industry if customer else None)
        project.salesperson_id = project.salesperson_id or salesperson_id
        contract.project_id = project.id
        bind_presale_context_to_project(db, project)
        db.commit()

        logger.info(f"合同 {contract_id} 成功关联已有项目 {project.id}")
        return ResponseModel(
            code=200, message="项目关联成功", data={"project_id": project.id}
        )

    if not project_request.project_code or not project_request.project_name:
        raise HTTPException(
            status_code=400, detail="创建项目必须提供项目编码和项目名称"
        )

    # 获取交付物清单
    deliverables = (
        db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    )

    # G4验证
    if not skip_g4_validation:
        is_valid, errors = validate_g4_contract_to_project(contract, deliverables, db)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"G4阶段门验证失败: {', '.join(errors)}")

    # 检查项目编码是否已存在
    existing = (
        db.query(Project).filter(Project.project_code == project_request.project_code).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    # P0-2: 使用事务保护确保数据一致性
    try:
        # 创建项目
        project = Project(
            project_code=project_request.project_code,
            project_name=project_request.project_name,
            customer_id=contract.customer_id,
            contract_no=contract.contract_code,
            customer_contract_no=getattr(contract, "customer_contract_no", None),
            contract_amount=contract.contract_amount,
            budget_amount=(
                quote_version.cost_total
                if quote_version and quote_version.cost_total is not None
                else 0
            ),
            contract_date=contract.signing_date,
            pm_id=project_request.pm_id,
            planned_start_date=project_request.planned_start_date,
            planned_end_date=project_request.planned_end_date,
            lead_id=lead_id,
            opportunity_id=contract.opportunity_id,
            contract_id=contract.id,
            project_type=opportunity.project_type if opportunity else None,
            product_category=opportunity.equipment_type if opportunity else None,
            industry=customer.industry if customer else None,
            salesperson_id=salesperson_id,
        )

        # 填充客户信息
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

        db.add(project)
        db.flush()

        # 关联合同和项目
        contract.project_id = project.id
        bind_presale_context_to_project(db, project)
        db.commit()

        logger.info(f"合同 {contract_id} 成功创建项目 {project.id}")
        return ResponseModel(code=200, message="项目创建成功", data={"project_id": project.id})

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"合同 {contract_id} 创建项目失败: {e}")
        raise HTTPException(status_code=500, detail="项目创建失败，请稍后重试")
