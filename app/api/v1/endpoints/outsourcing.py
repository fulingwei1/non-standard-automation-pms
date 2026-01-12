# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.outsourcing import (
    OutsourcingVendor, OutsourcingOrder, OutsourcingOrderItem,
    OutsourcingDelivery, OutsourcingDeliveryItem,
    OutsourcingInspection, OutsourcingProgress, OutsourcingEvaluation, OutsourcingPayment
)
from app.schemas.outsourcing import (
    VendorCreate, VendorUpdate, VendorResponse,
    OutsourcingOrderCreate, OutsourcingOrderUpdate, OutsourcingOrderResponse, OutsourcingOrderListResponse,
    OutsourcingOrderItemCreate, OutsourcingOrderItemResponse,
    OutsourcingDeliveryCreate, OutsourcingDeliveryResponse,
    OutsourcingInspectionCreate, OutsourcingInspectionResponse,
    OutsourcingProgressCreate, OutsourcingProgressResponse,
    OutsourcingPaymentCreate, OutsourcingPaymentUpdate, OutsourcingPaymentResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_order_no(db: Session) -> str:
    """生成外协订单号：OS-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order = (
        db.query(OutsourcingOrder)
        .filter(OutsourcingOrder.order_no.like(f"OS-{today}-%"))
        .order_by(desc(OutsourcingOrder.order_no))
        .first()
    )
    if max_order:
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"OS-{today}-{seq:03d}"


def generate_delivery_no(db: Session) -> str:
    """生成交付单号：DL-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_delivery = (
        db.query(OutsourcingDelivery)
        .filter(OutsourcingDelivery.delivery_no.like(f"DL-{today}-%"))
        .order_by(desc(OutsourcingDelivery.delivery_no))
        .first()
    )
    if max_delivery:
        seq = int(max_delivery.delivery_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"DL-{today}-{seq:03d}"


def generate_inspection_no(db: Session) -> str:
    """生成质检单号：IQ-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_inspection = (
        db.query(OutsourcingInspection)
        .filter(OutsourcingInspection.inspection_no.like(f"IQ-{today}-%"))
        .order_by(desc(OutsourcingInspection.inspection_no))
        .first()
    )
    if max_inspection:
        seq = int(max_inspection.inspection_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"IQ-{today}-{seq:03d}"


# ==================== 外协供应商 ====================

@router.get("/outsourcing-vendors", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_vendors(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（编码/名称）"),
    vendor_type: Optional[str] = Query(None, description="外协商类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协商列表
    """
    query = db.query(OutsourcingVendor)
    
    if keyword:
        query = query.filter(
            or_(
                OutsourcingVendor.vendor_code.like(f"%{keyword}%"),
                OutsourcingVendor.vendor_name.like(f"%{keyword}%"),
            )
        )
    
    if vendor_type:
        query = query.filter(OutsourcingVendor.vendor_type == vendor_type)
    
    if status:
        query = query.filter(OutsourcingVendor.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    vendors = query.order_by(OutsourcingVendor.created_at).offset(offset).limit(page_size).all()
    
    items = []
    for vendor in vendors:
        items.append(VendorResponse(
            id=vendor.id,
            vendor_code=vendor.vendor_code,
            vendor_name=vendor.vendor_name,
            vendor_short_name=vendor.vendor_short_name,
            vendor_type=vendor.vendor_type,
            contact_person=vendor.contact_person,
            contact_phone=vendor.contact_phone,
            quality_rating=vendor.quality_rating or Decimal("0"),
            delivery_rating=vendor.delivery_rating or Decimal("0"),
            service_rating=vendor.service_rating or Decimal("0"),
            overall_rating=vendor.overall_rating or Decimal("0"),
            status=vendor.status,
            cooperation_start=vendor.cooperation_start,
            last_order_date=vendor.last_order_date,
            created_at=vendor.created_at,
            updated_at=vendor.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/outsourcing-vendors/{vendor_id}", response_model=VendorResponse, status_code=status.HTTP_200_OK)
def read_vendor(
    vendor_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协商详情
    """
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    return VendorResponse(
        id=vendor.id,
        vendor_code=vendor.vendor_code,
        vendor_name=vendor.vendor_name,
        vendor_short_name=vendor.vendor_short_name,
        vendor_type=vendor.vendor_type,
        contact_person=vendor.contact_person,
        contact_phone=vendor.contact_phone,
        quality_rating=vendor.quality_rating or Decimal("0"),
        delivery_rating=vendor.delivery_rating or Decimal("0"),
        service_rating=vendor.service_rating or Decimal("0"),
        overall_rating=vendor.overall_rating or Decimal("0"),
        status=vendor.status,
        cooperation_start=vendor.cooperation_start,
        last_order_date=vendor.last_order_date,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at
    )


@router.post("/outsourcing-vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    *,
    db: Session = Depends(deps.get_db),
    vendor_in: VendorCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建外协商
    """
    # 检查编码是否已存在
    existing = db.query(OutsourcingVendor).filter(OutsourcingVendor.vendor_code == vendor_in.vendor_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="外协商编码已存在")
    
    vendor = OutsourcingVendor(
        vendor_code=vendor_in.vendor_code,
        vendor_name=vendor_in.vendor_name,
        vendor_short_name=vendor_in.vendor_short_name,
        vendor_type=vendor_in.vendor_type,
        contact_person=vendor_in.contact_person,
        contact_phone=vendor_in.contact_phone,
        contact_email=vendor_in.contact_email,
        address=vendor_in.address,
        business_license=vendor_in.business_license,
        qualification=vendor_in.qualification,
        capabilities=vendor_in.capabilities,
        bank_name=vendor_in.bank_name,
        bank_account=vendor_in.bank_account,
        tax_number=vendor_in.tax_number,
        status="ACTIVE",
        created_by=current_user.id,
        remark=vendor_in.remark
    )
    
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    return read_vendor(vendor.id, db, current_user)


@router.put("/outsourcing-vendors/{vendor_id}", response_model=VendorResponse, status_code=status.HTTP_200_OK)
def update_vendor(
    *,
    db: Session = Depends(deps.get_db),
    vendor_id: int,
    vendor_in: VendorUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新外协商
    """
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    update_data = vendor_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    return read_vendor(vendor_id, db, current_user)


@router.post("/outsourcing-vendors/{vendor_id}/evaluations", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_vendor_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    vendor_id: int,
    quality_rating: Decimal = Query(..., ge=0, le=5, description="质量评分"),
    delivery_rating: Decimal = Query(..., ge=0, le=5, description="交期评分"),
    service_rating: Decimal = Query(..., ge=0, le=5, description="服务评分"),
    eval_period: Optional[str] = Query(None, description="评价周期（如：2025-01）"),
    remark: Optional[str] = Query(None, description="评价备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协商评价
    """
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    # 计算综合评分（简单平均）
    overall_rating = (quality_rating + delivery_rating + service_rating) / 3
    
    # 更新外协商评分（取最近评价的平均值或直接更新）
    vendor.quality_rating = quality_rating
    vendor.delivery_rating = delivery_rating
    vendor.service_rating = service_rating
    vendor.overall_rating = overall_rating
    
    # 创建评价记录
    evaluation = OutsourcingEvaluation(
        vendor_id=vendor_id,
        eval_period=eval_period or datetime.now().strftime("%Y-%m"),
        quality_score=quality_rating,
        delivery_score=delivery_rating,
        service_score=service_rating,
        overall_score=overall_rating,
        evaluator_id=current_user.id,
        evaluated_at=datetime.now(),
        remark=remark
    )
    
    db.add(vendor)
    db.add(evaluation)
    db.commit()
    
    return ResponseModel(message="评价成功")


# ==================== 外协订单 ====================

@router.get("/outsourcing-orders", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（订单号/标题）"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    order_type: Optional[str] = Query(None, description="订单类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协订单列表
    """
    query = db.query(OutsourcingOrder)
    
    if keyword:
        query = query.filter(
            or_(
                OutsourcingOrder.order_no.like(f"%{keyword}%"),
                OutsourcingOrder.order_title.like(f"%{keyword}%"),
            )
        )
    
    if vendor_id:
        query = query.filter(OutsourcingOrder.vendor_id == vendor_id)
    
    if project_id:
        query = query.filter(OutsourcingOrder.project_id == project_id)
    
    if order_type:
        query = query.filter(OutsourcingOrder.order_type == order_type)
    
    if status:
        query = query.filter(OutsourcingOrder.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(desc(OutsourcingOrder.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for order in orders:
        vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
        project = db.query(Project).filter(Project.id == order.project_id).first()
        
        items.append(OutsourcingOrderListResponse(
            id=order.id,
            order_no=order.order_no,
            vendor_name=vendor.vendor_name if vendor else None,
            project_name=project.project_name if project else None,
            order_type=order.order_type,
            order_title=order.order_title,
            amount_with_tax=order.amount_with_tax or Decimal("0"),
            required_date=order.required_date,
            status=order.status,
            payment_status=order.payment_status,
            created_at=order.created_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/outsourcing-orders/{order_id}", response_model=OutsourcingOrderResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协订单详情
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
    
    # 获取订单明细
    items_data = []
    order_items = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.order_id == order_id).order_by(OutsourcingOrderItem.item_no).all()
    for item in order_items:
        items_data.append(OutsourcingOrderItemResponse(
            id=item.id,
            item_no=item.item_no,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            drawing_no=item.drawing_no,
            process_type=item.process_type,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            material_provided=item.material_provided,
            delivered_quantity=item.delivered_quantity or Decimal("0"),
            qualified_quantity=item.qualified_quantity or Decimal("0"),
            rejected_quantity=item.rejected_quantity or Decimal("0"),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return OutsourcingOrderResponse(
        id=order.id,
        order_no=order.order_no,
        vendor_id=order.vendor_id,
        vendor_name=vendor.vendor_name if vendor else None,
        project_id=order.project_id,
        project_name=project.project_name if project else None,
        machine_id=order.machine_id,
        machine_name=machine.machine_name if machine else None,
        order_type=order.order_type,
        order_title=order.order_title,
        total_amount=order.total_amount or Decimal("0"),
        tax_rate=order.tax_rate or Decimal("13"),
        tax_amount=order.tax_amount or Decimal("0"),
        amount_with_tax=order.amount_with_tax or Decimal("0"),
        required_date=order.required_date,
        estimated_date=order.estimated_date,
        actual_date=order.actual_date,
        status=order.status,
        payment_status=order.payment_status,
        paid_amount=order.paid_amount or Decimal("0"),
        items=items_data,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.post("/outsourcing-orders", response_model=OutsourcingOrderResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: OutsourcingOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建外协订单
    """
    # 验证外协商
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    # 验证项目
    project = db.query(Project).filter(Project.id == order_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证机台（如果提供）
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine or machine.project_id != order_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
    
    if not order_in.items:
        raise HTTPException(status_code=400, detail="订单明细不能为空")
    
    order_no = generate_order_no(db)
    
    # 计算金额
    total_amount = Decimal("0")
    for item in order_in.items:
        item_amount = item.quantity * item.unit_price
        total_amount += item_amount
    
    tax_amount = total_amount * (order_in.tax_rate / 100)
    amount_with_tax = total_amount + tax_amount
    
    order = OutsourcingOrder(
        order_no=order_no,
        vendor_id=order_in.vendor_id,
        project_id=order_in.project_id,
        machine_id=order_in.machine_id,
        order_type=order_in.order_type,
        order_title=order_in.order_title,
        order_description=order_in.order_description,
        tax_rate=order_in.tax_rate,
        total_amount=total_amount,
        tax_amount=tax_amount,
        amount_with_tax=amount_with_tax,
        required_date=order_in.required_date,
        contract_no=order_in.contract_no,
        status="DRAFT",
        created_by=current_user.id,
        remark=order_in.remark
    )
    
    db.add(order)
    db.flush()  # 获取order.id
    
    # 创建订单明细
    for idx, item_in in enumerate(order_in.items, start=1):
        item_amount = item_in.quantity * item_in.unit_price
        item = OutsourcingOrderItem(
            order_id=order.id,
            item_no=idx,
            material_id=item_in.material_id,
            material_code=item_in.material_code,
            material_name=item_in.material_name,
            specification=item_in.specification,
            drawing_no=item_in.drawing_no,
            process_type=item_in.process_type,
            process_content=item_in.process_content,
            process_requirements=item_in.process_requirements,
            unit=item_in.unit,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            amount=item_amount,
            material_provided=item_in.material_provided,
            provided_quantity=item_in.provided_quantity or Decimal("0"),
            remark=item_in.remark
        )
        db.add(item)
    
    db.commit()
    db.refresh(order)
    
    return read_outsourcing_order(order.id, db, current_user)


@router.put("/outsourcing-orders/{order_id}", response_model=OutsourcingOrderResponse, status_code=status.HTTP_200_OK)
def update_outsourcing_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: OutsourcingOrderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新外协订单
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能修改草稿状态的订单")
    
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_outsourcing_order(order_id, db, current_user)


@router.put("/outsourcing-orders/{order_id}/approve", response_model=OutsourcingOrderResponse, status_code=status.HTTP_200_OK)
def approve_outsourcing_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协订单审批
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    if order.status not in ["DRAFT", "SUBMITTED"]:
        raise HTTPException(status_code=400, detail="只能审批草稿或已提交状态的订单")
    
    order.status = "APPROVED"
    
    # 更新外协商的最后订单日期
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
    if vendor:
        vendor.last_order_date = datetime.now().date()
        db.add(vendor)
    
    db.add(order)
    db.commit()
    
    # 审批通过时自动归集成本
    if order.project_id:
        try:
            from app.services.cost_collection_service import CostCollectionService
            CostCollectionService.collect_from_outsourcing_order(
                db, order_id, created_by=current_user.id
            )
            db.commit()
        except Exception as e:
            # 成本归集失败不影响审批流程，只记录错误
            logger.error(f"Failed to collect cost from outsourcing order {order_id}: {e}")
    
    db.refresh(order)
    
    return read_outsourcing_order(order_id, db, current_user)


@router.get("/outsourcing-orders/{order_id}/items", response_model=List[OutsourcingOrderItemResponse], status_code=status.HTTP_200_OK)
def read_outsourcing_order_items(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协订单明细
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    items = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.order_id == order_id).order_by(OutsourcingOrderItem.item_no).all()
    
    items_data = []
    for item in items:
        items_data.append(OutsourcingOrderItemResponse(
            id=item.id,
            item_no=item.item_no,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            drawing_no=item.drawing_no,
            process_type=item.process_type,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            material_provided=item.material_provided,
            delivered_quantity=item.delivered_quantity or Decimal("0"),
            qualified_quantity=item.qualified_quantity or Decimal("0"),
            rejected_quantity=item.rejected_quantity or Decimal("0"),
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return items_data


# ==================== 外协交付 ====================

@router.get("/outsourcing-deliveries", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_deliveries(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    order_id: Optional[int] = Query(None, description="订单ID筛选"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取交付记录列表
    """
    query = db.query(OutsourcingDelivery)
    
    if order_id:
        query = query.filter(OutsourcingDelivery.order_id == order_id)
    
    if vendor_id:
        query = query.filter(OutsourcingDelivery.vendor_id == vendor_id)
    
    if status:
        query = query.filter(OutsourcingDelivery.status == status)
    
    total = query.count()
    offset = (page - 1) * page_size
    deliveries = query.order_by(desc(OutsourcingDelivery.delivery_date)).offset(offset).limit(page_size).all()
    
    items = []
    for delivery in deliveries:
        vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == delivery.vendor_id).first()
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()
        
        items.append(OutsourcingDeliveryResponse(
            id=delivery.id,
            delivery_no=delivery.delivery_no,
            order_id=delivery.order_id,
            order_no=order.order_no if order else None,
            vendor_name=vendor.vendor_name if vendor else None,
            delivery_date=delivery.delivery_date,
            delivery_type=delivery.delivery_type,
            status=delivery.status,
            received_at=delivery.received_at,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/outsourcing-deliveries", response_model=OutsourcingDeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_delivery(
    *,
    db: Session = Depends(deps.get_db),
    delivery_in: OutsourcingDeliveryCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建交付记录
    """
    # 验证订单
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery_in.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    if order.status not in ["APPROVED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能为已审批或进行中的订单创建交付记录")
    
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    if not delivery_in.items:
        raise HTTPException(status_code=400, detail="交付明细不能为空")
    
    delivery_no = generate_delivery_no(db)
    
    delivery = OutsourcingDelivery(
        delivery_no=delivery_no,
        order_id=delivery_in.order_id,
        vendor_id=order.vendor_id,
        delivery_date=delivery_in.delivery_date,
        delivery_type=delivery_in.delivery_type,
        delivery_person=delivery_in.delivery_person,
        logistics_company=delivery_in.logistics_company,
        tracking_no=delivery_in.tracking_no,
        status="PENDING",
        created_by=current_user.id,
        remark=delivery_in.remark
    )
    
    db.add(delivery)
    db.flush()  # 获取delivery.id
    
    # 创建交付明细
    for item_in in delivery_in.items:
        order_item = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.id == item_in.order_item_id).first()
        if not order_item or order_item.order_id != delivery_in.order_id:
            raise HTTPException(status_code=400, detail=f"订单明细ID {item_in.order_item_id} 不存在或不属于该订单")
        
        delivery_item = OutsourcingDeliveryItem(
            delivery_id=delivery.id,
            order_item_id=item_in.order_item_id,
            material_code=order_item.material_code,
            material_name=order_item.material_name,
            delivery_quantity=item_in.delivery_quantity,
            remark=item_in.remark
        )
        db.add(delivery_item)
        
        # 更新订单明细的已交付数量
        order_item.delivered_quantity = (order_item.delivered_quantity or Decimal("0")) + item_in.delivery_quantity
        db.add(order_item)
    
    # 更新订单状态
    if order.status == "APPROVED":
        order.status = "IN_PROGRESS"
        db.add(order)
    
    db.commit()
    db.refresh(delivery)
    
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == delivery.vendor_id).first()
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()
    
    return OutsourcingDeliveryResponse(
        id=delivery.id,
        delivery_no=delivery.delivery_no,
        order_id=delivery.order_id,
        order_no=order.order_no if order else None,
        vendor_name=vendor.vendor_name if vendor else None,
        delivery_date=delivery.delivery_date,
        delivery_type=delivery.delivery_type,
        status=delivery.status,
        received_at=delivery.received_at,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at
    )


# ==================== 外协质检 ====================

@router.get("/outsourcing-inspections", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_inspections(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    delivery_id: Optional[int] = Query(None, description="交付单ID筛选"),
    inspect_result: Optional[str] = Query(None, description="质检结果筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取质检记录列表
    """
    query = db.query(OutsourcingInspection)
    
    if delivery_id:
        query = query.filter(OutsourcingInspection.delivery_id == delivery_id)
    
    if inspect_result:
        query = query.filter(OutsourcingInspection.inspect_result == inspect_result)
    
    total = query.count()
    offset = (page - 1) * page_size
    inspections = query.order_by(desc(OutsourcingInspection.inspect_date)).offset(offset).limit(page_size).all()
    
    items = []
    for inspection in inspections:
        pass_rate = Decimal("0")
        if inspection.inspect_quantity and inspection.inspect_quantity > 0:
            pass_rate = (inspection.qualified_quantity or Decimal("0")) / inspection.inspect_quantity * 100
        
        items.append(OutsourcingInspectionResponse(
            id=inspection.id,
            inspection_no=inspection.inspection_no,
            delivery_id=inspection.delivery_id,
            inspect_type=inspection.inspect_type,
            inspect_date=inspection.inspect_date,
            inspector_name=inspection.inspector_name,
            inspect_quantity=inspection.inspect_quantity,
            qualified_quantity=inspection.qualified_quantity or Decimal("0"),
            rejected_quantity=inspection.rejected_quantity or Decimal("0"),
            inspect_result=inspection.inspect_result,
            pass_rate=pass_rate,
            disposition=inspection.disposition,
            created_at=inspection.created_at,
            updated_at=inspection.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/outsourcing-inspections", response_model=OutsourcingInspectionResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_in: OutsourcingInspectionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建质检记录
    """
    # 验证交付明细
    delivery_item = db.query(OutsourcingDeliveryItem).filter(OutsourcingDeliveryItem.id == inspection_in.delivery_item_id).first()
    if not delivery_item:
        raise HTTPException(status_code=404, detail="交付明细不存在")
    
    if delivery_item.delivery_id != inspection_in.delivery_id:
        raise HTTPException(status_code=400, detail="交付明细不属于该交付单")
    
    if inspection_in.inspect_quantity > delivery_item.delivery_quantity:
        raise HTTPException(status_code=400, detail="送检数量不能大于交付数量")
    
    if inspection_in.qualified_quantity + inspection_in.rejected_quantity > inspection_in.inspect_quantity:
        raise HTTPException(status_code=400, detail="合格数量+不合格数量不能大于送检数量")
    
    inspection_no = generate_inspection_no(db)
    
    # 计算合格率
    pass_rate = Decimal("0")
    if inspection_in.inspect_quantity > 0:
        pass_rate = inspection_in.qualified_quantity / inspection_in.inspect_quantity * 100
    
    inspection = OutsourcingInspection(
        inspection_no=inspection_no,
        delivery_id=inspection_in.delivery_id,
        delivery_item_id=inspection_in.delivery_item_id,
        inspect_type=inspection_in.inspect_type,
        inspect_date=inspection_in.inspect_date,
        inspector_id=current_user.id,
        inspector_name=current_user.real_name or current_user.username,
        inspect_quantity=inspection_in.inspect_quantity,
        sample_quantity=inspection_in.sample_quantity or Decimal("0"),
        qualified_quantity=inspection_in.qualified_quantity,
        rejected_quantity=inspection_in.rejected_quantity,
        inspect_result=inspection_in.inspect_result,
        pass_rate=pass_rate,
        defect_description=inspection_in.defect_description,
        defect_type=inspection_in.defect_type,
        disposition=inspection_in.disposition,
        disposition_note=inspection_in.disposition_note,
        remark=inspection_in.remark
    )
    
    # 更新交付明细的质检结果
    delivery_item.inspect_status = "COMPLETED"
    delivery_item.qualified_quantity = inspection_in.qualified_quantity
    delivery_item.rejected_quantity = inspection_in.rejected_quantity
    
    # 更新订单明细的合格数量和不合格数量
    order_item = db.query(OutsourcingOrderItem).filter(OutsourcingOrderItem.id == delivery_item.order_item_id).first()
    if order_item:
        order_item.qualified_quantity = (order_item.qualified_quantity or Decimal("0")) + inspection_in.qualified_quantity
        order_item.rejected_quantity = (order_item.rejected_quantity or Decimal("0")) + inspection_in.rejected_quantity
        db.add(order_item)
    
    db.add(inspection)
    db.add(delivery_item)
    db.commit()
    db.refresh(inspection)
    
    pass_rate = Decimal("0")
    if inspection.inspect_quantity and inspection.inspect_quantity > 0:
        pass_rate = (inspection.qualified_quantity or Decimal("0")) / inspection.inspect_quantity * 100
    
    return OutsourcingInspectionResponse(
        id=inspection.id,
        inspection_no=inspection.inspection_no,
        delivery_id=inspection.delivery_id,
        inspect_type=inspection.inspect_type,
        inspect_date=inspection.inspect_date,
        inspector_name=inspection.inspector_name,
        inspect_quantity=inspection.inspect_quantity,
        qualified_quantity=inspection.qualified_quantity or Decimal("0"),
        rejected_quantity=inspection.rejected_quantity or Decimal("0"),
        inspect_result=inspection.inspect_result,
        pass_rate=pass_rate,
        disposition=inspection.disposition,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )


@router.put("/outsourcing-inspections/{inspection_id}", response_model=OutsourcingInspectionResponse, status_code=status.HTTP_200_OK)
def update_outsourcing_inspection(
    *,
    db: Session = Depends(deps.get_db),
    inspection_id: int,
    inspect_result: Optional[str] = Query(None, description="质检结果"),
    disposition: Optional[str] = Query(None, description="处置方式"),
    disposition_note: Optional[str] = Query(None, description="处理说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新质检结果
    """
    inspection = db.query(OutsourcingInspection).filter(OutsourcingInspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="质检记录不存在")
    
    if inspect_result:
        inspection.inspect_result = inspect_result
    
    if disposition:
        inspection.disposition = disposition
    
    if disposition_note:
        inspection.disposition_note = disposition_note
    
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    
    pass_rate = Decimal("0")
    if inspection.inspect_quantity and inspection.inspect_quantity > 0:
        pass_rate = (inspection.qualified_quantity or Decimal("0")) / inspection.inspect_quantity * 100
    
    return OutsourcingInspectionResponse(
        id=inspection.id,
        inspection_no=inspection.inspection_no,
        delivery_id=inspection.delivery_id,
        inspect_type=inspection.inspect_type,
        inspect_date=inspection.inspect_date,
        inspector_name=inspection.inspector_name,
        inspect_quantity=inspection.inspect_quantity,
        qualified_quantity=inspection.qualified_quantity or Decimal("0"),
        rejected_quantity=inspection.rejected_quantity or Decimal("0"),
        inspect_result=inspection.inspect_result,
        pass_rate=pass_rate,
        disposition=inspection.disposition,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at
    )


# ==================== 外协进度 ====================

@router.get("/outsourcing-orders/{order_id}/progress-logs", response_model=List[OutsourcingProgressResponse], status_code=status.HTTP_200_OK)
def read_outsourcing_progress_logs(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取外协进度列表
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    progress_records = db.query(OutsourcingProgress).filter(OutsourcingProgress.order_id == order_id).order_by(desc(OutsourcingProgress.report_date)).all()
    
    items = []
    for progress in progress_records:
        items.append(OutsourcingProgressResponse(
            id=progress.id,
            order_id=progress.order_id,
            report_date=progress.report_date,
            progress_pct=progress.progress_pct or 0,
            completed_quantity=progress.completed_quantity or Decimal("0"),
            current_process=progress.current_process,
            estimated_complete=progress.estimated_complete,
            issues=progress.issues,
            risk_level=progress.risk_level,
            created_at=progress.created_at,
            updated_at=progress.updated_at
        ))
    
    return items


@router.put("/outsourcing-orders/{order_id}/progress", response_model=OutsourcingProgressResponse, status_code=status.HTTP_200_OK)
def update_outsourcing_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    progress_in: OutsourcingProgressCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协进度更新
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    if order.status not in ["APPROVED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能更新已审批或进行中订单的进度")
    
    progress = OutsourcingProgress(
        order_id=order_id,
        order_item_id=progress_in.order_item_id,
        report_date=progress_in.report_date,
        progress_pct=progress_in.progress_pct,
        completed_quantity=progress_in.completed_quantity or Decimal("0"),
        current_process=progress_in.current_process,
        next_process=progress_in.next_process,
        estimated_complete=progress_in.estimated_complete,
        issues=progress_in.issues,
        risk_level=progress_in.risk_level,
        attachments=progress_in.attachments,
        reported_by=current_user.id
    )
    
    db.add(progress)
    db.commit()
    db.refresh(progress)
    
    return OutsourcingProgressResponse(
        id=progress.id,
        order_id=progress.order_id,
        report_date=progress.report_date,
        progress_pct=progress.progress_pct or 0,
        completed_quantity=progress.completed_quantity or Decimal("0"),
        current_process=progress.current_process,
        estimated_complete=progress.estimated_complete,
        issues=progress.issues,
        risk_level=progress.risk_level,
        created_at=progress.created_at,
        updated_at=progress.updated_at
    )


# ==================== 外协付款 ====================

def generate_payment_no(db: Session) -> str:
    """生成付款单号：PY-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_payment = (
        db.query(OutsourcingPayment)
        .filter(OutsourcingPayment.payment_no.like(f"PY-{today}-%"))
        .order_by(desc(OutsourcingPayment.payment_no))
        .first()
    )
    if max_payment:
        seq = int(max_payment.payment_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"PY-{today}-{seq:03d}"


@router.get("/outsourcing-payments", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_outsourcing_payments(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    order_id: Optional[int] = Query(None, description="外协订单ID筛选"),
    payment_type: Optional[str] = Query(None, description="付款类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期筛选"),
    end_date: Optional[date] = Query(None, description="结束日期筛选"),
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    获取外协付款记录列表
    """
    query = db.query(OutsourcingPayment)
    
    if vendor_id:
        query = query.filter(OutsourcingPayment.vendor_id == vendor_id)
    
    if order_id:
        query = query.filter(OutsourcingPayment.order_id == order_id)
    
    if payment_type:
        query = query.filter(OutsourcingPayment.payment_type == payment_type)
    
    if status:
        query = query.filter(OutsourcingPayment.status == status)
    
    if start_date:
        query = query.filter(OutsourcingPayment.payment_date >= start_date)
    
    if end_date:
        query = query.filter(OutsourcingPayment.payment_date <= end_date)
    
    total = query.count()
    offset = (page - 1) * page_size
    payments = query.order_by(desc(OutsourcingPayment.payment_date)).offset(offset).limit(page_size).all()
    
    items = []
    for payment in payments:
        vendor_name = None
        if payment.vendor_id:
            vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == payment.vendor_id).first()
            vendor_name = vendor.vendor_name if vendor else None
        
        order_no = None
        if payment.order_id:
            order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment.order_id).first()
            order_no = order.order_no if order else None
        
        approved_by_name = None
        if payment.approved_by:
            approver = db.query(User).filter(User.id == payment.approved_by).first()
            approved_by_name = approver.real_name or approver.username if approver else None
        
        items.append(OutsourcingPaymentResponse(
            id=payment.id,
            payment_no=payment.payment_no,
            vendor_id=payment.vendor_id,
            vendor_name=vendor_name,
            order_id=payment.order_id,
            order_no=order_no,
            payment_type=payment.payment_type,
            payment_amount=payment.payment_amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            invoice_no=payment.invoice_no,
            invoice_amount=payment.invoice_amount,
            invoice_date=payment.invoice_date,
            status=payment.status,
            approved_by=payment.approved_by,
            approved_by_name=approved_by_name,
            approved_at=payment.approved_at,
            remark=payment.remark,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/outsourcing-payments", response_model=OutsourcingPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_outsourcing_payment(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: OutsourcingPaymentCreate,
    current_user: User = Depends(security.require_finance_access()),
) -> Any:
    """
    创建外协付款记录
    """
    # 验证外协商是否存在
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == payment_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")
    
    # 验证外协订单（如果提供）
    if payment_in.order_id:
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment_in.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="外协订单不存在")
        if order.vendor_id != payment_in.vendor_id:
            raise HTTPException(status_code=400, detail="外协订单不属于该外协商")
    
    payment_no = generate_payment_no(db)
    
    payment = OutsourcingPayment(
        payment_no=payment_no,
        vendor_id=payment_in.vendor_id,
        order_id=payment_in.order_id,
        payment_type=payment_in.payment_type,
        payment_amount=payment_in.payment_amount,
        payment_date=payment_in.payment_date,
        payment_method=payment_in.payment_method,
        invoice_no=payment_in.invoice_no,
        invoice_amount=payment_in.invoice_amount,
        invoice_date=payment_in.invoice_date,
        status="DRAFT",
        created_by=current_user.id
    )
    
    db.add(payment)
    
    # 如果关联了订单，更新订单的已付金额和付款状态
    if payment_in.order_id:
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment_in.order_id).first()
        if order:
            order.paid_amount = (order.paid_amount or Decimal("0")) + payment_in.payment_amount
            # 判断付款状态
            if order.paid_amount >= order.amount_with_tax:
                order.payment_status = "PAID"
            elif order.paid_amount > Decimal("0"):
                order.payment_status = "PARTIAL"
            else:
                order.payment_status = "UNPAID"
    
    db.commit()
    db.refresh(payment)
    
    # 构建响应
    vendor_name = vendor.vendor_name
    order_no = None
    if payment.order_id:
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == payment.order_id).first()
        order_no = order.order_no if order else None
    
    return OutsourcingPaymentResponse(
        id=payment.id,
        payment_no=payment.payment_no,
        vendor_id=payment.vendor_id,
        vendor_name=vendor_name,
        order_id=payment.order_id,
        order_no=order_no,
        payment_type=payment.payment_type,
        payment_amount=payment.payment_amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        invoice_no=payment.invoice_no,
        invoice_amount=payment.invoice_amount,
        invoice_date=payment.invoice_date,
        status=payment.status,
        approved_by=payment.approved_by,
        approved_by_name=None,
        approved_at=payment.approved_at,
        remark=payment.remark,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )


@router.get("/outsourcing-orders/{order_id}/print", response_model=dict, status_code=status.HTTP_200_OK)
def print_outsourcing_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协订单打印
    返回订单的打印数据（包含订单信息、明细、供应商信息等）
    """
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")
    
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == order.vendor_id).first()
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
    
    # 获取订单明细
    order_items = db.query(OutsourcingOrderItem).filter(
        OutsourcingOrderItem.order_id == order_id
    ).order_by(OutsourcingOrderItem.item_no).all()
    
    items_data = []
    for item in order_items:
        items_data.append({
            "item_no": item.item_no,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "specification": item.specification,
            "drawing_no": item.drawing_no,
            "process_type": item.process_type,
            "unit": item.unit,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "amount": float(item.amount),
            "material_provided": item.material_provided,
        })
    
    # 获取交付记录
    deliveries = db.query(OutsourcingDelivery).filter(
        OutsourcingDelivery.order_id == order_id
    ).order_by(OutsourcingDelivery.delivery_date).all()
    
    deliveries_data = []
    for delivery in deliveries:
        deliveries_data.append({
            "delivery_no": delivery.delivery_no,
            "delivery_date": delivery.delivery_date.isoformat() if delivery.delivery_date else None,
            "delivery_qty": float(delivery.delivery_qty or 0),
            "status": delivery.status,
        })
    
    # 获取付款记录
    payments = db.query(OutsourcingPayment).filter(
        OutsourcingPayment.order_id == order_id
    ).order_by(OutsourcingPayment.payment_date).all()
    
    payments_data = []
    for payment in payments:
        payments_data.append({
            "payment_type": payment.payment_type,
            "payment_amount": float(payment.payment_amount or 0),
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "payment_method": payment.payment_method,
            "status": payment.status,
        })
    
    return {
        "order": {
            "order_no": order.order_no,
            "order_title": order.order_title,
            "order_type": order.order_type,
            "total_amount": float(order.total_amount or 0),
            "tax_rate": float(order.tax_rate or 0),
            "tax_amount": float(order.tax_amount or 0),
            "amount_with_tax": float(order.amount_with_tax or 0),
            "required_date": order.required_date.isoformat() if order.required_date else None,
            "estimated_date": order.estimated_date.isoformat() if order.estimated_date else None,
            "actual_date": order.actual_date.isoformat() if order.actual_date else None,
            "status": order.status,
            "payment_status": order.payment_status,
            "paid_amount": float(order.paid_amount or 0),
            "created_at": order.created_at.isoformat() if order.created_at else None,
        },
        "vendor": {
            "vendor_name": vendor.vendor_name if vendor else None,
            "contact_person": vendor.contact_person if vendor else None,
            "contact_phone": vendor.contact_phone if vendor else None,
            "address": vendor.address if vendor else None,
        } if vendor else None,
        "project": {
            "project_name": project.project_name if project else None,
            "project_code": project.project_code if project else None,
        } if project else None,
        "machine": {
            "machine_name": machine.machine_name if machine else None,
            "machine_code": machine.machine_code if machine else None,
        } if machine else None,
        "items": items_data,
        "deliveries": deliveries_data,
        "payments": payments_data,
        "print_time": datetime.now().isoformat(),
    }


@router.get("/outsourcing-vendors/{vendor_id}/statement", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_vendor_statement(
    vendor_id: int,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    外协对账单
    生成指定供应商的对账单，包含订单、交付、付款等明细
    """
    vendor = db.query(OutsourcingVendor).filter(OutsourcingVendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="外协供应商不存在")
    
    # 获取订单列表
    orders_query = db.query(OutsourcingOrder).filter(OutsourcingOrder.vendor_id == vendor_id)
    if start_date:
        orders_query = orders_query.filter(OutsourcingOrder.order_date >= start_date)
    if end_date:
        orders_query = orders_query.filter(OutsourcingOrder.order_date <= end_date)
    orders = orders_query.order_by(OutsourcingOrder.order_date).all()
    
    # 构建对账单明细
    statement_items = []
    total_order_amount = Decimal("0")
    total_paid_amount = Decimal("0")
    total_pending_amount = Decimal("0")
    
    for order in orders:
        # 获取订单明细
        order_items = db.query(OutsourcingOrderItem).filter(
            OutsourcingOrderItem.order_id == order.id
        ).all()
        
        order_total = sum(float(item.unit_price or 0) * float(item.quantity or 0) for item in order_items)
        total_order_amount += Decimal(str(order_total))
        
        # 获取付款记录
        payments = db.query(OutsourcingPayment).filter(
            OutsourcingPayment.order_id == order.id,
            OutsourcingPayment.status == 'PAID'
        ).all()
        
        paid_amount = sum(float(payment.payment_amount or 0) for payment in payments)
        total_paid_amount += Decimal(str(paid_amount))
        
        pending_amount = order_total - paid_amount
        total_pending_amount += Decimal(str(pending_amount))
        
        # 获取交付记录
        deliveries = db.query(OutsourcingDelivery).filter(
            OutsourcingDelivery.order_id == order.id
        ).all()
        
        statement_items.append({
            "order_id": order.id,
            "order_no": order.order_no,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "order_amount": round(order_total, 2),
            "paid_amount": round(paid_amount, 2),
            "pending_amount": round(pending_amount, 2),
            "order_status": order.status,
            "deliveries": [
                {
                    "delivery_no": d.delivery_no,
                    "delivery_date": d.delivery_date.isoformat() if d.delivery_date else None,
                    "delivery_qty": float(d.total_qty or 0)
                }
                for d in deliveries
            ],
            "payments": [
                {
                    "payment_no": p.payment_no,
                    "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                    "payment_amount": float(p.payment_amount or 0),
                    "payment_type": p.payment_type
                }
                for p in payments
            ]
        })
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "vendor_id": vendor_id,
            "vendor_name": vendor.vendor_name,
            "vendor_code": vendor.vendor_code,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "summary": {
                "total_orders": len(orders),
                "total_order_amount": float(total_order_amount),
                "total_paid_amount": float(total_paid_amount),
                "total_pending_amount": float(total_pending_amount)
            },
            "items": statement_items,
            "generated_at": datetime.now().isoformat()
        }
    )

