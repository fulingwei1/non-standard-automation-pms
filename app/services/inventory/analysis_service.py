# -*- coding: utf-8 -*-
"""库存分析服务"""
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.inventory_tracking import MaterialStock, MaterialTransaction


class AnalysisService:
    """库存分析（周转率、库龄）"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def calculate_turnover_rate(
        self,
        material_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """计算库存周转率"""
        if not start_date:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.now()

        query = self.db.query(MaterialTransaction).filter(
            MaterialTransaction.tenant_id == self.tenant_id,
            MaterialTransaction.transaction_type == "ISSUE",
            MaterialTransaction.transaction_date >= start_date,
            MaterialTransaction.transaction_date <= end_date,
        )
        if material_id:
            query = query.filter(MaterialTransaction.material_id == material_id)

        total_issue_value = sum((t.total_amount or 0) for t in query.all())

        stock_query = self.db.query(MaterialStock).filter(MaterialStock.tenant_id == self.tenant_id)
        if material_id:
            stock_query = stock_query.filter(MaterialStock.material_id == material_id)

        avg_stock_value = sum((s.total_value or 0) for s in stock_query.all())
        turnover_rate = float(total_issue_value / avg_stock_value) if avg_stock_value > 0 else 0

        return {
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "total_issue_value": float(total_issue_value),
            "avg_stock_value": float(avg_stock_value),
            "turnover_rate": turnover_rate,
            "turnover_days": int(365 / turnover_rate) if turnover_rate > 0 else 0,
        }

    def analyze_aging(self, location: Optional[str] = None) -> Dict:
        """库龄分析"""
        query = self.db.query(MaterialStock).filter(
            MaterialStock.tenant_id == self.tenant_id, MaterialStock.quantity > 0
        )
        if location:
            query = query.filter(MaterialStock.location == location)

        stocks = query.all()
        results = []

        aging_summary = {
            "0-30天": {"count": 0, "total_quantity": 0, "total_value": 0},
            "31-90天": {"count": 0, "total_quantity": 0, "total_value": 0},
            "91-180天": {"count": 0, "total_quantity": 0, "total_value": 0},
            "181-365天": {"count": 0, "total_quantity": 0, "total_value": 0},
            "365天以上": {"count": 0, "total_quantity": 0, "total_value": 0},
        }

        for stock in stocks:
            if not stock.last_in_date:
                continue

            days_in_stock = (datetime.now() - stock.last_in_date).days

            if days_in_stock <= 30:
                aging_category = "0-30天"
            elif days_in_stock <= 90:
                aging_category = "31-90天"
            elif days_in_stock <= 180:
                aging_category = "91-180天"
            elif days_in_stock <= 365:
                aging_category = "181-365天"
            else:
                aging_category = "365天以上"

            quantity = float(stock.quantity or 0)
            total_value = float(stock.total_value or 0)

            aging_summary[aging_category]["count"] += 1
            aging_summary[aging_category]["total_quantity"] += quantity
            aging_summary[aging_category]["total_value"] += total_value

            results.append(
                {
                    "material_id": stock.material_id,
                    "material_code": stock.material_code,
                    "material_name": stock.material_name,
                    "location": stock.location,
                    "batch_number": stock.batch_number,
                    "quantity": quantity,
                    "unit_price": float(stock.unit_price or 0),
                    "total_value": total_value,
                    "last_in_date": stock.last_in_date.isoformat() if stock.last_in_date else None,
                    "days_in_stock": days_in_stock,
                    "aging_category": aging_category,
                }
            )

        return {"aging_summary": aging_summary, "details": results}
