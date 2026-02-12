# -*- coding: utf-8 -*-
"""
中标率预测服务 - 因子计算
"""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from app.models.enums import ProductMatchTypeEnum
from app.schemas.presales import DimensionScore

if TYPE_CHECKING:
    from app.services.win_rate_prediction_service import WinRatePredictionService


def calculate_base_score(service: "WinRatePredictionService", dimension_scores: DimensionScore) -> float:
    """计算基础分数（五维加权平均）"""
    return (
        dimension_scores.requirement_maturity * service.DIMENSION_WEIGHTS['requirement_maturity'] +
        dimension_scores.technical_feasibility * service.DIMENSION_WEIGHTS['technical_feasibility'] +
        dimension_scores.business_feasibility * service.DIMENSION_WEIGHTS['business_feasibility'] +
        dimension_scores.delivery_risk * service.DIMENSION_WEIGHTS['delivery_risk'] +
        dimension_scores.customer_relationship * service.DIMENSION_WEIGHTS['customer_relationship']
    ) / 100  # 转换为0-1


def calculate_salesperson_factor(historical_win_rate: float) -> float:
    """计算销售人员因子

    历史中标率高的销售人员获得更高的加成
    """
    # 基础系数0.5，最高加成到1.0
    return 0.5 + historical_win_rate * 0.5


def calculate_customer_factor(
    cooperation_count: int,
    success_count: int,
    is_repeat_customer: bool = False
) -> float:
    """计算客户关系因子"""
    if cooperation_count >= 5 and success_count >= 3:
        return 1.30  # 深度合作客户
    elif cooperation_count >= 3 and success_count >= 2:
        return 1.20  # 稳定客户
    elif cooperation_count >= 1:
        return 1.10  # 老客户
    elif is_repeat_customer:
        return 1.05  # 回头客
    return 1.0


def calculate_competitor_factor(competitor_count: int) -> float:
    """计算竞争态势因子"""
    if competitor_count <= 1:
        return 1.20  # 几乎无竞争
    elif competitor_count <= 2:
        return 1.05  # 少量竞争
    elif competitor_count <= 3:
        return 1.00  # 正常竞争
    elif competitor_count <= 5:
        return 0.85  # 激烈竞争
    return 0.70  # 极度激烈


def calculate_amount_factor(estimated_amount: Optional[Decimal]) -> float:
    """计算金额因子

    大金额项目通常更受重视，但也更难成交
    """
    if not estimated_amount:
        return 1.0

    amount = float(estimated_amount)
    if amount < 100000:  # < 10万
        return 1.10  # 小项目容易成交
    elif amount < 500000:  # 10-50万
        return 1.05
    elif amount < 1000000:  # 50-100万
        return 1.00
    elif amount < 5000000:  # 100-500万
        return 0.95
    return 0.90  # > 500万大项目难度高


def calculate_product_factor(product_match_type: Optional[str]) -> float:
    """计算产品因子

    优势产品（公司主推产品）加成15%，新产品降低15%

    Args:
        product_match_type: 产品匹配类型（ADVANTAGE/NEW/UNKNOWN）

    Returns:
        产品因子系数
    """
    if product_match_type == ProductMatchTypeEnum.ADVANTAGE.value:
        return 1.15  # 优势产品加成15%
    elif product_match_type == ProductMatchTypeEnum.NEW.value:
        return 0.85  # 新产品降低15%
    return 1.0  # 未指定，无影响
