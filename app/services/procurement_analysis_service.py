# -*- coding: utf-8 -*-
"""
采购分析服务
封装采购相关的数据分析逻辑
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, extract, func, or_
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory, MaterialSupplier, Supplier
from app.models.project import Project
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
)


class ProcurementAnalysisService:
    """采购分析服务类"""

    @staticmethod
    def get_cost_trend_data(
        db: Session,
        start_date: date,
        end_date: date,
        group_by: str = "month",
        category_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取采购成本趋势数据

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            group_by: 分组方式 (month/quarter/year)
            category_id: 物料分类ID
            project_id: 项目ID

        Returns:
            趋势数据字典
        """
        # 构建基础查询
        query = db.query(
            PurchaseOrder
        ).filter(
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date,
            PurchaseOrder.status.in_(['APPROVED', 'CONFIRMED', 'PARTIAL_RECEIVED', 'RECEIVED'])
        )

        # 项目筛选
        if project_id:
            query = query.filter(PurchaseOrder.project_id == project_id)

        # 获取所有符合条件的订单
        orders = query.all()

        # 按时间段分组统计
        trend_data = []
        current = start_date
        period_num = 1

        while current <= end_date:
            # 确定当前周期结束日期
            if group_by == "month":
                period_end = date(current.year, current.month + 1, 1) - timedelta(days=1) if current.month < 12 else date(current.year, 12, 31)
                period_key = f"{current.year}-{current.month:02d}"
                next_current = date(current.year, current.month + 1, 1) if current.month < 12 else date(current.year + 1, 1, 1)
            elif group_by == "quarter":
                quarter = (current.month - 1) // 3 + 1
                period_end = date(current.year, quarter * 3 + 1, 1) - timedelta(days=1)
                period_key = f"{current.year}-Q{quarter}"
                next_current = date(current.year, quarter * 3 + 1, 1) if quarter < 4 else date(current.year + 1, 1, 1)
            else:  # year
                period_end = date(current.year, 12, 31)
                period_key = str(current.year)
                next_current = date(current.year + 1, 1, 1)

            # 统计当前周期
            period_orders = [o for o in orders if current <= o.order_date <= min(period_end, end_date)]
            total_amount = sum(float(o.amount_with_tax or 0) for o in period_orders)
            order_count = len(period_orders)

            trend_data.append({
                'period': period_key,
                'amount': round(total_amount, 2),
                'order_count': order_count,
                'avg_amount': round(total_amount / order_count, 2) if order_count > 0 else 0
            })

            current = next_current
            period_num += 1

        # 计算环比增长率
        for i in range(len(trend_data)):
            if i > 0:
                prev_amount = trend_data[i - 1]['amount']
                if prev_amount > 0:
                    trend_data[i]['mom_rate'] = round(
                        (trend_data[i]['amount'] - prev_amount) / prev_amount * 100, 2
                    )
                else:
                    trend_data[i]['mom_rate'] = 0
            else:
                trend_data[i]['mom_rate'] = 0

        # 汇总统计
        total_amount = sum(d['amount'] for d in trend_data)

        return {
            'summary': {
                'total_amount': round(total_amount, 2),
                'total_orders': sum(d['order_count'] for d in trend_data),
                'avg_monthly_amount': round(total_amount / len(trend_data), 2) if trend_data else 0,
                'max_month_amount': max(d['amount'] for d in trend_data) if trend_data else 0,
                'min_month_amount': min(d['amount'] for d in trend_data) if trend_data else 0
            },
            'trend_data': trend_data
        }

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

    @staticmethod
    def get_delivery_performance_data(
        db: Session,
        start_date: date,
        end_date: date,
        supplier_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取供应商交期准时率数据

        对比 promised_date 和 actual_receipt_date
        """
        # 查询收货单和订单
        query = db.query(
            Supplier.id.label('supplier_id'),
            Supplier.supplier_name,
            Supplier.supplier_code,
            GoodsReceipt.id.label('receipt_id'),
            GoodsReceipt.receipt_date,
            GoodsReceipt.receipt_no,
            PurchaseOrder.promised_date,
            PurchaseOrder.order_no,
            PurchaseOrder.id.label('order_id')
        ).join(
            PurchaseOrder, GoodsReceipt.order_id == PurchaseOrder.id
        ).join(
            Supplier, GoodsReceipt.supplier_id == Supplier.id
        ).filter(
            GoodsReceipt.receipt_date >= start_date,
            GoodsReceipt.receipt_date <= end_date
            # 注释：实际数据库中没有status列，使用inspection_status代替
            # GoodsReceipt.status == 'COMPLETED'
        )

        if supplier_id:
            query = query.filter(Supplier.id == supplier_id)

        results = query.all()

        # 按供应商统计
        supplier_stats = {}
        delayed_orders = []

        for row in results:
            sid = row.supplier_id
            if sid not in supplier_stats:
                supplier_stats[sid] = {
                    'supplier_id': sid,
                    'supplier_name': row.supplier_name,
                    'supplier_code': row.supplier_code,
                    'total_deliveries': 0,
                    'on_time_deliveries': 0,
                    'delayed_deliveries': 0,
                    'total_delay_days': 0
                }

            supplier_stats[sid]['total_deliveries'] += 1

            # 计算是否准时
            delay_days = 0
            if row.promised_date and row.receipt_date:
                delay_days = (row.receipt_date - row.promised_date).days
                if delay_days <= 0:
                    supplier_stats[sid]['on_time_deliveries'] += 1
                else:
                    supplier_stats[sid]['delayed_deliveries'] += 1
                    supplier_stats[sid]['total_delay_days'] += delay_days

                    delayed_orders.append({
                        'order_no': row.order_no,
                        'receipt_no': row.receipt_no,
                        'promised_date': row.promised_date.isoformat(),
                        'actual_date': row.receipt_date.isoformat(),
                        'delay_days': delay_days,
                        'supplier_name': row.supplier_name
                    })

        # 计算准时率和平均延期天数
        performance_list = []
        for sid, stats in supplier_stats.items():
            total = stats['total_deliveries']
            on_time_rate = (stats['on_time_deliveries'] / total * 100) if total > 0 else 0

            # 计算该供应商平均延期天数
            supplier_delays = [d['delay_days'] for d in delayed_orders if d.get('supplier_id') == sid]
            avg_delay = sum(supplier_delays) / len(supplier_delays) if supplier_delays else 0

            performance_list.append({
                'supplier_id': sid,
                'supplier_name': stats['supplier_name'],
                'supplier_code': stats['supplier_code'],
                'total_deliveries': stats['total_deliveries'],
                'on_time_deliveries': stats['on_time_deliveries'],
                'delayed_deliveries': stats['delayed_deliveries'],
                'on_time_rate': round(on_time_rate, 2),
                'avg_delay_days': round(avg_delay, 1)
            })

        # 按准时率排序
        performance_list.sort(key=lambda x: x['on_time_rate'], reverse=True)

        return {
            'supplier_performance': performance_list,
            'delayed_orders': delayed_orders[:50],  # 返回前50条延期记录
            'summary': {
                'total_suppliers': len(performance_list),
                'avg_on_time_rate': round(sum(p['on_time_rate'] for p in performance_list) / len(performance_list), 2) if performance_list else 0,
                'total_delayed_orders': len(delayed_orders)
            }
        }

    @staticmethod
    def get_request_efficiency_data(
        db: Session,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        获取采购申请处理时效数据

        申请提交到订单创建的时间差
        """
        # 查询采购申请
        query = db.query(
            PurchaseRequest.id,
            PurchaseRequest.request_no,
            PurchaseRequest.requested_at,
            PurchaseRequest.status,
            PurchaseRequest.total_amount,
            PurchaseRequest.source_type,
            func.min(PurchaseOrder.created_at).label('order_created_at')
        ).outerjoin(
            PurchaseOrder, PurchaseRequest.id == PurchaseOrder.source_request_id
        ).filter(
            PurchaseRequest.requested_at >= start_date,
            PurchaseRequest.requested_at <= end_date
        ).group_by(
            PurchaseRequest.id
        )

        results = query.all()

        efficiency_data = []
        pending_count = 0
        processed_count = 0
        total_processing_hours = 0

        for row in results:
            requested_at = row.requested_at
            order_created_at = row.order_created_at

            if order_created_at:
                # 已处理
                processing_hours = (order_created_at - requested_at).total_seconds() / 3600
                total_processing_hours += processing_hours
                processed_count += 1

                efficiency_data.append({
                    'request_no': row.request_no,
                    'requested_at': requested_at.isoformat() if requested_at else None,
                    'order_created_at': order_created_at.isoformat() if order_created_at else None,
                    'processing_hours': round(processing_hours, 2),
                    'processing_days': round(processing_hours / 24, 1),
                    'status': row.status,
                    'amount': float(row.total_amount or 0)
                })
            else:
                # 未处理
                pending_hours = (datetime.now() - requested_at).total_seconds() / 3600
                pending_count += 1

                efficiency_data.append({
                    'request_no': row.request_no,
                    'requested_at': requested_at.isoformat() if requested_at else None,
                    'order_created_at': None,
                    'processing_hours': round(pending_hours, 2),
                    'processing_days': round(pending_hours / 24, 1),
                    'status': row.status,
                    'amount': float(row.total_amount or 0),
                    'is_pending': True
                })

        # 按处理时长排序
        efficiency_data.sort(key=lambda x: x['processing_hours'], reverse=True)

        # 计算统计数据
        avg_processing_hours = total_processing_hours / processed_count if processed_count > 0 else 0
        processed_within_24h = sum(1 for e in efficiency_data if not e.get('is_pending') and e['processing_hours'] <= 24)
        processed_within_48h = sum(1 for e in efficiency_data if not e.get('is_pending') and e['processing_hours'] <= 48)

        return {
            'efficiency_data': efficiency_data[:50],
            'summary': {
                'total_requests': len(results),
                'processed_count': processed_count,
                'pending_count': pending_count,
                'avg_processing_hours': round(avg_processing_hours, 2),
                'avg_processing_days': round(avg_processing_hours / 24, 1),
                'processed_within_24h': processed_within_24h,
                'processed_within_48h': processed_within_48h,
                'within_24h_rate': round(processed_within_24h / processed_count * 100, 2) if processed_count > 0 else 0
            }
        }

    @staticmethod
    def get_quality_rate_data(
        db: Session,
        start_date: date,
        end_date: date,
        supplier_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取物料质量合格率数据

        qualified_qty / (qualified_qty + rejected_qty)
        """
        # 查询收货明细
        query = db.query(
            Supplier.id.label('supplier_id'),
            Supplier.supplier_name,
            GoodsReceiptItem.material_code,
            GoodsReceiptItem.material_name,
            func.sum(GoodsReceiptItem.qualified_qty).label('total_qualified'),
            func.sum(GoodsReceiptItem.rejected_qty).label('total_rejected'),
            # 使用received_qty作为total_inspected（实际数据库中没有inspect_qty列）
            func.sum(GoodsReceiptItem.received_qty).label('total_inspected')
        ).join(
            GoodsReceipt, GoodsReceiptItem.receipt_id == GoodsReceipt.id
        ).join(
            PurchaseOrder, GoodsReceipt.order_id == PurchaseOrder.id
        ).join(
            Supplier, PurchaseOrder.supplier_id == Supplier.id
        ).filter(
            GoodsReceipt.receipt_date >= start_date,
            GoodsReceipt.receipt_date <= end_date
            # 注释：实际数据库中是inspection_status而不是inspect_status
            # GoodsReceipt.inspect_status == 'COMPLETED'
        )

        if supplier_id:
            query = query.filter(Supplier.id == supplier_id)

        results = query.group_by(
            Supplier.id, Supplier.supplier_name,
            GoodsReceiptItem.material_code, GoodsReceiptItem.material_name
        ).all()

        # 按供应商汇总
        supplier_quality = {}
        for row in results:
            sid = row.supplier_id
            if sid not in supplier_quality:
                supplier_quality[sid] = {
                    'supplier_id': sid,
                    'supplier_name': row.supplier_name,
                    'materials': []
                }

            qualified = float(row.total_qualified or 0)
            rejected = float(row.total_rejected or 0)
            total = qualified + rejected
            pass_rate = (qualified / total * 100) if total > 0 else 100

            supplier_quality[sid]['materials'].append({
                'material_code': row.material_code,
                'material_name': row.material_name,
                'qualified_qty': qualified,
                'rejected_qty': rejected,
                'total_qty': total,
                'pass_rate': round(pass_rate, 2)
            })

        # 计算供应商综合合格率
        quality_list = []
        for sid, data in supplier_quality.items():
            total_qualified = sum(m['qualified_qty'] for m in data['materials'])
            total_rejected = sum(m['rejected_qty'] for m in data['materials'])
            total = total_qualified + total_rejected
            overall_rate = (total_qualified / total * 100) if total > 0 else 100

            quality_list.append({
                'supplier_id': sid,
                'supplier_name': data['supplier_name'],
                'materials': data['materials'],
                'total_qualified': total_qualified,
                'total_rejected': total_rejected,
                'total_qty': total,
                'overall_pass_rate': round(overall_rate, 2),
                'material_count': len(data['materials'])
            })

        quality_list.sort(key=lambda x: x['overall_pass_rate'], reverse=True)

        return {
            'supplier_quality': quality_list,
            'summary': {
                'total_suppliers': len(quality_list),
                'avg_pass_rate': round(sum(q['overall_pass_rate'] for q in quality_list) / len(quality_list), 2) if quality_list else 0,
                'high_quality_suppliers': sum(1 for q in quality_list if q['overall_pass_rate'] >= 98),
                'low_quality_suppliers': sum(1 for q in quality_list if q['overall_pass_rate'] < 90)
            }
        }


# 创建单例
procurement_analysis_service = ProcurementAnalysisService()
