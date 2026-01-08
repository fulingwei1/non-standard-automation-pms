# -*- coding: utf-8 -*-
"""
采购管理 API endpoints
"""
from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.purchase import (
    PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem,
    PurchaseRequest, PurchaseRequestItem
)
from app.models.material import Material, Supplier
from app.models.project import Project, Machine
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderListResponse,
    PurchaseOrderItemResponse,
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    GoodsReceiptItemResponse,
    PurchaseRequestCreate,
    PurchaseRequestUpdate,
    PurchaseRequestResponse,
    PurchaseRequestListResponse,
    PurchaseRequestItemResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_order_no(db: Session) -> str:
    """生成采购订单编号：PO-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    # 查询今天最大的序号
    max_order = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.order_no.like(f"PO-{today}-%"))
        .order_by(desc(PurchaseOrder.order_no))
        .first()
    )
    
    if max_order:
        # 提取序号并加1
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    
    return f"PO-{today}-{seq:03d}"


@router.get("/", response_model=PaginatedResponse[PurchaseOrderListResponse])
def read_purchase_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（订单编号/标题）"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="订单状态筛选"),
    payment_status: Optional[str] = Query(None, description="付款状态筛选"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取采购订单列表（支持分页、搜索、筛选）
    """
    query = db.query(PurchaseOrder)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                PurchaseOrder.order_no.contains(keyword),
                PurchaseOrder.order_title.contains(keyword),
            )
        )
    
    # 供应商筛选
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    
    # 项目筛选
    if project_id:
        query = query.filter(PurchaseOrder.project_id == project_id)
    
    # 状态筛选
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    # 付款状态筛选
    if payment_status:
        query = query.filter(PurchaseOrder.payment_status == payment_status)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    orders = query.order_by(desc(PurchaseOrder.created_at)).offset(offset).limit(page_size).all()
    
    # 构建响应数据
    items = []
    for order in orders:
        item = PurchaseOrderListResponse(
            id=order.id,
            order_no=order.order_no,
            supplier_name=order.supplier.supplier_name if order.supplier else "",
            project_name=order.project.project_name if order.project else None,
            total_amount=order.total_amount or 0,
            amount_with_tax=order.amount_with_tax or 0,
            required_date=order.required_date,
            status=order.status,
            payment_status=order.payment_status,
            created_at=order.created_at,
        )
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
def read_purchase_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取采购订单详情
    """
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    # 获取订单明细
    items = []
    for item in order.items.order_by(PurchaseOrderItem.item_no).all():
        items.append(PurchaseOrderItemResponse(
            id=item.id,
            item_no=item.item_no,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price or 0,
            amount=item.amount or 0,
            tax_rate=item.tax_rate or 0,
            amount_with_tax=item.amount_with_tax or 0,
            required_date=item.required_date,
            promised_date=item.promised_date,
            received_qty=item.received_qty or 0,
            qualified_qty=item.qualified_qty or 0,
            status=item.status,
        ))
    
    return PurchaseOrderResponse(
        id=order.id,
        order_no=order.order_no,
        supplier_id=order.supplier_id,
        supplier_name=order.supplier.supplier_name if order.supplier else "",
        project_id=order.project_id,
        project_name=order.project.project_name if order.project else None,
        order_type=order.order_type,
        order_title=order.order_title,
        total_amount=order.total_amount or 0,
        tax_amount=order.tax_amount or 0,
        amount_with_tax=order.amount_with_tax or 0,
        order_date=order.order_date,
        required_date=order.required_date,
        status=order.status,
        payment_status=order.payment_status,
        paid_amount=order.paid_amount or 0,
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("/", response_model=PurchaseOrderResponse)
def create_purchase_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: PurchaseOrderCreate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    创建采购订单
    """
    # 检查供应商是否存在
    supplier = db.query(Supplier).filter(Supplier.id == order_in.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    # 检查项目是否存在
    if order_in.project_id:
        project = db.query(Project).filter(Project.id == order_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 生成订单编号
    order_no = generate_order_no(db)
    
    # 创建订单
    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=order_in.supplier_id,
        project_id=order_in.project_id,
        order_type=order_in.order_type,
        order_title=order_in.order_title,
        required_date=order_in.required_date,
        payment_terms=order_in.payment_terms,
        delivery_address=order_in.delivery_address,
        contract_no=order_in.contract_no,
        remark=order_in.remark,
        order_date=date.today(),
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(order)
    db.flush()
    
    # 创建订单明细
    total_amount = Decimal(0)
    total_tax_amount = Decimal(0)
    total_amount_with_tax = Decimal(0)
    
    for idx, item_in in enumerate(order_in.items, start=1):
        # 如果提供了物料ID，获取物料信息
        material = None
        if item_in.material_id:
            material = db.query(Material).filter(Material.id == item_in.material_id).first()
            if not material:
                raise HTTPException(status_code=404, detail=f"物料ID {item_in.material_id} 不存在")
        
        # 计算金额
        amount = item_in.quantity * item_in.unit_price
        tax_amount = amount * item_in.tax_rate / 100
        amount_with_tax = amount + tax_amount
        
        item = PurchaseOrderItem(
            order_id=order.id,
            item_no=idx,
            material_id=item_in.material_id,
            bom_item_id=item_in.bom_item_id,
            material_code=item_in.material_code,
            material_name=item_in.material_name,
            specification=item_in.specification,
            unit=item_in.unit,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            amount=amount,
            tax_rate=item_in.tax_rate,
            tax_amount=tax_amount,
            amount_with_tax=amount_with_tax,
            required_date=item_in.required_date,
            remark=item_in.remark,
            status="PENDING",
        )
        db.add(item)
        
        total_amount += amount
        total_tax_amount += tax_amount
        total_amount_with_tax += amount_with_tax
    
    # 更新订单总金额
    order.total_amount = total_amount
    order.tax_amount = total_tax_amount
    order.amount_with_tax = total_amount_with_tax
    
    db.commit()
    db.refresh(order)
    
    # 返回订单详情
    return read_purchase_order(db=db, order_id=order.id, current_user=current_user)


@router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: PurchaseOrderUpdate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    更新采购订单（仅草稿状态可更新）
    """
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    # 只有草稿状态才能更新
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的订单才能更新")
    
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_purchase_order(db=db, order_id=order.id, current_user=current_user)


@router.put("/{order_id}/submit", response_model=ResponseModel)
def submit_purchase_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    提交采购订单（提交审批）
    """
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    # 只有草稿状态才能提交
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的订单才能提交")
    
    # 检查是否有明细
    item_count = order.items.count()
    if item_count == 0:
        raise HTTPException(status_code=400, detail="订单没有明细，无法提交")
    
    # 更新状态为已提交
    order.status = "SUBMITTED"
    order.submitted_at = datetime.now()
    
    db.add(order)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="订单已提交，等待审批"
    )


@router.put("/{order_id}/approve", response_model=ResponseModel)
def approve_purchase_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    approved: bool = Query(True, description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    审批采购订单
    """
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    if order.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交的订单才能审批")
    
    if approved:
        order.status = "APPROVED"
        order.approved_by = current_user.id
        order.approved_at = datetime.now()
    else:
        order.status = "REJECTED"
    
    if approval_note:
        order.approval_note = approval_note
    
    db.add(order)
    db.commit()
    
    # 审批通过时自动归集成本
    if approved and order.project_id:
        try:
            from app.services.cost_collection_service import CostCollectionService
            CostCollectionService.collect_from_purchase_order(
                db, order_id, created_by=current_user.id
            )
            db.commit()
        except Exception as e:
            # 成本归集失败不影响审批流程，只记录错误
            print(f"Failed to collect cost from purchase order {order_id}: {e}")
    
    return ResponseModel(
        code=200,
        message="审批成功" if approved else "已驳回"
    )


@router.get("/{order_id}/items", response_model=List[PurchaseOrderItemResponse])
def get_purchase_order_items(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取采购订单明细列表
    """
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    items = []
    for item in order.items.order_by(PurchaseOrderItem.item_no).all():
        items.append(PurchaseOrderItemResponse(
            id=item.id,
            item_no=item.item_no,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price or 0,
            amount=item.amount or 0,
            tax_rate=item.tax_rate or 0,
            amount_with_tax=item.amount_with_tax or 0,
            required_date=item.required_date,
            promised_date=item.promised_date,
            received_qty=item.received_qty or 0,
            qualified_qty=item.qualified_qty or 0,
            status=item.status,
        ))
    
    return items


def generate_receipt_no(db: Session) -> str:
    """生成收货单编号：GR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    # 查询今天最大的序号
    max_receipt = (
        db.query(GoodsReceipt)
        .filter(GoodsReceipt.receipt_no.like(f"GR-{today}-%"))
        .order_by(desc(GoodsReceipt.receipt_no))
        .first()
    )
    
    if max_receipt:
        # 提取序号并加1
        seq = int(max_receipt.receipt_no.split("-")[-1]) + 1
    else:
        seq = 1
    
    return f"GR-{today}-{seq:03d}"


@router.get("/goods-receipts/", response_model=PaginatedResponse)
def read_goods_receipts(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（收货单号/送货单号）"),
    order_id: Optional[int] = Query(None, description="采购订单ID筛选"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    inspect_status: Optional[str] = Query(None, description="质检状态筛选"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取收货记录列表（支持分页、搜索、筛选）
    """
    query = db.query(GoodsReceipt)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                GoodsReceipt.receipt_no.contains(keyword),
                GoodsReceipt.delivery_note_no.contains(keyword),
            )
        )
    
    # 采购订单筛选
    if order_id:
        query = query.filter(GoodsReceipt.order_id == order_id)
    
    # 供应商筛选
    if supplier_id:
        query = query.filter(GoodsReceipt.supplier_id == supplier_id)
    
    # 状态筛选
    if status:
        query = query.filter(GoodsReceipt.status == status)
    
    # 质检状态筛选
    if inspect_status:
        query = query.filter(GoodsReceipt.inspect_status == inspect_status)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    receipts = query.order_by(desc(GoodsReceipt.created_at)).offset(offset).limit(page_size).all()
    
    # 构建响应数据
    items = []
    for receipt in receipts:
        items.append({
            "id": receipt.id,
            "receipt_no": receipt.receipt_no,
            "order_id": receipt.order_id,
            "order_no": receipt.order.order_no if receipt.order else "",
            "supplier_name": receipt.supplier.supplier_name if receipt.supplier else "",
            "receipt_date": receipt.receipt_date,
            "receipt_type": receipt.receipt_type,
            "status": receipt.status,
            "inspect_status": receipt.inspect_status,
            "created_at": receipt.created_at,
        })
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/goods-receipts/", response_model=GoodsReceiptResponse)
def create_goods_receipt(
    *,
    db: Session = Depends(deps.get_db),
    receipt_in: GoodsReceiptCreate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    创建收货单
    """
    # 检查采购订单是否存在
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == receipt_in.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    # 生成收货单编号
    receipt_no = generate_receipt_no(db)
    
    # 创建收货单
    receipt = GoodsReceipt(
        receipt_no=receipt_no,
        order_id=receipt_in.order_id,
        supplier_id=order.supplier_id,
        receipt_date=receipt_in.receipt_date,
        receipt_type=receipt_in.receipt_type,
        delivery_note_no=receipt_in.delivery_note_no,
        logistics_company=receipt_in.logistics_company,
        tracking_no=receipt_in.tracking_no,
        status="PENDING",
        inspect_status="PENDING",
        remark=receipt_in.remark,
        created_by=current_user.id,
    )
    db.add(receipt)
    db.flush()
    
    # 创建收货明细
    for item_in in receipt_in.items:
        # 检查订单明细是否存在
        order_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == item_in.order_item_id).first()
        if not order_item:
            raise HTTPException(status_code=404, detail=f"订单明细ID {item_in.order_item_id} 不存在")
        
        # 检查订单明细是否属于该采购订单
        if order_item.order_id != receipt_in.order_id:
            raise HTTPException(status_code=400, detail="订单明细不属于该采购订单")
        
        # 检查收货数量是否超过订单数量
        total_received = order_item.received_qty or 0
        if total_received + (item_in.received_qty or item_in.delivery_qty) > order_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"物料 {order_item.material_code} 的收货数量超过订单数量"
            )
        
        # 实收数量默认为送货数量
        received_qty = item_in.received_qty if item_in.received_qty is not None else item_in.delivery_qty
        
        receipt_item = GoodsReceiptItem(
            receipt_id=receipt.id,
            order_item_id=item_in.order_item_id,
            material_code=order_item.material_code,
            material_name=order_item.material_name,
            delivery_qty=item_in.delivery_qty,
            received_qty=received_qty,
            remark=item_in.remark,
        )
        db.add(receipt_item)
        
        # 更新订单明细的已收货数量
        order_item.received_qty = (order_item.received_qty or 0) + received_qty
        if order_item.received_qty >= order_item.quantity:
            order_item.status = "RECEIVED"
        else:
            order_item.status = "PARTIAL_RECEIVED"
    
    # 更新采购订单的已收货金额
    order.received_amount = sum(
        (item.received_qty or 0) * (item.unit_price or 0)
        for item in order.items.all()
    )
    
    db.commit()
    db.refresh(receipt)
    
    # 返回收货单详情
    return get_goods_receipt_detail(db=db, receipt_id=receipt.id, current_user=current_user)


@router.get("/goods-receipts/{receipt_id}", response_model=GoodsReceiptResponse)
def get_goods_receipt_detail(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取收货单详情
    """
    receipt = db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="收货单不存在")
    
    # 获取收货明细
    items = []
    for item in receipt.items.all():
        items.append(GoodsReceiptItemResponse(
            id=item.id,
            material_code=item.material_code,
            material_name=item.material_name,
            delivery_qty=item.delivery_qty,
            received_qty=item.received_qty or 0,
            inspect_qty=item.inspect_qty or 0,
            qualified_qty=item.qualified_qty or 0,
            rejected_qty=item.rejected_qty or 0,
            inspect_result=item.inspect_result,
        ))
    
    return GoodsReceiptResponse(
        id=receipt.id,
        receipt_no=receipt.receipt_no,
        order_id=receipt.order_id,
        order_no=receipt.order.order_no if receipt.order else "",
        supplier_name=receipt.supplier.supplier_name if receipt.supplier else "",
        receipt_date=receipt.receipt_date,
        receipt_type=receipt.receipt_type,
        status=receipt.status,
        inspect_status=receipt.inspect_status,
        items=items,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
    )


