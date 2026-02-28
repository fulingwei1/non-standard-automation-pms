# -*- coding: utf-8 -*-
"""
销售奖金计算器
基于合同签订和回款计算奖金
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusRule
from app.models.sales import Contract, Invoice
from app.services.bonus.base import BonusCalculatorBase


class SalesBonusCalculator(BonusCalculatorBase):
    """销售奖金计算器"""

    def __init__(self, db: Session):
        super().__init__(db)

    def calculate(
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

    def calculate_director_bonus(
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
            Contract.signing_date >= period_start,
            Contract.signing_date <= period_end,
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
