# -*- coding: utf-8 -*-
"""库存更新服务"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialStock
from app.models.material import Material


class InsufficientStockError(Exception):
    """库存不足异常"""
    pass


class StockUpdateService:
    """库存更新核心逻辑"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def update_stock(
        self,
        material_id: int,
        quantity: Decimal,
        transaction_type: str,
        location: str,
        batch_number: Optional[str] = None,
        unit_price: Decimal = Decimal(0),
        **kwargs,
    ) -> MaterialStock:
        """更新库存（基于交易类型）"""
        stock = (
            self.db.query(MaterialStock)
            .filter(
                MaterialStock.tenant_id == self.tenant_id,
                MaterialStock.material_id == material_id,
                MaterialStock.location == location,
                MaterialStock.batch_number == (batch_number or ""),
            )
            .first()
        )

        material = self.db.query(Material).get(material_id)

        if not stock:
            stock = MaterialStock(
                tenant_id=self.tenant_id,
                material_id=material_id,
                material_code=material.material_code,
                material_name=material.material_name,
                location=location,
                batch_number=batch_number or "",
                quantity=Decimal(0),
                available_quantity=Decimal(0),
                reserved_quantity=Decimal(0),
                unit=material.unit,
                unit_price=Decimal(0),
                total_value=Decimal(0),
            )
            self.db.add(stock)

        if transaction_type in ["PURCHASE_IN", "TRANSFER_IN", "RETURN"]:
            stock.quantity += quantity
            stock.available_quantity += quantity
            stock.last_in_date = datetime.now()
            if transaction_type == "PURCHASE_IN" and unit_price > 0:
                old_value = stock.quantity * stock.unit_price
                new_value = quantity * unit_price
                total_quantity = stock.quantity
                if total_quantity > 0:
                    stock.unit_price = (old_value + new_value) / total_quantity

        elif transaction_type in ["ISSUE", "SCRAP"]:
            if stock.available_quantity < quantity:
                raise InsufficientStockError(
                    f"库存不足: 物料{material.material_code}, "
                    f"需要{quantity}, 可用{stock.available_quantity}"
                )
            stock.quantity -= quantity
            stock.available_quantity -= quantity
            stock.last_out_date = datetime.now()

        elif transaction_type == "ADJUST":
            stock.quantity += quantity
            stock.available_quantity += quantity

        stock.total_value = stock.quantity * stock.unit_price
        stock.last_update = datetime.now()
        stock.status = self._calculate_stock_status(stock)
        self.db.flush()
        return stock

    def _calculate_stock_status(self, stock: MaterialStock) -> str:
        """计算库存状态"""
        if stock.expire_date and stock.expire_date < date.today():
            return "EXPIRED"
        elif stock.quantity <= 0:
            return "EMPTY"
        else:
            material = self.db.query(Material).get(stock.material_id)
            if material and material.safety_stock > 0:
                if stock.quantity < material.safety_stock:
                    return "LOW"
        return "NORMAL"
