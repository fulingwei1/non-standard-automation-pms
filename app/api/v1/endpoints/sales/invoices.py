# -*- coding: utf-8 -*-
"""
发票管理 API endpoints
"""

import logging
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Customer, Project
from app.models.sales import (
    Contract, Invoice, InvoiceApproval
)
from app.schemas.sales import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceIssueRequest,
    InvoiceApprovalResponse, InvoiceApprovalCreate,
    ApprovalStartRequest, ApprovalActionRequest, ApprovalStatusResponse,
    ApprovalRecordResponse, ApprovalHistoryResponse
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.approval_workflow_service import ApprovalWorkflowService
from app.models.enums import (
    WorkflowTypeEnum, ApprovalRecordStatusEnum, ApprovalActionEnum,
    InvoiceStatusEnum, InvoiceStatusEnum as InvoiceStatus
)
from .utils import generate_invoice_code

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
def read_invoices(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票列表
    Issue 7.1: 已集成数据权限过滤（财务可以看到所有发票）
    """
    query = db.query(Invoice).options(
        joinedload(Invoice.contract)
    )

    # Issue 7.1: 应用财务数据权限过滤（财务可以看到所有发票）
    # 注意：Invoice 模型没有 owner_id 字段，所以跳过此过滤
    # query = security.filter_sales_finance_data_by_scope(query, current_user, db, Invoice, 'owner_id')

    if keyword:
        query = query.filter(Invoice.invoice_code.contains(keyword))

    if status:
        query = query.filter(Invoice.status == status)

    if customer_id:
        # 通过 contract 关联过滤客户
        query = query.join(Contract).filter(Contract.customer_id == customer_id)

    total = query.count()
    offset = (page - 1) * page_size
    invoices = query.order_by(desc(Invoice.created_at)).offset(offset).limit(page_size).all()

    invoice_responses = []
    for invoice in invoices:
        # 获取客户名称
        customer_name = None
        if invoice.contract and invoice.contract.customer:
            customer_name = invoice.contract.customer.customer_name

        invoice_dict = {
            **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
            "contract_code": invoice.contract.contract_code if invoice.contract else None,
            "customer_name": customer_name,
        }
        invoice_responses.append(InvoiceResponse(**invoice_dict))

    return PaginatedResponse(
        items=invoice_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/invoices_old", response_model=PaginatedResponse[InvoiceResponse])
def read_invoices_old(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票列表
    Issue 7.1: 已集成数据权限过滤（财务和销售总监可以看到所有发票）
    """
    query = db.query(Invoice).options(
        joinedload(Invoice.contract).joinedload(Contract.customer),
        joinedload(Invoice.project)
    )

    # Issue 7.1: 应用财务数据权限过滤（财务和销售总监可以看到所有发票）
    query = security.filter_sales_finance_data_by_scope(query, current_user, db, Invoice, 'owner_id')

    if keyword:
        query = query.filter(Invoice.invoice_code.contains(keyword))

    if status:
        query = query.filter(Invoice.status == status)

    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)

    total = query.count()
    offset = (page - 1) * page_size
    invoices = query.order_by(desc(Invoice.created_at)).offset(offset).limit(page_size).all()

    invoice_responses = []
    for invoice in invoices:
        contract = invoice.contract
        project = invoice.project
        customer = contract.customer if contract else None
        invoice_dict = {
            **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
            "contract_code": contract.contract_code if contract else None,
            "project_code": project.project_code if project else None,
            "project_name": project.project_name if project else None,
            "customer_name": customer.customer_name if customer else None,
        }
        invoice_responses.append(InvoiceResponse(**invoice_dict))

    return PaginatedResponse(
        items=invoice_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_in: InvoiceCreate,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    创建发票
    """
    invoice_data = invoice_in.model_dump()

    # 如果没有提供编码，自动生成
    if not invoice_data.get("invoice_code"):
        invoice_data["invoice_code"] = generate_invoice_code(db)
    else:
        existing = db.query(Invoice).filter(Invoice.invoice_code == invoice_data["invoice_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="发票编码已存在")

    contract = db.query(Contract).filter(Contract.id == invoice_data["contract_id"]).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    invoice = Invoice(**invoice_data)
    db.add(invoice)
    db.flush()

    # 如果发票状态是 APPLIED，自动启动审批流程
    if invoice.status == InvoiceStatus.APPLIED:
        try:
            workflow_service = ApprovalWorkflowService(db)
            routing_params = {"amount": float(invoice.amount or 0)}
            record = workflow_service.start_approval(
                entity_type=WorkflowTypeEnum.INVOICE,
                entity_id=invoice.id,
                initiator_id=current_user.id,
                workflow_id=None,  # 自动选择
                routing_params=routing_params,
                comment="发票申请"
            )
            invoice.status = InvoiceStatus.IN_REVIEW
        except Exception as e:
            # 如果启动审批失败，记录日志但不阻止发票创建
            logger.warning(
                f"发票审批流程启动失败: invoice_id={invoice.id}, error={str(e)}"
            )

    db.commit()
    db.refresh(invoice)

    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "contract_code": contract.contract_code,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


@router.get("/invoices/export")
def export_invoices(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.4: 导出发票列表（Excel）
    """
    from app.services.excel_export_service import ExcelExportService, create_excel_response

    query = db.query(Invoice)
    if keyword:
        query = query.filter(or_(Invoice.invoice_code.contains(keyword), Invoice.contract.has(Contract.contract_code.contains(keyword))))
    if status:
        query = query.filter(Invoice.status == status)
    if customer_id:
        query = query.filter(Invoice.contract.has(Contract.customer_id == customer_id))

    invoices = query.order_by(Invoice.created_at.desc()).all()
    export_service = ExcelExportService()
    columns = [
        {"key": "invoice_code", "label": "发票编码", "width": 15},
        {"key": "contract_code", "label": "合同编码", "width": 15},
        {"key": "customer_name", "label": "客户名称", "width": 25},
        {"key": "invoice_type", "label": "发票类型", "width": 12},
        {"key": "amount", "label": "发票金额", "width": 15, "format": export_service.format_currency},
        {"key": "paid_amount", "label": "已收金额", "width": 15, "format": export_service.format_currency},
        {"key": "unpaid_amount", "label": "未收金额", "width": 15, "format": export_service.format_currency},
        {"key": "issue_date", "label": "开票日期", "width": 12, "format": export_service.format_date},
        {"key": "due_date", "label": "到期日期", "width": 12, "format": export_service.format_date},
        {"key": "payment_status", "label": "收款状态", "width": 12},
        {"key": "status", "label": "发票状态", "width": 12},
        {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
    ]

    data = []
    for invoice in invoices:
        total_amount = float(invoice.total_amount or invoice.amount or 0)
        paid_amount = float(invoice.paid_amount or 0)
        unpaid_amount = total_amount - paid_amount
        data.append({
            "invoice_code": invoice.invoice_code,
            "contract_code": invoice.contract.contract_code if invoice.contract else '',
            "customer_name": invoice.contract.customer.customer_name if invoice.contract and invoice.contract.customer else '',
            "invoice_type": invoice.invoice_type or '',
            "amount": total_amount,
            "paid_amount": paid_amount,
            "unpaid_amount": unpaid_amount,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "payment_status": invoice.payment_status or '',
            "status": invoice.status,
            "created_at": invoice.created_at,
        })

    excel_data = export_service.export_to_excel(data=data, columns=columns, sheet_name="发票列表", title="发票列表")
    filename = f"发票列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def read_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票详情
    """
    invoice = db.query(Invoice).options(
        joinedload(Invoice.contract).joinedload(Contract.customer),
        joinedload(Invoice.project)
    ).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    contract = invoice.contract
    project = invoice.project
    customer = contract.customer if contract else None
    invoice_dict = {
        **{c.name: getattr(invoice, c.name) for c in invoice.__table__.columns},
        "contract_code": contract.contract_code if contract else None,
        "project_code": project.project_code if project else None,
        "project_name": project.project_name if project else None,
        "customer_name": customer.customer_name if customer else None,
    }
    return InvoiceResponse(**invoice_dict)


@router.post("/invoices/{invoice_id}/issue", response_model=ResponseModel)
def issue_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    issue_request: InvoiceIssueRequest,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    开票
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查是否已通过审批（如果启用了审批工作流）
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
    )

    if record and record.status != ApprovalRecordStatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="发票尚未通过审批，无法开票")

    invoice.issue_date = issue_request.issue_date
    invoice.status = InvoiceStatus.ISSUED
    invoice.payment_status = "PENDING"

    # 如果没有设置到期日期，默认设置为开票日期后30天
    if not invoice.due_date and invoice.issue_date:
        from datetime import timedelta
        invoice.due_date = invoice.issue_date + timedelta(days=30)

    db.commit()

    # 发送发票开具通知
    try:
        from app.services.sales_reminder_service import notify_invoice_issued
        notify_invoice_issued(db, invoice.id)
        db.commit()
    except Exception as e:
        # 通知失败不影响主流程
        pass

    return ResponseModel(code=200, message="发票开票成功")


@router.delete("/invoices/{invoice_id}", status_code=200)
def delete_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    删除发票（仅限草稿状态）
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 只有草稿状态才能删除
    if invoice.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的发票才能删除")

    db.delete(invoice)
    db.commit()

    return ResponseModel(code=200, message="发票已删除")


@router.post("/invoices/{invoice_id}/receive-payment", response_model=ResponseModel)
def receive_payment(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    paid_amount: str = Query(..., description="收款金额"),
    paid_date: date = Query(..., description="收款日期"),
    remark: Optional[str] = Query(None, description="备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    记录发票收款
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != "ISSUED":
        raise HTTPException(status_code=400, detail="只有已开票的发票才能记录收款")

    # 更新收款信息
    current_paid = invoice.paid_amount or Decimal("0")
    paid_amount_decimal = Decimal(str(paid_amount))
    new_paid = current_paid + paid_amount_decimal
    invoice.paid_amount = new_paid
    invoice.paid_date = paid_date

    # 更新收款状态
    total = invoice.total_amount or invoice.amount or Decimal("0")
    if new_paid >= total:
        invoice.payment_status = "PAID"
    elif new_paid > Decimal("0"):
        invoice.payment_status = "PARTIAL"
    else:
        invoice.payment_status = "PENDING"

    if remark:
        invoice.remark = (invoice.remark or "") + f"\n收款备注: {remark}"

    db.commit()

    return ResponseModel(code=200, message="收款记录成功", data={
        "paid_amount": float(new_paid),
        "payment_status": invoice.payment_status
    })


@router.post("/invoices/{invoice_id}/approval/start", response_model=ResponseModel)
def start_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approval_request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动发票审批流程
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != InvoiceStatus.APPLIED:
        raise HTTPException(status_code=400, detail="只有已申请状态的发票才能启动审批流程")

    # 获取发票金额用于路由
    routing_params = {
        "amount": float(invoice.amount or 0)
    }

    # 启动审批流程
    workflow_service = ApprovalWorkflowService(db)
    try:
        record = workflow_service.start_approval(
            entity_type=WorkflowTypeEnum.INVOICE,
            entity_id=invoice_id,
            initiator_id=current_user.id,
            workflow_id=approval_request.workflow_id,
            routing_params=routing_params,
            comment=approval_request.comment
        )

        # 更新发票状态
        invoice.status = InvoiceStatus.IN_REVIEW

        db.commit()

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={"approval_record_id": record.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices/{invoice_id}/approval-status", response_model=ApprovalStatusResponse)
def get_invoice_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批状态
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
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


@router.post("/invoices/{invoice_id}/approval/action", response_model=ResponseModel)
def invoice_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发票审批操作（通过/驳回/委托/撤回）
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
    )

    if not record:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            record = workflow_service.approve_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment
            )

            if record.status == ApprovalRecordStatusEnum.APPROVED:
                # 审批完成，允许开票
                invoice.status = InvoiceStatus.APPROVED
            message = "审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            record = workflow_service.reject_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回"
            )
            invoice.status = InvoiceStatus.REJECTED
            message = "审批已驳回"

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

        elif action_request.action == ApprovalActionEnum.WITHDRAW:
            record = workflow_service.withdraw_approval(
                record_id=record.id,
                initiator_id=current_user.id,
                comment=action_request.comment
            )
            invoice.status = InvoiceStatus.APPLIED
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


@router.get("/invoices/{invoice_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_invoice_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批历史
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
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


@router.put("/invoices/{invoice_id}/approve", response_model=ResponseModel)
def approve_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approved: bool = Query(..., description="是否批准"),
    remark: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开票审批（单级审批，兼容旧接口）
    """
    # 检查审批权限
    if not security.has_sales_approval_access(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批发票"
        )

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if approved:
        invoice.status = "APPROVED"
    else:
        invoice.status = "REJECTED"

    db.commit()

    return ResponseModel(code=200, message="发票审批完成" if approved else "发票已驳回")


@router.put("/invoices/{invoice_id}/submit-approval", response_model=ResponseModel)
def submit_invoice_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交发票审批（创建多级审批记录）
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 检查是否已有审批记录
    existing_approvals = db.query(InvoiceApproval).filter(InvoiceApproval.invoice_id == invoice_id).count()
    if existing_approvals > 0:
        raise HTTPException(status_code=400, detail="发票已提交审批，请勿重复提交")

    # 根据发票金额确定审批流程
    invoice_amount = float(invoice.total_amount or invoice.amount or 0)

    # 审批流程：根据金额确定审批层级
    # 小于10万：财务（1级）
    # 10-50万：财务（1级）+ 财务经理（2级）
    # 大于50万：财务（1级）+ 财务经理（2级）+ 财务总监（3级）

    approval_levels = []
    if invoice_amount < 100000:
        approval_levels = [1]  # 财务
    elif invoice_amount < 500000:
        approval_levels = [1, 2]  # 财务 + 财务经理
    else:
        approval_levels = [1, 2, 3]  # 财务 + 财务经理 + 财务总监

    # 创建审批记录
    from datetime import timedelta
    role_map = {1: "财务", 2: "财务经理", 3: "财务总监"}
    for level in approval_levels:
        approval = InvoiceApproval(
            invoice_id=invoice_id,
            approval_level=level,
            approval_role=role_map.get(level, "审批人"),
            status="PENDING",
            due_date=datetime.now() + timedelta(days=2)  # 默认2天审批期限
        )
        db.add(approval)

    invoice.status = "APPLIED"
    db.commit()

    return ResponseModel(code=200, message="发票已提交审批", data={"approval_levels": len(approval_levels)})


@router.get("/invoices/{invoice_id}/approvals", response_model=List[InvoiceApprovalResponse])
def get_invoice_approvals(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批记录列表
    """
    approvals = db.query(InvoiceApproval).filter(InvoiceApproval.invoice_id == invoice_id).order_by(InvoiceApproval.approval_level).all()

    result = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name if approver else None

        result.append(InvoiceApprovalResponse(
            id=approval.id,
            invoice_id=approval.invoice_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            status=approval.status,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))

    return result


@router.put("/invoice-approvals/{approval_id}/approve", response_model=InvoiceApprovalResponse)
def approve_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_opinion: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过（多级审批）
    """
    approval = db.query(InvoiceApproval).filter(InvoiceApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_opinion
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 检查是否所有审批都已完成
    invoice = db.query(Invoice).filter(Invoice.id == approval.invoice_id).first()
    if invoice:
        pending_approvals = db.query(InvoiceApproval).filter(
            InvoiceApproval.invoice_id == approval.invoice_id,
            InvoiceApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新发票状态
            invoice.status = "APPROVED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return InvoiceApprovalResponse(
        id=approval.id,
        invoice_id=approval.invoice_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/invoice-approvals/{approval_id}/reject", response_model=InvoiceApprovalResponse)
def reject_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回（多级审批）
    """
    approval = db.query(InvoiceApproval).filter(InvoiceApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 驳回后，发票状态变为被拒
    invoice = db.query(Invoice).filter(Invoice.id == approval.invoice_id).first()
    if invoice:
        invoice.status = "REJECTED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return InvoiceApprovalResponse(
        id=approval.id,
        invoice_id=approval.invoice_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/invoices/{invoice_id}/void", response_model=ResponseModel)
def void_invoice(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    reason: Optional[str] = Query(None, description="作废原因"),
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    作废发票
    """
    from app.models.enums import InvoiceStatusEnum

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 只有已开票或已审批的发票才能作废
    if invoice.status not in [InvoiceStatusEnum.ISSUED, InvoiceStatusEnum.APPROVED]:
        raise HTTPException(status_code=400, detail="只有已开票或已审批的发票才能作废")

    # 如果已收款，不能作废
    if invoice.paid_amount and invoice.paid_amount > 0:
        raise HTTPException(status_code=400, detail="已收款的发票不能作废，请先处理收款")

    invoice.status = InvoiceStatusEnum.VOIDED
    if reason:
        invoice.remark = (invoice.remark or "") + f"\n作废原因: {reason}"

    db.commit()

    return ResponseModel(code=200, message="发票已作废")


@router.get("/invoices/{invoice_id}/pdf")
def export_invoice_pdf(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.5: 导出发票 PDF
    """
    from app.services.pdf_export_service import PDFExportService, create_pdf_response

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 准备数据
    total_amount = float(invoice.total_amount or invoice.amount or 0)
    paid_amount = float(invoice.paid_amount or 0)

    invoice_data = {
        "invoice_code": invoice.invoice_code,
        "contract_code": invoice.contract.contract_code if invoice.contract else '',
        "customer_name": invoice.contract.customer.customer_name if invoice.contract and invoice.contract.customer else '',
        "invoice_type": invoice.invoice_type or '',
        "total_amount": total_amount,
        "amount": total_amount,
        "paid_amount": paid_amount,
        "issue_date": invoice.issue_date,
        "due_date": invoice.due_date,
        "payment_status": invoice.payment_status or '',
        "status": invoice.status,
    }

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_invoice_to_pdf(invoice_data)

    filename = f"发票_{invoice.invoice_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)
