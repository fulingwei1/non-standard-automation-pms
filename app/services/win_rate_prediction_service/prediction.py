# -*- coding: utf-8 -*-
"""
中标率预测服务 - 预测功能
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.enums import ProductMatchTypeEnum, WinProbabilityLevelEnum
from app.schemas.presales import DimensionScore

from .factors import (
    calculate_amount_factor,
    calculate_base_score,
    calculate_competitor_factor,
    calculate_customer_factor,
    calculate_product_factor,
    calculate_salesperson_factor,
)
from .history import (
    get_customer_cooperation_history,
    get_salesperson_historical_win_rate,
    get_similar_leads_statistics,
)

logger = logging.getLogger(__name__)


def predict(
    service: "WinRatePredictionService",
    dimension_scores: DimensionScore,
    salesperson_id: int,
    customer_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    estimated_amount: Optional[Decimal] = None,
    competitor_count: int = 3,
    is_repeat_customer: bool = False,
    product_match_type: Optional[str] = None
) -> Dict[str, Any]:
    """预测中标率

    Returns:
        {
            'predicted_rate': float,
            'probability_level': str,
            'confidence': float,
            'factors': dict,
            'recommendations': list
        }
    """
    # 1. 计算基础分数
    base_score = calculate_base_score(service, dimension_scores)

    # 2. 获取销售人员历史数据
    salesperson_win_rate, sample_size = get_salesperson_historical_win_rate(service, salesperson_id)
    salesperson_factor = calculate_salesperson_factor(salesperson_win_rate)

    # 3. 获取客户历史数据
    coop_count, success_count = get_customer_cooperation_history(service, customer_id, customer_name)
    customer_factor = calculate_customer_factor(coop_count, success_count, is_repeat_customer)

    # 4. 计算竞争因子
    competitor_factor = calculate_competitor_factor(competitor_count)

    # 5. 计算金额因子
    amount_factor = calculate_amount_factor(estimated_amount)

    # 6. 计算产品因子
    product_factor = calculate_product_factor(product_match_type)

    # 7. 综合计算
    predicted_rate = (
        base_score *
        salesperson_factor *
        customer_factor *
        competitor_factor *
        amount_factor *
        product_factor
    )
    predicted_rate = min(max(predicted_rate, 0), 1)

    # 8. 确定概率等级
    level = WinProbabilityLevelEnum.VERY_LOW.value
    for prob_level, threshold in service.PROBABILITY_THRESHOLDS.items():
        if predicted_rate >= threshold:
            level = prob_level.value
            break

    # 9. 计算置信度（基于样本量）
    if sample_size >= 20:
        confidence = 0.85
    elif sample_size >= 10:
        confidence = 0.70
    elif sample_size >= 5:
        confidence = 0.55
    else:
        confidence = 0.40

    # 10. 生成因素分析
    factors = {
        'base_score': round(base_score, 3),
        'salesperson_factor': round(salesperson_factor, 3),
        'salesperson_win_rate': round(salesperson_win_rate, 3),
        'salesperson_sample_size': sample_size,
        'customer_factor': round(customer_factor, 3),
        'customer_cooperation_count': coop_count,
        'customer_success_count': success_count,
        'competitor_factor': round(competitor_factor, 3),
        'competitor_count': competitor_count,
        'amount_factor': round(amount_factor, 3),
        'product_factor': round(product_factor, 3),
        'product_match_type': product_match_type or ProductMatchTypeEnum.UNKNOWN.value,
        'dimension_scores': {
            'requirement_maturity': dimension_scores.requirement_maturity,
            'technical_feasibility': dimension_scores.technical_feasibility,
            'business_feasibility': dimension_scores.business_feasibility,
            'delivery_risk': dimension_scores.delivery_risk,
            'customer_relationship': dimension_scores.customer_relationship,
            'total': round(dimension_scores.total_score, 1)
        }
    }

    # 11. 生成建议
    recommendations = _generate_recommendations(
        predicted_rate,
        dimension_scores,
        salesperson_win_rate,
        competitor_count,
        product_match_type
    )

    # 12. 获取相似线索参考
    similar_count, similar_rate = get_similar_leads_statistics(service, dimension_scores)

    return {
        'predicted_rate': round(predicted_rate, 3),
        'probability_level': level,
        'confidence': confidence,
        'factors': factors,
        'recommendations': recommendations,
        'similar_leads_count': similar_count,
        'similar_leads_win_rate': round(similar_rate, 3) if similar_count > 0 else None
    }


def _generate_recommendations(
    predicted_rate: float,
    dimension_scores: DimensionScore,
    salesperson_win_rate: float,
    competitor_count: int,
    product_match_type: Optional[str] = None
) -> List[str]:
    """生成提升中标率的建议"""
    recommendations = []

    # 1. 五维评估低分项建议
    if dimension_scores.requirement_maturity < 60:
        recommendations.append("【需求成熟度】评分较低，建议与客户进一步澄清需求，明确边界条件")

    if dimension_scores.technical_feasibility < 60:
        recommendations.append("【技术可行性】评分较低，建议投入更多技术资源评估方案可行性")

    if dimension_scores.business_feasibility < 60:
        recommendations.append("【商务可行性】评分较低，建议重新评估定价策略，考虑适当调整报价")

    if dimension_scores.delivery_risk < 60:
        recommendations.append("【交付风险】评分较高，建议制定详细的风险应对计划和应急方案")

    if dimension_scores.customer_relationship < 60:
        recommendations.append("【客户关系】评分较低，建议加强客户高层关系维护，安排高管拜访")

    # 2. 销售人员建议
    if salesperson_win_rate < 0.25:
        recommendations.append("【销售支援】销售人员历史中标率较低，建议派遣经验丰富的销售骨干支援")
    elif salesperson_win_rate < 0.35:
        recommendations.append("【销售辅导】建议安排销售经理进行过程辅导，提供方案评审支持")

    # 3. 竞争态势建议
    if competitor_count > 4:
        recommendations.append("【差异化】竞争对手较多，建议深挖客户痛点，突出差异化优势")
    elif competitor_count > 2:
        recommendations.append("【竞争分析】建议进行竞争对手分析，制定针对性策略")

    # 4. 产品类型建议
    if product_match_type == ProductMatchTypeEnum.NEW.value:
        recommendations.append("【新产品风险】该产品不在公司优势产品列表中，建议评估技术风险和交付能力")
        recommendations.append("【产品替代】如有可能，建议推荐公司成熟产品替代，提升中标概率")
    elif product_match_type == ProductMatchTypeEnum.ADVANTAGE.value:
        recommendations.append("【优势发挥】该产品为公司优势产品，建议突出成功案例和技术优势")

    # 5. 整体建议
    if predicted_rate < 0.30:
        recommendations.append("【资源评估】预测中标率偏低(<30%)，建议评估是否继续投入资源，或调整策略")
    elif predicted_rate < 0.45:
        recommendations.append("【重点突破】预测中标率中等，建议聚焦关键决策人，寻找突破口")
    elif predicted_rate >= 0.70:
        recommendations.append("【全力冲刺】中标概率较高，建议作为重点项目关注，确保资源优先到位")

    return recommendations


def batch_predict(
    service: "WinRatePredictionService",
    leads: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """批量预测多个线索的中标率

    Args:
        service: WinRatePredictionService实例
        leads: 线索列表，每个线索包含 dimension_scores, salesperson_id, product_match_type 等

    Returns:
        预测结果列表
    """
    results = []
    for lead in leads:
        try:
            dimension_scores = DimensionScore(**lead.get('dimension_scores', {}))
            result = predict(
                service=service,
                dimension_scores=dimension_scores,
                salesperson_id=lead.get('salesperson_id'),
                customer_id=lead.get('customer_id'),
                customer_name=lead.get('customer_name'),
                estimated_amount=lead.get('estimated_amount'),
                competitor_count=lead.get('competitor_count', 3),
                is_repeat_customer=lead.get('is_repeat_customer', False),
                product_match_type=lead.get('product_match_type')
            )
            result['lead_id'] = lead.get('lead_id')
            results.append(result)
        except Exception as e:
            logger.error(f"预测失败 lead_id={lead.get('lead_id')}: {e}")
            results.append({
                'lead_id': lead.get('lead_id'),
                'error': str(e)
            })

    return results