@router.get("/goods-receipts/{receipt_id}/items", response_model=List[GoodsReceiptItemResponse])
def get_goods_receipt_items(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取收货单明细列表
    """
    receipt = db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="收货单不存在")
    
    items = []
    for item in receipt.items.all():
        items.append(GoodsReceiptItemResponse(
            id=item.id,
            material_code=item.material_code,
            material_name=item.material_name,
            delivery_qty=item.delivery_qty,
            received_qty=item.received_qty or 0,
            inspect_qty=item.inspect_qty or 0,
            qualified_qty=item.qualified_qty or 0,
            rejected_qty=item.rejected_qty or 0,
            inspect_result=item.inspect_result,
        ))
    
    return items


@router.put("/goods-receipts/{receipt_id}/receive", response_model=ResponseModel)
def update_receipt_status(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
    status: str = Query(..., description="状态：PENDING/RECEIVED/REJECTED"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    更新收货单状态
    """
    receipt = db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="收货单不存在")
    
    if status not in ["PENDING", "RECEIVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    receipt.status = status
    db.add(receipt)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="状态更新成功"
    )


@router.put("/purchase-order-items/{item_id}/receive", response_model=ResponseModel)
def update_order_item_receive_status(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    received_qty: Decimal = Query(..., description="已收货数量"),
    qualified_qty: Optional[Decimal] = Query(None, description="合格数量"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    更新采购订单明细的到货状态
    """
    order_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == item_id).first()
    if not order_item:
        raise HTTPException(status_code=404, detail="订单明细不存在")
    
    # 检查收货数量是否超过订单数量
    if received_qty > order_item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"收货数量 {received_qty} 超过订单数量 {order_item.quantity}"
        )
    
    # 更新收货数量
    order_item.received_qty = received_qty
    
    # 更新合格数量
    if qualified_qty is not None:
        if qualified_qty > received_qty:
            raise HTTPException(
                status_code=400,
                detail="合格数量不能超过收货数量"
            )
        order_item.qualified_qty = qualified_qty
        order_item.rejected_qty = received_qty - qualified_qty
    
    # 更新状态
    if received_qty >= order_item.quantity:
        order_item.status = "RECEIVED"
    elif received_qty > 0:
        order_item.status = "PARTIAL_RECEIVED"
    else:
        order_item.status = "PENDING"
    
    db.add(order_item)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="到货状态更新成功"
    )


@router.put("/goods-receipts/{receipt_id}/items/{item_id}/inspect", response_model=ResponseModel)
def update_receipt_item_inspect(
    *,
    db: Session = Depends(deps.get_db),
    receipt_id: int,
    item_id: int,
    inspect_qty: Decimal = Query(..., description="送检数量"),
    qualified_qty: Decimal = Query(..., description="合格数量"),
    rejected_qty: Optional[Decimal] = Query(None, description="不合格数量（自动计算）"),
    inspect_result: Optional[str] = Query(None, description="质检结果：QUALIFIED/UNQUALIFIED/PARTIAL"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    更新收货单明细的质检结果
    """
    from app.models.purchase import GoodsReceiptItem
    
    receipt_item = db.query(GoodsReceiptItem).filter(
        GoodsReceiptItem.id == item_id,
        GoodsReceiptItem.receipt_id == receipt_id
    ).first()
    
    if not receipt_item:
        raise HTTPException(status_code=404, detail="收货明细不存在")
    
    # 检查送检数量是否超过收货数量
    if inspect_qty > receipt_item.received_qty:
        raise HTTPException(
            status_code=400,
            detail=f"送检数量 {inspect_qty} 超过收货数量 {receipt_item.received_qty}"
        )
    
    # 计算不合格数量
    if rejected_qty is None:
        rejected_qty = inspect_qty - qualified_qty
    else:
        if qualified_qty + rejected_qty != inspect_qty:
            raise HTTPException(
                status_code=400,
                detail="合格数量 + 不合格数量必须等于送检数量"
            )
    
    if rejected_qty < 0:
        raise HTTPException(status_code=400, detail="不合格数量不能为负数")
    
    # 更新质检信息
    receipt_item.inspect_qty = inspect_qty
    receipt_item.qualified_qty = qualified_qty
    receipt_item.rejected_qty = rejected_qty
    
    # 自动判断质检结果
    if inspect_result is None:
        if qualified_qty == inspect_qty:
            inspect_result = "QUALIFIED"
        elif qualified_qty == 0:
            inspect_result = "UNQUALIFIED"
        else:
            inspect_result = "PARTIAL"
    
    receipt_item.inspect_result = inspect_result
    
    # 更新收货单的质检状态
    receipt = receipt_item.receipt
    all_items = receipt.items.all()
    all_inspected = all(item.inspect_qty > 0 for item in all_items)
    all_qualified = all(
        item.inspect_result == "QUALIFIED" 
        for item in all_items 
        if item.inspect_qty > 0
    )
    has_unqualified = any(
        item.inspect_result == "UNQUALIFIED" 
        for item in all_items 
        if item.inspect_qty > 0
    )
    
    if all_inspected:
        if all_qualified:
            receipt.inspect_status = "QUALIFIED"
        elif has_unqualified:
            receipt.inspect_status = "UNQUALIFIED"
        else:
            receipt.inspect_status = "PARTIAL"
    else:
        receipt.inspect_status = "INSPECTING"
    
    db.add(receipt_item)
    db.add(receipt)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="质检结果更新成功"
    )


# ==================== 采购申请 ====================

def generate_request_no(db: Session) -> str:
    """生成采购申请编号：PR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    # 查询今天最大的序号
    max_request = (
        db.query(PurchaseRequest)
        .filter(PurchaseRequest.request_no.like(f"PR-{today}-%"))
        .order_by(desc(PurchaseRequest.request_no))
        .first()
    )
    
    if max_request:
        # 提取序号并加1
        seq_str = max_request.request_no.split('-')[-1]
        seq = int(seq_str) + 1
    else:
        seq = 1
    
    return f"PR-{today}-{seq:03d}"


@router.get("/requests", response_model=PaginatedResponse[PurchaseRequestListResponse])
def read_purchase_requests(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（申请单号）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="设备ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取采购申请列表（支持分页、搜索、筛选）
    """
    query = db.query(PurchaseRequest)
    
    # 关键词搜索
    if keyword:
        query = query.filter(PurchaseRequest.request_no.contains(keyword))
    
    # 项目筛选
    if project_id:
        query = query.filter(PurchaseRequest.project_id == project_id)
    
    # 设备筛选
    if machine_id:
        query = query.filter(PurchaseRequest.machine_id == machine_id)
    
    # 状态筛选
    if status:
        query = query.filter(PurchaseRequest.status == status)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    requests = query.order_by(desc(PurchaseRequest.created_at)).offset(offset).limit(page_size).all()
    
    # 构建响应数据
    items = []
    for req in requests:
        item = PurchaseRequestListResponse(
            id=req.id,
            request_no=req.request_no,
            project_name=req.project.project_name if req.project else None,
            machine_name=req.machine.machine_code if req.machine else None,
            total_amount=req.total_amount or 0,
            required_date=req.required_date,
            status=req.status,
            requester_name=req.requester.username if req.requester else None,
            created_at=req.created_at,
        )
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/requests/{request_id}", response_model=PurchaseRequestResponse)
def read_purchase_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取采购申请详情
    """
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    
    # 获取明细
    items = []
    for item in request.items.all():
        items.append(PurchaseRequestItemResponse(
            id=item.id,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
            required_date=item.required_date,
            ordered_qty=item.ordered_qty,
            remark=item.remark,
        ))
    
    return PurchaseRequestResponse(
        id=request.id,
        request_no=request.request_no,
        project_id=request.project_id,
        project_name=request.project.project_name if request.project else None,
        machine_id=request.machine_id,
        machine_name=request.machine.machine_code if request.machine else None,
        request_type=request.request_type,
        request_reason=request.request_reason,
        required_date=request.required_date,
        total_amount=request.total_amount or 0,
        status=request.status,
        submitted_at=request.submitted_at,
        approved_by=request.approved_by,
        approved_at=request.approved_at,
        approval_note=request.approval_note,
        requested_by=request.requested_by,
        requested_at=request.requested_at,
        requester_name=request.requester.username if request.requester else None,
        approver_name=request.approver.username if request.approver else None,
        items=items,
        remark=request.remark,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


@router.post("/requests", response_model=PurchaseRequestResponse)
def create_purchase_request(
    *,
    db: Session = Depends(deps.get_db),
    request_in: PurchaseRequestCreate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    创建采购申请
    """
    # 检查项目是否存在
    if request_in.project_id:
        project = db.query(Project).filter(Project.id == request_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查设备是否存在
    if request_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == request_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="设备不存在")
    
    # 生成申请单号
    request_no = generate_request_no(db)
    
    # 创建申请
    request = PurchaseRequest(
        request_no=request_no,
        project_id=request_in.project_id,
        machine_id=request_in.machine_id,
        request_type=request_in.request_type,
        request_reason=request_in.request_reason,
        required_date=request_in.required_date,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(request)
    db.flush()
    
    # 创建申请明细
    total_amount = Decimal(0)
    
    for idx, item_in in enumerate(request_in.items, start=1):
        # 如果提供了物料ID，获取物料信息
        material = None
        if item_in.material_id:
            material = db.query(Material).filter(Material.id == item_in.material_id).first()
            if not material:
                raise HTTPException(status_code=404, detail=f"物料ID {item_in.material_id} 不存在")
        
        # 计算金额
        amount = item_in.quantity * item_in.unit_price
        
        item = PurchaseRequestItem(
            request_id=request.id,
            bom_item_id=item_in.bom_item_id,
            material_id=item_in.material_id,
            material_code=item_in.material_code,
            material_name=item_in.material_name,
            specification=item_in.specification,
            unit=item_in.unit,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            amount=amount,
            required_date=item_in.required_date,
            remark=item_in.remark,
        )
        db.add(item)
        
        total_amount += amount
    
    # 更新申请总金额
    request.total_amount = total_amount
    
    db.commit()
    db.refresh(request)
    
    # 返回申请详情
    return read_purchase_request(db=db, request_id=request.id, current_user=current_user)


@router.put("/requests/{request_id}", response_model=PurchaseRequestResponse)
def update_purchase_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    request_in: PurchaseRequestUpdate,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    更新采购申请（仅草稿状态可更新）
    """
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    
    # 只有草稿状态才能更新
    if request.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能更新")
    
    # 更新字段
    if request_in.request_reason is not None:
        request.request_reason = request_in.request_reason
    if request_in.required_date is not None:
        request.required_date = request_in.required_date
    if request_in.remark is not None:
        request.remark = request_in.remark
    
    db.commit()
    db.refresh(request)
    
    return read_purchase_request(db=db, request_id=request.id, current_user=current_user)


@router.put("/requests/{request_id}/submit", response_model=ResponseModel)
def submit_purchase_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    提交采购申请
    """
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    
    # 只有草稿状态才能提交
    if request.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能提交")
    
    # 检查是否有明细
    item_count = request.items.count()
    if item_count == 0:
        raise HTTPException(status_code=400, detail="申请必须至少包含一个物料明细")
    
    # 更新状态
    request.status = "SUBMITTED"
    request.submitted_at = datetime.now()
    request.requested_by = current_user.id
    request.requested_at = datetime.now()
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="采购申请已提交"
    )


@router.put("/requests/{request_id}/approve", response_model=ResponseModel)
def approve_purchase_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    approved: bool = Query(..., description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    审批采购申请
    """
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    
    # 只有已提交状态才能审批
    if request.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交状态的申请才能审批")
    
    # 更新状态
    if approved:
        request.status = "APPROVED"
    else:
        request.status = "REJECTED"
    
    request.approved_by = current_user.id
    request.approved_at = datetime.now()
    request.approval_note = approval_note
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="审批通过" if approved else "审批驳回"
    )


@router.delete("/requests/{request_id}", response_model=ResponseModel)
def delete_purchase_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    删除采购申请（仅草稿状态可删除）
    """
    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="采购申请不存在")
    
    # 只有草稿状态才能删除
    if request.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的申请才能删除")
    
    db.delete(request)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="采购申请已删除"
    )


