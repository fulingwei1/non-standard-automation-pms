# -*- coding: utf-8 -*-
"""
智能跟进提醒服务

基于规则引擎为业务员提供跟进提醒：
1. 线索/商机下次行动时间已过期
2. 超过行业平均周期未跟进
3. 报价即将过期提醒
4. 高优先级客户优先提醒
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.sales import Lead, LeadFollowUp, Opportunity, Quote

logger = logging.getLogger(__name__)


class ReminderType(str, Enum):
    """提醒类型"""
    OVERDUE_ACTION = "overdue_action"       # 行动已过期
    UPCOMING_ACTION = "upcoming_action"     # 即将到期行动
    NO_RECENT_FOLLOW_UP = "no_follow_up"    # 长时间未跟进
    QUOTE_EXPIRING = "quote_expiring"       # 报价即将过期
    HIGH_VALUE_IDLE = "high_value_idle"     # 高价值客户闲置


class ReminderPriority(str, Enum):
    """提醒优先级"""
    URGENT = "urgent"       # 紧急（今天必须处理）
    HIGH = "high"           # 高（3天内处理）
    MEDIUM = "medium"       # 中（本周内处理）
    LOW = "low"             # 低（下周处理）


@dataclass
class FollowUpReminder:
    """跟进提醒"""
    type: ReminderType
    priority: ReminderPriority
    entity_type: str            # lead / opportunity / quote
    entity_id: int
    entity_code: str
    entity_name: str
    customer_name: str
    owner_id: int
    owner_name: str
    message: str                # 提醒消息
    suggestion: str             # 建议行动
    days_overdue: int           # 逾期天数（负数表示提前）
    last_follow_up_at: Optional[datetime]
    next_action_at: Optional[datetime]
    est_amount: Optional[float]


# 行业跟进周期配置（天）
INDUSTRY_FOLLOW_UP_CYCLES = {
    "制造业": {"lead": 7, "opportunity": 5},
    "汽车": {"lead": 5, "opportunity": 3},
    "电子": {"lead": 7, "opportunity": 5},
    "医疗": {"lead": 10, "opportunity": 7},
    "default": {"lead": 7, "opportunity": 5},
}

# 商机阶段跟进周期（天）- 阶段越后期跟进越频繁
STAGE_FOLLOW_UP_CYCLES = {
    "DISCOVERY": 10,      # 发现阶段
    "QUALIFICATION": 7,   # 确认阶段
    "PROPOSAL": 5,        # 方案阶段
    "NEGOTIATION": 3,     # 谈判阶段
    "CLOSED_WON": 30,     # 已赢单（售后跟进）
    "CLOSED_LOST": 90,    # 已输单（复盘跟进）
    "default": 7,
}

# 金额阈值（高价值客户判定）
HIGH_VALUE_THRESHOLD = 500000


class FollowUpReminderService:
    """
    智能跟进提醒服务

    提供基于规则的跟进提醒，帮助业务员：
    1. 不遗漏任何需要跟进的线索/商机
    2. 根据客户价值和阶段智能排序
    3. 提供具体的跟进建议

    Usage:
        service = FollowUpReminderService(db)
        reminders = service.get_reminders_for_user(user_id=1)
        for r in reminders:
            print(f"[{r.priority}] {r.message}")
    """

    def __init__(self, db: Session):
        self.db = db

    def get_reminders_for_user(
        self,
        user_id: int,
        include_types: Optional[List[ReminderType]] = None,
        limit: int = 50,
    ) -> List[FollowUpReminder]:
        """
        获取用户的跟进提醒列表

        Args:
            user_id: 用户ID
            include_types: 包含的提醒类型（None表示全部）
            limit: 返回数量限制

        Returns:
            按优先级排序的提醒列表
        """
        reminders: List[FollowUpReminder] = []

        # 1. 检查线索跟进提醒
        if not include_types or ReminderType.OVERDUE_ACTION in include_types:
            reminders.extend(self._get_lead_overdue_reminders(user_id))

        if not include_types or ReminderType.NO_RECENT_FOLLOW_UP in include_types:
            reminders.extend(self._get_lead_no_follow_up_reminders(user_id))

        # 2. 检查商机跟进提醒
        if not include_types or ReminderType.NO_RECENT_FOLLOW_UP in include_types:
            reminders.extend(self._get_opportunity_reminders(user_id))

        if not include_types or ReminderType.HIGH_VALUE_IDLE in include_types:
            reminders.extend(self._get_high_value_idle_reminders(user_id))

        # 3. 检查报价过期提醒
        if not include_types or ReminderType.QUOTE_EXPIRING in include_types:
            reminders.extend(self._get_quote_expiring_reminders(user_id))

        # 按优先级排序
        priority_order = {
            ReminderPriority.URGENT: 0,
            ReminderPriority.HIGH: 1,
            ReminderPriority.MEDIUM: 2,
            ReminderPriority.LOW: 3,
        }
        reminders.sort(key=lambda r: (priority_order[r.priority], -abs(r.days_overdue)))

        return reminders[:limit]

    def _get_lead_overdue_reminders(self, user_id: int) -> List[FollowUpReminder]:
        """获取线索行动过期提醒"""
        reminders = []
        today = datetime.now()

        # 查询已过期的线索（next_action_at < 今天）
        # 注意：Lead 模型只有 customer_name 字段，没有 customer 关系
        leads = (
            self.db.query(Lead)
            .options(joinedload(Lead.owner))
            .filter(
                Lead.owner_id == user_id,
                Lead.status.in_(["NEW", "CONTACTED", "QUALIFIED"]),
                Lead.next_action_at < today,
            )
            .all()
        )

        for lead in leads:
            days_overdue = (today - lead.next_action_at).days
            priority = self._calculate_priority(days_overdue, None)
            # Lead 用 customer_name 作为展示名称
            display_name = lead.customer_name or lead.lead_code

            reminders.append(
                FollowUpReminder(
                    type=ReminderType.OVERDUE_ACTION,
                    priority=priority,
                    entity_type="lead",
                    entity_id=lead.id,
                    entity_code=lead.lead_code,
                    entity_name=display_name,
                    customer_name=lead.customer_name or "未知客户",
                    owner_id=user_id,
                    owner_name=lead.owner.real_name if lead.owner else "",
                    message=f"线索【{display_name}】计划行动已过期 {days_overdue} 天",
                    suggestion=self._get_follow_up_suggestion("lead", lead.status),
                    days_overdue=days_overdue,
                    last_follow_up_at=None,
                    next_action_at=lead.next_action_at,
                    est_amount=None,
                )
            )

        return reminders

    def _get_lead_upcoming_reminders(
        self, user_id: int, window_days: int = 3
    ) -> List[FollowUpReminder]:
        """获取线索临近行动提醒"""
        reminders = []
        now = datetime.now()
        window_end = now + timedelta(days=max(window_days, 0))

        leads = (
            self.db.query(Lead)
            .options(joinedload(Lead.owner))
            .filter(
                Lead.owner_id == user_id,
                Lead.status.in_(["NEW", "CONTACTED", "QUALIFIED"]),
                Lead.next_action_at.isnot(None),
                Lead.next_action_at >= now,
                Lead.next_action_at <= window_end,
            )
            .order_by(Lead.next_action_at.asc())
            .all()
        )

        for lead in leads:
            remaining = lead.next_action_at - now
            hours_until_due = max(remaining.total_seconds() / 3600, 0)
            days_until_due = max((lead.next_action_at.date() - now.date()).days, 0)

            if hours_until_due <= 24:
                priority = ReminderPriority.HIGH
                due_text = "今天内" if days_until_due == 0 else "1天内"
            elif hours_until_due <= 72:
                priority = ReminderPriority.MEDIUM
                due_text = f"{days_until_due}天内"
            else:
                priority = ReminderPriority.LOW
                due_text = f"{days_until_due}天内"

            display_name = lead.customer_name or lead.lead_code
            reminders.append(
                FollowUpReminder(
                    type=ReminderType.UPCOMING_ACTION,
                    priority=priority,
                    entity_type="lead",
                    entity_id=lead.id,
                    entity_code=lead.lead_code,
                    entity_name=display_name,
                    customer_name=lead.customer_name or "未知客户",
                    owner_id=user_id,
                    owner_name=lead.owner.real_name if lead.owner else "",
                    message=f"线索【{display_name}】计划行动将在{due_text}到期",
                    suggestion=self._get_follow_up_suggestion("lead", lead.status),
                    days_overdue=-days_until_due,
                    last_follow_up_at=None,
                    next_action_at=lead.next_action_at,
                    est_amount=None,
                )
            )

        return reminders

    def _get_lead_no_follow_up_reminders(self, user_id: int) -> List[FollowUpReminder]:
        """获取线索长时间未跟进提醒"""
        reminders = []
        today = datetime.now()

        # 子查询：获取每个线索的最后跟进时间
        last_follow_up_subq = (
            self.db.query(
                LeadFollowUp.lead_id,
                func.max(LeadFollowUp.created_at).label("last_follow_up_at"),
            )
            .group_by(LeadFollowUp.lead_id)
            .subquery()
        )

        # 查询活跃线索
        # 注意：Lead 模型只有 customer_name 和 industry 字段，没有 customer 关系
        leads = (
            self.db.query(Lead, last_follow_up_subq.c.last_follow_up_at)
            .outerjoin(last_follow_up_subq, Lead.id == last_follow_up_subq.c.lead_id)
            .options(joinedload(Lead.owner))
            .filter(
                Lead.owner_id == user_id,
                Lead.status.in_(["NEW", "CONTACTED", "QUALIFIED"]),
            )
            .all()
        )

        for lead, last_follow_up_at in leads:
            # 获取行业跟进周期（Lead 自身有 industry 字段）
            industry = lead.industry
            cycle_config = INDUSTRY_FOLLOW_UP_CYCLES.get(
                industry, INDUSTRY_FOLLOW_UP_CYCLES["default"]
            )
            max_days = cycle_config["lead"]

            # 计算距离上次跟进的天数
            if last_follow_up_at:
                days_since_follow_up = (today - last_follow_up_at).days
            else:
                # 从未跟进过，使用创建时间
                days_since_follow_up = (today - lead.created_at).days

            # 超过周期才提醒
            if days_since_follow_up > max_days:
                days_overdue = days_since_follow_up - max_days
                priority = self._calculate_priority(days_overdue, None)
                display_name = lead.customer_name or lead.lead_code

                reminders.append(
                    FollowUpReminder(
                        type=ReminderType.NO_RECENT_FOLLOW_UP,
                        priority=priority,
                        entity_type="lead",
                        entity_id=lead.id,
                        entity_code=lead.lead_code,
                        entity_name=display_name,
                        customer_name=lead.customer_name or "未知客户",
                        owner_id=user_id,
                        owner_name=lead.owner.real_name if lead.owner else "",
                        message=f"线索【{display_name}】已 {days_since_follow_up} 天未跟进（建议周期 {max_days} 天）",
                        suggestion=self._get_follow_up_suggestion("lead", lead.status),
                        days_overdue=days_overdue,
                        last_follow_up_at=last_follow_up_at,
                        next_action_at=lead.next_action_at,
                        est_amount=None,
                    )
                )

        return reminders

    def _get_opportunity_reminders(self, user_id: int) -> List[FollowUpReminder]:
        """获取商机跟进提醒"""
        reminders = []
        today = datetime.now()

        # 查询活跃商机
        opportunities = (
            self.db.query(Opportunity)
            .options(joinedload(Opportunity.owner), joinedload(Opportunity.customer))
            .filter(
                Opportunity.owner_id == user_id,
                Opportunity.stage.notin_(["CLOSED_WON", "CLOSED_LOST"]),
            )
            .all()
        )

        for opp in opportunities:
            # 根据阶段确定跟进周期
            stage_cycle = STAGE_FOLLOW_UP_CYCLES.get(
                opp.stage, STAGE_FOLLOW_UP_CYCLES["default"]
            )

            # 计算距离上次更新的天数（暂用 updated_at 作为活动时间）
            days_since_activity = (today - opp.updated_at).days

            if days_since_activity > stage_cycle:
                days_overdue = days_since_activity - stage_cycle
                est_amount = float(opp.est_amount) if opp.est_amount else None
                priority = self._calculate_priority(days_overdue, est_amount)

                reminders.append(
                    FollowUpReminder(
                        type=ReminderType.NO_RECENT_FOLLOW_UP,
                        priority=priority,
                        entity_type="opportunity",
                        entity_id=opp.id,
                        entity_code=opp.opp_code,
                        entity_name=opp.opp_name,
                        customer_name=opp.customer.customer_name if opp.customer else "未知客户",
                        owner_id=user_id,
                        owner_name=opp.owner.real_name if opp.owner else "",
                        message=f"商机【{opp.opp_name}】处于{opp.stage}阶段，已 {days_since_activity} 天无进展",
                        suggestion=self._get_follow_up_suggestion("opportunity", opp.stage),
                        days_overdue=days_overdue,
                        last_follow_up_at=opp.updated_at,
                        next_action_at=None,
                        est_amount=est_amount,
                    )
                )

        return reminders

    def _get_high_value_idle_reminders(self, user_id: int) -> List[FollowUpReminder]:
        """获取高价值客户闲置提醒"""
        reminders = []
        today = datetime.now()
        idle_threshold_days = 3  # 高价值客户超过3天未跟进就提醒

        opportunities = (
            self.db.query(Opportunity)
            .options(joinedload(Opportunity.owner), joinedload(Opportunity.customer))
            .filter(
                Opportunity.owner_id == user_id,
                Opportunity.stage.notin_(["CLOSED_WON", "CLOSED_LOST"]),
                Opportunity.est_amount >= HIGH_VALUE_THRESHOLD,
            )
            .all()
        )

        for opp in opportunities:
            days_since_activity = (today - opp.updated_at).days

            if days_since_activity > idle_threshold_days:
                est_amount = float(opp.est_amount) if opp.est_amount else None

                reminders.append(
                    FollowUpReminder(
                        type=ReminderType.HIGH_VALUE_IDLE,
                        priority=ReminderPriority.URGENT,  # 高价值始终紧急
                        entity_type="opportunity",
                        entity_id=opp.id,
                        entity_code=opp.opp_code,
                        entity_name=opp.opp_name,
                        customer_name=opp.customer.customer_name if opp.customer else "未知客户",
                        owner_id=user_id,
                        owner_name=opp.owner.real_name if opp.owner else "",
                        message=f"⚠️ 高价值商机【{opp.opp_name}】预估 {est_amount:,.0f} 元，已 {days_since_activity} 天未跟进",
                        suggestion="立即联系客户，确认项目进展和下一步计划",
                        days_overdue=days_since_activity - idle_threshold_days,
                        last_follow_up_at=opp.updated_at,
                        next_action_at=None,
                        est_amount=est_amount,
                    )
                )

        return reminders

    def _get_quote_expiring_reminders(self, user_id: int) -> List[FollowUpReminder]:
        """获取报价即将过期提醒"""
        reminders = []
        today = date.today()
        warning_days = 7  # 提前7天开始提醒

        quotes = (
            self.db.query(Quote)
            .options(
                joinedload(Quote.owner),
                joinedload(Quote.customer),
                joinedload(Quote.current_version),
            )
            .filter(
                Quote.owner_id == user_id,
                Quote.status.in_(["draft", "submitted", "approved"]),
                Quote.valid_until.isnot(None),
                Quote.valid_until <= today + timedelta(days=warning_days),
                Quote.valid_until >= today,  # 还没过期
            )
            .all()
        )

        for quote in quotes:
            days_until_expiry = (quote.valid_until - today).days
            total_price = (
                float(quote.current_version.total_price)
                if quote.current_version and quote.current_version.total_price
                else None
            )

            if days_until_expiry <= 3:
                priority = ReminderPriority.URGENT
            elif days_until_expiry <= 5:
                priority = ReminderPriority.HIGH
            else:
                priority = ReminderPriority.MEDIUM

            reminders.append(
                FollowUpReminder(
                    type=ReminderType.QUOTE_EXPIRING,
                    priority=priority,
                    entity_type="quote",
                    entity_id=quote.id,
                    entity_code=quote.quote_code,
                    entity_name=quote.title or f"报价 {quote.quote_code}",
                    customer_name=quote.customer.customer_name if quote.customer else "未知客户",
                    owner_id=user_id,
                    owner_name=quote.owner.real_name if quote.owner else "",
                    message=f"报价【{quote.quote_code}】将在 {days_until_expiry} 天后过期（{quote.valid_until}）",
                    suggestion="联系客户确认是否需要延期或重新报价",
                    days_overdue=-days_until_expiry,  # 负数表示还有几天
                    last_follow_up_at=quote.updated_at,
                    next_action_at=None,
                    est_amount=total_price,
                )
            )

        return reminders

    def _calculate_priority(
        self, days_overdue: int, est_amount: Optional[float]
    ) -> ReminderPriority:
        """根据逾期天数和金额计算优先级"""
        # 高价值客户提升优先级
        is_high_value = est_amount and est_amount >= HIGH_VALUE_THRESHOLD

        if days_overdue >= 14 or is_high_value:
            return ReminderPriority.URGENT
        elif days_overdue >= 7:
            return ReminderPriority.HIGH
        elif days_overdue >= 3:
            return ReminderPriority.MEDIUM
        else:
            return ReminderPriority.LOW

    def _get_follow_up_suggestion(self, entity_type: str, status_or_stage: str) -> str:
        """根据实体类型和状态生成跟进建议"""
        suggestions = {
            "lead": {
                "NEW": "电话联系客户，了解需求背景和时间计划",
                "CONTACTED": "发送产品资料或方案，约定下次沟通时间",
                "QUALIFIED": "安排技术评估或现场拜访",
                "default": "确认客户状态，推进到下一阶段",
            },
            "opportunity": {
                "DISCOVERY": "深入了解客户痛点，确认需求范围",
                "QUALIFICATION": "安排技术评估，明确技术可行性",
                "PROPOSAL": "准备报价方案，与客户讨论价格和条款",
                "NEGOTIATION": "处理客户异议，推动合同签署",
                "default": "确认商机状态，制定推进计划",
            },
        }

        entity_suggestions = suggestions.get(entity_type, {})
        return entity_suggestions.get(status_or_stage, entity_suggestions.get("default", "请跟进客户"))

    def get_due_action_digest(
        self, user_id: int, window_days: int = 3, limit: int = 50
    ) -> Dict[str, Any]:
        """获取线索行动提醒看板（超期 + 临近）"""
        overdue_items = self._get_lead_overdue_reminders(user_id)
        upcoming_items = self._get_lead_upcoming_reminders(user_id, window_days=window_days)

        priority_order = {
            ReminderPriority.URGENT: 0,
            ReminderPriority.HIGH: 1,
            ReminderPriority.MEDIUM: 2,
            ReminderPriority.LOW: 3,
        }
        overdue_items.sort(key=lambda r: (priority_order[r.priority], -r.days_overdue))
        upcoming_items.sort(
            key=lambda r: (
                priority_order[r.priority],
                r.next_action_at or datetime.max,
            )
        )

        high_priority_count = sum(
            1
            for reminder in [*overdue_items, *upcoming_items]
            if reminder.priority in {ReminderPriority.URGENT, ReminderPriority.HIGH}
        )

        return {
            "generated_at": datetime.now().isoformat(),
            "window_days": window_days,
            "overdue_count": len(overdue_items),
            "upcoming_count": len(upcoming_items),
            "high_priority_count": high_priority_count,
            "total": len(overdue_items) + len(upcoming_items),
            "overdue": overdue_items[:limit],
            "upcoming": upcoming_items[:limit],
        }

    def get_weekly_follow_up_report(
        self,
        user_id: int,
        week_start: Optional[date] = None,
        week_end: Optional[date] = None,
    ) -> Dict[str, Any]:
        """获取周维度跟进分析汇总"""
        reference_day = week_start or date.today()
        if week_start is None:
            reference_day = reference_day - timedelta(days=reference_day.weekday())

        period_start = week_start or reference_day
        period_end = week_end or (period_start + timedelta(days=6))

        start_dt = datetime.combine(period_start, time.min)
        end_exclusive = datetime.combine(period_end + timedelta(days=1), time.min)
        snapshot_at = min(end_exclusive, datetime.now())

        follow_up_count = (
            self.db.query(func.count(LeadFollowUp.id))
            .join(Lead, Lead.id == LeadFollowUp.lead_id)
            .filter(
                Lead.owner_id == user_id,
                LeadFollowUp.created_at >= start_dt,
                LeadFollowUp.created_at < end_exclusive,
            )
            .scalar()
            or 0
        )

        followed_lead_count = (
            self.db.query(func.count(func.distinct(LeadFollowUp.lead_id)))
            .join(Lead, Lead.id == LeadFollowUp.lead_id)
            .filter(
                Lead.owner_id == user_id,
                LeadFollowUp.created_at >= start_dt,
                LeadFollowUp.created_at < end_exclusive,
            )
            .scalar()
            or 0
        )

        overdue_count = (
            self.db.query(func.count(Lead.id))
            .filter(
                Lead.owner_id == user_id,
                Lead.status.in_(["NEW", "CONTACTED", "QUALIFIED"]),
                Lead.next_action_at.isnot(None),
                Lead.next_action_at < snapshot_at,
            )
            .scalar()
            or 0
        )

        converted_lead_count = (
            self.db.query(func.count(Lead.id))
            .filter(
                Lead.owner_id == user_id,
                Lead.status == "CONVERTED",
                Lead.updated_at >= start_dt,
                Lead.updated_at < end_exclusive,
            )
            .scalar()
            or 0
        )

        conversion_rate = round(
            ((converted_lead_count / followed_lead_count) * 100) if followed_lead_count else 0.0,
            2,
        )

        daily_rows = (
            self.db.query(
                func.date(LeadFollowUp.created_at).label("follow_up_date"),
                func.count(LeadFollowUp.id).label("follow_up_count"),
            )
            .join(Lead, Lead.id == LeadFollowUp.lead_id)
            .filter(
                Lead.owner_id == user_id,
                LeadFollowUp.created_at >= start_dt,
                LeadFollowUp.created_at < end_exclusive,
            )
            .group_by(func.date(LeadFollowUp.created_at))
            .order_by(func.date(LeadFollowUp.created_at))
            .all()
        )

        daily_breakdown = [
            {
                "date": row.follow_up_date,
                "follow_up_count": row.follow_up_count,
            }
            for row in daily_rows
        ]

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "snapshot_at": snapshot_at.isoformat(),
            "metrics": {
                "follow_up_count": int(follow_up_count),
                "followed_lead_count": int(followed_lead_count),
                "overdue_count": int(overdue_count),
                "converted_lead_count": int(converted_lead_count),
                "conversion_rate": conversion_rate,
            },
            "daily_breakdown": daily_breakdown,
        }

    def get_summary(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户跟进提醒摘要

        Returns:
            包含各类型数量和紧急程度的摘要
        """
        reminders = self.get_reminders_for_user(user_id, limit=200)

        summary = {
            "total": len(reminders),
            "by_priority": {
                "urgent": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "by_type": {
                "overdue_action": 0,
                "no_follow_up": 0,
                "quote_expiring": 0,
                "high_value_idle": 0,
            },
            "urgent_items": [],
        }

        for r in reminders:
            summary["by_priority"][r.priority.value] += 1
            summary["by_type"][r.type.value] += 1

            if r.priority == ReminderPriority.URGENT:
                summary["urgent_items"].append({
                    "type": r.type.value,
                    "entity_type": r.entity_type,
                    "entity_code": r.entity_code,
                    "message": r.message,
                })

        return summary
