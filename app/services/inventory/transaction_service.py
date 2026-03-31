# -*- coding: utf-8 -*-
"""交易记录服务"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialTransaction
from app.models.material import Material


class TransactionService:
    """交易记录管理"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def create_transaction(
        self,
        material_id: int,
        transaction_type: str,
        quantity: Decimal,
        unit_price: Decimal = Decimal(0),
        source_location: Optional[str] = None,
        target_location: Optional[str] = None,
        batch_number: Optional[str] = None,
        related_order_id: Optional[int] = None,
        related_order_type: Optional[str] = None,
        related_order_no: Optional[str] = None,
        operator_id: Optional[int] = None,
        remark: Optional[str] = None,
        cost_method: str = "WEIGHTED_AVG",
    ) -> MaterialTransaction:
        """创建交易记录"""
        material = self.db.query(Material).get(material_id)
        if not material:
            raise ValueError(f"物料不存在: {material_id}")

        transaction = MaterialTransaction(
            tenant_id=self.tenant_id,
            material_id=material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            transaction_type=transaction_type,
            quantity=quantity,
            unit=material.unit,
            unit_price=unit_price,
            total_amount=quantity * unit_price,
            source_location=source_location,
            target_location=target_location,
            batch_number=batch_number,
            related_order_id=related_order_id,
            related_order_type=related_order_type,
            related_order_no=related_order_no,
            transaction_date=datetime.now(),
            operator_id=operator_id,
            remark=remark,
            cost_method=cost_method,
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def get_transactions(
        self,
        material_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[MaterialTransaction]:
        """查询交易记录"""
        query = self.db.query(MaterialTransaction).filter(
            MaterialTransaction.tenant_id == self.tenant_id
        )
        if material_id:
            query = query.filter(MaterialTransaction.material_id == material_id)
        if transaction_type:
            query = query.filter(MaterialTransaction.transaction_type == transaction_type)
        if start_date:
            query = query.filter(MaterialTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(MaterialTransaction.transaction_date <= end_date)
        return query.order_by(MaterialTransaction.transaction_date.desc()).limit(limit).all()
