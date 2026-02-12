# -*- coding: utf-8 -*-
"""
库存分析服务
封装库存相关的数据分析逻辑
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)


class InventoryAnalysisService:
    """库存分析服务类"""

    @staticmethod
    def get_turnover_rate_data(
        db: Session,
        start_date: date,
        end_date: date,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取库存周转率数据

        周转率 = 本期消耗金额 / 平均库存价值
        周转天数 = 365 / 周转率
        """
        # 计算当前库存总价值
        query = db.query(
            Material.id,
            Material.material_code,
            Material.material_name,
            MaterialCategory.id.label('category_id'),
            MaterialCategory.category_name,
            Material.current_stock,
            Material.standard_price,
            Material.unit
        ).outerjoin(
            MaterialCategory, Material.category_id == MaterialCategory.id
        ).filter(
            Material.is_active
        )

        if category_id:
            query = query.filter(Material.category_id == category_id)

        materials = query.all()

        # 计算库存总价值
        total_inventory_value = 0
        category_inventory = {}

        for m in materials:
            stock = float(m.current_stock or 0)
            price = float(m.standard_price or 0)
            value = stock * price
            total_inventory_value += value

            cat_name = m.category_name or '未分类'
            if cat_name not in category_inventory:
                category_inventory[cat_name] = {'value': 0, 'count': 0}
            category_inventory[cat_name]['value'] += value
            category_inventory[cat_name]['count'] += 1

        # 计算本期消耗金额（从收货单合格数量推算）
        # 实际应从销售成本或领料记录获取
        consumption_query = db.query(
            func.sum(GoodsReceiptItem.qualified_qty * GoodsReceiptItem.inspect_qty / 100).label('qty')
        ).join(
            GoodsReceipt, GoodsReceiptItem.receipt_id == GoodsReceipt.id
        ).filter(
            GoodsReceipt.receipt_date >= start_date,
            GoodsReceipt.receipt_date <= end_date,
            GoodsReceipt.inspect_status == 'COMPLETED'
        )

        total_consumption_qty = float(consumption_query.scalar() or 0)
        # 使用平均价格估算消耗金额
        avg_price = total_inventory_value / sum(float(m.current_stock or 0) for m in materials) if materials else 0
        total_consumption = total_consumption_qty * avg_price

        # 计算周转率
        turnover_rate = (total_consumption / total_inventory_value * 100) if total_inventory_value > 0 else 0
        turnover_days = (365 / turnover_rate) if turnover_rate > 0 else 0

        # 按分类统计
        category_list = []
        for cat_name, data in category_inventory.items():
            category_list.append({
                'category_name': cat_name,
                'inventory_value': round(data['value'], 2),
                'material_count': data['count'],
                'value_percentage': round((data['value'] / total_inventory_value * 100) if total_inventory_value > 0 else 0, 2)
            })

        category_list.sort(key=lambda x: x['inventory_value'], reverse=True)

        return {
            'summary': {
                'total_inventory_value': round(total_inventory_value, 2),
                'total_materials': len(materials),
                'total_consumption': round(total_consumption, 2),
                'turnover_rate': round(turnover_rate, 2),
                'turnover_days': round(turnover_days, 1)
            },
            'category_breakdown': category_list
        }

    @staticmethod
    def get_stale_materials_data(
        db: Session,
        threshold_days: int = 90,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取呆滞物料数据

        库存 > 0 且 N 天无变动
        """
        date.today() - timedelta(days=threshold_days)

        # 查询有库存的物料
        query = db.query(
            Material.id,
            Material.material_code,
            Material.material_name,
            MaterialCategory.category_name,
            Material.current_stock,
            Material.standard_price,
            Material.updated_at,
            Material.unit
        ).outerjoin(
            MaterialCategory, Material.category_id == MaterialCategory.id
        ).filter(
            Material.current_stock > 0,
            Material.is_active
        )

        if category_id:
            query = query.filter(Material.category_id == category_id)

        materials = query.all()

        stale_materials = []
        age_distribution = {'30天以内': 0, '30-60天': 0, '60-90天': 0, '90天以上': 0}
        total_stale_value = 0

        for m in materials:
            # 计算库龄 (使用 updated_at 作为最近变动时间)
            if m.updated_at:
                days_since_update = (date.today() - m.updated_at.date()).days
            else:
                days_since_update = 999  # 无更新记录视为长期呆滞

            inventory_value = float(m.current_stock or 0) * float(m.standard_price or 0)

            # 统计库龄分布
            if days_since_update < 30:
                age_distribution['30天以内'] += inventory_value
            elif days_since_update < 60:
                age_distribution['30-60天'] += inventory_value
            elif days_since_update < 90:
                age_distribution['60-90天'] += inventory_value
            else:
                age_distribution['90天以上'] += inventory_value

            # 判断是否呆滞
            if days_since_update >= threshold_days:
                total_stale_value += inventory_value
                stale_materials.append({
                    'material_id': m.id,
                    'material_code': m.material_code,
                    'material_name': m.material_name,
                    'category_name': m.category_name,
                    'current_stock': float(m.current_stock),
                    'unit': m.unit,
                    'inventory_value': round(inventory_value, 2),
                    'last_activity': m.updated_at.isoformat() if m.updated_at else None,
                    'stale_days': days_since_update
                })

        # 按库存金额排序
        stale_materials.sort(key=lambda x: x['inventory_value'], reverse=True)

        # 创建age_distribution列表
        age_dist_list = [
            {'age_range': k, 'value': round(v, 2)}
            for k, v in age_distribution.items()
        ]

        return {
            'stale_materials': stale_materials,
            'age_distribution': age_dist_list,
            'summary': {
                'stale_count': len(stale_materials),
                'stale_value': round(total_stale_value, 2),
                'threshold_days': threshold_days,
                'total_value_with_stock': round(sum(d['value'] for d in age_dist_list), 2)
            }
        }

    @staticmethod
    def get_safety_stock_compliance_data(
        db: Session,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取安全库存达标率数据
        """
        query = db.query(
            Material.id,
            Material.material_code,
            Material.material_name,
            MaterialCategory.category_name,
            Material.current_stock,
            Material.safety_stock,
            Material.unit
        ).outerjoin(
            MaterialCategory, Material.category_id == MaterialCategory.id
        ).filter(
            Material.is_active
        )

        if category_id:
            query = query.filter(Material.category_id == category_id)

        materials = query.all()

        # 分类统计
        stats = {
            'total_materials': len(materials),
            'compliant': 0,        # current_stock >= safety_stock
            'warning': 0,          # 0 < current_stock < safety_stock
            'out_of_stock': 0,     # current_stock = 0
            'no_safety_stock_set': 0,  # 未设置安全库存
            'compliant_rate': 0
        }

        compliant_materials = []
        warning_materials = []
        out_of_stock_materials = []

        for m in materials:
            current = float(m.current_stock or 0)
            safety = float(m.safety_stock or 0)

            material_info = {
                'material_id': m.id,
                'material_code': m.material_code,
                'material_name': m.material_name,
                'category_name': m.category_name,
                'current_stock': current,
                'safety_stock': safety,
                'unit': m.unit,
                'shortage_qty': max(0, safety - current) if current < safety else 0
            }

            if safety == 0:
                stats['no_safety_stock_set'] += 1
            elif current >= safety:
                stats['compliant'] += 1
                if safety > 0:  # 只记录有设置安全库存的
                    compliant_materials.append(material_info)
            elif current > 0:
                stats['warning'] += 1
                warning_materials.append(material_info)
            else:
                stats['out_of_stock'] += 1
                out_of_stock_materials.append(material_info)

        # 计算达标率（排除未设置安全库存的物料）
        materials_with_safety_stock = stats['total_materials'] - stats['no_safety_stock_set']
        stats['compliant_rate'] = round(
            (stats['compliant'] / materials_with_safety_stock * 100) if materials_with_safety_stock > 0 else 0, 2
        )

        # 按缺货程度排序
        warning_materials.sort(key=lambda x: x['shortage_qty'], reverse=True)
        out_of_stock_materials.sort(key=lambda x: x['safety_stock'], reverse=True)

        return {
            'summary': stats,
            'compliant_materials': compliant_materials[:20],
            'warning_materials': warning_materials[:50],
            'out_of_stock_materials': out_of_stock_materials[:50]
        }

    @staticmethod
    def get_abc_analysis_data(
        db: Session,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        获取物料ABC分类数据

        按采购金额累计占比分类:
        - A类: 累计70% (高价值)
        - B类: 累计20% (中价值)
        - C类: 累计10% (低价值)
        """
        # 统计各物料的采购金额
        query = db.query(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            MaterialCategory.category_name,
            func.sum(PurchaseOrderItem.amount).label('total_amount'),
            func.count(PurchaseOrderItem.id).label('order_count')
        ).join(
            PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id
        ).outerjoin(
            Material, Material.material_code == PurchaseOrderItem.material_code
        ).outerjoin(
            MaterialCategory, Material.category_id == MaterialCategory.id
        ).filter(
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status.in_(['APPROVED', 'CONFIRMED', 'PARTIAL_RECEIVED', 'RECEIVED'])
        ).group_by(
            PurchaseOrderItem.material_code,
            PurchaseOrderItem.material_name,
            MaterialCategory.category_name
        )

        results = query.all()

        if not results:
            return {
                'abc_materials': [],
                'abc_summary': {'A': {'count': 0, 'amount_percent': 0, 'count_percent': 0},
                               'B': {'count': 0, 'amount_percent': 0, 'count_percent': 0},
                               'C': {'count': 0, 'amount_percent': 0, 'count_percent': 0}},
                'total_materials': 0,
                'total_amount': 0
            }

        # 计算总金额
        total_amount = sum(float(r.total_amount or 0) for r in results)

        # 按金额降序排序并分类
        sorted_results = sorted(results, key=lambda x: float(x.total_amount or 0), reverse=True)

        abc_materials = []
        cumulative_percent = 0
        a_count = b_count = c_count = 0

        for r in sorted_results:
            amount = float(r.total_amount or 0)
            percent = (amount / total_amount * 100) if total_amount > 0 else 0
            cumulative_percent += percent

            # 确定ABC分类
            if cumulative_percent <= 70:
                abc_class = 'A'
                a_count += 1
            elif cumulative_percent <= 90:
                abc_class = 'B'
                b_count += 1
            else:
                abc_class = 'C'
                c_count += 1

            abc_materials.append({
                'material_code': r.material_code,
                'material_name': r.material_name,
                'category_name': r.category_name,
                'total_amount': round(amount, 2),
                'amount_percent': round(percent, 2),
                'cumulative_percent': round(cumulative_percent, 2),
                'abc_class': abc_class,
                'order_count': r.order_count
            })

        # 统计各分类汇总
        total_count = len(abc_materials)
        abc_summary = {
            'A': {'count': a_count, 'amount_percent': 0, 'count_percent': 0},
            'B': {'count': b_count, 'amount_percent': 0, 'count_percent': 0},
            'C': {'count': c_count, 'amount_percent': 0, 'count_percent': 0}
        }

        for m in abc_materials:
            abc_summary[m['abc_class']]['amount_percent'] += m['amount_percent']

        for cls in ['A', 'B', 'C']:
            if total_count > 0:
                abc_summary[cls]['count_percent'] = round(abc_summary[cls]['count'] / total_count * 100, 2)
            abc_summary[cls]['amount_percent'] = round(abc_summary[cls]['amount_percent'], 2)

        return {
            'abc_materials': abc_materials[:100],
            'abc_summary': abc_summary,
            'total_materials': total_count,
            'total_amount': round(total_amount, 2)
        }

    @staticmethod
    def get_cost_occupancy_data(
        db: Session,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取库存成本占用数据
        """
        # 按分类统计库存价值
        query = db.query(
            MaterialCategory.id.label('category_id'),
            MaterialCategory.category_name,
            func.sum(Material.current_stock * Material.standard_price).label('inventory_value'),
            func.count(Material.id).label('material_count')
        ).outerjoin(
            Material, MaterialCategory.id == Material.category_id
        ).filter(
            Material.is_active
        ).group_by(
            MaterialCategory.id,
            MaterialCategory.category_name
        )

        if category_id:
            query = query.filter(MaterialCategory.id == category_id)

        results = query.all()

        total_value = sum(float(r.inventory_value or 0) for r in results)

        category_occupancy = []
        for r in results:
            value = float(r.inventory_value or 0)
            category_occupancy.append({
                'category_id': r.category_id,
                'category_name': r.category_name or '未分类',
                'inventory_value': round(value, 2),
                'material_count': r.material_count,
                'value_percentage': round((value / total_value * 100) if total_value > 0 else 0, 2)
            })

        category_occupancy.sort(key=lambda x: x['inventory_value'], reverse=True)

        # 获取高库存占用物料TOP榜
        top_materials_query = db.query(
            Material.material_code,
            Material.material_name,
            MaterialCategory.category_name,
            (Material.current_stock * Material.standard_price).label('inventory_value'),
            Material.current_stock,
            Material.unit
        ).outerjoin(
            MaterialCategory, Material.category_id == MaterialCategory.id
        ).filter(
            Material.is_active,
            Material.current_stock > 0
        ).order_by(
            (Material.current_stock * Material.standard_price).desc()
        ).limit(50)

        top_materials = []
        for m in top_materials_query.all():
            top_materials.append({
                'material_code': m.material_code,
                'material_name': m.material_name,
                'category_name': m.category_name,
                'inventory_value': float(m.inventory_value or 0),
                'current_stock': float(m.current_stock or 0),
                'unit': m.unit
            })

        return {
            'category_occupancy': category_occupancy,
            'top_materials': top_materials,
            'summary': {
                'total_inventory_value': round(total_value, 2),
                'total_categories': len(results)
            }
        }


# 创建单例
inventory_analysis_service = InventoryAnalysisService()
