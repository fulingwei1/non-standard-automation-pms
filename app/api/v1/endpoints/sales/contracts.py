# -*- coding: utf-8 -*-
"""
合同管理 API endpoints
"""

import logging
from typing import Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Customer, Project, ProjectMilestone, ProjectPaymentPlan
from app.schemas.project import ProjectPaymentPlanResponse
from app.models.sales import (
    Contract, ContractDeliverable, ContractAmendment,
    Quote, QuoteVersion, QuoteItem, Opportunity
)
from app.schemas.sales import (
    ContractCreate, ContractUpdate, ContractResponse, ContractDeliverableResponse,
    ContractAmendmentCreate, ContractAmendmentResponse,
    ContractSignRequest, ContractProjectCreateRequest,
    ApprovalStartRequest, ApprovalActionRequest, ApprovalStatusResponse,
    ApprovalRecordResponse, ApprovalHistoryResponse
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.approval_workflow_service import ApprovalWorkflowService
from app.models.enums import (
    WorkflowTypeEnum, ApprovalRecordStatusEnum, ApprovalActionEnum,
    ContractStatusEnum
)
from .utils import (
    get_entity_creator_id,
    generate_contract_code,
    generate_amendment_no,
    validate_g3_quote_to_contract,
    validate_g4_contract_to_project
)

router = APIRouter()


def _get_entity_creator_id(entity) -> Optional[int]:
    """Safely fetch created_by if the ORM model defines it."""
    return getattr(entity, "created_by", None)


def _generate_payment_plans_from_contract(db: Session, contract: Contract) -> List[ProjectPaymentPlan]:
    """
    根据合同自动生成收款计划
    默认规则：
    - 预付款：30%（合同签订后）
    - 发货款：40%（发货里程碑）
    - 验收款：25%（验收里程碑）
    - 质保款：5%（质保结束）
    """
    if not contract.project_id:
        return []

    project = db.query(Project).filter(Project.id == contract.project_id).first()
    if not project:
        return []

    contract_amount = float(contract.contract_amount or 0)
    if contract_amount <= 0:
        return []

    # 检查是否已有收款计划
    existing_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.contract_id == contract.id
    ).count()
    if existing_plans > 0:
        return []  # 已有计划，不重复生成

    # 默认收款计划配置
    payment_configs = [
        {
            "payment_no": 1,
            "payment_name": "预付款",
            "payment_type": "ADVANCE",
            "payment_ratio": 30.0,
            "trigger_milestone": "合同签订",
            "trigger_condition": "合同签订后"
        },
        {
            "payment_no": 2,
            "payment_name": "发货款",
            "payment_type": "DELIVERY",
            "payment_ratio": 40.0,
            "trigger_milestone": "发货",
            "trigger_condition": "设备发货后"
        },
        {
            "payment_no": 3,
            "payment_name": "验收款",
            "payment_type": "ACCEPTANCE",
            "payment_ratio": 25.0,
            "trigger_milestone": "终验通过",
            "trigger_condition": "终验通过后"
        },
        {
            "payment_no": 4,
            "payment_name": "质保款",
            "payment_type": "WARRANTY",
            "payment_ratio": 5.0,
            "trigger_milestone": "质保结束",
            "trigger_condition": "质保期结束后"
        }
    ]

    plans = []

    for config in payment_configs:
        planned_amount = contract_amount * config["payment_ratio"] / 100

        # 计算计划收款日期（基于合同签订日期和项目计划）
        planned_date = None
        if config["payment_no"] == 1:
            # 预付款：合同签订后7天
            planned_date = contract.signed_date + timedelta(days=7) if contract.signed_date else None
        elif config["payment_no"] == 2:
            # 发货款：预计项目中期
            if project.planned_end_date and project.planned_start_date:
                days = (project.planned_end_date - project.planned_start_date).days
                planned_date = project.planned_start_date + timedelta(days=int(days * 0.6)) if days > 0 else None
        elif config["payment_no"] == 3:
            # 验收款：项目结束前
            planned_date = project.planned_end_date
        elif config["payment_no"] == 4:
            # 质保款：项目结束后1年
            if project.planned_end_date:
                planned_date = project.planned_end_date + timedelta(days=365)

        # 尝试查找关联的里程碑（自动绑定）
        milestone_id = None
        if config["payment_no"] == 1:  # 预付款
            # 查找合同签订相关的里程碑（如果有）
            milestone = db.query(ProjectMilestone).filter(
                and_(
                    ProjectMilestone.project_id == contract.project_id,
                    or_(
                        ProjectMilestone.milestone_name.like("%合同%"),
                        ProjectMilestone.milestone_name.like("%签订%"),
                        ProjectMilestone.milestone_name.like("%立项%"),
                        ProjectMilestone.milestone_type == "GATE"
                    )
                )
            ).order_by(ProjectMilestone.planned_date.asc()).first()
            if milestone:
                milestone_id = milestone.id
        elif config["payment_no"] == 2:  # 发货款
            # 查找发货相关的里程碑
            milestone = db.query(ProjectMilestone).filter(
                and_(
                    ProjectMilestone.project_id == contract.project_id,
                    or_(
                        ProjectMilestone.milestone_name.like("%发货%"),
                        ProjectMilestone.milestone_name.like("%发运%"),
                        ProjectMilestone.milestone_name.like("%包装%"),
                        ProjectMilestone.milestone_type == "DELIVERY"
                    )
                )
            ).order_by(ProjectMilestone.planned_date.asc()).first()
            if milestone:
                milestone_id = milestone.id
        elif config["payment_no"] == 3:  # 验收款
            # 查找验收相关的里程碑
            milestone = db.query(ProjectMilestone).filter(
                and_(
                    ProjectMilestone.project_id == contract.project_id,
                    or_(
                        ProjectMilestone.milestone_name.like("%验收%"),
                        ProjectMilestone.milestone_name.like("%终验%"),
                        ProjectMilestone.milestone_name.like("%FAT%"),
                        ProjectMilestone.milestone_name.like("%SAT%"),
                        ProjectMilestone.milestone_type == "GATE"
                    )
                )
            ).order_by(ProjectMilestone.planned_date.desc()).first()  # 取最晚的验收里程碑
            if milestone:
                milestone_id = milestone.id
        elif config["payment_no"] == 4:  # 质保款
            # 查找质保结束相关的里程碑
            milestone = db.query(ProjectMilestone).filter(
                and_(
                    ProjectMilestone.project_id == contract.project_id,
                    or_(
                        ProjectMilestone.milestone_name.like("%质保%"),
                        ProjectMilestone.milestone_name.like("%结项%"),
                        ProjectMilestone.milestone_name.like("%完成%")
                    )
                )
            ).order_by(ProjectMilestone.planned_date.desc()).first()
            if milestone:
                milestone_id = milestone.id

        plan = ProjectPaymentPlan(
            project_id=contract.project_id,
            contract_id=contract.id,
            payment_no=config["payment_no"],
            payment_name=config["payment_name"],
            payment_type=config["payment_type"],
            payment_ratio=config["payment_ratio"],
            planned_amount=planned_amount,
            planned_date=planned_date,
            milestone_id=milestone_id,
            trigger_milestone=config["trigger_milestone"],
            trigger_condition=config["trigger_condition"],
            status="PENDING"
        )
        db.add(plan)
        plans.append(plan)

    db.flush()
    return plans


