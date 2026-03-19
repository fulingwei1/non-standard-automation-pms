# -*- coding: utf-8 -*-
"""
催款优先级排序服务

基于规则引擎为业务员提供催款优先级排序：
1. 综合评分：金额、逾期天数、客户关系、历史付款记录
2. 智能建议：根据客户情况生成催款策略
3. 风险预警：识别高风险应收账款
"""

import logging
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.models.sales import Contract, Customer, Invoice

logger = logging.getLogger(__name__)


class CollectionUrgency(str, Enum):
    """催款紧急程度"""
    CRITICAL = "critical"      # 紧急（需立即处理）
    HIGH = "high"              # 高优先级（本周处理）
    MEDIUM = "medium"          # 中优先级（两周内处理）
    LOW = "low"                # 低优先级（月内处理）


class CollectionRisk(str, Enum):
    """回款风险等级"""
    HIGH = "high"              # 高风险（可能坏账）
    MEDIUM = "medium"          # 中风险（需要关注）
    LOW = "low"                # 低风险（正常催收）


@dataclass
class CollectionItem:
    """催款项"""
    invoice_id: int
    invoice_code: str
    contract_id: int
    contract_code: str
    customer_id: int
    customer_name: str
    # 金额信息
    invoice_amount: float
    paid_amount: float
    unpaid_amount: float
    # 时间信息
    due_date: date
    overdue_days: int
    issue_date: Optional[date]
    # 优先级信息
    urgency: CollectionUrgency
    risk: CollectionRisk
    priority_score: int          # 0-100，越高越优先
    # 客户信息
    customer_credit_level: Optional[str]
    historical_payment_rate: float  # 历史付款率 0-100
    # 建议
    suggestion: str
    action_points: List[str]


# 逾期天数权重配置
OVERDUE_WEIGHTS = {
    "0-30": 20,
    "31-60": 40,
    "61-90": 60,
    "90+": 80,
}

# 金额权重配置（万元）
AMOUNT_THRESHOLDS = [
    (100, 30),   # >100万：30分
    (50, 25),    # 50-100万：25分
    (20, 20),    # 20-50万：20分
    (10, 15),    # 10-20万：15分
    (0, 10),     # <10万：10分
]

# 客户信用等级权重
CREDIT_WEIGHTS = {
    "A": -10,    # 优质客户，降低优先级
    "B": 0,      # 普通客户
    "C": 10,     # 关注客户，提高优先级
    "D": 20,     # 高风险客户，大幅提高
}


