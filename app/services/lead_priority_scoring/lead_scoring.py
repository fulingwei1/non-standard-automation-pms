# -*- coding: utf-8 -*-
"""
线索评分计算模块
提供线索优先级评分的计算功能
"""

from typing import Any, Dict

from app.models.project import Customer
from app.models.sales import Lead


class LeadScoringMixin:
    """线索评分计算功能混入类"""

    def calculate_lead_priority(self, lead_id: int) -> Dict[str, Any]:
        """计算线索优先级评分

        Returns:
            包含评分、各维度得分、优先级等级等的字典
        """
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"线索 {lead_id} 不存在")

        scores = {}
        total_score = 0

        # 1. 客户重要性（20分）
        customer_score = self._calculate_customer_importance(lead)
        scores["customer_importance"] = {
            "score": customer_score,
            "max": 20,
            "description": self._get_customer_level_description(lead),
        }
        total_score += customer_score

        # 2. 预估合同金额（25分）
        amount_score = self._calculate_contract_amount_score(lead)
        scores["contract_amount"] = {
            "score": amount_score,
            "max": 25,
            "description": self._get_contract_amount_description(lead),
        }
        total_score += amount_score

        # 3. 中标概率（20分）
        win_rate_score = self._calculate_win_rate_score(lead)
        scores["win_rate"] = {
            "score": win_rate_score,
            "max": 20,
            "description": self._get_win_rate_description(lead),
        }
        total_score += win_rate_score

        # 4. 需求成熟度（15分）
        maturity_score = self._calculate_requirement_maturity_score(lead)
        scores["requirement_maturity"] = {
            "score": maturity_score,
            "max": 15,
            "description": self._get_requirement_maturity_description(lead),
        }
        total_score += maturity_score

        # 5. 紧急程度（10分）
        urgency_score = self._calculate_urgency_score(lead)
        scores["urgency"] = {
            "score": urgency_score,
            "max": 10,
            "description": self._get_urgency_description(lead),
        }
        total_score += urgency_score

        # 6. 客户关系（10分）
        relationship_score = self._calculate_relationship_score(lead)
        scores["relationship"] = {
            "score": relationship_score,
            "max": 10,
            "description": self._get_relationship_description(lead),
        }
        total_score += relationship_score

        # 计算优先级等级
        priority_level = self._determine_priority_level(total_score, urgency_score)
        is_key_lead = total_score >= 70
        importance_level = self._determine_importance_level(total_score)
        urgency_level = self._determine_urgency_level(urgency_score)

        return {
            "lead_id": lead_id,
            "lead_code": lead.lead_code,
            "total_score": total_score,
            "max_score": 100,
            "scores": scores,
            "is_key_lead": is_key_lead,
            "priority_level": priority_level,
            "importance_level": importance_level,
            "urgency_level": urgency_level,
        }
