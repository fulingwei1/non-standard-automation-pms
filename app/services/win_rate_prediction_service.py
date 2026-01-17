# -*- coding: utf-8 -*-
"""
中标率预测服务

基于历史数据和规则模型预测销售线索的中标概率
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.enums import (
    LeadOutcomeEnum,
    ProductMatchTypeEnum,
    WinProbabilityLevelEnum,
)
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.presales import DimensionScore

logger = logging.getLogger(__name__)


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

    def get_salesperson_historical_win_rate(
        self,
        salesperson_id: int,
        lookback_months: int = 24
    ) -> Tuple[float, int]:
        """获取销售人员历史中标率

        Args:
            salesperson_id: 销售人员ID
            lookback_months: 回溯月数

        Returns:
            (中标率, 样本数)
        """
        cutoff_date = date.today() - timedelta(days=30 * lookback_months)

        stats = self.db.query(
            func.count(Project.id).label('total'),
            func.sum(func.case(
                (Project.outcome == LeadOutcomeEnum.WON.value, 1),
                else_=0
            )).label('won')
        ).filter(
            Project.salesperson_id == salesperson_id,
            Project.created_at >= cutoff_date,
            Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
        ).first()

        total = stats.total or 0
        won = stats.won or 0

        if total == 0:
            return 0.20, 0  # 无数据时返回行业平均值

        return won / total, total

    def get_customer_cooperation_history(
        self,
        customer_id: Optional[int] = None,
        customer_name: Optional[str] = None
    ) -> Tuple[int, int]:
        """获取客户历史合作情况

        Returns:
            (总合作次数, 成功次数)
        """
        query = self.db.query(Project)

        if customer_id:
            query = query.filter(Project.customer_id == customer_id)
        elif customer_name:
            # 通过客户名称查找
            customer = self.db.query(Customer).filter(
                Customer.name == customer_name
            ).first()
            if customer:
                query = query.filter(Project.customer_id == customer.id)
            else:
                return 0, 0
        else:
            return 0, 0

        total = query.count()
        won = query.filter(Project.outcome == LeadOutcomeEnum.WON.value).count()

        return total, won

    def get_similar_leads_statistics(
        self,
        dimension_scores: DimensionScore,
        score_tolerance: float = 10
    ) -> Tuple[int, float]:
        """获取相似线索统计

        Args:
            dimension_scores: 五维评估分数
            score_tolerance: 分数容差

        Returns:
            (相似线索数, 相似线索中标率)
        """
        total_score = dimension_scores.total_score

        similar_leads = self.db.query(Project).filter(
            Project.evaluation_score.between(
                total_score - score_tolerance,
                total_score + score_tolerance
            ),
            Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
        ).all()

        if not similar_leads:
            return 0, 0

        won = sum(1 for p in similar_leads if p.outcome == LeadOutcomeEnum.WON.value)
        return len(similar_leads), won / len(similar_leads)

    def calculate_base_score(self, dimension_scores: DimensionScore) -> float:
        """计算基础分数（五维加权平均）"""
        return (
            dimension_scores.requirement_maturity * self.DIMENSION_WEIGHTS['requirement_maturity'] +
            dimension_scores.technical_feasibility * self.DIMENSION_WEIGHTS['technical_feasibility'] +
            dimension_scores.business_feasibility * self.DIMENSION_WEIGHTS['business_feasibility'] +
            dimension_scores.delivery_risk * self.DIMENSION_WEIGHTS['delivery_risk'] +
            dimension_scores.customer_relationship * self.DIMENSION_WEIGHTS['customer_relationship']
        ) / 100  # 转换为0-1

    def calculate_salesperson_factor(self, historical_win_rate: float) -> float:
        """计算销售人员因子

        历史中标率高的销售人员获得更高的加成
        """
        # 基础系数0.5，最高加成到1.0
        return 0.5 + historical_win_rate * 0.5

    def calculate_customer_factor(
        self,
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

    def calculate_competitor_factor(self, competitor_count: int) -> float:
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

    def calculate_amount_factor(self, estimated_amount: Optional[Decimal]) -> float:
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

    def calculate_product_factor(self, product_match_type: Optional[str]) -> float:
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

    def predict(
        self,
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
        base_score = self.calculate_base_score(dimension_scores)

        # 2. 获取销售人员历史数据
        salesperson_win_rate, sample_size = self.get_salesperson_historical_win_rate(salesperson_id)
        salesperson_factor = self.calculate_salesperson_factor(salesperson_win_rate)

        # 3. 获取客户历史数据
        coop_count, success_count = self.get_customer_cooperation_history(customer_id, customer_name)
        customer_factor = self.calculate_customer_factor(coop_count, success_count, is_repeat_customer)

        # 4. 计算竞争因子
        competitor_factor = self.calculate_competitor_factor(competitor_count)

        # 5. 计算金额因子
        amount_factor = self.calculate_amount_factor(estimated_amount)

        # 6. 计算产品因子
        product_factor = self.calculate_product_factor(product_match_type)

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
        for prob_level, threshold in self.PROBABILITY_THRESHOLDS.items():
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
        recommendations = self._generate_recommendations(
            predicted_rate,
            dimension_scores,
            salesperson_win_rate,
            competitor_count,
            product_match_type
        )

        # 12. 获取相似线索参考
        similar_count, similar_rate = self.get_similar_leads_statistics(dimension_scores)

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
        self,
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
        self,
        leads: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量预测多个线索的中标率

        Args:
            leads: 线索列表，每个线索包含 dimension_scores, salesperson_id, product_match_type 等

        Returns:
            预测结果列表
        """
        results = []
        for lead in leads:
            try:
                dimension_scores = DimensionScore(**lead.get('dimension_scores', {}))
                result = self.predict(
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

    def get_win_rate_distribution(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取中标率分布统计

        Returns:
            按概率等级分组的线索数量分布
        """
        query = self.db.query(Project).filter(
            Project.predicted_win_rate.isnot(None)
        )

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at < end_date)

        projects = query.all()

        distribution = {
            WinProbabilityLevelEnum.VERY_HIGH.value: {'count': 0, 'won': 0},
            WinProbabilityLevelEnum.HIGH.value: {'count': 0, 'won': 0},
            WinProbabilityLevelEnum.MEDIUM.value: {'count': 0, 'won': 0},
            WinProbabilityLevelEnum.LOW.value: {'count': 0, 'won': 0},
            WinProbabilityLevelEnum.VERY_LOW.value: {'count': 0, 'won': 0}
        }

        for project in projects:
            rate = project.predicted_win_rate
            if rate >= 0.80:
                level = WinProbabilityLevelEnum.VERY_HIGH.value
            elif rate >= 0.60:
                level = WinProbabilityLevelEnum.HIGH.value
            elif rate >= 0.40:
                level = WinProbabilityLevelEnum.MEDIUM.value
            elif rate >= 0.20:
                level = WinProbabilityLevelEnum.LOW.value
            else:
                level = WinProbabilityLevelEnum.VERY_LOW.value

            distribution[level]['count'] += 1
            if project.outcome == LeadOutcomeEnum.WON.value:
                distribution[level]['won'] += 1

        # 计算各等级实际中标率
        for level in distribution:
            count = distribution[level]['count']
            won = distribution[level]['won']
            distribution[level]['actual_win_rate'] = round(won / count, 3) if count > 0 else 0

        return distribution

    def validate_model_accuracy(
        self,
        lookback_months: int = 12
    ) -> Dict[str, Any]:
        """验证预测模型准确度

        对比预测中标率与实际中标情况
        """
        cutoff_date = date.today() - timedelta(days=30 * lookback_months)

        projects = self.db.query(Project).filter(
            Project.predicted_win_rate.isnot(None),
            Project.created_at >= cutoff_date,
            Project.outcome.in_([LeadOutcomeEnum.WON.value, LeadOutcomeEnum.LOST.value])
        ).all()

        if not projects:
            return {'error': '无足够数据进行验证'}

        # 计算预测准确度
        correct_predictions = 0
        total = len(projects)

        for project in projects:
            predicted_win = project.predicted_win_rate >= 0.5
            actual_win = project.outcome == LeadOutcomeEnum.WON.value

            if predicted_win == actual_win:
                correct_predictions += 1

        accuracy = correct_predictions / total

        # 计算 Brier 分数（越低越好）
        brier_score = sum(
            (p.predicted_win_rate - (1 if p.outcome == LeadOutcomeEnum.WON.value else 0)) ** 2
            for p in projects
        ) / total

        return {
            'total_samples': total,
            'accuracy': round(accuracy, 3),
            'brier_score': round(brier_score, 4),
            'period_months': lookback_months
        }
