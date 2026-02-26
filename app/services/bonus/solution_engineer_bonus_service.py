# -*- coding: utf-8 -*-
"""
方案工程师奖金补偿服务
实现方案完成奖金、中标奖金、高质量方案补偿、成功率奖励
"""

from decimal import Decimal
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.performance import PerformancePeriod
from app.models.presale import (
    PresaleSolution,
    PresaleSupportTicket,
)
from app.models.sales import Contract


class SolutionEngineerBonusService:
    """方案工程师奖金补偿服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_solution_bonus(
        self,
        engineer_id: int,
        period_id: int,
        base_bonus_per_solution: Decimal = Decimal('500'),  # 每个方案基础奖金500元
        won_bonus_ratio: Decimal = Decimal('0.001'),  # 中标奖金比例0.1%
        high_quality_compensation: Decimal = Decimal('300'),  # 高质量方案补偿300元
        success_rate_bonus: Decimal = Decimal('2000')  # 成功率奖励2000元
    ) -> Dict[str, Any]:
        """
        计算方案工程师奖金

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID
            base_bonus_per_solution: 每个方案的基础奖金
            won_bonus_ratio: 中标奖金比例
            high_quality_compensation: 高质量方案补偿金额
            success_rate_bonus: 成功率奖励金额

        Returns:
            奖金计算详情
        """
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 获取周期内的所有方案
        solutions = self.db.query(PresaleSolution).filter(
            PresaleSolution.author_id == engineer_id,
            PresaleSolution.created_at.between(period.start_date, period.end_date)
        ).all()

        if not solutions:
            return {
                'engineer_id': engineer_id,
                'period_id': period_id,
                'total_solutions': 0,
                'completion_bonus': 0.0,
                'won_bonus': 0.0,
                'high_quality_compensation': 0.0,
                'success_rate_bonus': 0.0,
                'total_bonus': 0.0,
                'details': []
            }

        completion_bonus = Decimal('0')
        won_bonus = Decimal('0')
        high_quality_compensation_total = Decimal('0')
        won_solutions = []
        high_quality_unwon = []

        for solution in solutions:
            # 1. 方案完成奖金（每个完成的方案）
            if solution.status in ['APPROVED', 'SUBMITTED']:
                completion_bonus += base_bonus_per_solution

            # 2. 检查是否中标
            contract_amount = Decimal('0')
            if solution.opportunity_id:
                contract = self.db.query(Contract).filter(
                    Contract.opportunity_id == solution.opportunity_id,
                    Contract.status == 'SIGNED'
                ).first()
                if contract:
                    won_solutions.append(solution)
                    contract_amount = contract.contract_amount or Decimal('0')
                    # 中标奖金 = 合同金额 × 奖金比例
                    won_bonus += contract_amount * won_bonus_ratio

            # 3. 高质量方案补偿（未中标但质量评分≥4.5）
            if solution.ticket_id:
                ticket = self.db.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id == solution.ticket_id
                ).first()
                if ticket and ticket.satisfaction_score and ticket.satisfaction_score >= 4.5:
                    # 检查是否未中标
                    if solution not in won_solutions:
                        high_quality_unwon.append(solution)
                        high_quality_compensation_total += high_quality_compensation

        # 4. 成功率奖励（季度中标率≥40%）
        win_rate = len(won_solutions) / len(solutions) * 100 if solutions else 0
        success_rate_bonus_amount = Decimal('0')
        if win_rate >= 40:
            success_rate_bonus_amount = success_rate_bonus

        total_bonus = completion_bonus + won_bonus + high_quality_compensation_total + success_rate_bonus_amount

        return {
            'engineer_id': engineer_id,
            'period_id': period_id,
            'period_name': period.period_name,
            'total_solutions': len(solutions),
            'won_solutions': len(won_solutions),
            'win_rate': round(win_rate, 2),
            'high_quality_unwon_count': len(high_quality_unwon),
            'completion_bonus': float(completion_bonus),
            'won_bonus': float(won_bonus),
            'high_quality_compensation': float(high_quality_compensation_total),
            'success_rate_bonus': float(success_rate_bonus_amount),
            'total_bonus': float(total_bonus),
            'details': [
                {
                    'solution_id': s.id,
                    'solution_no': s.solution_no,
                    'solution_name': s.name,
                    'is_won': s in won_solutions,
                    'contract_amount': float(contract_amount) if s in won_solutions else 0.0,
                    'is_high_quality': s in high_quality_unwon,
                    'satisfaction_score': None  # 可以从ticket获取
                }
                for s in solutions
            ]
        }

    def get_solution_score_details(
        self,
        engineer_id: int,
        period_id: int
    ) -> Dict[str, Any]:
        """
        获取方案工程师得分详情

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID

        Returns:
            得分详情
        """
        from app.services.engineer_performance.engineer_performance_service import (
            EngineerPerformanceService,
        )

        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        service = EngineerPerformanceService(self.db)
        score = service._calculate_solution_score(engineer_id, period)

        # 获取方案数据
        solutions = self.db.query(PresaleSolution).filter(
            PresaleSolution.author_id == engineer_id,
            PresaleSolution.created_at.between(period.start_date, period.end_date)
        ).all()

        won_count = 0
        approved_count = 0
        high_quality_count = 0

        for solution in solutions:
            if solution.review_status == 'APPROVED':
                approved_count += 1

            if solution.opportunity_id:
                contract = self.db.query(Contract).filter(
                    Contract.opportunity_id == solution.opportunity_id,
                    Contract.status == 'SIGNED'
                ).first()
                if contract:
                    won_count += 1

            if solution.ticket_id:
                ticket = self.db.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id == solution.ticket_id
                ).first()
                if ticket and ticket.satisfaction_score and ticket.satisfaction_score >= 4.5:
                    high_quality_count += 1

        return {
            'engineer_id': engineer_id,
            'period_id': period_id,
            'dimension_scores': {
                'technical_score': float(score.technical_score or 0),
                'execution_score': float(score.execution_score or 0),
                'cost_quality_score': float(score.cost_quality_score or 0),
                'knowledge_score': float(score.knowledge_score or 0),
                'collaboration_score': float(score.collaboration_score or 0),
                'solution_success_score': float(score.solution_success_score or 0)
            },
            'solution_statistics': {
                'total_solutions': len(solutions),
                'won_solutions': won_count,
                'approved_solutions': approved_count,
                'high_quality_solutions': high_quality_count,
                'win_rate': round(won_count / len(solutions) * 100, 2) if solutions else 0.0,
                'approval_rate': round(approved_count / len(solutions) * 100, 2) if solutions else 0.0
            }
        }
