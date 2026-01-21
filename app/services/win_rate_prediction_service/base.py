# -*- coding: utf-8 -*-
"""
中标率预测服务 - 基础类和常量
"""
from sqlalchemy.orm import Session

from app.models.enums import WinProbabilityLevelEnum


class WinRatePredictionService:
    """中标率预测服务"""

    # 五维评估权重
    DIMENSION_WEIGHTS = {
        'requirement_maturity': 0.20,      # 需求成熟度
        'technical_feasibility': 0.25,     # 技术可行性
        'business_feasibility': 0.20,      # 商务可行性
        'delivery_risk': 0.15,             # 交付风险
        'customer_relationship': 0.20      # 客户关系
    }

    # 概率等级阈值
    PROBABILITY_THRESHOLDS = {
        WinProbabilityLevelEnum.VERY_HIGH: 0.80,
        WinProbabilityLevelEnum.HIGH: 0.60,
        WinProbabilityLevelEnum.MEDIUM: 0.40,
        WinProbabilityLevelEnum.LOW: 0.20,
        WinProbabilityLevelEnum.VERY_LOW: 0.0
    }

    def __init__(self, db: Session):
        self.db = db
