# -*- coding: utf-8 -*-
"""
商机评分计算模块
提供商机优先级评分的计算功能
"""

from decimal import Decimal
from typing import Any, Dict

from app.models.project import Customer
from app.models.sales import Opportunity


class OpportunityScoringMixin:
    """商机评分计算功能混入类"""

    def calculate_opportunity_priority(self, opportunity_id: int) -> Dict[str, Any]:
        """计算商机优先级评分"""
        opportunity = (
            self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        )
        if not opportunity:
            raise ValueError(f"商机 {opportunity_id} 不存在")

        scores = {}
        total_score = 0

        # 1. 客户重要性（20分）
        customer = (
            self.db.query(Customer)
            .filter(Customer.id == opportunity.customer_id)
            .first()
        )
        customer_score = self._get_customer_score(customer)
        scores["customer_importance"] = {
            "score": customer_score,
            "max": 20,
            "description": f"客户等级：{customer.credit_level if customer else '未知'}",
        }
        total_score += customer_score

        # 2. 预估合同金额（25分）
        est_amount = opportunity.est_amount or Decimal("0")
        amount_score = self._get_amount_score(float(est_amount))
        scores["contract_amount"] = {
            "score": amount_score,
            "max": 25,
            "description": f"预估金额：{est_amount}元",
        }
        total_score += amount_score

        # 3. 中标概率（20分）
        predicted_win_rate = opportunity.score / 100.0 if opportunity.score else 0.5
        win_rate_score = self._get_win_rate_score(predicted_win_rate)
        scores["win_rate"] = {
            "score": win_rate_score,
            "max": 20,
            "description": f"评分：{opportunity.score}/100",
        }
        total_score += win_rate_score

        # 4. 需求成熟度（15分）
        maturity = opportunity.requirement_maturity or 3
        maturity_score = self.REQUIREMENT_MATURITY_SCORES.get(maturity, 8)
        scores["requirement_maturity"] = {
            "score": maturity_score,
            "max": 15,
            "description": f"需求成熟度：{maturity}/5",
        }
        total_score += maturity_score

        # 5. 紧急程度（10分）- 从交付窗口判断
        urgency_score = self._calculate_opportunity_urgency(opportunity)
        scores["urgency"] = {
            "score": urgency_score,
            "max": 10,
            "description": f"交付窗口：{opportunity.delivery_window or '未指定'}",
        }
        total_score += urgency_score

        # 6. 客户关系（10分）
        relationship_score = self._calculate_opportunity_relationship(
            opportunity, customer
        )
        scores["relationship"] = {
            "score": relationship_score,
            "max": 10,
            "description": self._get_relationship_description_for_opp(
                opportunity, customer
            ),
        }
        total_score += relationship_score

        # 计算优先级等级
        urgency_level_score = urgency_score
        priority_level = self._determine_priority_level(
            total_score, urgency_level_score
        )
        is_key_opportunity = total_score >= 70
        importance_level = self._determine_importance_level(total_score)
        urgency_level = self._determine_urgency_level(urgency_level_score)

        return {
            "opportunity_id": opportunity_id,
            "opp_code": opportunity.opp_code,
            "total_score": total_score,
            "max_score": 100,
            "scores": scores,
            "is_key_opportunity": is_key_opportunity,
            "priority_level": priority_level,
            "importance_level": importance_level,
            "urgency_level": urgency_level,
        }
