# -*- coding: utf-8 -*-
"""
奖金计算引擎
提供各类奖金的计算逻辑
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.bonus import (
    BonusRule, BonusCalculation, BonusDistribution, TeamBonusAllocation
)
from app.models.performance import PerformanceResult, ProjectContribution
from app.models.project import Project, ProjectMilestone, ProjectMember
from app.models.acceptance import AcceptanceOrder
from app.models.sales import Contract, Invoice, Opportunity
from app.models.presale import PresaleSupportTicket, PresaleSolution
from app.models.enums import BonusTypeEnum, PerformanceLevelEnum
from app.services.project_evaluation_service import ProjectEvaluationService


class BonusCalculator:
    """奖金计算引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_trigger_condition(
        self,
        bonus_rule: BonusRule,
        context: Dict[str, Any]
    ) -> bool:
        """
        检查触发条件是否满足
        
        Args:
            bonus_rule: 奖金规则
            context: 上下文数据（包含绩效结果、项目、里程碑等信息）
        
        Returns:
            bool: 是否满足触发条件
        """
        if not bonus_rule.trigger_condition:
            return True
        
        condition = bonus_rule.trigger_condition
        
        # 检查绩效等级
        if 'performance_level' in condition:
            performance_result = context.get('performance_result')
            if not performance_result:
                return False
            if performance_result.level != condition['performance_level']:
                return False
        
        # 检查最低分数
        if 'min_score' in condition:
            performance_result = context.get('performance_result')
            if not performance_result or not performance_result.total_score:
                return False
            if float(performance_result.total_score) < condition['min_score']:
                return False
        
        # 检查里程碑类型
        if 'milestone_type' in condition:
            milestone = context.get('milestone')
            if not milestone:
                return False
            if milestone.milestone_type != condition['milestone_type']:
                return False
        
        # 检查里程碑状态
        if 'milestone_status' in condition:
            milestone = context.get('milestone')
            if not milestone:
                return False
            if milestone.status != condition['milestone_status']:
                return False
        
        # 检查项目阶段
        if 'stage' in condition:
            project = context.get('project')
            if not project:
                return False
            if project.stage != condition['stage']:
                return False
        
        return True
    
    def get_coefficient_by_level(self, level: str) -> Decimal:
        """
        根据绩效等级获取系数
        
        Args:
            level: 绩效等级
        
        Returns:
            Decimal: 系数
        """
        coefficients = {
            PerformanceLevelEnum.EXCELLENT: Decimal('1.5'),
            PerformanceLevelEnum.GOOD: Decimal('1.2'),
            PerformanceLevelEnum.QUALIFIED: Decimal('1.0'),
            PerformanceLevelEnum.NEEDS_IMPROVEMENT: Decimal('0.8'),
        }
        return coefficients.get(level, Decimal('1.0'))
    
    def get_role_coefficient(self, role_code: str, bonus_rule: BonusRule) -> Decimal:
        """
        根据角色获取系数
        
        Args:
            role_code: 角色编码
            bonus_rule: 奖金规则
        
        Returns:
            Decimal: 系数
        """
        # 默认角色系数（可在规则中配置）
        default_coefficients = {
            'PM': Decimal('1.5'),      # 项目经理
            'ME': Decimal('1.2'),     # 机械负责
            'EE': Decimal('1.2'),     # 电气负责
            'SW': Decimal('1.1'),     # 软件负责
            'DEBUG': Decimal('1.0'),   # 调试负责
            'QA': Decimal('1.0'),      # 质量负责
        }
        
        # 如果规则中有配置，使用规则配置
        if bonus_rule.trigger_condition and 'role_coefficients' in bonus_rule.trigger_condition:
            role_coefficients = bonus_rule.trigger_condition['role_coefficients']
            return Decimal(str(role_coefficients.get(role_code, 1.0)))
        
        return default_coefficients.get(role_code, Decimal('1.0'))
    
    def generate_calculation_code(self) -> str:
        """生成计算单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"BC{timestamp}"
    
    def calculate_performance_bonus(
        self,
        performance_result: PerformanceResult,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """
        基于绩效结果计算奖金
        
        Args:
            performance_result: 绩效结果
            bonus_rule: 奖金规则
        
        Returns:
            BonusCalculation: 计算记录，如果不满足条件则返回None
        """
        # 检查触发条件
        context = {'performance_result': performance_result}
        if not self.check_trigger_condition(bonus_rule, context):
            return None
        
        # 获取计算参数
        base_amount = bonus_rule.base_amount or Decimal('0')
        coefficient = self.get_coefficient_by_level(performance_result.level)
        
        # 计算奖金
        calculated_amount = base_amount * coefficient
        
        # 创建计算记录
        calculation = BonusCalculation(
            calculation_code=self.generate_calculation_code(),
            rule_id=bonus_rule.id,
            period_id=performance_result.period_id,
            user_id=performance_result.user_id,
            performance_result_id=performance_result.id,
            calculated_amount=calculated_amount,
            calculation_detail={
                "base_amount": float(base_amount),
                "coefficient": float(coefficient),
                "performance_level": performance_result.level,
                "performance_score": float(performance_result.total_score) if performance_result.total_score else 0
            },
            calculation_basis={
                "type": "performance",
                "period_id": performance_result.period_id,
                "performance_result_id": performance_result.id
            },
            status='CALCULATED'
        )
        
        return calculation
    
    def calculate_project_bonus(
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
    
    def calculate_milestone_bonus(
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
        # 注意：ProjectMember表没有machine_id字段，这里获取项目所有成员
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
    
    def calculate_stage_bonus(
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
    
    def calculate_team_bonus(
        self,
        project: Project,
        bonus_rule: BonusRule,
        period_id: Optional[int] = None
    ) -> TeamBonusAllocation:
        """
        计算团队总奖金并分配
        
        Args:
            project: 项目
            bonus_rule: 奖金规则
            period_id: 周期ID（可选）
        
        Returns:
            TeamBonusAllocation: 团队奖金分配记录
        """
        # 计算团队总奖金（基于项目金额）
        project_amount = project.contract_amount or Decimal('0')
        coefficient = bonus_rule.coefficient or Decimal('0')
        total_bonus = project_amount * (coefficient / Decimal('100'))
        
        # 获取项目成员贡献
        query = self.db.query(ProjectContribution).filter(
            ProjectContribution.project_id == project.id
        )
        if period_id:
            query = query.filter(ProjectContribution.period_id == period_id)
        contributions = query.all()
        
        # 按贡献分配
        allocation_detail = []
        # 使用工时占比作为贡献度
        total_contribution = sum(
            float(c.hours_percentage) if c.hours_percentage else 0
            for c in contributions
        )
        
        if total_contribution > 0:
            for contrib in contributions:
                contribution_score = float(contrib.hours_percentage) if contrib.hours_percentage else 0
                ratio = contribution_score / total_contribution
                amount = total_bonus * Decimal(str(ratio))
                
                allocation_detail.append({
                    "user_id": contrib.user_id,
                    "contribution_score": contribution_score,
                    "ratio": float(ratio),
                    "amount": float(amount)
                })
        else:
            # 如果没有贡献记录，平均分配
            members = self.db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id
            ).all()
            if members:
                avg_amount = total_bonus / Decimal(str(len(members)))
                for member in members:
                    allocation_detail.append({
                        "user_id": member.user_id,
                        "contribution_score": 0,
                        "ratio": 1.0 / len(members),
                        "amount": float(avg_amount)
                    })
        
        # 创建团队奖金分配记录
        team_allocation = TeamBonusAllocation(
            project_id=project.id,
            period_id=period_id,
            total_bonus_amount=total_bonus,
            allocation_method='BY_CONTRIBUTION' if total_contribution > 0 else 'EQUAL',
            allocation_detail=allocation_detail,
            status='PENDING'
        )
        
        return team_allocation
    
    def calculate_sales_bonus(
        self,
        contract: Contract,
        bonus_rule: BonusRule,
        based_on: str = 'CONTRACT'  # CONTRACT: 合同签订, PAYMENT: 回款
    ) -> Optional[BonusCalculation]:
        """
        计算销售奖金
        
        支持两种计算方式：
        1. 基于合同签订：合同签订时计算
        2. 基于回款：发票回款时计算
        
        Args:
            contract: 合同对象
            bonus_rule: 奖金规则
            based_on: 计算依据（CONTRACT/PAYMENT）
        
        Returns:
            BonusCalculation: 计算记录
        """
        # 检查触发条件
        context = {'contract': contract, 'based_on': based_on}
        if not self.check_trigger_condition(bonus_rule, context):
            return None
        
        if not contract.owner_id:
            return None
        
        contract_amount = contract.contract_amount or Decimal('0')
        
        if based_on == 'CONTRACT':
            # 基于合同金额计算
            bonus_ratio = (bonus_rule.coefficient or Decimal('0')) / Decimal('100')
            calculated_amount = contract_amount * bonus_ratio
            
            calculation = BonusCalculation(
                calculation_code=self.generate_calculation_code(),
                rule_id=bonus_rule.id,
                project_id=contract.project_id,
                user_id=contract.owner_id,
                calculated_amount=calculated_amount,
                calculation_detail={
                    "contract_code": contract.contract_code,
                    "contract_amount": float(contract_amount),
                    "bonus_ratio": float(bonus_ratio),
                    "based_on": "CONTRACT"
                },
                calculation_basis={
                    "type": "sales",
                    "contract_id": contract.id,
                    "based_on": "CONTRACT"
                },
                status='CALCULATED'
            )
            return calculation
        
        elif based_on == 'PAYMENT':
            # 基于回款金额计算
            # 获取该合同的所有已回款发票
            invoices = self.db.query(Invoice).filter(
                Invoice.contract_id == contract.id,
                Invoice.payment_status == 'PAID'
            ).all()
            
            total_paid = sum(float(inv.paid_amount or inv.total_amount or 0) for inv in invoices)
            
            if total_paid <= 0:
                return None
            
            bonus_ratio = (bonus_rule.coefficient or Decimal('0')) / Decimal('100')
            calculated_amount = Decimal(str(total_paid)) * bonus_ratio
            
            calculation = BonusCalculation(
                calculation_code=self.generate_calculation_code(),
                rule_id=bonus_rule.id,
                project_id=contract.project_id,
                user_id=contract.owner_id,
                calculated_amount=calculated_amount,
                calculation_detail={
                    "contract_code": contract.contract_code,
                    "total_paid": total_paid,
                    "bonus_ratio": float(bonus_ratio),
                    "based_on": "PAYMENT",
                    "invoice_count": len(invoices)
                },
                calculation_basis={
                    "type": "sales",
                    "contract_id": contract.id,
                    "based_on": "PAYMENT",
                    "invoice_ids": [inv.id for inv in invoices]
                },
                status='CALCULATED'
            )
            return calculation
        
        return None
    
    def calculate_sales_director_bonus(
        self,
        director_id: int,
        period_start: date,
        period_end: date,
        bonus_rule: BonusRule
    ) -> Optional[BonusCalculation]:
        """
        计算销售总监奖金（基于团队业绩）
        
        Args:
            director_id: 销售总监ID
            period_start: 统计周期开始日期
            period_end: 统计周期结束日期
            bonus_rule: 奖金规则
        
        Returns:
            BonusCalculation: 计算记录
        """
        # 检查触发条件
        context = {
            'director_id': director_id,
            'period_start': period_start,
            'period_end': period_end
        }
        if not self.check_trigger_condition(bonus_rule, context):
            return None
        
        # 获取该总监管理的销售团队业绩
        # 方式1：通过部门关系查找下属
        # 方式2：通过角色关系查找（假设有销售经理角色）
        # 这里先简化处理，查询该周期内所有合同
        
        # 查询周期内签订的合同
        contracts = self.db.query(Contract).filter(
            Contract.signed_date >= period_start,
            Contract.signed_date <= period_end,
            Contract.status == 'SIGNED'
        ).all()
        
        if not contracts:
            return None
        
        # 计算团队总业绩
        total_amount = sum(float(c.contract_amount or 0) for c in contracts)
        
        # 计算奖金（按团队业绩的百分比）
        bonus_ratio = (bonus_rule.coefficient or Decimal('0')) / Decimal('100')
        calculated_amount = Decimal(str(total_amount)) * bonus_ratio
        
        # 统计信息
        contract_count = len(contracts)
        sales_person_ids = list(set([c.owner_id for c in contracts if c.owner_id]))
        
        calculation = BonusCalculation(
            calculation_code=self.generate_calculation_code(),
            rule_id=bonus_rule.id,
            user_id=director_id,
            calculated_amount=calculated_amount,
            calculation_detail={
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "total_team_amount": total_amount,
                "contract_count": contract_count,
                "sales_person_count": len(sales_person_ids),
                "bonus_ratio": float(bonus_ratio)
            },
            calculation_basis={
                "type": "sales_director",
                "director_id": director_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "contract_ids": [c.id for c in contracts],
                "sales_person_ids": sales_person_ids
            },
            status='CALCULATED'
        )
        
        return calculation
    
    def calculate_presale_bonus(
        self,
        ticket: PresaleSupportTicket,
        bonus_rule: BonusRule,
        based_on: str = 'COMPLETION'  # COMPLETION: 工单完成, WON: 中标
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
        context = {'ticket': ticket, 'based_on': based_on}
        if not self.check_trigger_condition(bonus_rule, context):
            return None
        
        if not ticket.assignee_id:
            return None
        
        if based_on == 'COMPLETION':
            # 基于工单完成计算
            base_amount = bonus_rule.base_amount or Decimal('0')
            
            # 根据工单类型和紧急程度调整系数
            urgency_coef = Decimal('1.0')
            if ticket.urgency == 'VERY_URGENT':
                urgency_coef = Decimal('1.3')
            elif ticket.urgency == 'URGENT':
                urgency_coef = Decimal('1.1')
            
            # 根据满意度调整系数
            satisfaction_coef = Decimal('1.0')
            if ticket.satisfaction_score:
                if ticket.satisfaction_score >= 5:
                    satisfaction_coef = Decimal('1.2')
                elif ticket.satisfaction_score >= 4:
                    satisfaction_coef = Decimal('1.0')
                else:
                    satisfaction_coef = Decimal('0.8')
            
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
                    "based_on": "COMPLETION"
                },
                calculation_basis={
                    "type": "presale",
                    "ticket_id": ticket.id,
                    "based_on": "COMPLETION"
                },
                status='CALCULATED'
            )
            return calculation
        
        elif based_on == 'WON':
            # 基于中标计算
            # 查找关联的商机或项目
            opportunity = None
            project = None
            
            if ticket.opportunity_id:
                opportunity = self.db.query(Opportunity).filter(
                    Opportunity.id == ticket.opportunity_id
                ).first()
            
            if ticket.project_id:
                project = self.db.query(Project).filter(
                    Project.id == ticket.project_id
                ).first()
            
            # 检查是否中标
            is_won = False
            won_amount = Decimal('0')
            
            if opportunity and opportunity.stage == 'WON':
                is_won = True
                won_amount = opportunity.est_amount or Decimal('0')
            elif project and project.status in ['ST01', 'ST02']:  # 假设这些状态表示项目已启动/进行中
                is_won = True
                won_amount = project.contract_amount or Decimal('0')
            
            if not is_won:
                return None
            
            # 计算奖金（按中标金额的百分比）
            bonus_ratio = (bonus_rule.coefficient or Decimal('0')) / Decimal('100')
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
                    "project_id": ticket.project_id
                },
                calculation_basis={
                    "type": "presale",
                    "ticket_id": ticket.id,
                    "based_on": "WON",
                    "opportunity_id": ticket.opportunity_id,
                    "project_id": ticket.project_id
                },
                status='CALCULATED'
            )
            return calculation
        
        return None
    
    def trigger_acceptance_bonus_calculation(
        self,
        project: Project,
        acceptance_order
    ) -> List[Any]:
        """
        验收完成后触发奖金计算（仅计算总奖金，不分配到个人）
        
        计算以下总奖金：
        1. 销售奖金总额（给销售部门/团队）
        2. 售前技术奖金总额（给售前技术支持部门）
        3. 项目奖金总额（给项目团队）
        
        注意：个人奖金分配需要通过Excel导入，不会自动创建个人奖金记录
        
        Args:
            project: 项目
            acceptance_order: 验收单
        
        Returns:
            List: 团队奖金分配记录列表
        """
        from app.services.acceptance_bonus_service import (
            get_active_rules,
            calculate_sales_bonus,
            calculate_presale_bonus,
            calculate_project_bonus
        )
        
        allocations = []
        
        # 1. 计算销售奖金总额（团队奖金）
        sales_rules = get_active_rules(self.db, bonus_type='SALES_BASED')
        sales_allocation = calculate_sales_bonus(self.db, project, sales_rules)
        if sales_allocation:
            allocations.append(sales_allocation)
        
        # 2. 计算售前技术奖金总额（团队奖金）
        presale_rules = get_active_rules(self.db, bonus_type='PRESALE_BASED')
        presale_allocation = calculate_presale_bonus(self.db, project, presale_rules)
        if presale_allocation:
            allocations.append(presale_allocation)
        
        # 3. 计算项目奖金总额（团队奖金）
        project_rules = get_active_rules(self.db, bonus_type='PROJECT_BASED')
        project_allocation = calculate_project_bonus(self.db, project, project_rules)
        if project_allocation:
            allocations.append(project_allocation)
        
        # 提交所有团队奖金分配记录
        if allocations:
            self.db.flush()
        
        return allocations
    
    def get_active_rules(
        self,
        bonus_type: Optional[str] = None
    ) -> List[BonusRule]:
        """
        获取启用的奖金规则
        
        Args:
            bonus_type: 奖金类型（可选）
        
        Returns:
            List[BonusRule]: 规则列表
        """
        query = self.db.query(BonusRule).filter(BonusRule.is_active == True)
        
        # 检查生效日期
        today = date.today()
        query = query.filter(
            (BonusRule.effective_start_date.is_(None)) |
            (BonusRule.effective_start_date <= today)
        )
        query = query.filter(
            (BonusRule.effective_end_date.is_(None)) |
            (BonusRule.effective_end_date >= today)
        )
        
        if bonus_type:
            query = query.filter(BonusRule.bonus_type == bonus_type)
        
        # 按优先级排序
        query = query.order_by(BonusRule.priority.desc())
        
        return query.all()

