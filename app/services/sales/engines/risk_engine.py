# -*- coding: utf-8 -*-
"""
风险预警推荐引擎

分析合同和发票数据，提供风险预警：
- 合同即将到期提醒
- 逾期发票预警
- 客户信用风险提示
"""

import logging
from datetime import date, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session, joinedload

from app.services.sales.engines.base import (
    BaseRecommendationEngine,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)

logger = logging.getLogger(__name__)


class RiskEngine(BaseRecommendationEngine):
    """风险预警推荐引擎"""

    # 合同到期预警天数
    CONTRACT_EXPIRY_WARNING_DAYS = 30
    # 逾期天数阈值（超过此天数为严重）
    CRITICAL_OVERDUE_DAYS = 30

    def __init__(self, db: Session):
        super().__init__(db)

    def get_recommendations(self, user_id: int) -> List[Recommendation]:
        """获取风险预警推荐"""
        recommendations = []

        try:
            # 规则1: 合同即将到期
            recommendations.extend(
                self._get_expiring_contract_alerts(user_id)
            )

            # 规则2: 逾期发票
            recommendations.extend(
                self._get_overdue_invoice_alerts(user_id)
            )

        except Exception as e:
            logger.error(f"获取风险推荐失败: {e}")

        return recommendations

    def _get_expiring_contract_alerts(self, user_id: int) -> List[Recommendation]:
        """获取合同到期预警"""
        from app.models.sales import Contract

        recommendations = []
        today = date.today()

        # 使用 joinedload 预加载关联数据，避免 N+1 查询
        expiring_contracts = (
            self.db.query(Contract)
            .options(
                joinedload(Contract.customer),
                joinedload(Contract.sales_owner),
            )
            .filter(
                Contract.sales_owner_id == user_id,
                Contract.status.in_(["ACTIVE", "EXECUTING"]),
                Contract.expiry_date.isnot(None),
                Contract.expiry_date <= today + timedelta(days=self.CONTRACT_EXPIRY_WARNING_DAYS),
                Contract.expiry_date >= today,
            )
            .all()
        )

        for contract in expiring_contracts:
            days_to_expiry = (contract.expiry_date - today).days
            priority = (
                RecommendationPriority.HIGH
                if days_to_expiry <= 7
                else RecommendationPriority.MEDIUM
            )

            recommendations.append(
                Recommendation(
                    type=RecommendationType.RISK,
                    priority=priority,
                    title=f"合同即将到期: {contract.contract_code}",
                    description=f"合同将于 {contract.expiry_date} 到期，仅剩 {days_to_expiry} 天",
                    action="联系客户讨论续约事宜，准备续约方案",
                    entity_type="contract",
                    entity_id=contract.id,
                    confidence=0.95,
                    expected_impact="避免客户流失，确保续约",
                    data={"days_to_expiry": days_to_expiry},
                )
            )

        return recommendations

    def _get_overdue_invoice_alerts(self, user_id: int) -> List[Recommendation]:
        """获取逾期发票预警"""
        from app.models.sales import Contract, Invoice

        recommendations = []
        today = date.today()

        # 查询逾期发票，使用 joinedload 预加载合同信息避免 N+1 查询
        overdue_invoices = (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.contract).joinedload(Contract.sales_owner),
            )
            .filter(
                Invoice.status.in_(["SENT", "OVERDUE"]),
                Invoice.due_date < today,
            )
            .all()
        )

        # 按合同分组，同时过滤出当前用户负责的合同
        # 由于已经预加载了 Invoice.contract，直接从 invoice 获取合同信息，无需额外查询
        contract_invoices: Dict[int, tuple] = {}  # {contract_id: (contract, [invoices])}
        for inv in overdue_invoices:
            # 使用预加载的 contract 对象，避免 N+1 查询
            contract = inv.contract
            if contract is None or contract.sales_owner_id != user_id:
                continue

            if inv.contract_id not in contract_invoices:
                contract_invoices[inv.contract_id] = (contract, [])
            contract_invoices[inv.contract_id][1].append(inv)

        # 为用户负责的合同生成预警
        for contract_id, (contract, invoices) in contract_invoices.items():

            total_overdue = sum(inv.amount or 0 for inv in invoices)
            max_overdue_days = max(
                (today - inv.due_date).days for inv in invoices
            )

            priority = (
                RecommendationPriority.CRITICAL
                if max_overdue_days > self.CRITICAL_OVERDUE_DAYS
                else RecommendationPriority.HIGH
            )

            recommendations.append(
                Recommendation(
                    type=RecommendationType.RISK,
                    priority=priority,
                    title=f"发票逾期: {contract.contract_code}",
                    description=f"有 {len(invoices)} 张发票逾期，总金额 ¥{total_overdue:,.0f}，最长逾期 {max_overdue_days} 天",
                    action="立即联系客户催收，了解付款计划",
                    entity_type="contract",
                    entity_id=contract.id,
                    confidence=0.98,
                    expected_impact="改善现金流，降低坏账风险",
                    data={
                        "overdue_count": len(invoices),
                        "total_overdue": float(total_overdue),
                        "max_overdue_days": max_overdue_days,
                    },
                )
            )

        return recommendations
