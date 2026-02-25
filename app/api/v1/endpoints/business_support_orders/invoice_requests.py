# -*- coding: utf-8 -*-
"""
商务支持模块 - 开票申请管理 API endpoints
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.business_support import InvoiceRequest
from app.models.enums import InvoiceStatusEnum
from app.models.project import Customer, Project, ProjectPaymentPlan
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.business_support import (
    InvoiceRequestApproveRequest,
    InvoiceRequestCreate,
    InvoiceRequestRejectRequest,
    InvoiceRequestResponse,
    InvoiceRequestUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.utils.db_helpers import get_or_404

from .utils import (
    _serialize_attachments,
    _to_invoice_request_response,
    generate_invoice_code,
    generate_invoice_request_no,
)

router = APIRouter()


# ==================== 开票申请管理 ====================


@router.get("/invoice-requests", response_model=ResponseModel[PaginatedResponse[InvoiceRequestResponse]], summary="获取开票申请列表")
async def get_invoice_requests(
    pagination: PaginationParams = Depends(get_pagination_query),
    invoice_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    keyword: Optional[str] = Query(None, description="搜索申请号/项目"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """分页获取开票申请列表"""
    try:
        query = db.query(InvoiceRequest)
        if invoice_status:
            query = query.filter(InvoiceRequest.status == invoice_status)
        if contract_id:
            query = query.filter(InvoiceRequest.contract_id == contract_id)
        if customer_id:
            query = query.filter(InvoiceRequest.customer_id == customer_id)

        # 应用关键词过滤（申请号/项目名称/客户名称）
        query = apply_keyword_filter(query, InvoiceRequest, keyword, ["request_no", "project_name", "customer_name"])

        total = query.count()
        items = (
            query.order_by(desc(InvoiceRequest.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        responses = [_to_invoice_request_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取开票申请列表成功",
            data=PaginatedResponse(
                items=responses,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total)
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取开票申请列表失败: {str(exc)}")


@router.post("/invoice-requests", response_model=ResponseModel[InvoiceRequestResponse], summary="创建开票申请")
async def create_invoice_request(
    invoice_request_data: InvoiceRequestCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建开票申请"""
    try:
        contract = db.query(Contract).filter(Contract.id == invoice_request_data.contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")

        payment_plan = None
        if invoice_request_data.payment_plan_id:
            payment_plan = db.query(ProjectPaymentPlan).filter(
                ProjectPaymentPlan.id == invoice_request_data.payment_plan_id
            ).first()
            if not payment_plan:
                raise HTTPException(status_code=404, detail="收款计划不存在")
            if payment_plan.contract_id and payment_plan.contract_id != contract.id:
                raise HTTPException(status_code=400, detail="收款计划与合同不匹配")

        project_id = (
            invoice_request_data.project_id
            or (payment_plan.project_id if payment_plan else None)
            or contract.project_id
        )
        project = None
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()

        customer_id = (
            invoice_request_data.customer_id
            or (contract.customer_id if contract else None)
            or (project.customer_id if project and project.customer_id else None)
        )
        if not customer_id:
            raise HTTPException(status_code=400, detail="缺少客户信息")
        customer = get_or_404(db, Customer, customer_id, "客户不存在")

        tax_amount = invoice_request_data.tax_amount
        if tax_amount is None and invoice_request_data.tax_rate is not None:
            tax_amount = (invoice_request_data.amount * invoice_request_data.tax_rate) / Decimal("100")

        total_amount = invoice_request_data.total_amount
        if total_amount is None:
            if tax_amount is not None:
                total_amount = invoice_request_data.amount + tax_amount
            else:
                total_amount = invoice_request_data.amount

        invoice_request = InvoiceRequest(
            request_no=generate_invoice_request_no(db),
            contract_id=contract.id,
            project_id=project.id if project else None,
            project_name=project.project_name if project else None,
            customer_id=customer.id,
            customer_name=customer.customer_name,
            payment_plan_id=payment_plan.id if payment_plan else None,
            invoice_type=invoice_request_data.invoice_type,
            invoice_title=invoice_request_data.invoice_title,
            tax_rate=invoice_request_data.tax_rate,
            amount=invoice_request_data.amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=invoice_request_data.currency,
            expected_issue_date=invoice_request_data.expected_issue_date,
            expected_payment_date=invoice_request_data.expected_payment_date,
            reason=invoice_request_data.reason,
            attachments=_serialize_attachments(invoice_request_data.attachments),
            remark=invoice_request_data.remark,
            status="PENDING",
            requested_by=current_user.id,
            requested_by_name=current_user.real_name or current_user.username,
            receipt_status="UNPAID"
        )
        db.add(invoice_request)
        db.commit()
        db.refresh(invoice_request)

        return ResponseModel(
            code=200,
            message="创建开票申请成功",
            data=_to_invoice_request_response(invoice_request)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建开票申请失败: {str(exc)}")


@router.get("/invoice-requests/{request_id}", response_model=ResponseModel[InvoiceRequestResponse], summary="获取开票申请详情")
async def get_invoice_request(
    request_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取开票申请详情"""
    invoice_request = get_or_404(db, InvoiceRequest, request_id, "开票申请不存在")
    return ResponseModel(
        code=200,
        message="获取开票申请详情成功",
        data=_to_invoice_request_response(invoice_request)
    )


@router.put("/invoice-requests/{request_id}", response_model=ResponseModel[InvoiceRequestResponse], summary="更新开票申请")
async def update_invoice_request(
    request_id: int,
    request_in: InvoiceRequestUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新开票申请"""
    try:
        invoice_request = get_or_404(db, InvoiceRequest, request_id, "开票申请不存在")
        if invoice_request.status not in ("PENDING", "REJECTED"):
            raise HTTPException(status_code=400, detail="当前状态下不可编辑开票申请")

        if request_in.payment_plan_id:
            payment_plan = db.query(ProjectPaymentPlan).filter(
                ProjectPaymentPlan.id == request_in.payment_plan_id
            ).first()
            if not payment_plan:
                raise HTTPException(status_code=404, detail="收款计划不存在")
            if payment_plan.contract_id and payment_plan.contract_id != invoice_request.contract_id:
                raise HTTPException(status_code=400, detail="收款计划与合同不匹配")
            invoice_request.payment_plan_id = payment_plan.id
            invoice_request.project_id = payment_plan.project_id
            invoice_request.project_name = payment_plan.project.project_name if payment_plan.project else invoice_request.project_name

        update_data = request_in.model_dump(exclude_unset=True)
        if "attachments" in update_data:
            invoice_request.attachments = _serialize_attachments(update_data.pop("attachments"))
        for field, value in update_data.items():
            setattr(invoice_request, field, value)

        db.add(invoice_request)
        db.commit()
        db.refresh(invoice_request)

        return ResponseModel(
            code=200,
            message="更新开票申请成功",
            data=_to_invoice_request_response(invoice_request)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新开票申请失败: {str(exc)}")


@router.post("/invoice-requests/{request_id}/approve", response_model=ResponseModel[InvoiceRequestResponse], summary="审批开票申请")
async def approve_invoice_request(
    request_id: int,
    approve_in: InvoiceRequestApproveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """审批通过开票申请并生成发票"""
    try:
        invoice_request = get_or_404(db, InvoiceRequest, request_id, "开票申请不存在")
        if invoice_request.status != "PENDING":
            raise HTTPException(status_code=400, detail="当前状态不可审批")

        issue_date = approve_in.issue_date or invoice_request.expected_issue_date or date.today()
        invoice_code = approve_in.invoice_code or generate_invoice_code(db)
        total_amount = approve_in.total_amount or invoice_request.total_amount or invoice_request.amount

        invoice = Invoice(
            invoice_code=invoice_code,
            contract_id=invoice_request.contract_id,
            project_id=invoice_request.project_id,
            invoice_type=invoice_request.invoice_type,
            amount=invoice_request.amount,
            tax_rate=invoice_request.tax_rate,
            tax_amount=invoice_request.tax_amount,
            total_amount=total_amount,
            status=InvoiceStatusEnum.ISSUED,
            payment_status="PENDING",
            issue_date=issue_date,
            buyer_name=invoice_request.invoice_title or invoice_request.customer_name,
            remark=invoice_request.reason
        )
        db.add(invoice)
        db.flush()

        invoice_request.status = "APPROVED"
        invoice_request.approval_comment = approve_in.approval_comment
        invoice_request.approved_by = current_user.id
        invoice_request.approved_at = datetime.now(timezone.utc)
        invoice_request.invoice_id = invoice.id
        invoice_request.receipt_status = "UNPAID"
        invoice_request.receipt_updated_at = datetime.now(timezone.utc)

        if invoice_request.payment_plan_id:
            payment_plan = db.query(ProjectPaymentPlan).filter(
                ProjectPaymentPlan.id == invoice_request.payment_plan_id
            ).first()
            if payment_plan:
                payment_plan.invoice_id = invoice.id
                payment_plan.invoice_no = invoice.invoice_code
                payment_plan.invoice_date = issue_date
                payment_plan.invoice_amount = total_amount
                if payment_plan.status == "PENDING":
                    payment_plan.status = "INVOICED"
                db.add(payment_plan)

        db.add(invoice_request)
        db.commit()
        db.refresh(invoice_request)

        return ResponseModel(
            code=200,
            message="审批开票申请成功",
            data=_to_invoice_request_response(invoice_request)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批开票申请失败: {str(exc)}")


@router.post("/invoice-requests/{request_id}/reject", response_model=ResponseModel[InvoiceRequestResponse], summary="驳回开票申请")
async def reject_invoice_request(
    request_id: int,
    reject_in: InvoiceRequestRejectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """驳回开票申请"""
    try:
        invoice_request = get_or_404(db, InvoiceRequest, request_id, "开票申请不存在")
        if invoice_request.status != "PENDING":
            raise HTTPException(status_code=400, detail="当前状态不可驳回")

        invoice_request.status = "REJECTED"
        invoice_request.approval_comment = reject_in.approval_comment
        invoice_request.approved_by = current_user.id
        invoice_request.approved_at = datetime.now(timezone.utc)

        db.add(invoice_request)
        db.commit()
        db.refresh(invoice_request)

        return ResponseModel(
            code=200,
            message="驳回开票申请成功",
            data=_to_invoice_request_response(invoice_request)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"驳回开票申请失败: {str(exc)}")
