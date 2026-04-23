# -*- coding: utf-8 -*-
"""出库操作服务（领料 + 退料）"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialStock
from app.services.inventory.stock_update_service import InsufficientStockError, StockUpdateService
from app.services.inventory.transaction_service import TransactionService
from app.services.inventory.reservation_service import ReservationService


class OutboundService:
    """出库操作"""

    def __init__(self, db: Session, tenant_id: Optional[int] = None):
        self.db = db
        self.tenant_id = tenant_id
        self._tx = TransactionService(db, tenant_id) if tenant_id is not None else None
        self._stock = StockUpdateService(db, tenant_id) if tenant_id is not None else None
        self._reservation = ReservationService(db, tenant_id) if tenant_id is not None else None

    def issue_material(
        self,
        material_id: int,
        quantity: Decimal,
        location: str,
        work_order_id: Optional[int] = None,
        work_order_no: Optional[str] = None,
        project_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        remark: Optional[str] = None,
        cost_method: str = "FIFO",
    ) -> Dict:
        """领料出库"""
        if reservation_id:
            self._reservation._release_reservation(reservation_id, quantity)

        stocks = self._select_stock_for_issue(material_id, location, quantity, cost_method)
        transactions = []
        remaining = quantity

        for stock, issue_qty in stocks:
            transaction = self._tx.create_transaction(
                material_id=material_id,
                transaction_type="ISSUE",
                quantity=issue_qty,
                unit_price=stock.unit_price,
                source_location=location,
                batch_number=stock.batch_number,
                related_order_id=work_order_id,
                related_order_type="WORK_ORDER",
                related_order_no=work_order_no,
                operator_id=operator_id,
                remark=remark,
                cost_method=cost_method,
            )
            transactions.append(transaction)
            self._stock.update_stock(
                material_id=material_id,
                quantity=issue_qty,
                transaction_type="ISSUE",
                location=location,
                batch_number=stock.batch_number,
            )
            remaining -= issue_qty
            if remaining <= 0:
                break

        self.db.commit()
        return {
            "transactions": transactions,
            "total_quantity": quantity,
            "total_cost": sum(t.total_amount for t in transactions),
            "message": f"领料成功: {quantity}",
        }

    def return_material(
        self,
        material_id: int,
        quantity: Decimal,
        location: str,
        batch_number: Optional[str] = None,
        work_order_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> Dict:
        """退料入库"""
        if not batch_number:
            batch_number = f"RETURN-{datetime.now().strftime('%Y%m%d')}"

        transaction = self._tx.create_transaction(
            material_id=material_id,
            transaction_type="RETURN",
            quantity=quantity,
            target_location=location,
            batch_number=batch_number,
            related_order_id=work_order_id,
            related_order_type="WORK_ORDER",
            operator_id=operator_id,
            remark=remark,
        )
        stock = self._stock.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type="RETURN",
            location=location,
            batch_number=batch_number,
        )
        self.db.commit()
        return {"transaction": transaction, "stock": stock, "message": f"退料成功: {quantity}"}

    def _select_stock_for_issue(
        self, material_id: int, location: str, quantity: Decimal, cost_method: str
    ) -> List[tuple]:
        """根据成本核算方法选择库存"""
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id,
            MaterialStock.material_id == material_id,
            MaterialStock.location == location,
            MaterialStock.available_quantity > 0,
        )
        if cost_method == "FIFO":
            query = query.order_by(MaterialStock.last_in_date.asc())
        elif cost_method == "LIFO":
            query = query.order_by(MaterialStock.last_in_date.desc())
        else:
            query = query.order_by(MaterialStock.id.asc())

        stocks = query.all()
        if not stocks:
            raise InsufficientStockError(f"物料 {material_id} 在位置 {location} 无可用库存")

        total_available = sum(s.available_quantity for s in stocks)
        if total_available < quantity:
            raise InsufficientStockError(f"库存不足: 需要 {quantity}, 可用 {total_available}")

        result = []
        remaining = quantity
        for stock in stocks:
            if remaining <= 0:
                break
            issue_qty = min(stock.available_quantity, remaining)
            result.append((stock, issue_qty))
            remaining -= issue_qty
        return result
