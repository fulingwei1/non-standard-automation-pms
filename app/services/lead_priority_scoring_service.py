# -*- coding: utf-8 -*-
"""
销售线索优先级评分服务

建立关键/非关键、重要/紧急的科学排序机制
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.sales import Lead, Opportunity
from app.models.project import Project, Customer
from app.models.user import User

logger = logging.getLogger(__name__)


class LeadPriorityScoringService:
    """销售线索优先级评分服务"""

    # 客户重要性分数映射
    CUSTOMER_IMPORTANCE_SCORES = {
        "A": 20,  # A级客户
        "B": 15,  # B级客户
        "C": 10,  # C级客户
        "D": 5,  # D级客户
        "E": 2,  # E级客户
    }

    # 预估合同金额分数映射
    CONTRACT_AMOUNT_SCORES = [
        (1000000, 25),  # ≥100万：25分
        (500000, 20),  # 50-100万：20分
        (200000, 15),  # 20-50万：15分
        (100000, 10),  # 10-20万：10分
        (0, 5),  # <10万：5分
    ]

    # 中标概率分数映射
    WIN_RATE_SCORES = [
        (0.8, 20),  # ≥80%：20分
        (0.6, 15),  # 60-80%：15分
        (0.4, 10),  # 40-60%：10分
        (0.0, 5),  # <40%：5分
    ]

    # 需求成熟度分数映射
    REQUIREMENT_MATURITY_SCORES = {
        5: 15,  # 需求非常明确
        4: 12,  # 需求基本明确
        3: 8,  # 需求部分明确
        2: 5,  # 需求不明确
        1: 3,  # 需求很不明确
    }

    # 紧急程度分数映射
    URGENCY_SCORES = {
        "HIGH": 10,  # 客户要求紧急
        "MEDIUM": 7,  # 客户要求正常
        "LOW": 3,  # 客户要求不紧急
    }

    # 客户关系分数映射
    RELATIONSHIP_SCORES = {
        "EXISTING_GOOD": 10,  # 老客户/关系好
        "EXISTING_NORMAL": 7,  # 老客户/关系一般
        "NEW_NORMAL": 5,  # 新客户/关系一般
        "NEW_POOR": 2,  # 新客户/关系差
    }

    def __init__(self, db: Session):
        self.db = db

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

    def get_priority_ranking(
        self,
        entity_type: str = "lead",  # 'lead' or 'opportunity'
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取优先级排名"""
        rankings = []

        if entity_type == "lead":
            leads = self.db.query(Lead).filter(Lead.status != "INVALID").all()

            for lead in leads:
                try:
                    priority_data = self.calculate_lead_priority(lead.id)
                    rankings.append(
                        {
                            "id": lead.id,
                            "code": lead.lead_code,
                            "name": lead.customer_name or "未知客户",
                            "total_score": priority_data["total_score"],
                            "is_key": priority_data["is_key_lead"],
                            "priority_level": priority_data["priority_level"],
                            "importance_level": priority_data["importance_level"],
                            "urgency_level": priority_data["urgency_level"],
                        }
                    )
                except Exception as e:
                    logger.warning(f"计算线索 {lead.id} 优先级失败: {e}")
                    continue

        else:  # opportunity
            opportunities = (
                self.db.query(Opportunity)
                .filter(Opportunity.stage.notin_(["WON", "LOST"]))
                .all()
            )

            for opp in opportunities:
                try:
                    priority_data = self.calculate_opportunity_priority(opp.id)
                    rankings.append(
                        {
                            "id": opp.id,
                            "code": opp.opp_code,
                            "name": opp.opp_name,
                            "total_score": priority_data["total_score"],
                            "is_key": priority_data["is_key_opportunity"],
                            "priority_level": priority_data["priority_level"],
                            "importance_level": priority_data["importance_level"],
                            "urgency_level": priority_data["urgency_level"],
                        }
                    )
                except Exception as e:
                    logger.warning(f"计算商机 {opp.id} 优先级失败: {e}")
                    continue

        # 按总分排序
        rankings.sort(key=lambda x: x["total_score"], reverse=True)

        return rankings[:limit]

    def get_key_leads(self) -> List[Dict[str, Any]]:
        """获取关键线索列表"""
        rankings = self.get_priority_ranking("lead", limit=1000)
        return [r for r in rankings if r["is_key"]]

    def get_key_opportunities(self) -> List[Dict[str, Any]]:
        """获取关键商机列表"""
        rankings = self.get_priority_ranking("opportunity", limit=1000)
        return [r for r in rankings if r["is_key"]]

    # ==================== 私有方法 ====================

    def _calculate_customer_importance(self, lead: Lead) -> int:
        """计算客户重要性分数"""
        # 通过线索关联的商机查找客户
        if lead.opportunities:
            customer_id = lead.opportunities[0].customer_id
            customer = (
                self.db.query(Customer).filter(Customer.id == customer_id).first()
            )
            return self._get_customer_score(customer)

        # 如果没有商机，尝试通过客户名称查找
        if lead.customer_name:
            customer = (
                self.db.query(Customer)
                .filter(Customer.customer_name == lead.customer_name)
                .first()
            )
            return self._get_customer_score(customer)

        return 5  # 默认分数

    def _get_customer_score(self, customer: Optional[Customer]) -> int:
        """获取客户分数"""
        if not customer:
            return 5

        # 使用credit_level作为客户等级
        level = customer.credit_level or "C"
        level = level.upper()
        return self.CUSTOMER_IMPORTANCE_SCORES.get(level, 10)

    def _calculate_contract_amount_score(self, lead: Lead) -> int:
        """计算预估合同金额分数"""
        # 通过关联的商机获取预估金额
        if lead.opportunities:
            for opp in lead.opportunities:
                if opp.est_amount:
                    return self._get_amount_score(float(opp.est_amount))

        return 5  # 默认分数

    def _get_amount_score(self, amount: float) -> int:
        """根据金额获取分数"""
        for threshold, score in self.CONTRACT_AMOUNT_SCORES:
            if amount >= threshold:
                return score
        return 5

    def _calculate_win_rate_score(self, lead: Lead) -> int:
        """计算中标概率分数"""
        # 通过技术评估获取预测中标率
        if lead.assessment:
            # 如果有评估，使用评估分数
            if (
                hasattr(lead.assessment, "predicted_win_rate")
                and lead.assessment.predicted_win_rate
            ):
                win_rate = float(lead.assessment.predicted_win_rate)
                return self._get_win_rate_score(win_rate)

        # 通过关联的项目获取预测中标率
        if lead.opportunities:
            for opp in lead.opportunities:
                # 查找关联的项目
                projects = (
                    self.db.query(Project)
                    .filter(Project.opportunity_id == opp.id)
                    .all()
                )
                for project in projects:
                    if project.predicted_win_rate:
                        win_rate = float(project.predicted_win_rate)
                        return self._get_win_rate_score(win_rate)

        return 10  # 默认分数（中等概率）

    def _get_win_rate_score(self, win_rate: float) -> int:
        """根据中标概率获取分数"""
        for threshold, score in self.WIN_RATE_SCORES:
            if win_rate >= threshold:
                return score
        return 5

    def _calculate_requirement_maturity_score(self, lead: Lead) -> int:
        """计算需求成熟度分数"""
        # 通过completeness字段判断
        completeness = lead.completeness or 0
        if completeness >= 80:
            return 15
        elif completeness >= 60:
            return 12
        elif completeness >= 40:
            return 8
        elif completeness >= 20:
            return 5
        else:
            return 3

    def _calculate_urgency_score(self, lead: Lead) -> int:
        """计算紧急程度分数"""
        # 通过next_action_at判断
        if lead.next_action_at:
            days_until = (lead.next_action_at.date() - date.today()).days
            if days_until <= 3:
                return 10  # 紧急
            elif days_until <= 7:
                return 7  # 正常
            else:
                return 3  # 不紧急

        return 7  # 默认正常

    def _calculate_opportunity_urgency(self, opportunity: Opportunity) -> int:
        """计算商机紧急程度"""
        # 通过delivery_window判断
        if opportunity.delivery_window:
            # 简单判断：如果包含"紧急"、"急"等关键词
            if (
                "紧急" in opportunity.delivery_window
                or "急" in opportunity.delivery_window
            ):
                return 10
            elif (
                "正常" in opportunity.delivery_window
                or "常规" in opportunity.delivery_window
            ):
                return 7
            else:
                return 3

        return 7  # 默认正常

    def _calculate_relationship_score(self, lead: Lead) -> int:
        """计算客户关系分数"""
        # 判断是否老客户
        if lead.customer_name:
            customer = (
                self.db.query(Customer)
                .filter(Customer.customer_name == lead.customer_name)
                .first()
            )

            if customer:
                # 查询该客户的历史项目数
                project_count = (
                    self.db.query(Project)
                    .join(Customer)
                    .filter(Customer.id == customer.id, Project.outcome == "WON")
                    .count()
                )

                if project_count > 0:
                    return 10  # 老客户/关系好
                else:
                    return 5  # 新客户/关系一般

        return 5  # 默认分数

    def _calculate_opportunity_relationship(
        self, opportunity: Opportunity, customer: Optional[Customer]
    ) -> int:
        """计算商机客户关系分数"""
        if customer:
            # 查询该客户的历史项目数
            project_count = (
                self.db.query(Project)
                .filter(Project.customer_id == customer.id, Project.outcome == "WON")
                .count()
            )

            if project_count >= 3:
                return 10  # 老客户/关系好
            elif project_count >= 1:
                return 7  # 老客户/关系一般
            else:
                return 5  # 新客户/关系一般

        return 5  # 默认分数

    def _determine_priority_level(self, total_score: int, urgency_score: int) -> str:
        """确定优先级等级"""
        if total_score >= 80 and urgency_score >= 8:
            return "P1"  # 重要且紧急
        elif total_score >= 70:
            return "P2"  # 重要但不紧急
        elif urgency_score >= 8:
            return "P3"  # 不重要但紧急
        else:
            return "P4"  # 不重要且不紧急

    def _determine_importance_level(self, total_score: int) -> str:
        """确定重要程度"""
        if total_score >= 80:
            return "HIGH"
        elif total_score >= 60:
            return "MEDIUM"
        else:
            return "LOW"

    def _determine_urgency_level(self, urgency_score: int) -> str:
        """确定紧急程度"""
        if urgency_score >= 8:
            return "HIGH"
        elif urgency_score >= 5:
            return "MEDIUM"
        else:
            return "LOW"

    # ==================== 描述方法 ====================

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
