# -*- coding: utf-8 -*-
"""
置信度评分器

评估成本估算的可信度。
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.sales.presale_ai_cost import PresaleCostHistory
from app.schemas.sales.presale_ai_cost import CostEstimationInput


class ConfidenceScorer:
    """置信度评分器"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_score(self, input_data: CostEstimationInput) -> Decimal:
        """
        计算置信度评分

        基于输入数据的完整性和历史数据的丰富度评估可信度。

        Args:
            input_data: 估算输入数据

        Returns:
            置信度评分（0-1）
        """
        score = Decimal("0.5")  # 基础分

        # 硬件清单完整度
        if input_data.hardware_items and len(input_data.hardware_items) > 0:
            score += Decimal("0.2")

        # 软件需求明确度
        if input_data.software_requirements and len(input_data.software_requirements) > 100:
            score += Decimal("0.15")

        # 人天估算
        if input_data.estimated_man_days:
            score += Decimal("0.1")

        # 历史数据
        historical_count = self._count_historical_data(input_data.project_type)
        if historical_count > 10:
            score += Decimal("0.05")

        return min(score, Decimal("1.0"))

    def _count_historical_data(self, project_type: str) -> int:
        """统计历史数据数量"""
        return (
            self.db.query(PresaleCostHistory)
            .filter(
                PresaleCostHistory.project_features.contains(
                    f'"project_type": "{project_type}"'
                )
            )
            .count()
        )
