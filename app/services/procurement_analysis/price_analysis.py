# -*- coding: utf-8 -*-
"""
采购分析服务 - 价格波动分析
"""
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.material import Supplier


class PriceAnalyzer:
    """价格波动分析器"""

    @staticmethod
    def get_price_fluctuation_data(
        db: Session,
        material_code: Optional[str] = None,
        category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取物料价格波动数据

        查询同一物料在不同时间、不同供应商的采购价格
        """
        # 构建查询 - 从采购订单明细获取历史价格
        query = db.query(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            PurchaseOrderItem.unit_price,
            PurchaseOrder.order_date,
            Supplier.supplier_name,
            Supplier.id.label('supplier_id'),
            MaterialCategory.category_name,
            Material.standard_price
        ).join(
            PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id
        ).join(
            Supplier, PurchaseOrder.supplier_id == Supplier.id
        ).outerjoin(
            Material, Material.material_code == PurchaseOrderItem.material_code
        ).outerjoin(
            MaterialCategory, Material.category_id == MaterialCategory.id
        ).filter(
            PurchaseOrder.status.in_(['APPROVED', 'CONFIRMED', 'PARTIAL_RECEIVED', 'RECEIVED'])
        )

        # 筛选条件
        if material_code:
            query = query.filter(PurchaseOrderItem.material_code == material_code)
        if category_id:
            query = query.filter(Material.category_id == category_id)
        if start_date:
            query = query.filter(PurchaseOrder.order_date >= start_date)
        if end_date:
            query = query.filter(PurchaseOrder.order_date <= end_date)

        results = query.order_by(
            PurchaseOrderItem.material_code,
            PurchaseOrder.order_date.desc()
        ).limit(1000).all()

        # 按物料分组统计价格
        material_prices = {}
        for row in results:
            code = row.material_code
            if code not in material_prices:
                material_prices[code] = {
                    'material_code': code,
                    'material_name': row.material_name,
                    'category_name': row.category_name,
                    'standard_price': float(row.standard_price or 0) if row.standard_price else None,
                    'price_history': [],
                    'suppliers': set(),
                    'min_price': None,
                    'max_price': None,
                    'avg_price': 0,
                    'price_volatility': 0,
                    'latest_price': None
                }

            price = float(row.unit_price or 0)
            material_prices[code]['price_history'].append({
                'date': row.order_date.isoformat() if row.order_date else None,
                'price': price,
                'supplier': row.supplier_name,
                'supplier_id': row.supplier_id
            })
            material_prices[code]['suppliers'].add(row.supplier_name)

            # 更新最新价格
            if not material_prices[code]['latest_price']:
                material_prices[code]['latest_price'] = price

        # 计算统计指标
        for code, data in material_prices.items():
            prices = [p['price'] for p in data['price_history']]
            if prices:
                data['min_price'] = min(prices)
                data['max_price'] = max(prices)
                data['avg_price'] = round(sum(prices) / len(prices), 4)
                data['suppliers'] = list(data['suppliers'])
                # 价格波动率 = (最高价 - 最低价) / 平均价
                if data['avg_price'] > 0:
                    data['price_volatility'] = round(
                        (data['max_price'] - data['min_price']) / data['avg_price'] * 100, 2
                    )
            data['price_history'] = data['price_history'][:20]  # 限制返回条数

        # 转换为列表并按波动率排序
        materials_list = list(material_prices.values())
        materials_list.sort(key=lambda x: x['price_volatility'], reverse=True)

        return {
            'materials': materials_list[:limit],
            'summary': {
                'total_materials': len(material_prices),
                'high_volatility_count': sum(1 for m in material_prices.values() if m['price_volatility'] > 20),
                'avg_volatility': round(sum(m['price_volatility'] for m in material_prices.values()) / len(material_prices), 2) if material_prices else 0
            }
        }
