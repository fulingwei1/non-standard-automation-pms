# -*- coding: utf-8 -*-
"""
采购分析服务 - 成本趋势分析
"""
from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.purchase import PurchaseOrder


class CostTrendAnalyzer:
    """成本趋势分析器"""

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
