# -*- coding: utf-8 -*-
"""
商务支持模块 - 销售订单和发货管理 API endpoints
"""

import json
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.models.user import User
from app.models.project import Customer, Project, ProjectPaymentPlan
from app.models.business_support import (
    SalesOrder, SalesOrderItem, DeliveryOrder,
    AcceptanceTracking, AcceptanceTrackingRecord, Reconciliation,
    BiddingProject, InvoiceRequest, CustomerSupplierRegistration
)
from app.models.acceptance import AcceptanceOrder
from app.models.sales import Invoice, Contract
from app.models.enums import InvoiceStatusEnum
from app.schemas.business_support import (
    SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse,
    SalesOrderItemCreate, SalesOrderItemResponse,
    AssignProjectRequest, SendNoticeRequest,
    DeliveryOrderCreate, DeliveryOrderUpdate, DeliveryOrderResponse,
    DeliveryApprovalRequest,
    AcceptanceTrackingCreate, AcceptanceTrackingUpdate, AcceptanceTrackingResponse,
    ConditionCheckRequest, ReminderRequest, AcceptanceTrackingRecordResponse,
    ReconciliationCreate, ReconciliationUpdate, ReconciliationResponse,
    SalesReportResponse, PaymentReportResponse, ContractReportResponse, InvoiceReportResponse,
    InvoiceRequestCreate, InvoiceRequestUpdate, InvoiceRequestResponse,
    InvoiceRequestApproveRequest, InvoiceRequestRejectRequest,
    CustomerSupplierRegistrationCreate, CustomerSupplierRegistrationUpdate,
    CustomerSupplierRegistrationResponse, SupplierRegistrationReviewRequest
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 编码生成函数 ====================


def generate_order_no(db: Session) -> str:
    """生成销售订单编号：SO250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"SO{month_str}-"
    
    max_order = (
        db.query(SalesOrder)
        .filter(SalesOrder.order_no.like(f"{prefix}%"))
        .order_by(desc(SalesOrder.order_no))
        .first()
    )
    
    if max_order:
        try:
            seq = int(max_order.order_no.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_delivery_no(db: Session) -> str:
    """生成送货单号：DO250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"DO{month_str}-"
    
    max_delivery = (
        db.query(DeliveryOrder)
        .filter(DeliveryOrder.delivery_no.like(f"{prefix}%"))
        .order_by(desc(DeliveryOrder.delivery_no))
        .first()
    )
    
    if max_delivery:
        try:
            seq = int(max_delivery.delivery_no.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_invoice_request_no(db: Session) -> str:
    """生成开票申请编号：IR250101-001"""
    today = datetime.now()
    prefix = f"IR{today.strftime('%y%m%d')}-"

    latest = (
        db.query(InvoiceRequest)
        .filter(InvoiceRequest.request_no.like(f"{prefix}%"))
        .order_by(desc(InvoiceRequest.request_no))
        .first()
    )
    if latest:
        try:
            seq = int(latest.request_no.split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_registration_no(db: Session) -> str:
    """生成客户供应商入驻编号：CR250101-001"""
    today = datetime.now()
    prefix = f"CR{today.strftime('%y%m%d')}-"

    latest = (
        db.query(CustomerSupplierRegistration)
        .filter(CustomerSupplierRegistration.registration_no.like(f"{prefix}%"))
        .order_by(desc(CustomerSupplierRegistration.registration_no))
        .first()
    )
    if latest:
        try:
            seq = int(latest.registration_no.split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_invoice_code(db: Session) -> str:
    """生成发票编码：INV-250101-001"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"INV-{today}-"

    latest = (
        db.query(Invoice)
        .filter(Invoice.invoice_code.like(f"{prefix}%"))
        .order_by(desc(Invoice.invoice_code))
        .first()
    )
    if latest:
        try:
            seq = int(latest.invoice_code.split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def _serialize_attachments(items: Optional[List[str]]) -> Optional[str]:
    if not items:
        return None
    try:
        return json.dumps(items, ensure_ascii=False)
    except Exception:
        return json.dumps([str(item) for item in items], ensure_ascii=False)


def _deserialize_attachments(payload: Optional[str]) -> Optional[List[str]]:
    if not payload:
        return None
    try:
        data = json.loads(payload)
        if isinstance(data, list):
            return data
    except Exception:
        return [payload]
    return None


def _to_invoice_request_response(invoice_request: InvoiceRequest) -> InvoiceRequestResponse:
    contract_code = invoice_request.contract.contract_code if invoice_request.contract else None
    project_name = invoice_request.project.project_name if invoice_request.project else invoice_request.project_name
    customer_name = invoice_request.customer.customer_name if invoice_request.customer else invoice_request.customer_name
    approved_by_name = None
    if invoice_request.approver:
        approved_by_name = invoice_request.approver.real_name or invoice_request.approver.username
    invoice_code = invoice_request.invoice.invoice_code if invoice_request.invoice else None

    return InvoiceRequestResponse(
        id=invoice_request.id,
        request_no=invoice_request.request_no,
        contract_id=invoice_request.contract_id,
        contract_code=contract_code,
        project_id=invoice_request.project_id,
        project_name=project_name,
        customer_id=invoice_request.customer_id,
        customer_name=customer_name,
        payment_plan_id=invoice_request.payment_plan_id,
        invoice_type=invoice_request.invoice_type,
        invoice_title=invoice_request.invoice_title,
        tax_rate=invoice_request.tax_rate,
        amount=invoice_request.amount,
        tax_amount=invoice_request.tax_amount,
        total_amount=invoice_request.total_amount,
        currency=invoice_request.currency,
        expected_issue_date=invoice_request.expected_issue_date,
        expected_payment_date=invoice_request.expected_payment_date,
        reason=invoice_request.reason,
        attachments=_deserialize_attachments(invoice_request.attachments),
        remark=invoice_request.remark,
        status=invoice_request.status,
        approval_comment=invoice_request.approval_comment,
        requested_by=invoice_request.requested_by,
        requested_by_name=invoice_request.requested_by_name,
        approved_by=invoice_request.approved_by,
        approved_by_name=approved_by_name,
        approved_at=invoice_request.approved_at,
        invoice_id=invoice_request.invoice_id,
        invoice_code=invoice_code,
        receipt_status=invoice_request.receipt_status,
        receipt_updated_at=invoice_request.receipt_updated_at,
        created_at=invoice_request.created_at,
        updated_at=invoice_request.updated_at,
    )


def _to_registration_response(record: CustomerSupplierRegistration) -> CustomerSupplierRegistrationResponse:
    reviewer_name = None
    if record.reviewer:
        reviewer_name = record.reviewer.real_name or record.reviewer.username
    return CustomerSupplierRegistrationResponse(
        id=record.id,
        registration_no=record.registration_no,
        customer_id=record.customer_id,
        customer_name=record.customer_name,
        platform_name=record.platform_name,
        platform_url=record.platform_url,
        registration_status=record.registration_status,
        application_date=record.application_date,
        approved_date=record.approved_date,
        expire_date=record.expire_date,
        contact_person=record.contact_person,
        contact_phone=record.contact_phone,
        contact_email=record.contact_email,
        required_docs=_deserialize_attachments(record.required_docs),
        reviewer_id=record.reviewer_id,
        reviewer_name=reviewer_name,
        review_comment=record.review_comment,
        external_sync_status=record.external_sync_status,
        last_sync_at=record.last_sync_at,
        remark=record.remark,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# ==================== 销售订单管理 ====================


@router.get("/sales-orders", response_model=ResponseModel[PaginatedResponse[SalesOrderResponse]], summary="获取销售订单列表")
async def get_sales_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    order_status: Optional[str] = Query(None, description="订单状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售订单列表"""
    try:
        query = db.query(SalesOrder)
        
        # 筛选条件
        if contract_id:
            query = query.filter(SalesOrder.contract_id == contract_id)
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        if project_id:
            query = query.filter(SalesOrder.project_id == project_id)
        if order_status:
            query = query.filter(SalesOrder.order_status == order_status)
        if search:
            query = query.filter(
                or_(
                    SalesOrder.order_no.like(f"%{search}%"),
                    SalesOrder.customer_name.like(f"%{search}%"),
                    SalesOrder.contract_no.like(f"%{search}%")
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(SalesOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        order_list = []
        for item in items:
            # 查询订单明细
            items_data = [
                SalesOrderItemResponse(
                    id=oi.id,
                    sales_order_id=oi.sales_order_id,
                    item_name=oi.item_name,
                    item_spec=oi.item_spec,
                    qty=oi.qty,
                    unit=oi.unit,
                    unit_price=oi.unit_price,
                    amount=oi.amount,
                    remark=oi.remark,
                    created_at=oi.created_at,
                    updated_at=oi.updated_at
                )
                for oi in item.order_items
            ]
            
            order_list.append(SalesOrderResponse(
                id=item.id,
                order_no=item.order_no,
                contract_id=item.contract_id,
                contract_no=item.contract_no,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                project_id=item.project_id,
                project_no=item.project_no,
                order_type=item.order_type,
                order_amount=item.order_amount,
                currency=item.currency,
                required_date=item.required_date,
                promised_date=item.promised_date,
                order_status=item.order_status,
                project_no_assigned=item.project_no_assigned,
                project_no_assigned_date=item.project_no_assigned_date,
                project_notice_sent=item.project_notice_sent,
                project_notice_date=item.project_notice_date,
                erp_order_no=item.erp_order_no,
                erp_sync_status=item.erp_sync_status,
                sales_person_id=item.sales_person_id,
                sales_person_name=item.sales_person_name,
                support_person_id=item.support_person_id,
                remark=item.remark,
                items=items_data,
                created_at=item.created_at,
                updated_at=item.updated_at
            ))
        
        return ResponseModel(
            code=200,
            message="获取销售订单列表成功",
            data=PaginatedResponse(
                items=order_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售订单列表失败: {str(e)}")


@router.post("/sales-orders", response_model=ResponseModel[SalesOrderResponse], summary="创建销售订单")
async def create_sales_order(
    order_data: SalesOrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建销售订单"""
    try:
        # 生成订单编号
        order_no = order_data.order_no or generate_order_no(db)
        
        # 检查订单编号是否已存在
        existing = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
        if existing:
            raise HTTPException(status_code=400, detail="订单编号已存在")
        
        # 获取客户名称
        customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 获取合同编号（如果有）
        contract_no = None
        if order_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == order_data.contract_id).first()
            if contract:
                contract_no = contract.contract_code
        
        # 创建销售订单
        sales_order = SalesOrder(
            order_no=order_no,
            contract_id=order_data.contract_id,
            contract_no=contract_no,
            customer_id=order_data.customer_id,
            customer_name=customer.customer_name,
            project_id=order_data.project_id,
            order_type=order_data.order_type or "standard",
            order_amount=order_data.order_amount,
            currency=order_data.currency or "CNY",
            required_date=order_data.required_date,
            promised_date=order_data.promised_date,
            order_status="draft",
            sales_person_id=order_data.sales_person_id,
            sales_person_name=order_data.sales_person_name,
            support_person_id=current_user.id,
            remark=order_data.remark
        )
        
        db.add(sales_order)
        db.flush()  # 获取订单ID
        
        # 创建订单明细
        if order_data.items:
            for item_data in order_data.items:
                order_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    item_name=item_data.item_name,
                    item_spec=item_data.item_spec,
                    qty=item_data.qty,
                    unit=item_data.unit,
                    unit_price=item_data.unit_price,
                    amount=item_data.amount,
                    remark=item_data.remark
                )
                db.add(order_item)
        
        db.commit()
        db.refresh(sales_order)
        
        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]
        
        return ResponseModel(
            code=200,
            message="创建销售订单成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建销售订单失败: {str(e)}")


@router.get("/sales-orders/{order_id}", response_model=ResponseModel[SalesOrderResponse], summary="获取销售订单详情")
async def get_sales_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售订单详情"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")
        
        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]
        
        return ResponseModel(
            code=200,
            message="获取销售订单详情成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售订单详情失败: {str(e)}")


@router.put("/sales-orders/{order_id}", response_model=ResponseModel[SalesOrderResponse], summary="更新销售订单")
async def update_sales_order(
    order_id: int,
    order_data: SalesOrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新销售订单"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")
        
        # 更新字段
        update_data = order_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sales_order, key, value)
        
        db.commit()
        db.refresh(sales_order)
        
        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]
        
        return ResponseModel(
            code=200,
            message="更新销售订单成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新销售订单失败: {str(e)}")


@router.post("/sales-orders/{order_id}/assign-project", response_model=ResponseModel[SalesOrderResponse], summary="分配项目号")
async def assign_project_to_order(
    order_id: int,
    assign_data: AssignProjectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """为销售订单分配项目号"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")
        
        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == assign_data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 分配项目号和项目ID
        sales_order.project_id = assign_data.project_id
        sales_order.project_no = assign_data.project_no or project.project_code
        sales_order.project_no_assigned = True
        sales_order.project_no_assigned_date = datetime.now()
        
        db.commit()
        db.refresh(sales_order)
        
        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]
        
        return ResponseModel(
            code=200,
            message="分配项目号成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"分配项目号失败: {str(e)}")


@router.post("/sales-orders/{order_id}/send-notice", response_model=ResponseModel, summary="发送项目通知单")
async def send_project_notice(
    order_id: int,
    notice_data: SendNoticeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """发送项目通知单"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")
        
        if not sales_order.project_no_assigned:
            raise HTTPException(status_code=400, detail="订单尚未分配项目号，无法发送通知单")
        
        # 更新通知单发送状态
        sales_order.project_notice_sent = True
        sales_order.project_notice_date = datetime.now()
        
        db.commit()
        
        # TODO: 实际发送通知给相关部门（PMC、生产、采购等）
        # 这里可以集成通知系统或消息队列
        
        return ResponseModel(
            code=200,
            message="项目通知单发送成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送项目通知单失败: {str(e)}")


# ==================== 发货管理 ====================


@router.get("/delivery-orders", response_model=ResponseModel[PaginatedResponse[DeliveryOrderResponse]], summary="获取发货单列表")
async def get_delivery_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    order_id: Optional[int] = Query(None, description="销售订单ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    delivery_status: Optional[str] = Query(None, description="发货状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取发货单列表"""
    try:
        query = db.query(DeliveryOrder)
        
        # 筛选条件
        if order_id:
            query = query.filter(DeliveryOrder.order_id == order_id)
        if customer_id:
            query = query.filter(DeliveryOrder.customer_id == customer_id)
        if approval_status:
            query = query.filter(DeliveryOrder.approval_status == approval_status)
        if delivery_status:
            query = query.filter(DeliveryOrder.delivery_status == delivery_status)
        if search:
            query = query.filter(
                or_(
                    DeliveryOrder.delivery_no.like(f"%{search}%"),
                    DeliveryOrder.customer_name.like(f"%{search}%"),
                    DeliveryOrder.tracking_no.like(f"%{search}%")
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(DeliveryOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        delivery_list = [
            DeliveryOrderResponse(
                id=item.id,
                delivery_no=item.delivery_no,
                order_id=item.order_id,
                order_no=item.order_no,
                contract_id=item.contract_id,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                project_id=item.project_id,
                delivery_date=item.delivery_date,
                delivery_type=item.delivery_type,
                logistics_company=item.logistics_company,
                tracking_no=item.tracking_no,
                receiver_name=item.receiver_name,
                receiver_phone=item.receiver_phone,
                receiver_address=item.receiver_address,
                delivery_amount=item.delivery_amount,
                approval_status=item.approval_status,
                approval_comment=item.approval_comment,
                approved_by=item.approved_by,
                approved_at=item.approved_at,
                special_approval=item.special_approval,
                special_approver_id=item.special_approver_id,
                special_approval_reason=item.special_approval_reason,
                delivery_status=item.delivery_status,
                print_date=item.print_date,
                ship_date=item.ship_date,
                receive_date=item.receive_date,
                return_status=item.return_status,
                return_date=item.return_date,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]
        
        return ResponseModel(
            code=200,
            message="获取发货单列表成功",
            data=PaginatedResponse(
                items=delivery_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货单列表失败: {str(e)}")


@router.post("/delivery-orders", response_model=ResponseModel[DeliveryOrderResponse], summary="创建发货单")
async def create_delivery_order(
    delivery_data: DeliveryOrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建发货单"""
    try:
        # 检查销售订单是否存在
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == delivery_data.order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")
        
        # 生成送货单号
        delivery_no = delivery_data.delivery_no or generate_delivery_no(db)
        
        # 检查送货单号是否已存在
        existing = db.query(DeliveryOrder).filter(DeliveryOrder.delivery_no == delivery_no).first()
        if existing:
            raise HTTPException(status_code=400, detail="送货单号已存在")
        
        # 创建发货单
        delivery_order = DeliveryOrder(
            delivery_no=delivery_no,
            order_id=delivery_data.order_id,
            order_no=sales_order.order_no,
            contract_id=sales_order.contract_id,
            customer_id=sales_order.customer_id,
            customer_name=sales_order.customer_name,
            project_id=sales_order.project_id,
            delivery_date=delivery_data.delivery_date,
            delivery_type=delivery_data.delivery_type,
            logistics_company=delivery_data.logistics_company,
            tracking_no=delivery_data.tracking_no,
            receiver_name=delivery_data.receiver_name,
            receiver_phone=delivery_data.receiver_phone,
            receiver_address=delivery_data.receiver_address,
            delivery_amount=delivery_data.delivery_amount,
            approval_status="pending",
            special_approval=delivery_data.special_approval or False,
            special_approval_reason=delivery_data.special_approval_reason,
            delivery_status="draft",
            remark=delivery_data.remark
        )
        
        db.add(delivery_order)
        db.commit()
        db.refresh(delivery_order)
        
        return ResponseModel(
            code=200,
            message="创建发货单成功",
            data=DeliveryOrderResponse(
                id=delivery_order.id,
                delivery_no=delivery_order.delivery_no,
                order_id=delivery_order.order_id,
                order_no=delivery_order.order_no,
                contract_id=delivery_order.contract_id,
                customer_id=delivery_order.customer_id,
                customer_name=delivery_order.customer_name,
                project_id=delivery_order.project_id,
                delivery_date=delivery_order.delivery_date,
                delivery_type=delivery_order.delivery_type,
                logistics_company=delivery_order.logistics_company,
                tracking_no=delivery_order.tracking_no,
                receiver_name=delivery_order.receiver_name,
                receiver_phone=delivery_order.receiver_phone,
                receiver_address=delivery_order.receiver_address,
                delivery_amount=delivery_order.delivery_amount,
                approval_status=delivery_order.approval_status,
                approval_comment=delivery_order.approval_comment,
                approved_by=delivery_order.approved_by,
                approved_at=delivery_order.approved_at,
                special_approval=delivery_order.special_approval,
                special_approver_id=delivery_order.special_approver_id,
                special_approval_reason=delivery_order.special_approval_reason,
                delivery_status=delivery_order.delivery_status,
                print_date=delivery_order.print_date,
                ship_date=delivery_order.ship_date,
                receive_date=delivery_order.receive_date,
                return_status=delivery_order.return_status,
                return_date=delivery_order.return_date,
                remark=delivery_order.remark,
                created_at=delivery_order.created_at,
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建发货单失败: {str(e)}")


@router.get("/delivery-orders/pending-approval", response_model=ResponseModel[List[DeliveryOrderResponse]], summary="获取待审批发货单列表")
async def get_pending_approval_deliveries(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取待审批发货单列表"""
    try:
        deliveries = (
            db.query(DeliveryOrder)
            .filter(DeliveryOrder.approval_status == "pending")
            .order_by(DeliveryOrder.created_at.asc())
            .all()
        )
        
        delivery_list = [
            DeliveryOrderResponse(
                id=item.id,
                delivery_no=item.delivery_no,
                order_id=item.order_id,
                order_no=item.order_no,
                contract_id=item.contract_id,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                project_id=item.project_id,
                delivery_date=item.delivery_date,
                delivery_type=item.delivery_type,
                logistics_company=item.logistics_company,
                tracking_no=item.tracking_no,
                receiver_name=item.receiver_name,
                receiver_phone=item.receiver_phone,
                receiver_address=item.receiver_address,
                delivery_amount=item.delivery_amount,
                approval_status=item.approval_status,
                approval_comment=item.approval_comment,
                approved_by=item.approved_by,
                approved_at=item.approved_at,
                special_approval=item.special_approval,
                special_approver_id=item.special_approver_id,
                special_approval_reason=item.special_approval_reason,
                delivery_status=item.delivery_status,
                print_date=item.print_date,
                ship_date=item.ship_date,
                receive_date=item.receive_date,
                return_status=item.return_status,
                return_date=item.return_date,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in deliveries
        ]
        
        return ResponseModel(
            code=200,
            message="获取待审批发货单列表成功",
            data=delivery_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待审批发货单列表失败: {str(e)}")


@router.post("/delivery-orders/{delivery_id}/approve", response_model=ResponseModel[DeliveryOrderResponse], summary="审批发货单")
async def approve_delivery_order(
    delivery_id: int,
    approval_data: DeliveryApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """审批发货单"""
    try:
        delivery_order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
        if not delivery_order:
            raise HTTPException(status_code=404, detail="发货单不存在")
        
        if delivery_order.approval_status != "pending":
            raise HTTPException(status_code=400, detail="发货单已审批，无法重复审批")
        
        # 更新审批状态
        delivery_order.approval_status = "approved" if approval_data.approved else "rejected"
        delivery_order.approval_comment = approval_data.approval_comment
        delivery_order.approved_by = current_user.id
        delivery_order.approved_at = datetime.now()
        
        # 如果审批通过，更新发货状态
        if approval_data.approved:
            delivery_order.delivery_status = "approved"
        
        db.commit()
        db.refresh(delivery_order)
        
        return ResponseModel(
            code=200,
            message="审批发货单成功",
            data=DeliveryOrderResponse(
                id=delivery_order.id,
                delivery_no=delivery_order.delivery_no,
                order_id=delivery_order.order_id,
                order_no=delivery_order.order_no,
                contract_id=delivery_order.contract_id,
                customer_id=delivery_order.customer_id,
                customer_name=delivery_order.customer_name,
                project_id=delivery_order.project_id,
                delivery_date=delivery_order.delivery_date,
                delivery_type=delivery_order.delivery_type,
                logistics_company=delivery_order.logistics_company,
                tracking_no=delivery_order.tracking_no,
                receiver_name=delivery_order.receiver_name,
                receiver_phone=delivery_order.receiver_phone,
                receiver_address=delivery_order.receiver_address,
                delivery_amount=delivery_order.delivery_amount,
                approval_status=delivery_order.approval_status,
                approval_comment=delivery_order.approval_comment,
                approved_by=delivery_order.approved_by,
                approved_at=delivery_order.approved_at,
                special_approval=delivery_order.special_approval,
                special_approver_id=delivery_order.special_approver_id,
                special_approval_reason=delivery_order.special_approval_reason,
                delivery_status=delivery_order.delivery_status,
                print_date=delivery_order.print_date,
                ship_date=delivery_order.ship_date,
                receive_date=delivery_order.receive_date,
                return_status=delivery_order.return_status,
                return_date=delivery_order.return_date,
                remark=delivery_order.remark,
                created_at=delivery_order.created_at,
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批发货单失败: {str(e)}")


@router.get("/delivery-orders/{delivery_id}", response_model=ResponseModel[DeliveryOrderResponse], summary="获取发货单详情")
async def get_delivery_order(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取发货单详情"""
    try:
        delivery_order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
        if not delivery_order:
            raise HTTPException(status_code=404, detail="发货单不存在")
        
        return ResponseModel(
            code=200,
            message="获取发货单详情成功",
            data=DeliveryOrderResponse(
                id=delivery_order.id,
                delivery_no=delivery_order.delivery_no,
                order_id=delivery_order.order_id,
                order_no=delivery_order.order_no,
                contract_id=delivery_order.contract_id,
                customer_id=delivery_order.customer_id,
                customer_name=delivery_order.customer_name,
                project_id=delivery_order.project_id,
                delivery_date=delivery_order.delivery_date,
                delivery_type=delivery_order.delivery_type,
                logistics_company=delivery_order.logistics_company,
                tracking_no=delivery_order.tracking_no,
                receiver_name=delivery_order.receiver_name,
                receiver_phone=delivery_order.receiver_phone,
                receiver_address=delivery_order.receiver_address,
                delivery_amount=delivery_order.delivery_amount,
                approval_status=delivery_order.approval_status,
                approval_comment=delivery_order.approval_comment,
                approved_by=delivery_order.approved_by,
                approved_at=delivery_order.approved_at,
                special_approval=delivery_order.special_approval,
                special_approver_id=delivery_order.special_approver_id,
                special_approval_reason=delivery_order.special_approval_reason,
                delivery_status=delivery_order.delivery_status,
                print_date=delivery_order.print_date,
                ship_date=delivery_order.ship_date,
                receive_date=delivery_order.receive_date,
                return_status=delivery_order.return_status,
                return_date=delivery_order.return_date,
                remark=delivery_order.remark,
                created_at=delivery_order.created_at,
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货单详情失败: {str(e)}")


@router.put("/delivery-orders/{delivery_id}", response_model=ResponseModel[DeliveryOrderResponse], summary="更新发货单")
async def update_delivery_order(
    delivery_id: int,
    delivery_data: DeliveryOrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新发货单"""
    try:
        delivery_order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
        if not delivery_order:
            raise HTTPException(status_code=404, detail="发货单不存在")
        
        # 更新字段
        update_data = delivery_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(delivery_order, key, value)
        
        db.commit()
        db.refresh(delivery_order)
        
        return ResponseModel(
            code=200,
            message="更新发货单成功",
            data=DeliveryOrderResponse(
                id=delivery_order.id,
                delivery_no=delivery_order.delivery_no,
                order_id=delivery_order.order_id,
                order_no=delivery_order.order_no,
                contract_id=delivery_order.contract_id,
                customer_id=delivery_order.customer_id,
                customer_name=delivery_order.customer_name,
                project_id=delivery_order.project_id,
                delivery_date=delivery_order.delivery_date,
                delivery_type=delivery_order.delivery_type,
                logistics_company=delivery_order.logistics_company,
                tracking_no=delivery_order.tracking_no,
                receiver_name=delivery_order.receiver_name,
                receiver_phone=delivery_order.receiver_phone,
                receiver_address=delivery_order.receiver_address,
                delivery_amount=delivery_order.delivery_amount,
                approval_status=delivery_order.approval_status,
                approval_comment=delivery_order.approval_comment,
                approved_by=delivery_order.approved_by,
                approved_at=delivery_order.approved_at,
                special_approval=delivery_order.special_approval,
                special_approver_id=delivery_order.special_approver_id,
                special_approval_reason=delivery_order.special_approval_reason,
                delivery_status=delivery_order.delivery_status,
                print_date=delivery_order.print_date,
                ship_date=delivery_order.ship_date,
                receive_date=delivery_order.receive_date,
                return_status=delivery_order.return_status,
                return_date=delivery_order.return_date,
                remark=delivery_order.remark,
                created_at=delivery_order.created_at,
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新发货单失败: {str(e)}")


# ==================== 验收单跟踪 ====================


@router.get("/acceptance-tracking", response_model=ResponseModel[PaginatedResponse[AcceptanceTrackingResponse]], summary="获取验收单跟踪列表")
async def get_acceptance_tracking(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    tracking_status: Optional[str] = Query(None, description="跟踪状态筛选"),
    condition_check_status: Optional[str] = Query(None, description="验收条件检查状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取验收单跟踪列表（商务支持角度）"""
    try:
        query = db.query(AcceptanceTracking)
        
        # 筛选条件
        if project_id:
            query = query.filter(AcceptanceTracking.project_id == project_id)
        if customer_id:
            query = query.filter(AcceptanceTracking.customer_id == customer_id)
        if tracking_status:
            query = query.filter(AcceptanceTracking.tracking_status == tracking_status)
        if condition_check_status:
            query = query.filter(AcceptanceTracking.condition_check_status == condition_check_status)
        if search:
            query = query.filter(
                or_(
                    AcceptanceTracking.acceptance_order_no.like(f"%{search}%"),
                    AcceptanceTracking.customer_name.like(f"%{search}%"),
                    AcceptanceTracking.project_code.like(f"%{search}%")
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(AcceptanceTracking.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        tracking_list = []
        for item in items:
            # 查询跟踪记录
            records_data = [
                {
                    "id": r.id,
                    "tracking_id": r.tracking_id,
                    "record_type": r.record_type,
                    "record_content": r.record_content,
                    "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                    "operator_id": r.operator_id,
                    "operator_name": r.operator_name,
                    "result": r.result,
                    "remark": r.remark,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                    "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
                }
                for r in item.tracking_records
            ]
            
            tracking_list.append(AcceptanceTrackingResponse(
                id=item.id,
                acceptance_order_id=item.acceptance_order_id,
                acceptance_order_no=item.acceptance_order_no,
                project_id=item.project_id,
                project_code=item.project_code,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                condition_check_status=item.condition_check_status,
                condition_check_result=item.condition_check_result,
                condition_check_date=item.condition_check_date,
                condition_checker_id=item.condition_checker_id,
                tracking_status=item.tracking_status,
                reminder_count=item.reminder_count,
                last_reminder_date=item.last_reminder_date,
                last_reminder_by=item.last_reminder_by,
                received_date=item.received_date,
                signed_file_id=item.signed_file_id,
                report_status=item.report_status,
                report_generated_date=item.report_generated_date,
                report_signed_date=item.report_signed_date,
                report_archived_date=item.report_archived_date,
                warranty_start_date=item.warranty_start_date,
                warranty_end_date=item.warranty_end_date,
                warranty_status=item.warranty_status,
                warranty_expiry_reminded=item.warranty_expiry_reminded,
                contract_id=item.contract_id,
                contract_no=item.contract_no,
                sales_person_id=item.sales_person_id,
                sales_person_name=item.sales_person_name,
                support_person_id=item.support_person_id,
                remark=item.remark,
                tracking_records=records_data,
                created_at=item.created_at,
                updated_at=item.updated_at
            ))
        
        return ResponseModel(
            code=200,
            message="获取验收单跟踪列表成功",
            data=PaginatedResponse(
                items=tracking_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验收单跟踪列表失败: {str(e)}")


@router.post("/acceptance-tracking", response_model=ResponseModel[AcceptanceTrackingResponse], summary="创建验收单跟踪记录")
async def create_acceptance_tracking(
    tracking_data: AcceptanceTrackingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建验收单跟踪记录"""
    try:
        # 检查验收单是否存在
        acceptance_order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == tracking_data.acceptance_order_id).first()
        if not acceptance_order:
            raise HTTPException(status_code=404, detail="验收单不存在")
        
        # 检查是否已有跟踪记录
        existing = db.query(AcceptanceTracking).filter(
            AcceptanceTracking.acceptance_order_id == tracking_data.acceptance_order_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该验收单已有跟踪记录")
        
        # 获取项目信息
        project = db.query(Project).filter(Project.id == acceptance_order.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取客户信息（从项目获取）
        customer = project.customer if hasattr(project, 'customer') else None
        if not customer:
            # 尝试从合同获取
            if tracking_data.contract_id:
                contract = db.query(Contract).filter(Contract.id == tracking_data.contract_id).first()
                if contract:
                    customer = contract.customer
        
        if not customer:
            raise HTTPException(status_code=404, detail="无法获取客户信息")
        
        # 获取业务员信息
        sales_person_id = tracking_data.sales_person_id
        sales_person_name = None
        if sales_person_id:
            sales_person = db.query(User).filter(User.id == sales_person_id).first()
            if sales_person:
                sales_person_name = sales_person.username
        
        # 获取合同信息
        contract_no = None
        if tracking_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == tracking_data.contract_id).first()
            if contract:
                contract_no = contract.contract_code
        
        # 创建跟踪记录
        tracking = AcceptanceTracking(
            acceptance_order_id=tracking_data.acceptance_order_id,
            acceptance_order_no=acceptance_order.order_no,
            project_id=acceptance_order.project_id,
            project_code=project.project_code,
            customer_id=customer.id,
            customer_name=customer.customer_name,
            contract_id=tracking_data.contract_id,
            contract_no=contract_no,
            sales_person_id=sales_person_id,
            sales_person_name=sales_person_name,
            support_person_id=current_user.id,
            condition_check_status="pending",
            tracking_status="pending",
            report_status="pending",
            warranty_status="not_started",
            remark=tracking_data.remark
        )
        
        db.add(tracking)
        db.commit()
        db.refresh(tracking)
        
        return ResponseModel(
            code=200,
            message="创建验收单跟踪记录成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=[],
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建验收单跟踪记录失败: {str(e)}")


@router.get("/acceptance-tracking/{tracking_id}", response_model=ResponseModel[AcceptanceTrackingResponse], summary="获取验收单跟踪详情")
async def get_acceptance_tracking_detail(
    tracking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取验收单跟踪详情"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")
        
        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]
        
        return ResponseModel(
            code=200,
            message="获取验收单跟踪详情成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验收单跟踪详情失败: {str(e)}")


@router.post("/acceptance-tracking/{tracking_id}/check-condition", response_model=ResponseModel[AcceptanceTrackingResponse], summary="验收条件检查")
async def check_acceptance_condition(
    tracking_id: int,
    check_data: ConditionCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """验收条件检查"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")
        
        # 更新验收条件检查状态
        tracking.condition_check_status = check_data.condition_check_status
        tracking.condition_check_result = check_data.condition_check_result
        tracking.condition_check_date = datetime.now()
        tracking.condition_checker_id = current_user.id
        
        # 创建跟踪记录
        record = AcceptanceTrackingRecord(
            tracking_id=tracking_id,
            record_type="condition_check",
            record_content=f"验收条件检查：{check_data.condition_check_status} - {check_data.condition_check_result}",
            record_date=datetime.now(),
            operator_id=current_user.id,
            operator_name=current_user.username,
            result="success" if check_data.condition_check_status == "met" else "pending",
            remark=check_data.remark
        )
        db.add(record)
        
        db.commit()
        db.refresh(tracking)
        
        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]
        
        return ResponseModel(
            code=200,
            message="验收条件检查成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"验收条件检查失败: {str(e)}")


@router.post("/acceptance-tracking/{tracking_id}/remind", response_model=ResponseModel[AcceptanceTrackingResponse], summary="催签验收单")
async def remind_acceptance_signature(
    tracking_id: int,
    reminder_data: ReminderRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """催签验收单"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")
        
        # 更新催签信息
        tracking.reminder_count = (tracking.reminder_count or 0) + 1
        tracking.last_reminder_date = datetime.now()
        tracking.last_reminder_by = current_user.id
        tracking.tracking_status = "reminded"
        
        # 创建跟踪记录
        record = AcceptanceTrackingRecord(
            tracking_id=tracking_id,
            record_type="reminder",
            record_content=reminder_data.reminder_content or f"第{tracking.reminder_count}次催签验收单",
            record_date=datetime.now(),
            operator_id=current_user.id,
            operator_name=current_user.username,
            result="success",
            remark=reminder_data.remark
        )
        db.add(record)
        
        db.commit()
        db.refresh(tracking)
        
        # TODO: 实际发送催签通知（邮件、短信、系统消息等）
        
        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]
        
        return ResponseModel(
            code=200,
            message="催签成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"催签失败: {str(e)}")


@router.put("/acceptance-tracking/{tracking_id}", response_model=ResponseModel[AcceptanceTrackingResponse], summary="更新验收单跟踪记录")
async def update_acceptance_tracking(
    tracking_id: int,
    tracking_data: AcceptanceTrackingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新验收单跟踪记录"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")
        
        # 更新字段
        update_data = tracking_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tracking, key, value)
        
        db.commit()
        db.refresh(tracking)
        
        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]
        
        return ResponseModel(
            code=200,
            message="更新验收单跟踪记录成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新验收单跟踪记录失败: {str(e)}")


# ==================== 客户对账单 ====================


def generate_reconciliation_no(db: Session) -> str:
    """生成对账单号：RC250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"RC{month_str}-"
    
    max_reconciliation = (
        db.query(Reconciliation)
        .filter(Reconciliation.reconciliation_no.like(f"{prefix}%"))
        .order_by(desc(Reconciliation.reconciliation_no))
        .first()
    )
    
    if max_reconciliation:
        try:
            seq = int(max_reconciliation.reconciliation_no.split("-")[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


@router.post("/reconciliations", response_model=ResponseModel[ReconciliationResponse], summary="生成客户对账单")
async def create_reconciliation(
    reconciliation_data: ReconciliationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """生成客户对账单"""
    try:
        # 检查客户是否存在
        customer = db.query(Customer).filter(Customer.id == reconciliation_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 生成对账单号
        reconciliation_no = generate_reconciliation_no(db)
        
        # 计算对账期间的数据
        # 1. 期初余额 = 对账开始日期之前的应收余额
        from sqlalchemy import text
        opening_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as balance
            FROM project_payment_plans
            WHERE project_id IN (
                SELECT id FROM projects WHERE customer_id = :customer_id
            )
            AND planned_date < :period_start
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {
            "customer_id": reconciliation_data.customer_id,
            "period_start": reconciliation_data.period_start.strftime("%Y-%m-%d")
        }).fetchone()
        opening_balance = Decimal(str(opening_result[0])) if opening_result and opening_result[0] else Decimal("0")
        
        # 2. 本期销售 = 对账期间内签订的合同金额
        period_sales_result = db.execute(text("""
            SELECT COALESCE(SUM(contract_amount), 0) as sales
            FROM contracts
            WHERE customer_id = :customer_id
            AND signed_date >= :period_start
            AND signed_date <= :period_end
            AND status IN ('SIGNED', 'EXECUTING')
        """), {
            "customer_id": reconciliation_data.customer_id,
            "period_start": reconciliation_data.period_start.strftime("%Y-%m-%d"),
            "period_end": reconciliation_data.period_end.strftime("%Y-%m-%d")
        }).fetchone()
        period_sales = Decimal(str(period_sales_result[0])) if period_sales_result and period_sales_result[0] else Decimal("0")
        
        # 3. 本期回款 = 对账期间内的实际回款金额
        period_receipt_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as receipt
            FROM project_payment_plans
            WHERE project_id IN (
                SELECT id FROM projects WHERE customer_id = :customer_id
            )
            AND planned_date >= :period_start
            AND planned_date <= :period_end
            AND actual_amount > 0
        """), {
            "customer_id": reconciliation_data.customer_id,
            "period_start": reconciliation_data.period_start.strftime("%Y-%m-%d"),
            "period_end": reconciliation_data.period_end.strftime("%Y-%m-%d")
        }).fetchone()
        period_receipt = Decimal(str(period_receipt_result[0])) if period_receipt_result and period_receipt_result[0] else Decimal("0")
        
        # 4. 期末余额 = 期初余额 + 本期销售 - 本期回款
        closing_balance = opening_balance + period_sales - period_receipt
        
        # 创建对账单
        reconciliation = Reconciliation(
            reconciliation_no=reconciliation_no,
            customer_id=reconciliation_data.customer_id,
            customer_name=customer.customer_name,
            period_start=reconciliation_data.period_start,
            period_end=reconciliation_data.period_end,
            opening_balance=opening_balance,
            period_sales=period_sales,
            period_receipt=period_receipt,
            closing_balance=closing_balance,
            status="draft",
            remark=reconciliation_data.remark
        )
        
        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)
        
        return ResponseModel(
            code=200,
            message="生成客户对账单成功",
            data=ReconciliationResponse(
                id=reconciliation.id,
                reconciliation_no=reconciliation.reconciliation_no,
                customer_id=reconciliation.customer_id,
                customer_name=reconciliation.customer_name,
                period_start=reconciliation.period_start,
                period_end=reconciliation.period_end,
                opening_balance=reconciliation.opening_balance,
                period_sales=reconciliation.period_sales,
                period_receipt=reconciliation.period_receipt,
                closing_balance=reconciliation.closing_balance,
                status=reconciliation.status,
                sent_date=reconciliation.sent_date,
                confirm_date=reconciliation.confirm_date,
                customer_confirmed=reconciliation.customer_confirmed,
                customer_confirm_date=reconciliation.customer_confirm_date,
                customer_difference=reconciliation.customer_difference,
                difference_reason=reconciliation.difference_reason,
                reconciliation_file_id=reconciliation.reconciliation_file_id,
                confirmed_file_id=reconciliation.confirmed_file_id,
                remark=reconciliation.remark,
                created_at=reconciliation.created_at,
                updated_at=reconciliation.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成客户对账单失败: {str(e)}")


@router.get("/reconciliations", response_model=ResponseModel[PaginatedResponse[ReconciliationResponse]], summary="获取客户对账单列表")
async def get_reconciliations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取客户对账单列表"""
    try:
        query = db.query(Reconciliation)
        
        # 筛选条件
        if customer_id:
            query = query.filter(Reconciliation.customer_id == customer_id)
        if status:
            query = query.filter(Reconciliation.status == status)
        if search:
            query = query.filter(
                or_(
                    Reconciliation.reconciliation_no.like(f"%{search}%"),
                    Reconciliation.customer_name.like(f"%{search}%")
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(Reconciliation.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        reconciliation_list = [
            ReconciliationResponse(
                id=item.id,
                reconciliation_no=item.reconciliation_no,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                period_start=item.period_start,
                period_end=item.period_end,
                opening_balance=item.opening_balance,
                period_sales=item.period_sales,
                period_receipt=item.period_receipt,
                closing_balance=item.closing_balance,
                status=item.status,
                sent_date=item.sent_date,
                confirm_date=item.confirm_date,
                customer_confirmed=item.customer_confirmed,
                customer_confirm_date=item.customer_confirm_date,
                customer_difference=item.customer_difference,
                difference_reason=item.difference_reason,
                reconciliation_file_id=item.reconciliation_file_id,
                confirmed_file_id=item.confirmed_file_id,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]
        
        return ResponseModel(
            code=200,
            message="获取客户对账单列表成功",
            data=PaginatedResponse(
                items=reconciliation_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户对账单列表失败: {str(e)}")


@router.get("/reconciliations/{reconciliation_id}", response_model=ResponseModel[ReconciliationResponse], summary="获取客户对账单详情")
async def get_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取客户对账单详情"""
    try:
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            raise HTTPException(status_code=404, detail="客户对账单不存在")
        
        return ResponseModel(
            code=200,
            message="获取客户对账单详情成功",
            data=ReconciliationResponse(
                id=reconciliation.id,
                reconciliation_no=reconciliation.reconciliation_no,
                customer_id=reconciliation.customer_id,
                customer_name=reconciliation.customer_name,
                period_start=reconciliation.period_start,
                period_end=reconciliation.period_end,
                opening_balance=reconciliation.opening_balance,
                period_sales=reconciliation.period_sales,
                period_receipt=reconciliation.period_receipt,
                closing_balance=reconciliation.closing_balance,
                status=reconciliation.status,
                sent_date=reconciliation.sent_date,
                confirm_date=reconciliation.confirm_date,
                customer_confirmed=reconciliation.customer_confirmed,
                customer_confirm_date=reconciliation.customer_confirm_date,
                customer_difference=reconciliation.customer_difference,
                difference_reason=reconciliation.difference_reason,
                reconciliation_file_id=reconciliation.reconciliation_file_id,
                confirmed_file_id=reconciliation.confirmed_file_id,
                remark=reconciliation.remark,
                created_at=reconciliation.created_at,
                updated_at=reconciliation.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户对账单详情失败: {str(e)}")


@router.put("/reconciliations/{reconciliation_id}", response_model=ResponseModel[ReconciliationResponse], summary="更新客户对账单")
async def update_reconciliation(
    reconciliation_id: int,
    reconciliation_data: ReconciliationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新客户对账单"""
    try:
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            raise HTTPException(status_code=404, detail="客户对账单不存在")
        
        # 更新字段
        update_data = reconciliation_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(reconciliation, key, value)
        
        # 如果客户确认，更新确认日期
        if reconciliation_data.customer_confirmed and not reconciliation.customer_confirm_date:
            reconciliation.customer_confirm_date = date.today()
            reconciliation.status = "confirmed"
        
        db.commit()
        db.refresh(reconciliation)
        
        return ResponseModel(
            code=200,
            message="更新客户对账单成功",
            data=ReconciliationResponse(
                id=reconciliation.id,
                reconciliation_no=reconciliation.reconciliation_no,
                customer_id=reconciliation.customer_id,
                customer_name=reconciliation.customer_name,
                period_start=reconciliation.period_start,
                period_end=reconciliation.period_end,
                opening_balance=reconciliation.opening_balance,
                period_sales=reconciliation.period_sales,
                period_receipt=reconciliation.period_receipt,
                closing_balance=reconciliation.closing_balance,
                status=reconciliation.status,
                sent_date=reconciliation.sent_date,
                confirm_date=reconciliation.confirm_date,
                customer_confirmed=reconciliation.customer_confirmed,
                customer_confirm_date=reconciliation.customer_confirm_date,
                customer_difference=reconciliation.customer_difference,
                difference_reason=reconciliation.difference_reason,
                reconciliation_file_id=reconciliation.reconciliation_file_id,
                confirmed_file_id=reconciliation.confirmed_file_id,
                remark=reconciliation.remark,
                created_at=reconciliation.created_at,
                updated_at=reconciliation.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新客户对账单失败: {str(e)}")


@router.post("/reconciliations/{reconciliation_id}/send", response_model=ResponseModel, summary="发送对账单")
async def send_reconciliation(
    reconciliation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """发送对账单给客户"""
    try:
        reconciliation = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
        if not reconciliation:
            raise HTTPException(status_code=404, detail="客户对账单不存在")
        
        if reconciliation.status != "draft":
            raise HTTPException(status_code=400, detail="对账单已发送，无法重复发送")
        
        # 更新状态
        reconciliation.status = "sent"
        reconciliation.sent_date = date.today()
        
        db.commit()
        
        # TODO: 实际发送对账单（邮件、系统消息等）
        
        return ResponseModel(
            code=200,
            message="发送对账单成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送对账单失败: {str(e)}")


# ==================== 开票申请管理 ====================


@router.get("/invoice-requests", response_model=ResponseModel[PaginatedResponse[InvoiceRequestResponse]], summary="获取开票申请列表")
async def get_invoice_requests(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: Optional[str] = Query(None, description="状态筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    keyword: Optional[str] = Query(None, description="搜索申请号/项目"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """分页获取开票申请列表"""
    try:
        query = db.query(InvoiceRequest)
        if status:
            query = query.filter(InvoiceRequest.status == status)
        if contract_id:
            query = query.filter(InvoiceRequest.contract_id == contract_id)
        if customer_id:
            query = query.filter(InvoiceRequest.customer_id == customer_id)
        if keyword:
            query = query.filter(
                or_(
                    InvoiceRequest.request_no.like(f"%{keyword}%"),
                    InvoiceRequest.project_name.like(f"%{keyword}%"),
                    InvoiceRequest.customer_name.like(f"%{keyword}%")
                )
            )

        total = query.count()
        items = (
            query.order_by(desc(InvoiceRequest.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        responses = [_to_invoice_request_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取开票申请列表成功",
            data=PaginatedResponse(
                items=responses,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
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
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")

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
    invoice_request = db.query(InvoiceRequest).filter(InvoiceRequest.id == request_id).first()
    if not invoice_request:
        raise HTTPException(status_code=404, detail="开票申请不存在")
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
        invoice_request = db.query(InvoiceRequest).filter(InvoiceRequest.id == request_id).first()
        if not invoice_request:
            raise HTTPException(status_code=404, detail="开票申请不存在")
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
        invoice_request = db.query(InvoiceRequest).filter(InvoiceRequest.id == request_id).first()
        if not invoice_request:
            raise HTTPException(status_code=404, detail="开票申请不存在")
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
        invoice_request.approved_at = datetime.utcnow()
        invoice_request.invoice_id = invoice.id
        invoice_request.receipt_status = "UNPAID"
        invoice_request.receipt_updated_at = datetime.utcnow()

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
        invoice_request = db.query(InvoiceRequest).filter(InvoiceRequest.id == request_id).first()
        if not invoice_request:
            raise HTTPException(status_code=404, detail="开票申请不存在")
        if invoice_request.status != "PENDING":
            raise HTTPException(status_code=400, detail="当前状态不可驳回")

        invoice_request.status = "REJECTED"
        invoice_request.approval_comment = reject_in.approval_comment
        invoice_request.approved_by = current_user.id
        invoice_request.approved_at = datetime.utcnow()

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


# ==================== 客户供应商入驻 ====================


@router.get("/customer-registrations", response_model=ResponseModel[PaginatedResponse[CustomerSupplierRegistrationResponse]], summary="获取客户供应商入驻列表")
async def get_customer_registrations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    platform_name: Optional[str] = Query(None, description="平台名称筛选"),
    keyword: Optional[str] = Query(None, description="搜索入驻编号/客户"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """分页获取客户供应商入驻记录"""
    try:
        query = db.query(CustomerSupplierRegistration)
        if customer_id:
            query = query.filter(CustomerSupplierRegistration.customer_id == customer_id)
        if status:
            query = query.filter(CustomerSupplierRegistration.registration_status == status)
        if platform_name:
            query = query.filter(CustomerSupplierRegistration.platform_name == platform_name)
        if keyword:
            query = query.filter(
                or_(
                    CustomerSupplierRegistration.registration_no.like(f"%{keyword}%"),
                    CustomerSupplierRegistration.customer_name.like(f"%{keyword}%")
                )
            )

        total = query.count()
        items = (
            query.order_by(desc(CustomerSupplierRegistration.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        responses = [_to_registration_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取客户供应商入驻列表成功",
            data=PaginatedResponse(
                items=responses,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取客户供应商入驻列表失败: {str(exc)}")


@router.post("/customer-registrations", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="创建客户供应商入驻申请")
async def create_customer_registration(
    registration_in: CustomerSupplierRegistrationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建客户供应商入驻申请"""
    try:
        customer = db.query(Customer).filter(Customer.id == registration_in.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")

        registration = CustomerSupplierRegistration(
            registration_no=generate_registration_no(db),
            customer_id=customer.id,
            customer_name=registration_in.customer_name or customer.customer_name,
            platform_name=registration_in.platform_name,
            platform_url=registration_in.platform_url,
            registration_status="PENDING",
            application_date=registration_in.application_date or date.today(),
            contact_person=registration_in.contact_person,
            contact_phone=registration_in.contact_phone,
            contact_email=registration_in.contact_email,
            required_docs=_serialize_attachments(registration_in.required_docs),
            remark=registration_in.remark,
            external_sync_status="pending"
        )
        db.add(registration)
        db.commit()
        db.refresh(registration)

        return ResponseModel(
            code=200,
            message="创建客户供应商入驻申请成功",
            data=_to_registration_response(registration)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建客户供应商入驻申请失败: {str(exc)}")


@router.get("/customer-registrations/{registration_id}", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="获取入驻详情")
async def get_customer_registration(
    registration_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取客户供应商入驻详情"""
    record = db.query(CustomerSupplierRegistration).filter(
        CustomerSupplierRegistration.id == registration_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="入驻记录不存在")
    return ResponseModel(
        code=200,
        message="获取客户供应商入驻详情成功",
        data=_to_registration_response(record)
    )


@router.put("/customer-registrations/{registration_id}", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="更新入驻记录")
async def update_customer_registration(
    registration_id: int,
    registration_in: CustomerSupplierRegistrationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新客户供应商入驻记录"""
    try:
        record = db.query(CustomerSupplierRegistration).filter(
            CustomerSupplierRegistration.id == registration_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="入驻记录不存在")

        update_data = registration_in.model_dump(exclude_unset=True)
        if "required_docs" in update_data:
            record.required_docs = _serialize_attachments(update_data.pop("required_docs"))
        for field, value in update_data.items():
            setattr(record, field, value)

        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            code=200,
            message="更新入驻记录成功",
            data=_to_registration_response(record)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新入驻记录失败: {str(exc)}")


@router.post("/customer-registrations/{registration_id}/approve", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="审批客户入驻申请")
async def approve_customer_registration(
    registration_id: int,
    review_in: SupplierRegistrationReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """审批通过客户供应商入驻申请"""
    try:
        record = db.query(CustomerSupplierRegistration).filter(
            CustomerSupplierRegistration.id == registration_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="入驻记录不存在")
        if record.registration_status == "APPROVED":
            raise HTTPException(status_code=400, detail="申请已审批通过")

        record.registration_status = "APPROVED"
        record.approved_date = date.today()
        record.reviewer_id = current_user.id
        record.review_comment = review_in.review_comment
        record.external_sync_status = "pending"

        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            code=200,
            message="审批客户供应商入驻成功",
            data=_to_registration_response(record)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批客户供应商入驻失败: {str(exc)}")


@router.post("/customer-registrations/{registration_id}/reject", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="驳回客户入驻申请")
async def reject_customer_registration(
    registration_id: int,
    review_in: SupplierRegistrationReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """驳回客户供应商入驻申请"""
    try:
        record = db.query(CustomerSupplierRegistration).filter(
            CustomerSupplierRegistration.id == registration_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="入驻记录不存在")
        if record.registration_status == "APPROVED":
            raise HTTPException(status_code=400, detail="审批通过的申请不可驳回")

        record.registration_status = "REJECTED"
        record.reviewer_id = current_user.id
        record.review_comment = review_in.review_comment
        record.approved_date = None

        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            code=200,
            message="驳回客户供应商入驻成功",
            data=_to_registration_response(record)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"驳回客户供应商入驻失败: {str(exc)}")


# ==================== 销售报表 ====================


@router.get("/reports/sales-daily", response_model=ResponseModel[SalesReportResponse], summary="获取销售日报")
async def get_sales_daily_report(
    report_date: Optional[str] = Query(None, description="报表日期（YYYY-MM-DD格式），不提供则使用今天"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售日报"""
    try:
        from datetime import timedelta
        from sqlalchemy import text
        
        # 确定报表日期
        if report_date:
            try:
                report_dt = datetime.strptime(report_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            report_dt = date.today()
        
        report_date_str = report_dt.strftime("%Y-%m-%d")
        
        # 1. 合同统计
        new_contracts = (
            db.query(Contract)
            .filter(
                func.date(Contract.signed_date) == report_dt,
                Contract.status.in_(["SIGNED", "EXECUTING"])
            )
            .all()
        )
        new_contracts_count = len(new_contracts)
        new_contracts_amount = sum(c.contract_amount or Decimal("0") for c in new_contracts)
        
        active_contracts = (
            db.query(Contract)
            .filter(Contract.status.in_(["SIGNED", "EXECUTING"]))
            .count()
        )
        
        completed_contracts = (
            db.query(Contract)
            .filter(Contract.status == "COMPLETED")
            .count()
        )
        
        # 2. 订单统计
        new_orders = (
            db.query(SalesOrder)
            .filter(func.date(SalesOrder.created_at) == report_dt)
            .all()
        )
        new_orders_count = len(new_orders)
        new_orders_amount = sum(o.order_amount or Decimal("0") for o in new_orders)
        
        # 3. 回款统计
        planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date = :report_date
        """), {"report_date": report_date_str}).fetchone()
        planned_receipt_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")
        
        actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date = :report_date
            AND actual_amount > 0
        """), {"report_date": report_date_str}).fetchone()
        actual_receipt_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")
        
        receipt_completion_rate = (actual_receipt_amount / planned_receipt_amount * 100) if planned_receipt_amount > 0 else Decimal("0")
        
        overdue_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :report_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"report_date": report_date_str}).fetchone()
        overdue_amount = Decimal(str(overdue_result[0])) if overdue_result and overdue_result[0] else Decimal("0")
        
        # 4. 开票统计
        invoices = (
            db.query(Invoice)
            .filter(func.date(Invoice.issue_date) == report_dt, Invoice.status == "ISSUED")
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)
        
        # 计算开票率（简化处理）
        total_needed = db.execute(text("""
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date <= :report_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"report_date": report_date_str}).fetchone()
        invoice_rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")
        
        # 5. 投标统计
        new_bidding = (
            db.query(BiddingProject)
            .filter(func.date(BiddingProject.created_at) == report_dt)
            .count()
        )
        
        won_bidding = (
            db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.result_date) == report_dt,
                BiddingProject.bid_result == "won"
            )
            .count()
        )
        
        total_bidding = db.query(BiddingProject).count()
        bidding_win_rate = (Decimal(won_bidding) / Decimal(total_bidding) * 100) if total_bidding > 0 else Decimal("0")
        
        return ResponseModel(
            code=200,
            message="获取销售日报成功",
            data=SalesReportResponse(
                report_date=report_date_str,
                report_type="daily",
                new_contracts_count=new_contracts_count,
                new_contracts_amount=new_contracts_amount,
                active_contracts_count=active_contracts,
                completed_contracts_count=completed_contracts,
                new_orders_count=new_orders_count,
                new_orders_amount=new_orders_amount,
                planned_receipt_amount=planned_receipt_amount,
                actual_receipt_amount=actual_receipt_amount,
                receipt_completion_rate=receipt_completion_rate,
                overdue_amount=overdue_amount,
                invoices_count=invoices_count,
                invoices_amount=invoices_amount,
                invoice_rate=invoice_rate,
                new_bidding_count=new_bidding,
                won_bidding_count=won_bidding,
                bidding_win_rate=bidding_win_rate
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售日报失败: {str(e)}")


@router.get("/reports/sales-weekly", response_model=ResponseModel[SalesReportResponse], summary="获取销售周报")
async def get_sales_weekly_report(
    week: Optional[str] = Query(None, description="周（YYYY-WW格式），不提供则使用当前周"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售周报"""
    try:
        from datetime import timedelta
        from sqlalchemy import text
        
        # 确定报表周期
        if week:
            try:
                year, week_num = map(int, week.split("-W"))
                # 计算该周的第一天（周一）
                jan1 = date(year, 1, 1)
                days_offset = (week_num - 1) * 7
                week_start = jan1 + timedelta(days=-jan1.weekday() + days_offset)
                week_end = week_start + timedelta(days=6)
            except:
                raise HTTPException(status_code=400, detail="周格式错误，应为YYYY-WW")
        else:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            year = today.year
            week_num = (today - date(today.year, 1, 1)).days // 7 + 1
        
        week_str = f"{year}-W{week_num:02d}"
        
        # 使用与日报类似的逻辑，但统计周期为一周
        # 1. 合同统计
        new_contracts = (
            db.query(Contract)
            .filter(
                Contract.signed_date >= week_start,
                Contract.signed_date <= week_end,
                Contract.status.in_(["SIGNED", "EXECUTING"])
            )
            .all()
        )
        new_contracts_count = len(new_contracts)
        new_contracts_amount = sum(c.contract_amount or Decimal("0") for c in new_contracts)
        
        active_contracts = db.query(Contract).filter(Contract.status.in_(["SIGNED", "EXECUTING"])).count()
        completed_contracts = db.query(Contract).filter(Contract.status == "COMPLETED").count()
        
        # 2. 订单统计
        new_orders = (
            db.query(SalesOrder)
            .filter(
                func.date(SalesOrder.created_at) >= week_start,
                func.date(SalesOrder.created_at) <= week_end
            )
            .all()
        )
        new_orders_count = len(new_orders)
        new_orders_amount = sum(o.order_amount or Decimal("0") for o in new_orders)
        
        # 3. 回款统计
        planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
        """), {"start_date": week_start.strftime("%Y-%m-%d"), "end_date": week_end.strftime("%Y-%m-%d")}).fetchone()
        planned_receipt_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")
        
        actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND actual_amount > 0
        """), {"start_date": week_start.strftime("%Y-%m-%d"), "end_date": week_end.strftime("%Y-%m-%d")}).fetchone()
        actual_receipt_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")
        
        receipt_completion_rate = (actual_receipt_amount / planned_receipt_amount * 100) if planned_receipt_amount > 0 else Decimal("0")
        
        overdue_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": week_end.strftime("%Y-%m-%d")}).fetchone()
        overdue_amount = Decimal(str(overdue_result[0])) if overdue_result and overdue_result[0] else Decimal("0")
        
        # 4. 开票统计
        invoices = (
            db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= week_start,
                func.date(Invoice.issue_date) <= week_end,
                Invoice.status == "ISSUED"
            )
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)
        
        total_needed = db.execute(text("""
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date <= :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": week_end.strftime("%Y-%m-%d")}).fetchone()
        invoice_rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")
        
        # 5. 投标统计
        new_bidding = (
            db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.created_at) >= week_start,
                func.date(BiddingProject.created_at) <= week_end
            )
            .count()
        )
        
        won_bidding = (
            db.query(BiddingProject)
            .filter(
                BiddingProject.result_date >= week_start,
                BiddingProject.result_date <= week_end,
                BiddingProject.bid_result == "won"
            )
            .count()
        )
        
        total_bidding = db.query(BiddingProject).count()
        bidding_win_rate = (Decimal(won_bidding) / Decimal(total_bidding) * 100) if total_bidding > 0 else Decimal("0")
        
        return ResponseModel(
            code=200,
            message="获取销售周报成功",
            data=SalesReportResponse(
                report_date=week_str,
                report_type="weekly",
                new_contracts_count=new_contracts_count,
                new_contracts_amount=new_contracts_amount,
                active_contracts_count=active_contracts,
                completed_contracts_count=completed_contracts,
                new_orders_count=new_orders_count,
                new_orders_amount=new_orders_amount,
                planned_receipt_amount=planned_receipt_amount,
                actual_receipt_amount=actual_receipt_amount,
                receipt_completion_rate=receipt_completion_rate,
                overdue_amount=overdue_amount,
                invoices_count=invoices_count,
                invoices_amount=invoices_amount,
                invoice_rate=invoice_rate,
                new_bidding_count=new_bidding,
                won_bidding_count=won_bidding,
                bidding_win_rate=bidding_win_rate
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售周报失败: {str(e)}")


@router.get("/reports/sales-monthly", response_model=ResponseModel[SalesReportResponse], summary="获取销售月报")
async def get_sales_monthly_report(
    month: Optional[str] = Query(None, description="月份（YYYY-MM格式），不提供则使用当前月份"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售月报"""
    try:
        from datetime import timedelta
        from sqlalchemy import text
        
        # 确定报表周期
        if month:
            try:
                year, month_num = map(int, month.split("-"))
                month_start = date(year, month_num, 1)
                if month_num == 12:
                    month_end = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(year, month_num + 1, 1) - timedelta(days=1)
            except:
                raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
        else:
            today = date.today()
            year = today.year
            month_num = today.month
            month_start = date(year, month_num, 1)
            if month_num == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month_num + 1, 1) - timedelta(days=1)
        
        month_str = f"{year}-{month_num:02d}"
        
        # 使用与日报类似的逻辑，但统计周期为一个月
        # 1. 合同统计
        new_contracts = (
            db.query(Contract)
            .filter(
                Contract.signed_date >= month_start,
                Contract.signed_date <= month_end,
                Contract.status.in_(["SIGNED", "EXECUTING"])
            )
            .all()
        )
        new_contracts_count = len(new_contracts)
        new_contracts_amount = sum(c.contract_amount or Decimal("0") for c in new_contracts)
        
        active_contracts = db.query(Contract).filter(Contract.status.in_(["SIGNED", "EXECUTING"])).count()
        completed_contracts = db.query(Contract).filter(Contract.status == "COMPLETED").count()
        
        # 2. 订单统计
        new_orders = (
            db.query(SalesOrder)
            .filter(
                func.date(SalesOrder.created_at) >= month_start,
                func.date(SalesOrder.created_at) <= month_end
            )
            .all()
        )
        new_orders_count = len(new_orders)
        new_orders_amount = sum(o.order_amount or Decimal("0") for o in new_orders)
        
        # 3. 回款统计
        planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        planned_receipt_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")
        
        actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND actual_amount > 0
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        actual_receipt_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")
        
        receipt_completion_rate = (actual_receipt_amount / planned_receipt_amount * 100) if planned_receipt_amount > 0 else Decimal("0")
        
        overdue_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        overdue_amount = Decimal(str(overdue_result[0])) if overdue_result and overdue_result[0] else Decimal("0")
        
        # 4. 开票统计
        invoices = (
            db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= month_start,
                func.date(Invoice.issue_date) <= month_end,
                Invoice.status == "ISSUED"
            )
            .all()
        )
        invoices_count = len(invoices)
        invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)
        
        total_needed = db.execute(text("""
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date <= :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        invoice_rate = (Decimal(invoices_count) / Decimal(total_needed[0]) * 100) if total_needed and total_needed[0] > 0 else Decimal("0")
        
        # 5. 投标统计
        new_bidding = (
            db.query(BiddingProject)
            .filter(
                func.date(BiddingProject.created_at) >= month_start,
                func.date(BiddingProject.created_at) <= month_end
            )
            .count()
        )
        
        won_bidding = (
            db.query(BiddingProject)
            .filter(
                BiddingProject.result_date >= month_start,
                BiddingProject.result_date <= month_end,
                BiddingProject.bid_result == "won"
            )
            .count()
        )
        
        total_bidding = db.query(BiddingProject).count()
        bidding_win_rate = (Decimal(won_bidding) / Decimal(total_bidding) * 100) if total_bidding > 0 else Decimal("0")
        
        return ResponseModel(
            code=200,
            message="获取销售月报成功",
            data=SalesReportResponse(
                report_date=month_str,
                report_type="monthly",
                new_contracts_count=new_contracts_count,
                new_contracts_amount=new_contracts_amount,
                active_contracts_count=active_contracts,
                completed_contracts_count=completed_contracts,
                new_orders_count=new_orders_count,
                new_orders_amount=new_orders_amount,
                planned_receipt_amount=planned_receipt_amount,
                actual_receipt_amount=actual_receipt_amount,
                receipt_completion_rate=receipt_completion_rate,
                overdue_amount=overdue_amount,
                invoices_count=invoices_count,
                invoices_amount=invoices_amount,
                invoice_rate=invoice_rate,
                new_bidding_count=new_bidding,
                won_bidding_count=won_bidding,
                bidding_win_rate=bidding_win_rate
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售月报失败: {str(e)}")


@router.get("/reports/payment", response_model=ResponseModel[PaymentReportResponse], summary="获取回款统计报表")
async def get_payment_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取回款统计报表"""
    try:
        from sqlalchemy import text
        
        # 确定统计周期
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt = date(today.year, today.month, 1)
            if today.month == 12:
                end_dt = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        report_date_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}"
        
        # 回款汇总
        total_planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_planned_amount = Decimal(str(total_planned_result[0])) if total_planned_result and total_planned_result[0] else Decimal("0")
        
        total_actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND actual_amount > 0
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_actual_amount = Decimal(str(total_actual_result[0])) if total_actual_result and total_actual_result[0] else Decimal("0")
        
        total_pending_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as pending
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_pending_amount = Decimal(str(total_pending_result[0])) if total_pending_result and total_pending_result[0] else Decimal("0")
        
        total_overdue_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount - actual_amount), 0) as overdue
            FROM project_payment_plans
            WHERE planned_date < :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"end_date": end_dt.strftime("%Y-%m-%d")}).fetchone()
        total_overdue_amount = Decimal(str(total_overdue_result[0])) if total_overdue_result and total_overdue_result[0] else Decimal("0")
        
        completion_rate = (total_actual_amount / total_planned_amount * 100) if total_planned_amount > 0 else Decimal("0")
        
        # 按类型统计（简化处理，实际应从payment_type字段查询）
        # 这里假设所有回款计划都有payment_type字段
        prepayment_planned = Decimal("0")
        prepayment_actual = Decimal("0")
        delivery_payment_planned = Decimal("0")
        delivery_payment_actual = Decimal("0")
        acceptance_payment_planned = Decimal("0")
        acceptance_payment_actual = Decimal("0")
        warranty_payment_planned = Decimal("0")
        warranty_payment_actual = Decimal("0")
        
        # 按客户统计（前10名）
        top_customers_result = db.execute(text("""
            SELECT 
                c.customer_name,
                COALESCE(SUM(ppp.actual_amount), 0) as receipt_amount
            FROM project_payment_plans ppp
            JOIN projects p ON ppp.project_id = p.id
            JOIN customers c ON p.customer_id = c.id
            WHERE ppp.planned_date >= :start_date
            AND ppp.planned_date <= :end_date
            AND ppp.actual_amount > 0
            GROUP BY c.id, c.customer_name
            ORDER BY receipt_amount DESC
            LIMIT 10
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchall()
        
        top_customers = [
            {"customer_name": row[0], "receipt_amount": float(row[1])}
            for row in top_customers_result
        ]
        
        return ResponseModel(
            code=200,
            message="获取回款统计报表成功",
            data=PaymentReportResponse(
                report_date=report_date_str,
                report_type="payment",
                total_planned_amount=total_planned_amount,
                total_actual_amount=total_actual_amount,
                total_pending_amount=total_pending_amount,
                total_overdue_amount=total_overdue_amount,
                completion_rate=completion_rate,
                prepayment_planned=prepayment_planned,
                prepayment_actual=prepayment_actual,
                delivery_payment_planned=delivery_payment_planned,
                delivery_payment_actual=delivery_payment_actual,
                acceptance_payment_planned=acceptance_payment_planned,
                acceptance_payment_actual=acceptance_payment_actual,
                warranty_payment_planned=warranty_payment_planned,
                warranty_payment_actual=warranty_payment_actual,
                top_customers=top_customers
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回款统计报表失败: {str(e)}")


@router.get("/reports/contract", response_model=ResponseModel[ContractReportResponse], summary="获取合同执行报表")
async def get_contract_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取合同执行报表"""
    try:
        from sqlalchemy import text
        
        # 确定统计周期
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt = date(today.year, today.month, 1)
            if today.month == 12:
                end_dt = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        report_date_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}"
        
        # 合同状态统计
        draft_count = db.query(Contract).filter(Contract.status == "DRAFT").count()
        signed_count = db.query(Contract).filter(Contract.status == "SIGNED").count()
        executing_count = db.query(Contract).filter(Contract.status == "EXECUTING").count()
        completed_count = db.query(Contract).filter(Contract.status == "COMPLETED").count()
        cancelled_count = db.query(Contract).filter(Contract.status == "CANCELLED").count()
        
        # 合同金额统计
        total_contracts = db.query(Contract).all()
        total_contract_amount = sum(c.contract_amount or Decimal("0") for c in total_contracts)
        
        signed_contracts = db.query(Contract).filter(Contract.status == "SIGNED").all()
        signed_amount = sum(c.contract_amount or Decimal("0") for c in signed_contracts)
        
        executing_contracts = db.query(Contract).filter(Contract.status == "EXECUTING").all()
        executing_amount = sum(c.contract_amount or Decimal("0") for c in executing_contracts)
        
        completed_contracts = db.query(Contract).filter(Contract.status == "COMPLETED").all()
        completed_amount = sum(c.contract_amount or Decimal("0") for c in completed_contracts)
        
        # 执行进度（简化处理，使用回款进度）
        avg_progress_result = db.execute(text("""
            SELECT AVG(
                CASE 
                    WHEN SUM(ppp.planned_amount) > 0 
                    THEN (SUM(ppp.actual_amount) / SUM(ppp.planned_amount)) * 100
                    ELSE 0
                END
            ) as avg_progress
            FROM contracts c
            LEFT JOIN projects p ON c.project_id = p.id
            LEFT JOIN project_payment_plans ppp ON p.id = ppp.project_id
            WHERE c.status IN ('SIGNED', 'EXECUTING')
            GROUP BY c.id
        """)).fetchone()
        average_execution_rate = Decimal(str(avg_progress_result[0])) if avg_progress_result and avg_progress_result[0] else Decimal("0")
        
        # 按客户统计（前10名）
        top_customers_result = db.execute(text("""
            SELECT 
                c.customer_name,
                COALESCE(SUM(ct.contract_amount), 0) as contract_amount
            FROM contracts ct
            JOIN customers c ON ct.customer_id = c.id
            WHERE ct.signed_date >= :start_date
            AND ct.signed_date <= :end_date
            GROUP BY c.id, c.customer_name
            ORDER BY contract_amount DESC
            LIMIT 10
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchall()
        
        top_customers = [
            {"customer_name": row[0], "contract_amount": float(row[1])}
            for row in top_customers_result
        ]
        
        return ResponseModel(
            code=200,
            message="获取合同执行报表成功",
            data=ContractReportResponse(
                report_date=report_date_str,
                report_type="contract",
                draft_count=draft_count,
                signed_count=signed_count,
                executing_count=executing_count,
                completed_count=completed_count,
                cancelled_count=cancelled_count,
                total_contract_amount=total_contract_amount,
                signed_amount=signed_amount,
                executing_amount=executing_amount,
                completed_amount=completed_amount,
                average_execution_rate=average_execution_rate,
                top_customers=top_customers
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同执行报表失败: {str(e)}")


@router.get("/reports/invoice", response_model=ResponseModel[InvoiceReportResponse], summary="获取开票统计报表")
async def get_invoice_report(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取开票统计报表"""
    try:
        from sqlalchemy import text
        
        # 确定统计周期
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")
        else:
            # 默认本月
            today = date.today()
            start_dt = date(today.year, today.month, 1)
            if today.month == 12:
                end_dt = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        report_date_str = f"{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}"
        
        # 开票汇总
        invoices = (
            db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= start_dt,
                func.date(Invoice.issue_date) <= end_dt,
                Invoice.status == "ISSUED"
            )
            .all()
        )
        total_invoices_count = len(invoices)
        total_invoices_amount = sum(i.invoice_amount or Decimal("0") for i in invoices)
        total_tax_amount = sum(i.tax_amount or Decimal("0") for i in invoices)
        
        # 按类型统计（简化处理，假设Invoice有invoice_type字段）
        special_invoice_count = 0
        special_invoice_amount = Decimal("0")
        normal_invoice_count = 0
        normal_invoice_amount = Decimal("0")
        electronic_invoice_count = 0
        electronic_invoice_amount = Decimal("0")
        
        for invoice in invoices:
            # 这里需要根据实际的invoice_type字段来判断
            # 暂时简化处理
            special_invoice_count += 1
            special_invoice_amount += invoice.invoice_amount or Decimal("0")
        
        # 开票及时率
        on_time_invoices_count = (
            db.query(Invoice)
            .filter(
                func.date(Invoice.issue_date) >= start_dt,
                func.date(Invoice.issue_date) <= end_dt,
                Invoice.status == "ISSUED"
            )
            .count()
        )
        
        overdue_invoices_count = 0  # 简化处理
        timeliness_rate = Decimal("100") if total_invoices_count > 0 else Decimal("0")
        
        # 按客户统计（前10名）
        top_customers_result = db.execute(text("""
            SELECT 
                c.customer_name,
                COALESCE(SUM(i.invoice_amount), 0) as invoice_amount
            FROM invoices i
            JOIN contracts ct ON i.contract_id = ct.id
            JOIN customers c ON ct.customer_id = c.id
            WHERE i.issue_date >= :start_date
            AND i.issue_date <= :end_date
            AND i.status = 'ISSUED'
            GROUP BY c.id, c.customer_name
            ORDER BY invoice_amount DESC
            LIMIT 10
        """), {"start_date": start_dt.strftime("%Y-%m-%d"), "end_date": end_dt.strftime("%Y-%m-%d")}).fetchall()
        
        top_customers = [
            {"customer_name": row[0], "invoice_amount": float(row[1])}
            for row in top_customers_result
        ]
        
        return ResponseModel(
            code=200,
            message="获取开票统计报表成功",
            data=InvoiceReportResponse(
                report_date=report_date_str,
                report_type="invoice",
                total_invoices_count=total_invoices_count,
                total_invoices_amount=total_invoices_amount,
                total_tax_amount=total_tax_amount,
                special_invoice_count=special_invoice_count,
                special_invoice_amount=special_invoice_amount,
                normal_invoice_count=normal_invoice_count,
                normal_invoice_amount=normal_invoice_amount,
                electronic_invoice_count=electronic_invoice_count,
                electronic_invoice_amount=electronic_invoice_amount,
                on_time_invoices_count=on_time_invoices_count,
                overdue_invoices_count=overdue_invoices_count,
                timeliness_rate=timeliness_rate,
                top_customers=top_customers
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取开票统计报表失败: {str(e)}")
