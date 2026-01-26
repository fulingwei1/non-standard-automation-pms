# -*- coding: utf-8 -*-
"""
报告生成模块
提供资源浪费综合报告生成功能
"""

from datetime import date, datetime
from typing import Any, Dict


class ReportGenerationMixin:
    """报告生成功能混入类"""

    def generate_waste_report(
        self,
        period: str  # 'YYYY' or 'YYYY-MM'
    ) -> Dict[str, Any]:
        """生成资源浪费综合报告

        Returns:
            完整的资源浪费分析报告
        """
        # 解析周期
        if len(period) == 7:  # YYYY-MM
            year, month = int(period[:4]), int(period[5:7])
            start_date = date(year, month, 1)
            end_date = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
        else:  # YYYY
            year = int(period)
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)

        # 1. 总体统计
        overall_stats = self.calculate_waste_by_period(start_date, end_date)

        # 2. 销售人员排行（Top 10 浪费最多）
        top_wasters = self.get_salesperson_waste_ranking(start_date, end_date, limit=10)

        # 3. 失败模式分析
        failure_patterns = self.analyze_failure_patterns(start_date, end_date)

        # 4. 月度趋势（如果是年度报告）
        monthly_trend = []
        if len(period) == 4:  # 年度
            monthly_trend = self.get_monthly_trend(12)

        # 5. 部门对比
        department_comparison = self.get_department_comparison(start_date, end_date)

        return {
            'report_period': period,
            'generated_at': datetime.now().isoformat(),
            'overall_statistics': overall_stats,
            'top_resource_wasters': top_wasters,
            'failure_pattern_analysis': failure_patterns,
            'monthly_trend': monthly_trend,
            'department_comparison': department_comparison,
            'summary': {
                'total_wasted_cost': overall_stats['wasted_cost'],
                'waste_rate': overall_stats['waste_rate'],
                'top_loss_reason': max(
                    overall_stats['loss_reasons'].items(),
                    key=lambda x: x[1]
                )[0] if overall_stats['loss_reasons'] else 'N/A',
                'key_recommendation': failure_patterns['recommendations'][0]
                if failure_patterns['recommendations'] else '暂无建议'
            }
        }
