# -*- coding: utf-8 -*-
"""
绩效奖金计算器
基于绩效结果计算奖金
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusRule
from app.models.performance import PerformanceResult
from app.services.bonus.base import BonusCalculatorBase


class PerformanceBonusCalculator(BonusCalculatorBase):
    """绩效奖金计算器"""

    def __init__(self, db: Session):
        super().__init__(db)

    def calculate(
        self,
        performance_result: PerformanceResult,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """
        基于绩效结果计算奖金

        Args:
            performance_result: 绩效结果
            bonus_rule: 奖金规则

        Returns:
            BonusCalculation: 计算记录，如果不满足条件则返回None
        """
        # 检查触发条件
        context = {'performance_result': performance_result}
        if not self.check_trigger_condition(bonus_rule, context):
            return None

        # 获取计算参数
        base_amount = bonus_rule.base_amount or Decimal('0')
        coefficient = self.get_coefficient_by_level(performance_result.level)

        # 计算奖金
        calculated_amount = base_amount * coefficient

        # 创建计算记录
        calculation = BonusCalculation(
            calculation_code=self.generate_calculation_code(),
            rule_id=bonus_rule.id,
            period_id=performance_result.period_id,
            user_id=performance_result.user_id,
            performance_result_id=performance_result.id,
            calculated_amount=calculated_amount,
            calculation_detail={
                "base_amount": float(base_amount),
                "coefficient": float(coefficient),
                "performance_level": performance_result.level,
                "performance_score": float(performance_result.total_score) if performance_result.total_score else 0
            },
            calculation_basis={
                "type": "performance",
                "period_id": performance_result.period_id,
                "performance_result_id": performance_result.id
            },
            status='CALCULATED'
        )

        return calculation
