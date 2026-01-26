# -*- coding: utf-8 -*-
"""
售前集成 - 辅助工具函数
"""

from typing import Any, Dict, List, Tuple

from app.models.enums import WinProbabilityLevelEnum
from app.schemas.presales import DimensionScore


def convert_lead_code_to_project_code(lead_id: str) -> str:
    """将线索编号转换为项目编号

    XS2501001 -> PJ2501001
    """
    if lead_id.upper().startswith('XS'):
        return 'PJ' + lead_id[2:]
    return 'PJ' + lead_id


def calculate_win_rate(
    dimension_scores: DimensionScore,
    salesperson_win_rate: float,
    customer_cooperation_count: int,
    competitor_count: int = 3,
    is_repeat_customer: bool = False
) -> Tuple[float, str, Dict[str, Any]]:
    """计算中标率预测

    返回: (预测中标率, 概率等级, 影响因素)
    """
    # 1. 基础分数（五维评估加权）
    base_score = dimension_scores.total_score / 100  # 转换为0-1

    # 2. 销售人员历史中标率调整
    salesperson_factor = 0.5 + salesperson_win_rate * 0.5

    # 3. 客户关系调整
    customer_factor = 1.0
    if customer_cooperation_count > 5:
        customer_factor = 1.3
    elif customer_cooperation_count > 3:
        customer_factor = 1.2
    elif customer_cooperation_count > 1:
        customer_factor = 1.1
    elif is_repeat_customer:
        customer_factor = 1.05

    # 4. 竞争对手调整
    competitor_factor = 1.0
    if competitor_count <= 1:
        competitor_factor = 1.2
    elif competitor_count <= 3:
        competitor_factor = 1.0
    elif competitor_count <= 5:
        competitor_factor = 0.85
    else:
        competitor_factor = 0.7

    # 5. 综合计算
    predicted_rate = base_score * salesperson_factor * customer_factor * competitor_factor
    predicted_rate = min(max(predicted_rate, 0), 1)  # 限制在0-1范围

    # 6. 确定概率等级
    if predicted_rate >= 0.8:
        level = WinProbabilityLevelEnum.VERY_HIGH.value
    elif predicted_rate >= 0.6:
        level = WinProbabilityLevelEnum.HIGH.value
    elif predicted_rate >= 0.4:
        level = WinProbabilityLevelEnum.MEDIUM.value
    elif predicted_rate >= 0.2:
        level = WinProbabilityLevelEnum.LOW.value
    else:
        level = WinProbabilityLevelEnum.VERY_LOW.value

    # 7. 影响因素分析
    factors = {
        "base_score": round(base_score, 3),
        "salesperson_factor": round(salesperson_factor, 3),
        "salesperson_win_rate": round(salesperson_win_rate, 3),
        "customer_factor": round(customer_factor, 3),
        "customer_cooperation_count": customer_cooperation_count,
        "competitor_factor": round(competitor_factor, 3),
        "competitor_count": competitor_count,
        "dimension_scores": {
            "requirement_maturity": dimension_scores.requirement_maturity,
            "technical_feasibility": dimension_scores.technical_feasibility,
            "business_feasibility": dimension_scores.business_feasibility,
            "delivery_risk": dimension_scores.delivery_risk,
            "customer_relationship": dimension_scores.customer_relationship
        }
    }

    return predicted_rate, level, factors


def get_win_rate_recommendations(
    predicted_rate: float,
    factors: Dict[str, Any]
) -> List[str]:
    """根据预测结果生成提升中标率的建议"""
    recommendations = []

    dim_scores = factors.get("dimension_scores", {})

    # 1. 五维评估低分项建议
    if dim_scores.get("requirement_maturity", 100) < 60:
        recommendations.append("需求成熟度较低，建议与客户进一步澄清需求")
    if dim_scores.get("technical_feasibility", 100) < 60:
        recommendations.append("技术可行性评分较低，建议投入更多技术资源评估方案")
    if dim_scores.get("business_feasibility", 100) < 60:
        recommendations.append("商务可行性评分较低，建议重新评估定价策略")
    if dim_scores.get("delivery_risk", 100) < 60:
        recommendations.append("交付风险评分高，建议制定详细的风险应对计划")
    if dim_scores.get("customer_relationship", 100) < 60:
        recommendations.append("客户关系评分较低，建议加强客户高层关系维护")

    # 2. 销售人员建议
    if factors.get("salesperson_win_rate", 1) < 0.3:
        recommendations.append("销售人员历史中标率较低，建议派遣经验丰富的销售支援")

    # 3. 竞争态势建议
    if factors.get("competitor_count", 0) > 3:
        recommendations.append("竞争对手较多，建议突出差异化优势")

    # 4. 整体建议
    if predicted_rate < 0.4:
        recommendations.append("预测中标率偏低，建议评估是否继续投入资源")
    elif predicted_rate >= 0.7:
        recommendations.append("中标概率较高，建议重点关注，确保资源到位")

    return recommendations
