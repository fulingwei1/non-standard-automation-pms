# -*- coding: utf-8 -*-
"""
验收奖金计算服务
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusRule, TeamBonusAllocation
from app.models.enums import TeamBonusAllocationMethodEnum
from app.models.presale import PresaleSupportTicket
from app.models.project import Project, ProjectMember
from app.models.sales import Contract, Opportunity
from app.services.project_evaluation_service import ProjectEvaluationService


def get_active_rules(
    db: Session,
    bonus_type: str
) -> List[BonusRule]:
    """
    获取激活的奖金规则

    Returns:
        List[BonusRule]: 奖金规则列表
    """
    return db.query(BonusRule).filter(
        BonusRule.bonus_type == bonus_type,
        BonusRule.is_active
    ).all()


def calculate_sales_bonus(
    db: Session,
    project: Project,
    sales_rules: List[BonusRule]
) -> Optional[TeamBonusAllocation]:
    """
    计算销售奖金总额（团队奖金）

    Returns:
        Optional[TeamBonusAllocation]: 团队奖金分配记录，如果计算失败返回None
    """
    try:
        contract = db.query(Contract).filter(
           Contract.contract_code == project.contract_no
        ).first()

        if not contract:
            return None

        for rule in sales_rules:
            # 检查触发条件：验收完成
            trigger_condition = rule.trigger_condition or {}
            if trigger_condition.get('acceptance_completed') or not trigger_condition:
                # 计算总奖金（不分配到个人）
                bonus_ratio = (rule.coefficient or Decimal('0')) / Decimal('100')
                contract_amount = contract.contract_amount or Decimal('0')
                total_bonus = contract_amount * bonus_ratio

                if total_bonus > 0:
                    # 创建团队奖金分配记录
                    allocation = TeamBonusAllocation(
                        project_id=project.id,
                        total_bonus_amount=total_bonus,
                        allocation_method=TeamBonusAllocationMethodEnum.CUSTOM.value,
                        allocation_detail={
                            "bonus_type": "SALES_BASED",
                            "rule_id": rule.id,
                            "rule_name": rule.rule_name,
                            "contract_id": contract.id,
                            "contract_amount": float(contract_amount),
                            "bonus_ratio": float(bonus_ratio),
                            "calculation_basis": {
                                "type": "sales",
                                "contract_id": contract.id,
                                "based_on": "CONTRACT"
                            }
                        },
                        status='PENDING'  # 待审批
                    )
                    db.add(allocation)
                    return allocation

        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"计算销售奖金总额失败: {str(e)}", exc_info=True)
        return None


def calculate_presale_bonus(
    db: Session,
    project: Project,
    presale_rules: List[BonusRule]
) -> Optional[TeamBonusAllocation]:
    """
    计算售前技术奖金总额（团队奖金）

    Returns:
        Optional[TeamBonusAllocation]: 团队奖金分配记录，如果计算失败返回None
    """
    try:
        if not presale_rules:
            return None

        # 查找项目关联的售前工单
        presale_tickets = db.query(PresaleSupportTicket).filter(
            PresaleSupportTicket.project_id == project.id,
            PresaleSupportTicket.status == 'COMPLETED'
        ).all()

        if not presale_tickets:
            return None

        # 计算总奖金（基于中标）
        for rule in presale_rules:
            # 使用第一个工单作为代表计算总奖金
            ticket = presale_tickets[0]

            # 查找关联的商机或项目
            opportunity = None
            if ticket.opportunity_id:
                opportunity = db.query(Opportunity).filter(
                    Opportunity.id == ticket.opportunity_id
                ).first()

            won_amount = Decimal('0')
            if opportunity and opportunity.stage == 'WON':
                won_amount = opportunity.est_amount or Decimal('0')
            elif project and project.status in ['ST01', 'ST02']:
                won_amount = project.contract_amount or Decimal('0')

            if won_amount > 0:
                # 计算总奖金（按中标金额的百分比）
                bonus_ratio = (rule.coefficient or Decimal('0')) / Decimal('100')
                total_bonus = won_amount * bonus_ratio

                if total_bonus > 0:
                    # 统计参与售前支持的人员数量（用于后续分配参考）
                    assignee_ids = list(set([t.assignee_id for t in presale_tickets if t.assignee_id]))

                    # 创建团队奖金分配记录
                    allocation = TeamBonusAllocation(
                        project_id=project.id,
                        total_bonus_amount=total_bonus,
                        allocation_method=TeamBonusAllocationMethodEnum.CUSTOM.value,
                        allocation_detail={
                            "bonus_type": "PRESALE_BASED",
                            "rule_id": rule.id,
                            "rule_name": rule.rule_name,
                            "won_amount": float(won_amount),
                            "bonus_ratio": float(bonus_ratio),
                            "ticket_count": len(presale_tickets),
                            "participant_count": len(assignee_ids),
                            "participant_ids": assignee_ids,
                            "calculation_basis": {
                                "type": "presale",
                                "ticket_ids": [t.id for t in presale_tickets],
                                "based_on": "WON"
                            }
                        },
                        status='PENDING'  # 待审批
                    )
                    db.add(allocation)
                    return allocation

        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"计算售前技术奖金总额失败: {str(e)}", exc_info=True)
        return None


def calculate_project_bonus(
    db: Session,
    project: Project,
    project_rules: List[BonusRule]
) -> Optional[TeamBonusAllocation]:
    """
    计算项目奖金总额（团队奖金）

    Returns:
        Optional[TeamBonusAllocation]: 团队奖金分配记录，如果计算失败返回None
    """
    try:
        if not project_rules:
            return None

        # 计算总奖金（按项目金额的百分比）
        for rule in project_rules:
            bonus_ratio = (rule.coefficient or Decimal('0')) / Decimal('100')
            project_amount = project.contract_amount or Decimal('0')
            total_bonus = project_amount * bonus_ratio

            # 应用项目评价系数
            eval_service = ProjectEvaluationService(db)
            difficulty_coef = eval_service.get_difficulty_bonus_coefficient(project)
            new_tech_coef = eval_service.get_new_tech_bonus_coefficient(project)
            bonus_coefficient = max(difficulty_coef, new_tech_coef)
            total_bonus = total_bonus * bonus_coefficient

            if total_bonus > 0:
                # 获取项目成员信息（用于后续分配参考）
                members = db.query(ProjectMember).filter(
                    ProjectMember.project_id == project.id,
                    ProjectMember.is_active
                ).all()

                # 获取项目贡献记录（如果有）
                from app.models.performance import ProjectContribution
                contributions = db.query(ProjectContribution).filter(
                    ProjectContribution.project_id == project.id
                ).all()

                # 创建团队奖金分配记录
                allocation = TeamBonusAllocation(
                    project_id=project.id,
                    total_bonus_amount=total_bonus,
                    allocation_method=TeamBonusAllocationMethodEnum.CUSTOM.value,
                    allocation_detail={
                        "bonus_type": "PROJECT_BASED",
                        "rule_id": rule.id,
                        "rule_name": rule.rule_name,
                        "project_amount": float(project_amount),
                        "bonus_ratio": float(bonus_ratio),
                        "difficulty_coefficient": float(difficulty_coef),
                        "new_tech_coefficient": float(new_tech_coef),
                        "final_coefficient": float(bonus_coefficient),
                        "member_count": len(members),
                        "contribution_count": len(contributions),
                        "calculation_basis": {
                            "type": "project",
                            "project_id": project.id,
                            "has_contributions": len(contributions) > 0
                        }
                    },
                    status='PENDING'  # 待审批
                )
                db.add(allocation)
                return allocation

        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"计算项目奖金总额失败: {str(e)}", exc_info=True)
        return None