# ==================== 合同列表与创建 ====================


@router.get("/contracts", response_model=PaginatedResponse[ContractResponse])
def read_contracts(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
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

    if keyword:
        query = query.filter(Contract.contract_code.contains(keyword))

    if status:
        query = query.filter(Contract.status == status)

    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)

    total = query.count()
    offset = (page - 1) * page_size
    contracts = query.order_by(desc(Contract.created_at)).offset(offset).limit(page_size).all()

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
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
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


# ==================== 合同详情与更新 ====================


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
        _get_entity_creator_id(contract),
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


# ==================== 合同签订与项目生成 ====================


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
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    contract.signed_date = sign_request.signed_date
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
        from app.services.sales_reminder_service import notify_contract_signed
        notify_contract_signed(db, contract.id)
        db.commit()
    except Exception as e:
        # 通知失败不影响主流程
        pass

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
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

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

    # 创建项目
    project = Project(
        project_code=project_request.project_code,
        project_name=project_request.project_name,
        customer_id=contract.customer_id,
        contract_no=contract.contract_code,
        contract_amount=contract.contract_amount,
        contract_date=contract.signed_date,
        pm_id=project_request.pm_id,
        planned_start_date=project_request.planned_start_date,
        planned_end_date=project_request.planned_end_date,
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


# ==================== 收款计划 ====================


@router.get("/contracts/{contract_id}/payment-plans", response_model=List[ProjectPaymentPlanResponse])
def get_contract_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同的收款计划列表
    """

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 查询收款计划
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.contract_id == contract_id
    ).options(
        joinedload(ProjectPaymentPlan.milestone),
        joinedload(ProjectPaymentPlan.project)
    ).order_by(ProjectPaymentPlan.payment_no).all()

    result = []
    for plan in payment_plans:
        plan_dict = {
            **{c.name: getattr(plan, c.name) for c in plan.__table__.columns},
            "project_code": plan.project.project_code if plan.project else None,
            "project_name": plan.project.project_name if plan.project else None,
            "contract_code": contract.contract_code,
            "milestone_code": plan.milestone.milestone_code if plan.milestone else None,
            "milestone_name": plan.milestone.milestone_name if plan.milestone else None,
        }
        result.append(ProjectPaymentPlanResponse(**plan_dict))

    return result


# ==================== 交付物与变更 ====================


@router.get("/contracts/{contract_id}/deliverables", response_model=List[ContractDeliverableResponse])
def get_contract_deliverables(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同交付物清单
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()
    return [ContractDeliverableResponse(**{c.name: getattr(d, c.name) for c in d.__table__.columns}) for d in deliverables]


@router.get("/contracts/{contract_id}/amendments", response_model=List[ContractAmendmentResponse])
def get_contract_amendments(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同变更记录列表
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    query = db.query(ContractAmendment).filter(ContractAmendment.contract_id == contract_id)

    if status:
        query = query.filter(ContractAmendment.status == status)

    amendments = query.order_by(desc(ContractAmendment.request_date), desc(ContractAmendment.created_at)).all()

    result = []
    for amendment in amendments:
        result.append({
            "id": amendment.id,
            "contract_id": amendment.contract_id,
            "amendment_no": amendment.amendment_no,
            "amendment_type": amendment.amendment_type,
            "title": amendment.title,
            "description": amendment.description,
            "reason": amendment.reason,
            "old_value": amendment.old_value,
            "new_value": amendment.new_value,
            "amount_change": amendment.amount_change,
            "schedule_impact": amendment.schedule_impact,
            "other_impact": amendment.other_impact,
            "requestor_id": amendment.requestor_id,
            "requestor_name": amendment.requestor.real_name if amendment.requestor else None,
            "request_date": amendment.request_date,
            "status": amendment.status,
            "approver_id": amendment.approver_id,
            "approver_name": amendment.approver.real_name if amendment.approver else None,
            "approval_date": amendment.approval_date,
            "approval_comment": amendment.approval_comment,
            "attachments": amendment.attachments,
            "created_at": amendment.created_at,
            "updated_at": amendment.updated_at,
        })

    return result


@router.post("/contracts/{contract_id}/amendments", response_model=ContractAmendmentResponse, status_code=201)
def create_contract_amendment(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    amendment_in: ContractAmendmentCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建合同变更记录
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 生成变更编号
    amendment_no = generate_amendment_no(db, contract.contract_code)

    amendment = ContractAmendment(
        contract_id=contract_id,
        amendment_no=amendment_no,
        amendment_type=amendment_in.amendment_type,
        title=amendment_in.title,
        description=amendment_in.description,
        reason=amendment_in.reason,
        old_value=amendment_in.old_value,
        new_value=amendment_in.new_value,
        amount_change=amendment_in.amount_change,
        schedule_impact=amendment_in.schedule_impact,
        other_impact=amendment_in.other_impact,
        requestor_id=current_user.id,
        request_date=amendment_in.request_date,
        status="PENDING",
        attachments=amendment_in.attachments,
    )

    db.add(amendment)
    db.commit()
    db.refresh(amendment)

    return {
        "id": amendment.id,
        "contract_id": amendment.contract_id,
        "amendment_no": amendment.amendment_no,
        "amendment_type": amendment.amendment_type,
        "title": amendment.title,
        "description": amendment.description,
        "reason": amendment.reason,
        "old_value": amendment.old_value,
        "new_value": amendment.new_value,
        "amount_change": amendment.amount_change,
        "schedule_impact": amendment.schedule_impact,
        "other_impact": amendment.other_impact,
        "requestor_id": amendment.requestor_id,
        "requestor_name": amendment.requestor.real_name if amendment.requestor else None,
        "request_date": amendment.request_date,
        "status": amendment.status,
        "approver_id": amendment.approver_id,
        "approver_name": amendment.approver.real_name if amendment.approver else None,
        "approval_date": amendment.approval_date,
        "approval_comment": amendment.approval_comment,
        "attachments": amendment.attachments,
        "created_at": amendment.created_at,
        "updated_at": amendment.updated_at,
    }


# ==================== 审批工作流 ====================


@router.post("/contracts/{contract_id}/approval/start", response_model=ResponseModel)
def start_contract_approval(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    approval_request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动合同审批流程
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    if contract.status != ContractStatusEnum.DRAFT and contract.status != ContractStatusEnum.IN_REVIEW:
        raise HTTPException(status_code=400, detail="只有草稿或待审批状态的合同才能启动审批流程")

    # 获取合同金额用于路由
    routing_params = {
        "amount": float(contract.contract_amount or 0)
    }

    # 启动审批流程
    workflow_service = ApprovalWorkflowService(db)
    try:
        record = workflow_service.start_approval(
            entity_type=WorkflowTypeEnum.CONTRACT,
            entity_id=contract_id,
            initiator_id=current_user.id,
            workflow_id=approval_request.workflow_id,
            routing_params=routing_params,
            comment=approval_request.comment
        )

        # 更新合同状态
        contract.status = ContractStatusEnum.IN_REVIEW

        db.commit()

        # 发送审批通知给当前审批人
        from app.services.notification_service import notification_service, NotificationType, NotificationPriority
        try:
            # 获取当前待审批的步骤
            current_step = workflow_service.get_current_step(record.id)
            if current_step and current_step.get("approver_id"):
                notification_service.send_notification(
                    db=db,
                    recipient_id=current_step["approver_id"],
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"待审批合同: {contract.contract_name}",
                    content=f"合同编码: {contract.contract_no}\n合同金额: ¥{float(contract.contract_amount or 0):,.2f}\n发起人: {current_user.real_name or current_user.username}",
                    priority=NotificationPriority.HIGH,
                    link=f"/sales/contracts/{contract.id}/approval"
                )
        except Exception:
            pass  # 通知失败不影响主流程

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={"approval_record_id": record.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contracts/{contract_id}/approval-status", response_model=ApprovalStatusResponse)
def get_contract_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同审批状态
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.CONTRACT,
        entity_id=contract_id
    )

    if not record:
        return ApprovalStatusResponse(
            record=None,
            current_step_info=None,
            can_approve=False,
            can_reject=False,
            can_delegate=False,
            can_withdraw=False
        )

    current_step_info = workflow_service.get_current_step(record.id)

    can_approve = False
    can_reject = False
    can_delegate = False
    can_withdraw = False

    if record.status == ApprovalRecordStatusEnum.PENDING:
        if current_step_info:
            if current_step_info.get("approver_id") == current_user.id:
                can_approve = True
                can_reject = True
                if current_step_info.get("can_delegate"):
                    can_delegate = True

        if record.initiator_id == current_user.id:
            can_withdraw = True

    record_dict = {
        **{c.name: getattr(record, c.name) for c in record.__table__.columns},
        "workflow_name": record.workflow.workflow_name if record.workflow else None,
        "initiator_name": record.initiator.real_name if record.initiator else None,
        "history": []
    }

    history_list = workflow_service.get_approval_history(record.id)
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        record_dict["history"].append(ApprovalHistoryResponse(**history_dict))

    return ApprovalStatusResponse(
        record=ApprovalRecordResponse(**record_dict),
        current_step_info=current_step_info,
        can_approve=can_approve,
        can_reject=can_reject,
        can_delegate=can_delegate,
        can_withdraw=can_withdraw
    )


@router.post("/contracts/{contract_id}/approval/action", response_model=ResponseModel)
def contract_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同审批操作（通过/驳回/委托/撤回）
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.CONTRACT,
        entity_id=contract_id
    )

    if not record:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            record = workflow_service.approve_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment
            )

            if record.status == ApprovalRecordStatusEnum.APPROVED:
                # 审批完成，允许合同签订
                contract.status = ContractStatusEnum.IN_REVIEW  # 保持待审批状态，等待签订

                # 发送审批完成通知
                from app.services.notification_service import notification_service, NotificationType, NotificationPriority
                try:
                    # 通知合同创建人审批已完成
                    notification_service.send_notification(
                        db=db,
                        recipient_id=contract.created_by,
                        notification_type=NotificationType.TASK_APPROVED,
                        title=f"合同审批已完成: {contract.contract_name}",
                        content=f"合同编号: {contract.contract_no}\n审批人: {current_user.real_name or current_user.username}",
                        priority=NotificationPriority.NORMAL,
                        link=f"/sales/contracts/{contract.id}"
                    )
                except Exception:
                    pass  # 通知失败不影响主流程
            message = "审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            record = workflow_service.reject_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回"
            )
            contract.status = ContractStatusEnum.CANCELLED
            message = "审批已驳回"

            # 发送驳回通知
            from app.services.notification_service import notification_service, NotificationType, NotificationPriority
            try:
                notification_service.send_notification(
                    db=db,
                    recipient_id=contract.created_by,
                    notification_type=NotificationType.TASK_REJECTED,
                    title=f"合同审批已驳回: {contract.contract_name}",
                    content=f"合同编号: {contract.contract_no}\n驳回原因: {action_request.comment or '无'}",
                    priority=NotificationPriority.HIGH,
                    link=f"/sales/contracts/{contract.id}"
                )
            except Exception:
                pass

        elif action_request.action == ApprovalActionEnum.DELEGATE:
            if not action_request.delegate_to_id:
                raise HTTPException(status_code=400, detail="委托操作需要指定委托给的用户ID")

            record = workflow_service.delegate_step(
                record_id=record.id,
                approver_id=current_user.id,
                delegate_to_id=action_request.delegate_to_id,
                comment=action_request.comment
            )
            message = "审批已委托"

            # 发送委托通知
            from app.services.notification_service import notification_service, NotificationType
            try:
                notification_service.send_notification(
                    db=db,
                    recipient_id=action_request.delegate_to_id,
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"合同审批已委托给您: {contract.contract_name}",
                    content=f"原审批人: {current_user.real_name or current_user.username}\n合同编码: {contract.contract_no}",
                    priority=notification_service.NotificationPriority.NORMAL,
                    link=f"/sales/contracts/{contract.id}/approval"
                )
            except Exception:
                pass

        elif action_request.action == ApprovalActionEnum.WITHDRAW:
            record = workflow_service.withdraw_approval(
                record_id=record.id,
                initiator_id=current_user.id,
                comment=action_request.comment
            )
            contract.status = ContractStatusEnum.DRAFT
            message = "审批已撤回"

        else:
            raise HTTPException(status_code=400, detail=f"不支持的审批操作: {action_request.action}")

        db.commit()

        return ResponseModel(
            code=200,
            message=message,
            data={"approval_record_id": record.id, "status": record.status}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contracts/{contract_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_contract_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同审批历史
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.CONTRACT,
        entity_id=contract_id
    )

    if not record:
        return []

    history_list = workflow_service.get_approval_history(record.id)
    result = []
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        result.append(ApprovalHistoryResponse(**history_dict))

    return result


# ==================== 简单审批（兼容旧接口） ====================


@router.put("/contracts/{contract_id}/approve", response_model=ResponseModel)
def approve_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    approved: bool = Query(..., description="是否批准"),
    remark: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同审批
    """
    # 检查审批权限
    if not security.has_sales_approval_access(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批合同"
        )

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    if approved:
        contract.status = "APPROVED"
    else:
        contract.status = "REJECTED"

    db.commit()

    return ResponseModel(code=200, message="合同审批完成" if approved else "合同已驳回")


# ==================== 导出功能 ====================


@router.get("/contracts/export")
def export_contracts(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.3: 导出合同列表（Excel）
    """
    from app.services.excel_export_service import ExcelExportService, create_excel_response

    query = db.query(Contract)
    if keyword:
        query = query.filter(or_(Contract.contract_code.contains(keyword), Contract.contract_name.contains(keyword), Contract.opportunity.has(Opportunity.opp_name.contains(keyword))))
    if status:
        query = query.filter(Contract.status == status)
    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)
    if owner_id:
        query = query.filter(Contract.owner_id == owner_id)

    contracts = query.order_by(Contract.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "contract_code", "label": "合同编码", "width": 15},
        {"key": "contract_name", "label": "合同名称", "width": 30},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "contract_amount", "label": "合同金额", "width": 15, "format": export_service.format_currency},
        {"key": "signed_date", "label": "签订日期", "width": 12, "format": export_service.format_date},
        {"key": "delivery_deadline", "label": "交期", "width": 12, "format": export_service.format_date},
        {"key": "status", "label": "状态", "width": 12},
        {"key": "project_code", "label": "项目编码", "width": 15},
        {"key": "owner_name", "label": "负责人", "width": 12},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = [{
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name or '',
        "customer_name": contract.customer.customer_name if contract.customer else '',
        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
        "signed_date": contract.signed_date,
        "delivery_deadline": contract.delivery_deadline,
        "status": contract.status,
        "project_code": contract.project.project_code if contract.project else '',
        "owner_name": contract.owner.real_name if contract.owner else '',
        "created_at": contract.created_at,
    } for contract in contracts]

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="合同列表", title="合同列表")
    filename = f"合同列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)


@router.get("/contracts/{contract_id}/pdf")
def export_contract_pdf(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.5: 导出合同 PDF
    """
    from app.services.pdf_export_service import PDFExportService, create_pdf_response

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    deliverables = db.query(ContractDeliverable).filter(ContractDeliverable.contract_id == contract_id).all()

    # 准备数据
    contract_data = {
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name or '',
        "customer_name": contract.customer.customer_name if contract.customer else '',
        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
        "signed_date": contract.signed_date,
        "delivery_deadline": contract.delivery_deadline,
        "status": contract.status,
    }

    deliverable_list = [{
        "deliverable_name": d.deliverable_name or '',
        "quantity": float(d.quantity) if d.quantity else 0,
        "unit": d.unit or '',
        "remark": d.remark or '',
    } for d in deliverables]

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_contract_to_pdf(contract_data, deliverable_list)

    filename = f"合同_{contract.contract_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)
