# -*- coding: utf-8 -*-
"""
描述生成模块
提供各种评分维度的描述生成功能
"""

from typing import Optional

from app.models.project import Customer
from app.models.sales import Lead, Opportunity


class DescriptionsMixin:
    """描述生成功能混入类"""

    def _get_customer_level_description(self, lead: Lead) -> str:
        """获取客户等级描述"""
        score = self._calculate_customer_importance(lead)
        level_map = {20: "A级", 15: "B级", 10: "C级", 5: "D级", 2: "E级"}
        level = level_map.get(score, "未知")
        return f"客户等级：{level}"

    def _get_contract_amount_description(self, lead: Lead) -> str:
        """获取合同金额描述"""
        score = self._calculate_contract_amount_score(lead)
        amount_map = {
            25: "≥100万",
            20: "50-100万",
            15: "20-50万",
            10: "10-20万",
            5: "<10万",
        }
        amount = amount_map.get(score, "未知")
        return f"预估金额：{amount}"

    def _get_win_rate_description(self, lead: Lead) -> str:
        """获取中标概率描述"""
        score = self._calculate_win_rate_score(lead)
        rate_map = {20: "≥80%", 15: "60-80%", 10: "40-60%", 5: "<40%"}
        rate = rate_map.get(score, "未知")
        return f"预测中标率：{rate}"

    def _get_requirement_maturity_description(self, lead: Lead) -> str:
        """获取需求成熟度描述"""
        completeness = lead.completeness or 0
        if completeness >= 80:
            return "需求非常明确"
        elif completeness >= 60:
            return "需求基本明确"
        elif completeness >= 40:
            return "需求部分明确"
        else:
            return "需求不明确"

    def _get_urgency_description(self, lead: Lead) -> str:
        """获取紧急程度描述"""
        score = self._calculate_urgency_score(lead)
        urgency_map = {10: "客户要求紧急", 7: "客户要求正常", 3: "客户要求不紧急"}
        urgency = urgency_map.get(score, "未知")
        return urgency

    def _get_relationship_description(self, lead: Lead) -> str:
        """获取客户关系描述"""
        score = self._calculate_relationship_score(lead)
        relationship_map = {
            10: "老客户/关系好",
            7: "老客户/关系一般",
            5: "新客户/关系一般",
            2: "新客户/关系差",
        }
        relationship = relationship_map.get(score, "未知")
        return relationship

    def _get_relationship_description_for_opp(
        self, opportunity: Opportunity, customer: Optional[Customer]
    ) -> str:
        """获取商机客户关系描述"""
        score = self._calculate_opportunity_relationship(opportunity, customer)
        relationship_map = {
            10: "老客户/关系好",
            7: "老客户/关系一般",
            5: "新客户/关系一般",
            2: "新客户/关系差",
        }
        relationship = relationship_map.get(score, "未知")
        return relationship
