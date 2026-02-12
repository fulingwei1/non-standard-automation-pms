# -*- coding: utf-8 -*-
"""
奖金计算器主类
整合所有奖金计算模块
"""

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusRule, TeamBonusAllocation
from app.models.performance import PerformanceResult, ProjectContribution
from app.models.presale import PresaleSupportTicket
from app.models.project import Project, ProjectMilestone
from app.models.sales import Contract
from app.services.bonus.acceptance import AcceptanceBonusTrigger
from app.services.bonus.base import BonusCalculatorBase
from app.services.bonus.performance import PerformanceBonusCalculator
from app.services.bonus.presale import PresaleBonusCalculator
from app.services.bonus.project import ProjectBonusCalculator
from app.services.bonus.sales import SalesBonusCalculator
from app.services.bonus.team import TeamBonusCalculator


class BonusCalculator(BonusCalculatorBase):
    """
    奖金计算引擎主类
    整合所有奖金计算模块
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.performance_calculator = PerformanceBonusCalculator(db)
        self.project_calculator = ProjectBonusCalculator(db)
        self.sales_calculator = SalesBonusCalculator(db)
        self.team_calculator = TeamBonusCalculator(db)
        self.presale_calculator = PresaleBonusCalculator(db)
        self.acceptance_trigger = AcceptanceBonusTrigger(db)

    # 绩效奖金计算
    def calculate_performance_bonus(
        self,
        performance_result: PerformanceResult,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """基于绩效结果计算奖金"""
        return self.performance_calculator.calculate(performance_result, bonus_rule)

    # 项目奖金计算
    def calculate_project_bonus(
        self,
        project_contribution: ProjectContribution,
        project: Project,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """基于项目贡献计算奖金"""
        return self.project_calculator.calculate_by_contribution(
            project_contribution, project, bonus_rule
        )

    def calculate_milestone_bonus(
        self,
        milestone: ProjectMilestone,
        project: Project,
        bonus_rule: BonusRule
    ) -> List[BonusCalculation]:
        """基于里程碑完成计算奖金"""
        return self.project_calculator.calculate_by_milestone(
            milestone, project, bonus_rule
        )

    def calculate_stage_bonus(
        self,
        project: Project,
        old_stage: str,
        new_stage: str,
        bonus_rule: BonusRule
    ) -> List[BonusCalculation]:
        """基于项目阶段推进计算奖金"""
        return self.project_calculator.calculate_by_stage(
            project, old_stage, new_stage, bonus_rule
        )

    # 销售奖金计算
    def calculate_sales_bonus(
        self,
        contract: Contract,
        bonus_rule: BonusRule,
        based_on: str = 'CONTRACT'
    ) -> Optional[BonusCalculation]:
        """计算销售奖金"""
        return self.sales_calculator.calculate(contract, bonus_rule, based_on)

    def calculate_sales_director_bonus(
        self,
        director_id: int,
        period_start: date,
        period_end: date,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """计算销售总监奖金"""
        return self.sales_calculator.calculate_director_bonus(
            director_id, period_start, period_end, bonus_rule
        )

    # 团队奖金计算
    def calculate_team_bonus(
        self,
        project: Project,
        bonus_rule: BonusRule,
        period_id: Optional[int] = None
    ) -> TeamBonusAllocation:
        """计算团队总奖金并分配"""
        return self.team_calculator.calculate(project, bonus_rule, period_id)

    # 售前奖金计算
    def calculate_presale_bonus(
        self,
        ticket: PresaleSupportTicket,
        bonus_rule: BonusRule,
        based_on: str = 'COMPLETION'
    ) -> Optional[BonusCalculation]:
        """计算售前技术支持奖金"""
        return self.presale_calculator.calculate(ticket, bonus_rule, based_on)

    # 验收奖金触发
    def trigger_acceptance_bonus_calculation(
        self,
        project: Project,
        acceptance_order
    ) -> List:
        """验收完成后触发奖金计算"""
        return self.acceptance_trigger.trigger_calculation(project, acceptance_order)
