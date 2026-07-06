# -*- coding: utf-8 -*-
"""
售前奖金计算器
基于售前工单完成和中标计算奖金
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusRule
from app.models.presale import PresaleSupportTicket
from app.models.project import Project
from app.models.sales import Opportunity
from app.services.bonus.base import BonusCalculatorBase


class PresaleBonusCalculator(BonusCalculatorBase):
    """售前奖金计算器"""

    def __init__(self, db: Session):
        super().__init__(db)

    def _get_urgency_coefficient(self, bonus_rule: BonusRule, urgency: str) -> Decimal:
        coefficients = {}
        trigger_condition = getattr(bonus_rule, "trigger_condition", None)
        if isinstance(trigger_condition, dict):
            coefficients = trigger_condition.get("urgency_coefficients") or {}
        if urgency in coefficients:
            return Decimal(str(coefficients[urgency]))
        if "default" in coefficients:
            return Decimal(str(coefficients["default"]))
        if urgency == "VERY_URGENT":
            return Decimal("1.3")
        if urgency == "URGENT":
            return Decimal("1.1")
        return Decimal("1.0")

    def _get_satisfaction_coefficient(
        self, bonus_rule: BonusRule, satisfaction_score: Optional[int]
    ) -> Decimal:
        coefficients = {}
        trigger_condition = getattr(bonus_rule, "trigger_condition", None)
        if isinstance(trigger_condition, dict):
            coefficients = trigger_condition.get("satisfaction_coefficients") or {}
        if satisfaction_score is not None:
            thresholds = []
            for key, value in coefficients.items():
                if key.startswith("score_gte_"):
                    try:
                        thresholds.append((int(key.removeprefix("score_gte_")), value))
                    except ValueError:
                        continue
            for threshold, value in sorted(thresholds, reverse=True):
                if satisfaction_score >= threshold:
                    return Decimal(str(value))
            if "default" in coefficients:
                return Decimal(str(coefficients["default"]))

            if satisfaction_score >= 5:
                return Decimal("1.2")
            if satisfaction_score >= 4:
                return Decimal("1.0")
            return Decimal("0.8")
        return Decimal(str(coefficients.get("no_score", "1.0")))

    def calculate(
        self,
        ticket: PresaleSupportTicket,
        bonus_rule: BonusRule,
        based_on: str = "COMPLETION",  # COMPLETION: 工单完成, WON: 中标
    ) -> Optional[BonusCalculation]:
        """
        计算售前技术支持奖金

        支持两种计算方式：
        1. 基于工单完成：工单完成时计算
        2. 基于中标：关联商机/项目中标时计算

        Args:
            ticket: 售前支持工单
            bonus_rule: 奖金规则
            based_on: 计算依据（COMPLETION/WON）

        Returns:
            BonusCalculation: 计算记录
        """
        # 检查触发条件
        context = {"ticket": ticket, "based_on": based_on}
        if not self.check_trigger_condition(bonus_rule, context):
            return None

        if not ticket.assignee_id:
            return None

        if based_on == "COMPLETION":
            # 基于工单完成计算
            base_amount = bonus_rule.base_amount or Decimal("0")

            # 根据工单类型和紧急程度调整系数
            urgency_coef = self._get_urgency_coefficient(bonus_rule, ticket.urgency)

            # 根据满意度调整系数
            satisfaction_coef = self._get_satisfaction_coefficient(
                bonus_rule, ticket.satisfaction_score
            )

            calculated_amount = base_amount * urgency_coef * satisfaction_coef

            calculation = BonusCalculation(
                calculation_code=self.generate_calculation_code(),
                rule_id=bonus_rule.id,
                user_id=ticket.assignee_id,
                calculated_amount=calculated_amount,
                calculation_detail={
                    "ticket_no": ticket.ticket_no,
                    "ticket_type": ticket.ticket_type,
                    "urgency": ticket.urgency,
                    "base_amount": float(base_amount),
                    "urgency_coefficient": float(urgency_coef),
                    "satisfaction_coefficient": float(satisfaction_coef),
                    "satisfaction_score": ticket.satisfaction_score,
                    "based_on": "COMPLETION",
                },
                calculation_basis={
                    "type": "presale",
                    "ticket_id": ticket.id,
                    "based_on": "COMPLETION",
                },
                status="CALCULATED",
            )
            return calculation

        elif based_on == "WON":
            # 基于中标计算
            # 查找关联的商机或项目
            opportunity = None
            project = None

            if ticket.opportunity_id:
                opportunity = (
                    self.db.query(Opportunity)
                    .filter(Opportunity.id == ticket.opportunity_id)
                    .first()
                )

            if ticket.project_id:
                project = self.db.query(Project).filter(Project.id == ticket.project_id).first()

            # 检查是否中标
            is_won = False
            won_amount = Decimal("0")

            if opportunity and opportunity.stage == "WON":
                is_won = True
                won_amount = opportunity.est_amount or Decimal("0")
            elif project and project.status in [
                "ST01",
                "ST02",
            ]:  # 假设这些状态表示项目已启动/进行中
                is_won = True
                won_amount = project.contract_amount or Decimal("0")

            if not is_won:
                return None

            # 计算奖金（按中标金额的百分比）
            bonus_ratio = (bonus_rule.coefficient or Decimal("0")) / Decimal("100")
            calculated_amount = won_amount * bonus_ratio

            calculation = BonusCalculation(
                calculation_code=self.generate_calculation_code(),
                rule_id=bonus_rule.id,
                project_id=ticket.project_id,
                user_id=ticket.assignee_id,
                calculated_amount=calculated_amount,
                calculation_detail={
                    "ticket_no": ticket.ticket_no,
                    "won_amount": float(won_amount),
                    "bonus_ratio": float(bonus_ratio),
                    "based_on": "WON",
                    "opportunity_id": ticket.opportunity_id,
                    "project_id": ticket.project_id,
                },
                calculation_basis={
                    "type": "presale",
                    "ticket_id": ticket.id,
                    "based_on": "WON",
                    "opportunity_id": ticket.opportunity_id,
                    "project_id": ticket.project_id,
                },
                status="CALCULATED",
            )
            return calculation

        return None
