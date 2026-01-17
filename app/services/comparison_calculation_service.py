# -*- coding: utf-8 -*-
"""
对比计算服务
计算环比（与上月对比）和同比（与去年同期对比）
"""
from calendar import monthrange
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.metric_calculation_service import MetricCalculationService


class ComparisonCalculationService:
    """对比计算服务"""

    def __init__(self, db: Session):
        self.db = db
        self.metric_service = MetricCalculationService(db)

    def calculate_mom_comparison(
        self,
        metric_code: str,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        计算环比（Month-over-Month，与上月对比）

        Args:
            metric_code: 指标编码
            year: 当前年份
            month: 当前月份

        Returns:
            对比结果
        """
        # 计算当前月周期
        period_start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        period_end = date(year, month, last_day)

        # 计算上月周期
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1

        prev_period_start = date(prev_year, prev_month, 1)
        _, prev_last_day = monthrange(prev_year, prev_month)
        prev_period_end = date(prev_year, prev_month, prev_last_day)

        # 计算当前月指标值
        current_result = self.metric_service.calculate_metric(metric_code, period_start, period_end)
        current_value = current_result.get('value', 0)

        # 计算上月指标值
        prev_result = self.metric_service.calculate_metric(metric_code, prev_period_start, prev_period_end)
        prev_value = prev_result.get('value', 0)

        # 计算变化
        change = current_value - prev_value
        change_rate = (change / prev_value * 100) if prev_value != 0 else (100 if current_value > 0 else 0)

        return {
            "metric_code": metric_code,
            "metric_name": current_result.get('metric_name'),
            "current_period": f"{year}-{month:02d}",
            "previous_period": f"{prev_year}-{prev_month:02d}",
            "current_value": current_value,
            "previous_value": prev_value,
            "change": change,
            "change_rate": change_rate,
            "change_rate_formatted": f"{change_rate:+.2f}%",
            "is_increase": change > 0,
            "is_decrease": change < 0,
            "unit": current_result.get('unit', ''),
            "format_type": current_result.get('format_type', 'NUMBER')
        }

    def calculate_yoy_comparison(
        self,
        metric_code: str,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        计算同比（Year-over-Year，与去年同期对比）

        Args:
            metric_code: 指标编码
            year: 当前年份
            month: 当前月份

        Returns:
            对比结果
        """
        # 计算当前月周期
        period_start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        period_end = date(year, month, last_day)

        # 计算去年同期周期
        prev_year = year - 1
        prev_period_start = date(prev_year, month, 1)
        _, prev_last_day = monthrange(prev_year, month)
        prev_period_end = date(prev_year, month, prev_last_day)

        # 计算当前月指标值
        current_result = self.metric_service.calculate_metric(metric_code, period_start, period_end)
        current_value = current_result.get('value', 0)

        # 计算去年同期指标值
        prev_result = self.metric_service.calculate_metric(metric_code, prev_period_start, prev_period_end)
        prev_value = prev_result.get('value', 0)

        # 计算变化
        change = current_value - prev_value
        change_rate = (change / prev_value * 100) if prev_value != 0 else (100 if current_value > 0 else 0)

        return {
            "metric_code": metric_code,
            "metric_name": current_result.get('metric_name'),
            "current_period": f"{year}-{month:02d}",
            "previous_period": f"{prev_year}-{month:02d}",
            "current_value": current_value,
            "previous_value": prev_value,
            "change": change,
            "change_rate": change_rate,
            "change_rate_formatted": f"{change_rate:+.2f}%",
            "is_increase": change > 0,
            "is_decrease": change < 0,
            "unit": current_result.get('unit', ''),
            "format_type": current_result.get('format_type', 'NUMBER')
        }

    def calculate_annual_yoy_comparison(
        self,
        metric_code: str,
        year: int
    ) -> Dict[str, Any]:
        """
        计算年度同比（与去年全年对比）

        Args:
            metric_code: 指标编码
            year: 当前年份

        Returns:
            对比结果
        """
        # 计算当前年周期
        period_start = date(year, 1, 1)
        period_end = date(year, 12, 31)

        # 计算去年周期
        prev_year = year - 1
        prev_period_start = date(prev_year, 1, 1)
        prev_period_end = date(prev_year, 12, 31)

        # 计算当前年指标值
        current_result = self.metric_service.calculate_metric(metric_code, period_start, period_end)
        current_value = current_result.get('value', 0)

        # 计算去年指标值
        prev_result = self.metric_service.calculate_metric(metric_code, prev_period_start, prev_period_end)
        prev_value = prev_result.get('value', 0)

        # 计算变化
        change = current_value - prev_value
        change_rate = (change / prev_value * 100) if prev_value != 0 else (100 if current_value > 0 else 0)

        return {
            "metric_code": metric_code,
            "metric_name": current_result.get('metric_name'),
            "current_period": str(year),
            "previous_period": str(prev_year),
            "current_value": current_value,
            "previous_value": prev_value,
            "change": change,
            "change_rate": change_rate,
            "change_rate_formatted": f"{change_rate:+.2f}%",
            "is_increase": change > 0,
            "is_decrease": change < 0,
            "unit": current_result.get('unit', ''),
            "format_type": current_result.get('format_type', 'NUMBER')
        }

    def calculate_comparisons_batch(
        self,
        metric_codes: List[str],
        year: int,
        month: Optional[int] = None,
        enable_mom: bool = True,
        enable_yoy: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量计算对比数据

        Args:
            metric_codes: 指标编码列表
            year: 年份
            month: 月份（如果为None，则计算年度对比）
            enable_mom: 是否计算环比
            enable_yoy: 是否计算同比

        Returns:
            对比结果字典
        """
        results = {}

        for metric_code in metric_codes:
            try:
                # 获取指标定义，检查是否支持对比
                from app.models.management_rhythm import ReportMetricDefinition
                metric_def = self.db.query(ReportMetricDefinition).filter(
                    ReportMetricDefinition.metric_code == metric_code
                ).first()

                if not metric_def:
                    continue

                comparison_data = {
                    "metric_code": metric_code,
                    "metric_name": metric_def.metric_name
                }

                if month:
                    # 月度对比
                    if enable_mom and metric_def.support_mom:
                        try:
                            mom_result = self.calculate_mom_comparison(metric_code, year, month)
                            comparison_data["mom"] = mom_result
                        except Exception as e:
                            comparison_data["mom_error"] = str(e)

                    if enable_yoy and metric_def.support_yoy:
                        try:
                            yoy_result = self.calculate_yoy_comparison(metric_code, year, month)
                            comparison_data["yoy"] = yoy_result
                        except Exception as e:
                            comparison_data["yoy_error"] = str(e)
                else:
                    # 年度对比
                    if enable_yoy and metric_def.support_yoy:
                        try:
                            yoy_result = self.calculate_annual_yoy_comparison(metric_code, year)
                            comparison_data["yoy"] = yoy_result
                        except Exception as e:
                            comparison_data["yoy_error"] = str(e)

                results[metric_code] = comparison_data

            except Exception as e:
                results[metric_code] = {
                    "metric_code": metric_code,
                    "error": str(e)
                }

        return results
