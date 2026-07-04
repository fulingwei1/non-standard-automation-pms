# -*- coding: utf-8 -*-
"""
采购管理服务

从 purchase.py 拆分出来的业务逻辑
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
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
from app.services.purchase.order_state_machine import transition_purchase_order_status


class PurchaseService:
    """采购管理服务"""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _decimal_or_zero(value) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    def get_purchase_orders(
        self,
        skip: int = 0,
        limit: int = 50,
        project_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[PurchaseOrder]:
        """获取采购订单列表"""
        # Note: items关系使用lazy='dynamic'，不支持selectinload
        query = self.db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.vendor), joinedload(PurchaseOrder.project)
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
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.vendor), joinedload(PurchaseOrder.project))
            .filter(PurchaseOrder.id == order_id)
            .first()
        )

    def create_purchase_order(self, order_data: Dict[str, Any]) -> PurchaseOrder:
        """创建采购订单"""
        purchase_order = PurchaseOrder(
            order_no=order_data.get("order_code") or order_data.get("order_no"),
            supplier_id=order_data.get("supplier_id"),
            project_id=order_data.get("project_id"),
            total_amount=order_data.get("total_amount"),
            order_date=order_data.get("order_date"),
            required_date=order_data.get("expected_date"),
            status="DRAFT",
        )

        self.db.add(purchase_order)
        self.db.flush()

        # 创建订单项
        items = order_data.get("items", [])
        for idx, item_data in enumerate(items):
            item = PurchaseOrderItem(
                order_id=purchase_order.id,
                item_no=idx + 1,
                material_id=item_data.get("material_id"),
                material_code=item_data.get("material_code", ""),
                material_name=item_data.get("material_name", ""),
                quantity=item_data.get("quantity"),
                unit_price=item_data.get("unit_price"),
                amount=item_data.get("total_amount") or item_data.get("amount", 0),
            )
            self.db.add(item)

        return purchase_order

    def update_purchase_order(
        self, order_id: int, update_data: Dict[str, Any]
    ) -> Optional[PurchaseOrder]:
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

        transition_purchase_order_status(order, "SUBMITTED")
        order.submitted_at = datetime.now()
        return True

    def approve_purchase_order(self, order_id: int, approver_id: int) -> bool:
        """审批采购订单"""
        order = self.get_purchase_order_by_id(order_id)
        if not order:
            return False

        transition_purchase_order_status(order, "APPROVED")
        order.approved_at = datetime.now()
        order.approver_id = approver_id
        return True

    def get_goods_receipts(
        self,
        skip: int = 0,
        limit: int = 50,
        order_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[GoodsReceipt]:
        """获取收货记录列表"""
        query = self.db.query(GoodsReceipt).options(joinedload(GoodsReceipt.order))

        if order_id:
            query = query.filter(GoodsReceipt.order_id == order_id)
        if status:
            query = query.filter(GoodsReceipt.status == status)

        return apply_pagination(query.order_by(GoodsReceipt.receipt_date.desc()), skip, limit).all()

    def create_goods_receipt(self, receipt_data: Dict[str, Any]) -> GoodsReceipt:
        """创建收货记录"""
        receipt = GoodsReceipt(
            receipt_no=receipt_data.get(
                "receipt_no", f"GR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            ),
            order_id=receipt_data.get("order_id"),
            supplier_id=receipt_data.get("supplier_id", 0),
            receipt_date=receipt_data.get("receipt_date"),
            status="COMPLETED",
        )

        self.db.add(receipt)
        self.db.flush()

        # 创建收货项
        items = receipt_data.get("items", [])
        for item_data in items:
            item = GoodsReceiptItem(
                receipt_id=receipt.id,
                order_item_id=item_data.get("order_item_id"),
                material_code=item_data.get("material_code", ""),
                material_name=item_data.get("material_name", ""),
                delivery_qty=item_data.get("delivery_qty") or item_data.get("received_quantity"),
                received_qty=item_data.get("received_qty") or item_data.get("received_quantity"),
                qualified_qty=item_data.get("qualified_qty") or item_data.get("qualified_quantity"),
                remark=item_data.get("remark"),
            )
            self.db.add(item)

        return receipt

    def get_purchase_requests(
        self,
        skip: int = 0,
        limit: int = 50,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[PurchaseRequest]:
        """获取采购申请列表"""
        query = self.db.query(PurchaseRequest).options(
            joinedload(PurchaseRequest.project), joinedload(PurchaseRequest.requester)
        )

        if project_id:
            query = query.filter(PurchaseRequest.project_id == project_id)
        if status:
            query = query.filter(PurchaseRequest.status == status)

        return apply_pagination(
            query.order_by(PurchaseRequest.created_at.desc()), skip, limit
        ).all()

    def create_purchase_request(self, request_data: Dict[str, Any]) -> PurchaseRequest:
        """创建采购申请"""
        request = PurchaseRequest(
            request_no=request_data.get("request_code") or request_data.get("request_no"),
            project_id=request_data.get("project_id"),
            requested_by=request_data.get("requester_id"),
            request_reason=request_data.get("description") or request_data.get("title"),
            total_amount=request_data.get("total_amount"),
            required_date=request_data.get("expected_date"),
            status="DRAFT",
        )

        self.db.add(request)
        self.db.flush()

        # 创建申请项
        items = request_data.get("items", [])
        for item_data in items:
            item = PurchaseRequestItem(
                request_id=request.id,
                material_id=item_data.get("material_id"),
                material_code=item_data.get("material_code", ""),
                material_name=item_data.get("material_name", ""),
                specification=item_data.get("specification"),
                unit=item_data.get("unit", "件"),
                quantity=item_data.get("quantity"),
                unit_price=item_data.get("unit_price"),
                amount=item_data.get("amount") or item_data.get("total_amount"),
            )
            self.db.add(item)

        return request

    def generate_orders_from_request(self, request_id: int, supplier_id: int) -> bool:
        """从采购申请生成订单"""
        request = self.db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
        if not request:
            return False

        if request.status != "APPROVED":
            raise HTTPException(status_code=400, detail="只有已审批的采购申请才能生成采购订单")

        existing_order = (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.source_request_id == request_id)
            .first()
        )
        if existing_order:
            raise HTTPException(status_code=400, detail="该采购申请已生成采购订单，不能重复生成")

        request_items = request.items.all() if hasattr(request.items, "all") else list(request.items)
        if not request_items:
            raise HTTPException(status_code=400, detail="采购申请没有明细")

        # 创建采购订单
        order = PurchaseOrder(
            order_no=f'PO-{datetime.now().strftime("%Y%m%d")}-{request.id:04d}',
            supplier_id=supplier_id,
            project_id=request.project_id,
            total_amount=request.total_amount,
            source_request_id=request_id,
            status="DRAFT",
        )

        self.db.add(order)
        self.db.flush()

        # 复制申请项到订单项
        for index, request_item in enumerate(request_items, start=1):
            quantity = self._decimal_or_zero(request_item.quantity)
            order_item = PurchaseOrderItem(
                order_id=order.id,
                item_no=index,
                material_id=request_item.material_id,
                bom_item_id=getattr(request_item, "bom_item_id", None),
                material_code=request_item.material_code,
                material_name=request_item.material_name,
                specification=getattr(request_item, "specification", None),
                unit=getattr(request_item, "unit", None) or "件",
                quantity=quantity,
                unit_price=request_item.unit_price,
                amount=getattr(request_item, "amount", None) or 0,
                required_date=getattr(request_item, "required_date", None),
            )
            self.db.add(order_item)
            request_item.ordered_qty = self._decimal_or_zero(
                getattr(request_item, "ordered_qty", 0)
            ) + quantity

        request.status = "ORDER_GENERATED"
        request.auto_po_created = all(
            (item.ordered_qty or 0) >= (item.quantity or 0) for item in request_items
        )
        if request.auto_po_created:
            request.auto_po_created_at = datetime.now()
        return True
