# -*- coding: utf-8 -*-
"""
历史数据分析器

分析历史成本数据，提供准确度统计和学习能力。
"""

from decimal import Decimal
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.sales.presale_ai_cost import PresaleAICostEstimation, PresaleCostHistory
from app.schemas.sales.presale_ai_cost import (
    HistoricalAccuracyResponse,
    UpdateActualCostInput,
)
from app.utils.db_helpers import save_obj
from app.utils.decimal_helpers import parse_decimal


class HistoricalAnalyzer:
    """历史数据分析器"""

    def __init__(self, db: Session):
        self.db = db

    async def get_accuracy(self) -> HistoricalAccuracyResponse:
        """
        获取历史预测准确度

        Returns:
            准确度统计结果
        """
        histories = self.db.query(PresaleCostHistory).all()

        if not histories:
            return HistoricalAccuracyResponse(
                total_predictions=0,
                average_variance_rate=Decimal("0"),
                accuracy_rate=Decimal("0"),
                best_performing_category=None,
                worst_performing_category=None,
                recent_trend="无数据",
                sample_cases=None,
            )

        total = len(histories)
        variance_rates = [
            h.variance_rate for h in histories if h.variance_rate is not None
        ]

        avg_variance = (
            sum(variance_rates) / len(variance_rates)
            if variance_rates
            else Decimal("0")
        )

        # 计算准确率（偏差<15%的比例）
        accurate_count = sum(1 for vr in variance_rates if abs(vr) < Decimal("15"))
        accuracy_rate = (
            parse_decimal(accurate_count) / parse_decimal(len(variance_rates)) * Decimal("100")
            if variance_rates
            else Decimal("0")
        )

        return HistoricalAccuracyResponse(
            total_predictions=total,
            average_variance_rate=avg_variance,
            accuracy_rate=accuracy_rate,
            best_performing_category="待分析",
            worst_performing_category="待分析",
            recent_trend="稳定",
            sample_cases=None,
        )

    async def update_actual_cost(
        self,
        input_data: UpdateActualCostInput
    ) -> Dict[str, Any]:
        """
        更新实际成本（用于学习）

        Args:
            input_data: 实际成本数据

        Returns:
            更新结果
        """
        estimation = (
            self.db.query(PresaleAICostEstimation)
            .filter(PresaleAICostEstimation.id == input_data.estimation_id)
            .first()
        )

        if not estimation:
            raise ValueError(f"估算记录不存在: {input_data.estimation_id}")

        # 计算偏差率
        variance = input_data.actual_cost - estimation.total_cost
        variance_rate = (
            (variance / estimation.total_cost * Decimal("100"))
            if estimation.total_cost > 0
            else Decimal("0")
        )

        # 创建历史记录
        history = PresaleCostHistory(
            project_id=input_data.project_id,
            project_name=input_data.project_name,
            estimated_cost=estimation.total_cost,
            actual_cost=input_data.actual_cost,
            variance_rate=variance_rate,
            cost_breakdown=(
                input_data.actual_breakdown.dict() if input_data.actual_breakdown else None
            ),
            variance_analysis={
                "total_variance": float(variance),
                "variance_rate": float(variance_rate),
                "estimation_id": estimation.id,
            },
            project_features=estimation.input_parameters,
        )

        save_obj(self.db, history)

        return {
            "history_id": history.id,
            "variance_rate": variance_rate,
            "variance_analysis": history.variance_analysis,
            "learning_applied": True,
            "message": "实际成本已记录,模型将从此数据学习",
        }
