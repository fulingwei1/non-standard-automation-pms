# -*- coding: utf-8 -*-
"""
成本计算器

提供各类成本的计算逻辑：
- 硬件成本
- 软件成本
- 安装调试成本
- 售后服务成本
- 风险储备金
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales.presale_ai_cost import PresaleCostHistory
from app.utils.decimal_helpers import parse_decimal, safe_decimal_from_dict


class CostCalculator:
    """成本计算器"""

    # 成本系数（可从配置文件读取）
    HARDWARE_MARKUP = Decimal("1.15")  # 硬件加成 15%
    SOFTWARE_HOURLY_RATE = Decimal("800")  # 软件开发时薪 800 元
    INSTALLATION_BASE_COST = Decimal("5000")  # 安装基础成本
    SERVICE_ANNUAL_RATE = Decimal("0.10")  # 年服务费率 10%
    RISK_RESERVE_RATE = Decimal("0.08")  # 风险储备金 8%

    def __init__(self, db: Session):
        self.db = db

    def calculate_hardware_cost(
        self, hardware_items: Optional[List[Dict[str, Any]]]
    ) -> Decimal:
        """
        计算硬件成本

        Args:
            hardware_items: 硬件清单

        Returns:
            硬件总成本（含加成）
        """
        if not hardware_items:
            return Decimal("0")

        total = Decimal("0")
        for item in hardware_items:
            unit_price = safe_decimal_from_dict(item, "unit_price", default="0")
            quantity = safe_decimal_from_dict(item, "quantity", default="1")
            total += unit_price * quantity

        # 加成（运费、损耗等）
        return total * self.HARDWARE_MARKUP

    def calculate_software_cost(
        self,
        requirements: Optional[str],
        man_days: Optional[int]
    ) -> Decimal:
        """
        计算软件成本

        Args:
            requirements: 需求描述
            man_days: 估算人天

        Returns:
            软件开发成本
        """
        if not man_days:
            # 基于需求描述估算人天（简化版，实际可用 AI 分析）
            if not requirements:
                return Decimal("0")

            word_count = len(requirements)
            if word_count < 100:
                man_days = 5
            elif word_count < 500:
                man_days = 15
            else:
                man_days = 30

        # 人天 * 8 小时 * 时薪
        return parse_decimal(man_days) * Decimal("8") * self.SOFTWARE_HOURLY_RATE

    def calculate_installation_cost(
        self,
        difficulty: Optional[str],
        hardware_cost: Decimal
    ) -> Decimal:
        """
        计算安装调试成本

        Args:
            difficulty: 安装难度（low/medium/high）
            hardware_cost: 硬件成本

        Returns:
            安装调试成本
        """
        base_cost = self.INSTALLATION_BASE_COST

        if difficulty == "high":
            multiplier = Decimal("2.0")
        elif difficulty == "medium":
            multiplier = Decimal("1.5")
        else:
            multiplier = Decimal("1.0")

        # 基础成本 + 硬件成本的 5%
        return base_cost * multiplier + hardware_cost * Decimal("0.05")

    def calculate_service_cost(
        self,
        base_cost: Decimal,
        years: int
    ) -> Decimal:
        """
        计算售后服务成本

        Args:
            base_cost: 基础成本（硬件+软件）
            years: 服务年限

        Returns:
            售后服务成本
        """
        return base_cost * self.SERVICE_ANNUAL_RATE * parse_decimal(years)

    def calculate_risk_reserve(
        self,
        project_type: str,
        complexity: str,
        base_cost: Decimal
    ) -> Decimal:
        """
        计算风险储备金

        Args:
            project_type: 项目类型
            complexity: 复杂度（low/medium/high）
            base_cost: 基础成本

        Returns:
            风险储备金
        """
        rate = self.RISK_RESERVE_RATE

        # 基于复杂度调整
        if complexity == "high":
            rate = rate * Decimal("1.5")
        elif complexity == "low":
            rate = rate * Decimal("0.5")

        # 从历史数据学习
        historical_variance = self._get_historical_variance(project_type)
        if historical_variance:
            rate = rate * (Decimal("1") + historical_variance)

        return base_cost * rate

    def _get_historical_variance(self, project_type: str) -> Optional[Decimal]:
        """获取历史偏差率"""
        result = (
            self.db.query(func.avg(PresaleCostHistory.variance_rate))
            .filter(
                PresaleCostHistory.project_features.contains(
                    f'"project_type": "{project_type}"'
                )
            )
            .scalar()
        )

        return parse_decimal(result) / Decimal("100") if result else None
