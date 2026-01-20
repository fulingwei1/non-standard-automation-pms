# -*- coding: utf-8 -*-
"""
趋势和对比分析模块
提供月度趋势数据功能
"""

from datetime import date, timedelta
from typing import Any, Dict, List


class TrendsComparisonMixin:
    """趋势和对比分析功能混入类"""

    def get_monthly_trend(
        self,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """获取月度趋势数据

        Returns:
            近N个月的浪费趋势
        """
        results = []
        today = date.today()

        for i in range(months - 1, -1, -1):
            # 计算月份起止日期
            month_start = date(today.year, today.month, 1) - timedelta(days=30 * i)
            month_start = date(month_start.year, month_start.month, 1)

            if month_start.month == 12:
                month_end = date(month_start.year + 1, 1, 1)
            else:
                month_end = date(month_start.year, month_start.month + 1, 1)

            # 计算该月数据
            month_data = self.calculate_waste_by_period(month_start, month_end)

            results.append({
                'month': month_start.strftime('%Y-%m'),
                'total_leads': month_data['total_leads'],
                'won_leads': month_data['won_leads'],
                'lost_leads': month_data['lost_leads'],
                'win_rate': month_data['win_rate'],
                'total_hours': month_data['total_investment_hours'],
                'wasted_hours': month_data['wasted_hours'],
                'waste_rate': month_data['waste_rate'],
                'wasted_cost': float(month_data['wasted_cost'])
            })

        return results
