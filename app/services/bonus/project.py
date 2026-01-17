# -*- coding: utf-8 -*-
"""
项目奖金计算器
基于项目贡献、里程碑完成、阶段推进计算奖金
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusRule
from app.models.performance import ProjectContribution
from app.models.project import Project, ProjectMember, ProjectMilestone
from app.services.bonus.base import BonusCalculatorBase
from app.services.project_evaluation_service import ProjectEvaluationService


class ProjectBonusCalculator(BonusCalculatorBase):
    """项目奖金计算器"""

    def __init__(self, db: Session):
        super().__init__(db)

    def calculate_by_contribution(
        self,
        project_contribution: ProjectContribution,
        project: Project,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """
        基于项目贡献计算奖金

        Args:
            project_contribution: 项目贡献记录
            project: 项目
            bonus_rule: 奖金规则

        Returns:
            BonusCalculation: 计算记录
        """
        # 检查触发条件
        context = {'project': project, 'project_contribution': project_contribution}
        if not self.check_trigger_condition(bonus_rule, context):
            return None

        # 获取项目金额和贡献占比
        project_amount = project.contract_amount or Decimal('0')
        hours_percentage = project_contribution.hours_percentage or Decimal('0')
        contribution_ratio = hours_percentage / Decimal('100')

        # 计算基础奖金（按项目金额的百分比）
        bonus_ratio = (bonus_rule.coefficient or Decimal('0')) / Decimal('100')
        base_amount = project_amount * bonus_ratio * contribution_ratio

        # 应用项目评价系数（难度、新技术等）
        eval_service = ProjectEvaluationService(self.db)
        difficulty_coef = eval_service.get_difficulty_bonus_coefficient(project)
        new_tech_coef = eval_service.get_new_tech_bonus_coefficient(project)

        # 综合系数（取较高值，或可配置为乘积）
        bonus_coefficient = max(difficulty_coef, new_tech_coef)
        calculated_amount = base_amount * bonus_coefficient

        # 创建计算记录
        calculation = BonusCalculation(
            calculation_code=self.generate_calculation_code(),
            rule_id=bonus_rule.id,
            project_id=project.id,
            user_id=project_contribution.user_id,
            project_contribution_id=project_contribution.id,
            calculated_amount=calculated_amount,
            calculation_detail={
                "project_amount": float(project_amount),
                "contribution_ratio": float(contribution_ratio),
                "bonus_ratio": float(bonus_ratio),
                "base_amount": float(base_amount),
                "difficulty_coefficient": float(difficulty_coef),
                "new_tech_coefficient": float(new_tech_coef),
                "final_coefficient": float(bonus_coefficient),
                "hours_spent": float(project_contribution.hours_spent) if project_contribution.hours_spent else 0
            },
            calculation_basis={
                "type": "project",
                "project_id": project.id,
                "project_contribution_id": project_contribution.id
            },
            status='CALCULATED'
        )

        return calculation

    def calculate_by_milestone(
        self,
        milestone: ProjectMilestone,
        project: Project,
        bonus_rule: BonusRule
    ) -> List[BonusCalculation]:
        """
        基于里程碑完成计算奖金（可能涉及多个项目成员）

        Args:
            milestone: 项目里程碑
            project: 项目
            bonus_rule: 奖金规则

        Returns:
            List[BonusCalculation]: 计算记录列表
        """
        # 检查触发条件
        context = {'milestone': milestone, 'project': project}
        if not self.check_trigger_condition(bonus_rule, context):
            return []

        calculations = []

        # 获取项目成员
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.is_active == True
        ).all()

        if not members:
            return []

        # 按角色分配奖金
        base_amount = bonus_rule.base_amount or Decimal('0')

        # 应用项目评价系数（如果项目有评价）
        eval_service = ProjectEvaluationService(self.db)
        project_coef = eval_service.get_bonus_coefficient(project)

        for member in members:
            role_coefficient = self.get_role_coefficient(member.role_code, bonus_rule)
            base_with_role = base_amount * role_coefficient
            amount = base_with_role * project_coef

            calculation = BonusCalculation(
                calculation_code=self.generate_calculation_code(),
                rule_id=bonus_rule.id,
                project_id=project.id,
                milestone_id=milestone.id,
                user_id=member.user_id,
                calculated_amount=amount,
                calculation_detail={
                    "milestone_name": milestone.milestone_name,
                    "milestone_type": milestone.milestone_type,
                    "role": member.role_code,
                    "role_coefficient": float(role_coefficient),
                    "project_coefficient": float(project_coef),
                    "base_amount": float(base_with_role)
                },
                calculation_basis={
                    "type": "milestone",
                    "project_id": project.id,
                    "milestone_id": milestone.id
                },
                status='CALCULATED'
            )
            calculations.append(calculation)

        return calculations

    def calculate_by_stage(
        self,
        project: Project,
        old_stage: str,
        new_stage: str,
        bonus_rule: BonusRule
    ) -> List[BonusCalculation]:
        """
        基于项目阶段推进计算奖金

        Args:
            project: 项目
            old_stage: 旧阶段
            new_stage: 新阶段
            bonus_rule: 奖金规则

        Returns:
            List[BonusCalculation]: 计算记录列表
        """
        # 检查是否触发阶段奖金规则
        context = {'project': project, 'stage': new_stage}
        if not self.check_trigger_condition(bonus_rule, context):
            return []

        calculations = []

        # 获取项目成员
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id
        ).all()

        if not members:
            return []

        # 按角色分配奖金
        base_amount = bonus_rule.base_amount or Decimal('0')
        for member in members:
            role_coefficient = self.get_role_coefficient(member.role_code, bonus_rule)
            amount = base_amount * role_coefficient

            # 应用项目评价系数
            eval_service = ProjectEvaluationService(self.db)
            project_coef = eval_service.get_bonus_coefficient(project)
            final_amount = amount * project_coef

            calculation = BonusCalculation(
                calculation_code=self.generate_calculation_code(),
                rule_id=bonus_rule.id,
                project_id=project.id,
                user_id=member.user_id,
                calculated_amount=final_amount,
                calculation_detail={
                    "old_stage": old_stage,
                    "new_stage": new_stage,
                    "role": member.role_code,
                    "role_coefficient": float(role_coefficient),
                    "project_coefficient": float(project_coef),
                    "base_amount": float(amount)
                },
                calculation_basis={
                    "type": "stage",
                    "project_id": project.id,
                    "old_stage": old_stage,
                    "new_stage": new_stage
                },
                status='CALCULATED'
            )
            calculations.append(calculation)

        return calculations
