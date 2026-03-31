# -*- coding: utf-8 -*-
"""库存查询服务"""
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialStock


class StockQueryService:
    """库存查询"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def get_stock(
        self, material_id: int, location: Optional[str] = None, batch_number: Optional[str] = None
    ) -> List[MaterialStock]:
        """查询库存"""
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id, MaterialStock.material_id == material_id
        )
        if location:
            query = query.filter(MaterialStock.location == location)
        if batch_number:
            query = query.filter(MaterialStock.batch_number == batch_number)
        return query.all()

    def get_available_quantity(self, material_id: int, location: Optional[str] = None) -> Decimal:
        """获取可用库存数量"""
        query = self.db.query(func.sum(MaterialStock.available_quantity)).filter(
            MaterialStock.tenant_id == self.tenant_id, MaterialStock.material_id == material_id
        )
        if location:
            query = query.filter(MaterialStock.location == location)
        result = query.scalar()
        return Decimal(result or 0)

    def get_total_quantity(self, material_id: int) -> Decimal:
        """获取总库存数量"""
        result = (
            self.db.query(func.sum(MaterialStock.quantity))
            .filter(
                MaterialStock.tenant_id == self.tenant_id, MaterialStock.material_id == material_id
            )
            .scalar()
        )
        return Decimal(result or 0)

    def get_all_stocks(
        self, location: Optional[str] = None, status: Optional[str] = None, limit: int = 100
    ) -> List[MaterialStock]:
        """查询所有库存"""
        query = self.db.query(MaterialStock).filter(MaterialStock.tenant_id == self.tenant_id)
        if location:
            query = query.filter(MaterialStock.location == location)
        if status:
            query = query.filter(MaterialStock.status == status)
        return query.limit(limit).all()
