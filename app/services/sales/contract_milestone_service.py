# -*- coding: utf-8 -*-
"""
合同里程碑提醒服务

监控合同关键节点，提前预警：
1. 付款节点到期
2. 交付里程碑
3. 质保期到期
4. 合同到期续签
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.sales import Contract

logger = logging.getLogger(__name__)


class MilestoneType(str, Enum):
    """里程碑类型"""
    PAYMENT = "payment"           # 付款节点
    DELIVERY = "delivery"         # 交付节点
    WARRANTY_END = "warranty"     # 质保到期
    CONTRACT_END = "contract"     # 合同到期


class MilestoneUrgency(str, Enum):
    """紧急程度"""
    OVERDUE = "overdue"          # 已过期
    URGENT = "urgent"            # 紧急（7天内）
    WARNING = "warning"          # 预警（14天内）
    UPCOMING = "upcoming"        # 即将到来（30天内）


@dataclass
class ContractMilestone:
    """合同里程碑"""
    contract_id: int
    contract_code: str
    contract_name: str
    customer_name: str
    # 里程碑信息
    milestone_type: MilestoneType
    milestone_name: str
    due_date: date
    # 状态
    days_until: int              # 距离到期天数（负数表示已过期）
    urgency: MilestoneUrgency
    # 金额（如适用）
    amount: Optional[float]
    # 建议
    suggestion: str


# 里程碑配置
MILESTONE_CONFIG = {
    MilestoneType.PAYMENT: {
        "warning_days": 14,
        "urgent_days": 7,
    },
    MilestoneType.DELIVERY: {
        "warning_days": 14,
        "urgent_days": 7,
    },
    MilestoneType.WARRANTY_END: {
        "warning_days": 30,
        "urgent_days": 14,
    },
    MilestoneType.CONTRACT_END: {
        "warning_days": 60,
        "urgent_days": 30,
    },
}


class ContractMilestoneService:
    """
    合同里程碑提醒服务

    监控合同关键节点，帮助业务员：
    1. 不遗漏任何付款节点
    2. 及时跟进交付进度
    3. 提前准备质保续签

    Usage:
        service = ContractMilestoneService(db)
        milestones = service.get_upcoming_milestones(user_id=1)
        for m in milestones:
            print(f"[{m.urgency}] {m.contract_code}: {m.milestone_name}")
    """

    def __init__(self, db: Session):
        self.db = db

    def get_upcoming_milestones(
        self,
        user_id: int,
        include_types: Optional[List[MilestoneType]] = None,
        days_ahead: int = 60,
        include_overdue: bool = True,
        limit: int = 50,
    ) -> List[ContractMilestone]:
        """
        获取即将到来的里程碑

        Args:
            user_id: 用户ID
            include_types: 包含的里程碑类型
            days_ahead: 提前天数
            include_overdue: 是否包含已过期
            limit: 返回数量限制

        Returns:
            按紧急程度排序的里程碑列表
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        start_date = today - timedelta(days=90) if include_overdue else today

        # 获取用户负责的合同
        contracts = (
            self.db.query(Contract)
            .options(joinedload(Contract.customer))
            .filter(
                Contract.sales_owner_id == user_id,
                Contract.status.in_(["ACTIVE", "EXECUTING", "SIGNED"]),
            )
            .all()
        )

        milestones = []

        for contract in contracts:
            # 检查各类里程碑
            contract_milestones = self._extract_milestones(
                contract, today, start_date, end_date
            )

            for m in contract_milestones:
                if include_types is None or m.milestone_type in include_types:
                    milestones.append(m)

        # 按紧急程度排序
        urgency_order = {
            MilestoneUrgency.OVERDUE: 0,
            MilestoneUrgency.URGENT: 1,
            MilestoneUrgency.WARNING: 2,
            MilestoneUrgency.UPCOMING: 3,
        }
        milestones.sort(key=lambda m: (urgency_order[m.urgency], m.days_until))

        return milestones[:limit]

    def _extract_milestones(
        self,
        contract: Contract,
        today: date,
        start_date: date,
        end_date: date,
    ) -> List[ContractMilestone]:
        """从合同中提取里程碑"""
        milestones = []
        customer_name = contract.customer.customer_name if contract.customer else "未知客户"

        # 1. 合同到期检查
        if contract.end_date:
            if start_date <= contract.end_date <= end_date:
                days_until = (contract.end_date - today).days
                milestones.append(
                    ContractMilestone(
                        contract_id=contract.id,
                        contract_code=contract.contract_code,
                        contract_name=contract.contract_name or contract.contract_code,
                        customer_name=customer_name,
                        milestone_type=MilestoneType.CONTRACT_END,
                        milestone_name="合同到期",
                        due_date=contract.end_date,
                        days_until=days_until,
                        urgency=self._get_urgency(days_until, MilestoneType.CONTRACT_END),
                        amount=float(contract.contract_amount) if contract.contract_amount else None,
                        suggestion=self._get_suggestion(MilestoneType.CONTRACT_END, days_until),
                    )
                )

        # 2. 质保到期检查
        warranty_end = getattr(contract, 'warranty_end_date', None)
        if warranty_end:
            if start_date <= warranty_end <= end_date:
                days_until = (warranty_end - today).days
                milestones.append(
                    ContractMilestone(
                        contract_id=contract.id,
                        contract_code=contract.contract_code,
                        contract_name=contract.contract_name or contract.contract_code,
                        customer_name=customer_name,
                        milestone_type=MilestoneType.WARRANTY_END,
                        milestone_name="质保到期",
                        due_date=warranty_end,
                        days_until=days_until,
                        urgency=self._get_urgency(days_until, MilestoneType.WARRANTY_END),
                        amount=None,
                        suggestion=self._get_suggestion(MilestoneType.WARRANTY_END, days_until),
                    )
                )

        # 3. 从收款计划中提取付款里程碑
        # 尝试从关联的收款计划获取
        payment_plans = getattr(contract, 'payment_plans', [])
        for plan in payment_plans:
            plan_date = getattr(plan, 'planned_date', None) or getattr(plan, 'due_date', None)
            if plan_date and start_date <= plan_date <= end_date:
                plan_status = getattr(plan, 'status', None)
                if plan_status not in ['PAID', 'COMPLETED']:
                    days_until = (plan_date - today).days
                    plan_amount = getattr(plan, 'amount', None) or getattr(plan, 'planned_amount', None)
                    milestones.append(
                        ContractMilestone(
                            contract_id=contract.id,
                            contract_code=contract.contract_code,
                            contract_name=contract.contract_name or contract.contract_code,
                            customer_name=customer_name,
                            milestone_type=MilestoneType.PAYMENT,
                            milestone_name=getattr(plan, 'payment_name', '付款节点'),
                            due_date=plan_date,
                            days_until=days_until,
                            urgency=self._get_urgency(days_until, MilestoneType.PAYMENT),
                            amount=float(plan_amount) if plan_amount else None,
                            suggestion=self._get_suggestion(MilestoneType.PAYMENT, days_until),
                        )
                    )

        # 4. 从交付物中提取交付里程碑
        deliverables = getattr(contract, 'deliverables', [])
        for d in deliverables:
            due_date = getattr(d, 'due_date', None) or getattr(d, 'planned_date', None)
            if due_date and start_date <= due_date <= end_date:
                d_status = getattr(d, 'status', None)
                if d_status not in ['DELIVERED', 'COMPLETED']:
                    days_until = (due_date - today).days
                    milestones.append(
                        ContractMilestone(
                            contract_id=contract.id,
                            contract_code=contract.contract_code,
                            contract_name=contract.contract_name or contract.contract_code,
                            customer_name=customer_name,
                            milestone_type=MilestoneType.DELIVERY,
                            milestone_name=getattr(d, 'name', '交付节点'),
                            due_date=due_date,
                            days_until=days_until,
                            urgency=self._get_urgency(days_until, MilestoneType.DELIVERY),
                            amount=None,
                            suggestion=self._get_suggestion(MilestoneType.DELIVERY, days_until),
                        )
                    )

        return milestones

    def _get_urgency(self, days_until: int, milestone_type: MilestoneType) -> MilestoneUrgency:
        """确定紧急程度"""
        config = MILESTONE_CONFIG.get(milestone_type, MILESTONE_CONFIG[MilestoneType.PAYMENT])

        if days_until < 0:
            return MilestoneUrgency.OVERDUE
        elif days_until <= config["urgent_days"]:
            return MilestoneUrgency.URGENT
        elif days_until <= config["warning_days"]:
            return MilestoneUrgency.WARNING
        else:
            return MilestoneUrgency.UPCOMING

    def _get_suggestion(self, milestone_type: MilestoneType, days_until: int) -> str:
        """生成建议"""
        suggestions = {
            MilestoneType.PAYMENT: {
                "overdue": "⚠️ 付款已逾期，立即联系客户催款",
                "urgent": "付款节点临近，确认客户付款计划",
                "warning": "提前与客户确认付款安排",
                "upcoming": "关注付款节点，适时跟进",
            },
            MilestoneType.DELIVERY: {
                "overdue": "⚠️ 交付已逾期，确认进度并与客户沟通",
                "urgent": "交付临近，确保各项准备就绪",
                "warning": "检查交付准备情况，预留缓冲时间",
                "upcoming": "关注交付进度，定期同步状态",
            },
            MilestoneType.WARRANTY_END: {
                "overdue": "质保已到期，联系客户洽谈续保",
                "urgent": "质保即将到期，准备续保方案",
                "warning": "提前联系客户，了解续保意向",
                "upcoming": "关注质保到期，准备续保资料",
            },
            MilestoneType.CONTRACT_END: {
                "overdue": "合同已到期，尽快处理续签事宜",
                "urgent": "合同即将到期，推进续签谈判",
                "warning": "准备续签方案，与客户沟通意向",
                "upcoming": "提前规划续签策略",
            },
        }

        type_suggestions = suggestions.get(milestone_type, suggestions[MilestoneType.PAYMENT])

        if days_until < 0:
            return type_suggestions["overdue"]
        elif days_until <= MILESTONE_CONFIG[milestone_type]["urgent_days"]:
            return type_suggestions["urgent"]
        elif days_until <= MILESTONE_CONFIG[milestone_type]["warning_days"]:
            return type_suggestions["warning"]
        else:
            return type_suggestions["upcoming"]

    def get_milestone_summary(self, user_id: int) -> Dict[str, Any]:
        """
        获取里程碑汇总统计

        Returns:
            包含各类型和紧急程度的统计
        """
        milestones = self.get_upcoming_milestones(user_id, days_ahead=90, limit=500)

        summary = {
            "total_count": len(milestones),
            "by_urgency": {
                "overdue": {"count": 0, "amount": 0},
                "urgent": {"count": 0, "amount": 0},
                "warning": {"count": 0, "amount": 0},
                "upcoming": {"count": 0, "amount": 0},
            },
            "by_type": {
                "payment": {"count": 0, "amount": 0},
                "delivery": {"count": 0},
                "warranty": {"count": 0},
                "contract": {"count": 0, "amount": 0},
            },
            "critical_items": [],
        }

        for m in milestones:
            # 按紧急程度统计
            urgency_key = m.urgency.value
            summary["by_urgency"][urgency_key]["count"] += 1
            if m.amount:
                summary["by_urgency"][urgency_key]["amount"] += m.amount

            # 按类型统计
            type_key = m.milestone_type.value
            summary["by_type"][type_key]["count"] += 1
            if m.amount and "amount" in summary["by_type"][type_key]:
                summary["by_type"][type_key]["amount"] += m.amount

            # 收集紧急项
            if m.urgency in [MilestoneUrgency.OVERDUE, MilestoneUrgency.URGENT]:
                summary["critical_items"].append({
                    "contract_code": m.contract_code,
                    "customer_name": m.customer_name,
                    "milestone_type": m.milestone_type.value,
                    "milestone_name": m.milestone_name,
                    "due_date": m.due_date.isoformat(),
                    "days_until": m.days_until,
                    "amount": m.amount,
                    "suggestion": m.suggestion,
                })

        # 只保留前10个紧急项
        summary["critical_items"] = summary["critical_items"][:10]

        return summary
