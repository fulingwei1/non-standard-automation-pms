# -*- coding: utf-8 -*-
"""入库操作服务"""
from datetime import date
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.services.inventory.transaction_service import TransactionService
from app.services.inventory.stock_update_service import StockUpdateService


class InboundService:
    """入库操作"""

    def __init__(self, db: Session, tenant_id: int = 1):
        self.db = db
        self.tenant_id = tenant_id
        self._tx = TransactionService(db, tenant_id)
        self._stock = StockUpdateService(db, tenant_id)

    def purchase_in(
        self,
        material_id: int,
        quantity: Decimal,
        unit_price: Decimal,
        location: str,
        batch_number: Optional[str] = None,
        purchase_order_id: Optional[int] = None,
        purchase_order_no: Optional[str] = None,
        operator_id: Optional[int] = None,
        production_date: Optional[date] = None,
        expire_date: Optional[date] = None,
        remark: Optional[str] = None,
    ) -> Dict:
        """采购入库"""
        transaction = self._tx.create_transaction(
            material_id=material_id,
            transaction_type="PURCHASE_IN",
            quantity=quantity,
            unit_price=unit_price,
            target_location=location,
            batch_number=batch_number,
            related_order_id=purchase_order_id,
            related_order_type="PURCHASE_ORDER",
            related_order_no=purchase_order_no,
            operator_id=operator_id,
            remark=remark,
        )
        stock = self._stock.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type="PURCHASE_IN",
            location=location,
            batch_number=batch_number,
            unit_price=unit_price,
        )
        if production_date:
            stock.production_date = production_date
        if expire_date:
            stock.expire_date = expire_date
        self.db.commit()
        return {
            "transaction": transaction,
            "stock": stock,
            "message": f"入库成功: {quantity} {stock.unit}",
        }