class CollectionPriorityService:
    """
    催款优先级排序服务

    提供智能催款排序，帮助业务员：
    1. 识别最需要催款的客户
    2. 根据客户情况制定催款策略
    3. 预警高风险应收账款

    Usage:
        service = CollectionPriorityService(db)
        items = service.get_prioritized_collections(user_id=1)
        for item in items:
            print(f"[{item.urgency}] {item.customer_name}: {item.unpaid_amount}元")
    """

    def __init__(self, db: Session):
        self.db = db

    def get_prioritized_collections(
        self,
        user_id: int,
        include_non_overdue: bool = False,
        limit: int = 50,
    ) -> List[CollectionItem]:
        """
        获取优先级排序的催款列表

        Args:
            user_id: 用户ID
            include_non_overdue: 是否包含未逾期的应收
            limit: 返回数量限制

        Returns:
            按优先级排序的催款列表
        """
        today = date.today()

        # 查询应收发票
        query = (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.contract).joinedload(Contract.customer),
            )
            .filter(
                Invoice.status == "ISSUED",
                Invoice.payment_status.in_(["PENDING", "PARTIAL", "OVERDUE"]),
            )
        )

        # 仅查询逾期的
        if not include_non_overdue:
            query = query.filter(
                Invoice.due_date.isnot(None),
                Invoice.due_date < today,
            )

        invoices = query.all()

        # 计算每个发票的优先级
        items = []
        for invoice in invoices:
            item = self._build_collection_item(invoice, today, user_id)
            if item:
                items.append(item)

        # 按优先级得分排序（高分优先）
        items.sort(key=lambda x: (-x.priority_score, -x.unpaid_amount))

        return items[:limit]

    def _build_collection_item(
        self, invoice: Invoice, today: date, user_id: int
    ) -> Optional[CollectionItem]:
        """构建催款项"""
        contract = invoice.contract
        if not contract:
            return None

        customer = contract.customer
        customer_name = customer.customer_name if customer else "未知客户"
        customer_id = contract.customer_id or 0

        # 计算金额
        invoice_amount = float(invoice.total_amount or invoice.amount or 0)
        paid_amount = float(invoice.paid_amount or 0)
        unpaid_amount = invoice_amount - paid_amount

        if unpaid_amount <= 0:
            return None

        # 计算逾期天数
        due_date = invoice.due_date
        overdue_days = (today - due_date).days if due_date else 0

        # 获取客户信用信息
        credit_level = self._get_customer_credit_level(customer)
        historical_rate = self._get_historical_payment_rate(customer_id)

        # 计算优先级得分
        priority_score = self._calculate_priority_score(
            unpaid_amount, overdue_days, credit_level, historical_rate
        )

        # 确定紧急程度和风险
        urgency = self._determine_urgency(overdue_days, unpaid_amount, priority_score)
        risk = self._determine_risk(overdue_days, historical_rate, credit_level)

        # 生成建议
        suggestion, action_points = self._generate_suggestion(
            urgency, risk, overdue_days, unpaid_amount, customer_name, historical_rate
        )

        return CollectionItem(
            invoice_id=invoice.id,
            invoice_code=invoice.invoice_code or "",
            contract_id=contract.id,
            contract_code=contract.contract_code or "",
            customer_id=customer_id,
            customer_name=customer_name,
            invoice_amount=invoice_amount,
            paid_amount=paid_amount,
            unpaid_amount=unpaid_amount,
            due_date=due_date,
            overdue_days=max(0, overdue_days),
            issue_date=invoice.issue_date,
            urgency=urgency,
            risk=risk,
            priority_score=priority_score,
            customer_credit_level=credit_level,
            historical_payment_rate=historical_rate,
            suggestion=suggestion,
            action_points=action_points,
        )

    def _get_customer_credit_level(self, customer: Optional[Customer]) -> Optional[str]:
        """获取客户信用等级"""
        if not customer:
            return None
        # 尝试从客户模型获取信用等级字段
        return getattr(customer, "credit_level", None) or getattr(customer, "credit_rating", None)

    def _get_historical_payment_rate(self, customer_id: int) -> float:
        """
        计算客户历史付款率

        基于该客户过去所有发票的按时付款情况计算
        """
        if not customer_id:
            return 50.0  # 默认中等

        # 查询该客户所有已完成的发票
        # 使用 SQLAlchemy case 表达式计算已付款数量
        # SQLAlchemy 2.x 语法：positional elements
        paid_case = case(
            (Invoice.payment_status == "PAID", 1),
            else_=0
        )
        result = (
            self.db.query(
                func.count(Invoice.id).label("total"),
                func.sum(paid_case).label("paid_count"),
            )
            .join(Contract)
            .filter(
                Contract.customer_id == customer_id,
                Invoice.status == "ISSUED",
            )
            .first()
        )

        if not result or not result.total or result.total == 0:
            return 50.0

        paid_count = result.paid_count or 0
        return round((paid_count / result.total) * 100, 1)

    def _calculate_priority_score(
        self,
        unpaid_amount: float,
        overdue_days: int,
        credit_level: Optional[str],
        historical_rate: float,
    ) -> int:
        """
        计算优先级得分 (0-100)

        得分组成：
        - 金额权重：最高30分
        - 逾期天数权重：最高40分
        - 信用等级权重：-10 ~ +20分
        - 历史付款率权重：最高10分
        """
        score = 0

        # 1. 金额权重（万元）
        amount_wan = unpaid_amount / 10000
        for threshold, weight in AMOUNT_THRESHOLDS:
            if amount_wan >= threshold:
                score += weight
                break

        # 2. 逾期天数权重
        if overdue_days > 90:
            score += OVERDUE_WEIGHTS["90+"]
        elif overdue_days > 60:
            score += OVERDUE_WEIGHTS["61-90"]
        elif overdue_days > 30:
            score += OVERDUE_WEIGHTS["31-60"]
        elif overdue_days > 0:
            score += OVERDUE_WEIGHTS["0-30"]

        # 3. 信用等级权重
        if credit_level and credit_level in CREDIT_WEIGHTS:
            score += CREDIT_WEIGHTS[credit_level]

        # 4. 历史付款率权重（付款率越低，优先级越高）
        if historical_rate < 50:
            score += 10
        elif historical_rate < 70:
            score += 5

        return max(0, min(100, score))

    def _determine_urgency(
        self, overdue_days: int, unpaid_amount: float, priority_score: int
    ) -> CollectionUrgency:
        """确定催款紧急程度"""
        # 高优先级得分 + 高金额 = 紧急
        if priority_score >= 70 or (overdue_days > 60 and unpaid_amount > 100000):
            return CollectionUrgency.CRITICAL
        elif priority_score >= 50 or overdue_days > 30:
            return CollectionUrgency.HIGH
        elif priority_score >= 30 or overdue_days > 0:
            return CollectionUrgency.MEDIUM
        else:
            return CollectionUrgency.LOW

    def _determine_risk(
        self, overdue_days: int, historical_rate: float, credit_level: Optional[str]
    ) -> CollectionRisk:
        """确定回款风险等级"""
        # 多因素判断风险
        risk_factors = 0

        if overdue_days > 90:
            risk_factors += 2
        elif overdue_days > 60:
            risk_factors += 1

        if historical_rate < 50:
            risk_factors += 2
        elif historical_rate < 70:
            risk_factors += 1

        if credit_level == "D":
            risk_factors += 2
        elif credit_level == "C":
            risk_factors += 1

        if risk_factors >= 4:
            return CollectionRisk.HIGH
        elif risk_factors >= 2:
            return CollectionRisk.MEDIUM
        else:
            return CollectionRisk.LOW

    def _generate_suggestion(
        self,
        urgency: CollectionUrgency,
        risk: CollectionRisk,
        overdue_days: int,
        unpaid_amount: float,
        customer_name: str,
        historical_rate: float,
    ) -> Tuple[str, List[str]]:
        """生成催款建议和行动要点"""
        action_points = []

        # 根据紧急程度生成主建议
        if urgency == CollectionUrgency.CRITICAL:
            suggestion = f"⚠️ 紧急催款：{customer_name} 逾期 {overdue_days} 天，欠款 {unpaid_amount:,.0f} 元"
            action_points.append("立即电话联系客户财务负责人")
            action_points.append("发送正式催款函")
            if risk == CollectionRisk.HIGH:
                action_points.append("评估是否需要启动法律程序")
        elif urgency == CollectionUrgency.HIGH:
            suggestion = f"高优先催款：{customer_name} 逾期 {overdue_days} 天"
            action_points.append("本周内完成电话催款")
            action_points.append("确认客户付款计划")
        elif urgency == CollectionUrgency.MEDIUM:
            suggestion = f"常规催款：{customer_name} 应收 {unpaid_amount:,.0f} 元"
            action_points.append("发送催款邮件")
            action_points.append("跟进确认付款时间")
        else:
            suggestion = f"正常跟进：{customer_name}"
            action_points.append("定期跟进客户付款进度")

        # 根据历史付款率添加建议
        if historical_rate < 50:
            action_points.append("该客户历史付款率较低，建议优先催收")
        elif historical_rate > 90:
            action_points.append("该客户信用良好，可适当宽松处理")

        return suggestion, action_points

    def get_collection_summary(self, user_id: int) -> Dict[str, Any]:
        """
        获取催款汇总统计

        Returns:
            包含各维度统计数据的汇总
        """
        items = self.get_prioritized_collections(user_id, include_non_overdue=True, limit=500)

        summary = {
            "total_count": len(items),
            "total_unpaid": sum(item.unpaid_amount for item in items),
            "by_urgency": {
                "critical": {"count": 0, "amount": 0},
                "high": {"count": 0, "amount": 0},
                "medium": {"count": 0, "amount": 0},
                "low": {"count": 0, "amount": 0},
            },
            "by_risk": {
                "high": {"count": 0, "amount": 0},
                "medium": {"count": 0, "amount": 0},
                "low": {"count": 0, "amount": 0},
            },
            "overdue_aging": {
                "0-30": {"count": 0, "amount": 0},
                "31-60": {"count": 0, "amount": 0},
                "61-90": {"count": 0, "amount": 0},
                "90+": {"count": 0, "amount": 0},
            },
            "top_priority_items": [],
        }

        for item in items:
            # 按紧急程度统计
            urgency_key = item.urgency.value
            summary["by_urgency"][urgency_key]["count"] += 1
            summary["by_urgency"][urgency_key]["amount"] += item.unpaid_amount

            # 按风险统计
            risk_key = item.risk.value
            summary["by_risk"][risk_key]["count"] += 1
            summary["by_risk"][risk_key]["amount"] += item.unpaid_amount

            # 按账龄统计
            if item.overdue_days > 90:
                aging_key = "90+"
            elif item.overdue_days > 60:
                aging_key = "61-90"
            elif item.overdue_days > 30:
                aging_key = "31-60"
            else:
                aging_key = "0-30"
            summary["overdue_aging"][aging_key]["count"] += 1
            summary["overdue_aging"][aging_key]["amount"] += item.unpaid_amount

        # 取优先级最高的5项
        summary["top_priority_items"] = [
            {
                "invoice_code": item.invoice_code,
                "customer_name": item.customer_name,
                "unpaid_amount": item.unpaid_amount,
                "overdue_days": item.overdue_days,
                "urgency": item.urgency.value,
                "suggestion": item.suggestion,
            }
            for item in items[:5]
        ]

        return summary
