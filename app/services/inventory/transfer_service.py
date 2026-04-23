# -*- coding: utf-8 -*-
"""库存转移服务"""
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.services.inventory.transaction_service import TransactionService
from app.services.inventory.stock_update_service import StockUpdateService


class TransferService:
    """库存转移"""

    def __init__(self, db: Session, tenant_id: int = 0):
        self.db = db
        self.tenant_id = tenant_id
        self._tx = TransactionService(db, tenant_id)
        self._stock = StockUpdateService(db, tenant_id)

    def transfer_stock(
        self,
        material_id: int,
        quantity: Decimal,
        from_location: str,
        to_location: str,
        batch_number: Optional[str] = None,
        operator_id: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> Dict:
        """库存转移"""
        out_transaction = self._tx.create_transaction(
            material_id=material_id,
            transaction_type="ISSUE",
            quantity=quantity,
            source_location=from_location,
            batch_number=batch_number,
            operator_id=operator_id,
            remark=f"转移至 {to_location} - {remark or ''}",
        )
        from_stock = self._stock.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type="ISSUE",
            location=from_location,
            batch_number=batch_number,
        )
        in_transaction = self._tx.create_transaction(
            material_id=material_id,
            transaction_type="TRANSFER_IN",
            quantity=quantity,
            unit_price=from_stock.unit_price,
            source_location=from_location,
            target_location=to_location,
            batch_number=batch_number,
            operator_id=operator_id,
            remark=f"从 {from_location} 转入 - {remark or ''}",
        )
        to_stock = self._stock.update_stock(
            material_id=material_id,
            quantity=quantity,
            transaction_type="TRANSFER_IN",
            location=to_location,
            batch_number=batch_number,
            unit_price=from_stock.unit_price,
        )
        self.db.commit()
        return {
            "out_transaction": out_transaction,
            "in_transaction": in_transaction,
            "from_stock": from_stock,
            "to_stock": to_stock,
            "message": f"转移成功: {from_location} -> {to_location}, {quantity}",
        }
