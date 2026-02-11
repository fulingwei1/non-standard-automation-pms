# -*- coding: utf-8 -*-
"""
采购管理服务

从 purchase.py 拆分出来的业务逻辑
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.common.query_filters import apply_pagination
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)


class PurchaseService:
    """采购管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_purchase_orders(self, skip: int = 0, limit: int = 50,
                          project_id: Optional[int] = None,
                          supplier_id: Optional[int] = None,
                          status: Optional[str] = None) -> List[PurchaseOrder]:
        """获取采购订单列表"""
        # Note: items关系使用lazy='dynamic'，不支持selectinload
        query = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.project)
        )

        if project_id:
            query = query.filter(PurchaseOrder.project_id == project_id)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)

        return apply_pagination(query.order_by(PurchaseOrder.created_at.desc()), skip, limit).all()

    def get_purchase_order_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        """根据ID获取采购订单"""
        # Note: items关系使用lazy='dynamic'，不支持selectinload
        return self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.vendor),
            joinedload(PurchaseOrder.project)
        ).filter(PurchaseOrder.id == order_id).first()

    def create_purchase_order(self, order_data: Dict[str, Any]) -> PurchaseOrder:
        """创建采购订单"""
        purchase_order = PurchaseOrder(
            order_no=order_data.get('order_code') or order_data.get('order_no'),
            supplier_id=order_data.get('supplier_id'),
            project_id=order_data.get('project_id'),
            total_amount=order_data.get('total_amount'),
            order_date=order_data.get('order_date'),
            required_date=order_data.get('expected_date'),
            status='DRAFT'
        )

        self.db.add(purchase_order)
        self.db.flush()

        # 创建订单项
        items = order_data.get('items', [])
        for idx, item_data in enumerate(items):
            item = PurchaseOrderItem(
                order_id=purchase_order.id,
                item_no=idx + 1,
                material_id=item_data.get('material_id'),
                material_code=item_data.get('material_code', ''),
                material_name=item_data.get('material_name', ''),
                quantity=item_data.get('quantity'),
                unit_price=item_data.get('unit_price'),
                amount=item_data.get('total_amount') or item_data.get('amount', 0)
            )
            self.db.add(item)

        return purchase_order

    def update_purchase_order(self, order_id: int, update_data: Dict[str, Any]) -> Optional[PurchaseOrder]:
        """更新采购订单"""
        order = self.get_purchase_order_by_id(order_id)
        if not order:
            return None

        for key, value in update_data.items():
            if hasattr(order, key):
                setattr(order, key, value)

        return order

    def submit_purchase_order(self, order_id: int) -> bool:
        """提交采购订单"""
        order = self.get_purchase_order_by_id(order_id)
        if not order:
            return False

        order.status = 'SUBMITTED'
        order.submitted_at = datetime.now()
        return True

    def approve_purchase_order(self, order_id: int, approver_id: int) -> bool:
        """审批采购订单"""
        order = self.get_purchase_order_by_id(order_id)
        if not order:
            return False

        order.status = 'APPROVED'
        order.approved_at = datetime.now()
        order.approver_id = approver_id
        return True

    def get_goods_receipts(self, skip: int = 0, limit: int = 50,
                         order_id: Optional[int] = None,
                         status: Optional[str] = None) -> List[GoodsReceipt]:
        """获取收货记录列表"""
        query = self.db.query(GoodsReceipt).options(
            joinedload(GoodsReceipt.order)
        )

        if order_id:
            query = query.filter(GoodsReceipt.order_id == order_id)
        if status:
            query = query.filter(GoodsReceipt.status == status)

        return apply_pagination(query.order_by(GoodsReceipt.receipt_date.desc()), skip, limit).all()

    def create_goods_receipt(self, receipt_data: Dict[str, Any]) -> GoodsReceipt:
        """创建收货记录"""
        receipt = GoodsReceipt(
            receipt_no=receipt_data.get('receipt_no', f"GR-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            order_id=receipt_data.get('order_id'),
            supplier_id=receipt_data.get('supplier_id', 0),
            receipt_date=receipt_data.get('receipt_date'),
            status='COMPLETED'
        )

        self.db.add(receipt)
        self.db.flush()

        # 创建收货项
        items = receipt_data.get('items', [])
        for item_data in items:
            item = GoodsReceiptItem(
                receipt_id=receipt.id,
                order_item_id=item_data.get('order_item_id'),
                received_quantity=item_data.get('received_quantity'),
                qualified_quantity=item_data.get('qualified_quantity'),
                remark=item_data.get('remark')
            )
            self.db.add(item)

        return receipt

    def get_purchase_requests(self, skip: int = 0, limit: int = 50,
                           project_id: Optional[int] = None,
                           status: Optional[str] = None) -> List[PurchaseRequest]:
        """获取采购申请列表"""
        query = self.db.query(PurchaseRequest).options(
            joinedload(PurchaseRequest.project),
            joinedload(PurchaseRequest.requester)
        )

        if project_id:
            query = query.filter(PurchaseRequest.project_id == project_id)
        if status:
            query = query.filter(PurchaseRequest.status == status)

        return apply_pagination(query.order_by(PurchaseRequest.created_at.desc()), skip, limit).all()

    def create_purchase_request(self, request_data: Dict[str, Any]) -> PurchaseRequest:
        """创建采购申请"""
        request = PurchaseRequest(
            request_no=request_data.get('request_code') or request_data.get('request_no'),
            project_id=request_data.get('project_id'),
            requested_by=request_data.get('requester_id'),
            request_reason=request_data.get('description') or request_data.get('title'),
            total_amount=request_data.get('total_amount'),
            required_date=request_data.get('expected_date'),
            status='DRAFT'
        )

        self.db.add(request)
        self.db.flush()

        # 创建申请项
        items = request_data.get('items', [])
        for item_data in items:
            item = PurchaseRequestItem(
                request_id=request.id,
                material_id=item_data.get('material_id'),
                quantity=item_data.get('quantity'),
                unit_price=item_data.get('unit_price'),
                total_amount=item_data.get('total_amount')
            )
            self.db.add(item)

        return request

    def generate_orders_from_request(self, request_id: int, supplier_id: int) -> bool:
        """从采购申请生成订单"""
        request = self.db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
        if not request:
            return False

        # 创建采购订单
        order = PurchaseOrder(
            order_no=f'PO-{datetime.now().strftime("%Y%m%d")}-{request.id:04d}',
            supplier_id=supplier_id,
            project_id=request.project_id,
            total_amount=request.total_amount,
            source_request_id=request_id,
            status='DRAFT'
        )

        self.db.add(order)
        self.db.flush()

        # 复制申请项到订单项
        for request_item in request.items:
            order_item = PurchaseOrderItem(
                order_id=order.id,
                material_id=request_item.material_id,
                quantity=request_item.quantity,
                unit_price=request_item.unit_price,
                total_amount=request_item.total_amount,
                request_item_id=request_item.id
            )
            self.db.add(order_item)

        request.status = 'ORDER_GENERATED'
        return True