# ==================== 从BOM生成采购订单 ====================

@router.post("/from-bom", response_model=ResponseModel)
def create_purchase_orders_from_bom(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int = Query(..., description="BOM ID"),
    supplier_id: Optional[int] = Query(None, description="默认供应商ID（可选）"),
    project_id: Optional[int] = Query(None, description="项目ID（可选，从BOM获取）"),
    create_orders: bool = Query(True, description="是否直接创建采购订单（False则只返回预览）"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    从BOM批量创建采购订单
    根据BOM明细中需要采购的物料，按供应商分组，批量创建采购订单
    """
    from app.models.material import BomHeader, BomItem, Material
    from collections import defaultdict
    
    # 获取BOM
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    
    # 使用BOM的项目ID，如果提供了project_id则使用提供的
    target_project_id = project_id or bom.project_id
    
    # 获取BOM明细中需要采购的物料
    bom_items = bom.items.filter(
        BomItem.source_type == "PURCHASE"
    ).all()
    
    if not bom_items:
        raise HTTPException(status_code=400, detail="BOM中没有需要采购的物料")
    
    # 按供应商分组物料
    supplier_items = defaultdict(list)
    
    for item in bom_items:
        # 确定供应商
        target_supplier_id = supplier_id
        if not target_supplier_id and item.supplier_id:
            target_supplier_id = item.supplier_id
        elif not target_supplier_id and item.material_id:
            # 尝试从物料获取默认供应商
            material = db.query(Material).filter(Material.id == item.material_id).first()
            if material and material.default_supplier_id:
                target_supplier_id = material.default_supplier_id
        
        if not target_supplier_id:
            # 如果没有供应商，使用默认供应商ID 0（表示未指定）
            target_supplier_id = 0
        
        supplier_items[target_supplier_id].append(item)
    
    # 生成采购订单预览
    purchase_orders_preview = []
    created_orders = []
    
    for supplier_id_key, items in supplier_items.items():
        if supplier_id_key == 0:
            # 跳过未指定供应商的物料
            continue
        
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id_key).first()
        if not supplier:
            continue
        
        # 构建订单明细
        order_items = []
        total_amount = Decimal(0)
        total_tax_amount = Decimal(0)
        total_amount_with_tax = Decimal(0)
        
        for idx, item in enumerate(items, start=1):
            # 计算未采购数量
            remaining_qty = item.quantity - (item.purchased_qty or 0)
            if remaining_qty <= 0:
                continue  # 跳过已完全采购的物料
            
            unit_price = item.unit_price or 0
            tax_rate = Decimal(13)  # 默认税率13%
            amount = remaining_qty * unit_price
            tax_amount = amount * tax_rate / 100
            amount_with_tax = amount + tax_amount
            
            total_amount += amount
            total_tax_amount += tax_amount
            total_amount_with_tax += amount_with_tax
            
            order_items.append({
                "item_no": idx,
                "material_id": item.material_id,
                "bom_item_id": item.id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "unit": item.unit or "件",
                "quantity": remaining_qty,
                "unit_price": unit_price,
                "tax_rate": tax_rate,
                "amount": amount,
                "tax_amount": tax_amount,
                "amount_with_tax": amount_with_tax,
                "required_date": item.required_date,
            })
        
        if not order_items:
            continue
        
        # 生成订单预览
        order_preview = {
            "supplier_id": supplier_id_key,
            "supplier_name": supplier.supplier_name,
            "project_id": target_project_id,
            "project_name": bom.project.project_name if bom.project else None,
            "order_type": "NORMAL",
            "order_title": f"{bom.bom_no} - {supplier.supplier_name}",
            "total_amount": float(total_amount),
            "tax_amount": float(total_tax_amount),
            "amount_with_tax": float(total_amount_with_tax),
            "item_count": len(order_items),
            "items": order_items,
        }
        purchase_orders_preview.append(order_preview)
        
        # 如果create_orders为True，创建采购订单
        if create_orders:
            # 生成订单编号
            order_no = generate_order_no(db)
            
            # 创建订单
            order = PurchaseOrder(
                order_no=order_no,
                supplier_id=supplier_id_key,
                project_id=target_project_id,
                order_type="NORMAL",
                order_title=order_preview["order_title"],
                required_date=bom.required_date if hasattr(bom, 'required_date') else None,
                order_date=date.today(),
                status="DRAFT",
                total_amount=total_amount,
                tax_amount=total_tax_amount,
                amount_with_tax=total_amount_with_tax,
                created_by=current_user.id,
            )
            db.add(order)
            db.flush()
            
            # 创建订单明细
            for item_data in order_items:
                order_item = PurchaseOrderItem(
                    order_id=order.id,
                    item_no=item_data["item_no"],
                    material_id=item_data["material_id"],
                    bom_item_id=item_data["bom_item_id"],
                    material_code=item_data["material_code"],
                    material_name=item_data["material_name"],
                    specification=item_data["specification"],
                    unit=item_data["unit"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    amount=item_data["amount"],
                    tax_rate=item_data["tax_rate"],
                    tax_amount=item_data["tax_amount"],
                    amount_with_tax=item_data["amount_with_tax"],
                    required_date=item_data["required_date"],
                    status="PENDING",
                )
                db.add(order_item)
            
            created_orders.append({
                "order_id": order.id,
                "order_no": order_no,
                "supplier_name": supplier.supplier_name,
                "total_amount": float(total_amount_with_tax),
            })
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"已生成{len(purchase_orders_preview)}个采购订单预览" if not create_orders else f"已创建{len(created_orders)}个采购订单",
        data={
            "bom_id": bom_id,
            "bom_no": bom.bom_no,
            "project_id": target_project_id,
            "preview": purchase_orders_preview,
            "created_orders": created_orders if create_orders else None,
            "summary": {
                "total_orders": len(purchase_orders_preview),
                "total_items": sum(len(order["items"]) for order in purchase_orders_preview),
                "total_amount": sum(order["total_amount"] for order in purchase_orders_preview),
                "total_amount_with_tax": sum(order["amount_with_tax"] for order in purchase_orders_preview),
            }
        }
    )

