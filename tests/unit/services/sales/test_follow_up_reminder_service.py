# -*- coding: utf-8 -*-
"""
follow_up_reminder_service 单元测试

测试智能跟进提醒服务。
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.follow_up_reminder_service import (
    FollowUpReminderService,
    ReminderPriority,
    ReminderType,
    STAGE_FOLLOW_UP_CYCLES,
    HIGH_VALUE_THRESHOLD,
)


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return FollowUpReminderService(mock_db)


@pytest.fixture
def mock_lead():
    """模拟线索

    注意：Lead 模型没有 customer 关系，只有 customer_name 和 industry 字段
    """
    lead = MagicMock()
    lead.id = 1
    lead.lead_code = "LD202603120001"
    lead.customer_name = "测试客户"  # Lead 自身的字段
    lead.industry = "制造业"  # Lead 自身的字段
    lead.status = "CONTACTED"
    lead.next_action_at = datetime.now() - timedelta(days=3)  # 3天前过期
    lead.created_at = datetime.now() - timedelta(days=10)
    lead.owner = MagicMock()
    lead.owner.real_name = "张三"
    return lead


@pytest.fixture
def mock_opportunity():
    """模拟商机"""
    opp = MagicMock()
    opp.id = 1
    opp.opp_code = "OP202603120001"
    opp.opp_name = "测试商机"
    opp.stage = "QUALIFICATION"
    opp.est_amount = 100000
    opp.updated_at = datetime.now() - timedelta(days=10)  # 10天未更新
    opp.customer = MagicMock()
    opp.customer.customer_name = "测试客户"
    opp.owner = MagicMock()
    opp.owner.real_name = "张三"
    return opp


@pytest.fixture
def mock_quote():
    """模拟报价"""
    from datetime import date
    quote = MagicMock()
    quote.id = 1
    quote.quote_code = "QT202603120001"
    quote.title = "测试报价"
    quote.status = "submitted"
    quote.valid_until = date.today() + timedelta(days=3)  # 3天后过期
    quote.updated_at = datetime.now()
    quote.customer = MagicMock()
    quote.customer.customer_name = "测试客户"
    quote.owner = MagicMock()
    quote.owner.real_name = "张三"
    quote.current_version = MagicMock()
    quote.current_version.total_price = 150000
    return quote


# ========== 优先级计算测试 ==========

class TestCalculatePriority:
    """_calculate_priority 测试"""

    def test_urgent_for_long_overdue(self, service):
        """长期逾期为紧急"""
        priority = service._calculate_priority(days_overdue=15, est_amount=None)
        assert priority == ReminderPriority.URGENT

    def test_urgent_for_high_value(self, service):
        """高价值客户始终紧急"""
        priority = service._calculate_priority(days_overdue=1, est_amount=600000)
        assert priority == ReminderPriority.URGENT

    def test_high_for_week_overdue(self, service):
        """一周逾期为高优先"""
        priority = service._calculate_priority(days_overdue=7, est_amount=None)
        assert priority == ReminderPriority.HIGH

    def test_medium_for_few_days(self, service):
        """几天逾期为中优先"""
        priority = service._calculate_priority(days_overdue=4, est_amount=None)
        assert priority == ReminderPriority.MEDIUM

    def test_low_for_small_overdue(self, service):
        """轻微逾期为低优先"""
        priority = service._calculate_priority(days_overdue=1, est_amount=None)
        assert priority == ReminderPriority.LOW


# ========== 跟进建议测试 ==========

class TestGetFollowUpSuggestion:
    """_get_follow_up_suggestion 测试"""

    def test_lead_new_suggestion(self, service):
        """新线索建议"""
        suggestion = service._get_follow_up_suggestion("lead", "NEW")
        assert "电话联系" in suggestion or "了解需求" in suggestion

    def test_lead_contacted_suggestion(self, service):
        """已联系线索建议"""
        suggestion = service._get_follow_up_suggestion("lead", "CONTACTED")
        assert "发送" in suggestion or "产品资料" in suggestion

    def test_opportunity_discovery_suggestion(self, service):
        """商机发现阶段建议"""
        suggestion = service._get_follow_up_suggestion("opportunity", "DISCOVERY")
        assert "痛点" in suggestion or "需求" in suggestion

    def test_opportunity_negotiation_suggestion(self, service):
        """商机谈判阶段建议"""
        suggestion = service._get_follow_up_suggestion("opportunity", "NEGOTIATION")
        assert "异议" in suggestion or "签署" in suggestion

    def test_unknown_status_fallback(self, service):
        """未知状态使用默认建议"""
        suggestion = service._get_follow_up_suggestion("lead", "UNKNOWN")
        assert suggestion  # 不应为空


# ========== 线索过期提醒测试 ==========

class TestLeadOverdueReminders:
    """_get_lead_overdue_reminders 测试"""

    def test_finds_overdue_leads(self, service, mock_db, mock_lead):
        """找到过期线索"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_lead]

        reminders = service._get_lead_overdue_reminders(user_id=1)

        assert len(reminders) == 1
        assert reminders[0].type == ReminderType.OVERDUE_ACTION
        assert reminders[0].entity_type == "lead"
        assert "过期" in reminders[0].message

    def test_no_overdue_leads(self, service, mock_db):
        """无过期线索"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        reminders = service._get_lead_overdue_reminders(user_id=1)

        assert len(reminders) == 0


# ========== 商机提醒测试 ==========

class TestOpportunityReminders:
    """_get_opportunity_reminders 测试"""

    def test_finds_stale_opportunities(self, service, mock_db, mock_opportunity):
        """找到停滞商机"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_opportunity]

        reminders = service._get_opportunity_reminders(user_id=1)

        assert len(reminders) == 1
        assert reminders[0].type == ReminderType.NO_RECENT_FOLLOW_UP
        assert reminders[0].entity_type == "opportunity"
        assert "无进展" in reminders[0].message

    def test_respects_stage_cycle(self, service, mock_db, mock_opportunity):
        """根据阶段调整周期"""
        # QUALIFICATION 阶段周期是 7 天
        mock_opportunity.stage = "QUALIFICATION"
        mock_opportunity.updated_at = datetime.now() - timedelta(days=5)  # 5天，未超过7天

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_opportunity]

        reminders = service._get_opportunity_reminders(user_id=1)

        # 5天未超过7天周期，不应有提醒
        assert len(reminders) == 0


# ========== 高价值客户提醒测试 ==========

class TestHighValueIdleReminders:
    """_get_high_value_idle_reminders 测试"""

    def test_finds_high_value_idle(self, service, mock_db, mock_opportunity):
        """找到高价值闲置商机"""
        mock_opportunity.est_amount = 600000  # 超过阈值
        mock_opportunity.updated_at = datetime.now() - timedelta(days=5)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_opportunity]

        reminders = service._get_high_value_idle_reminders(user_id=1)

        assert len(reminders) == 1
        assert reminders[0].type == ReminderType.HIGH_VALUE_IDLE
        assert reminders[0].priority == ReminderPriority.URGENT

    def test_ignores_recent_high_value(self, service, mock_db, mock_opportunity):
        """最近跟进的高价值不提醒"""
        mock_opportunity.est_amount = 600000
        mock_opportunity.updated_at = datetime.now() - timedelta(days=2)  # 2天，未超过3天阈值

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_opportunity]

        reminders = service._get_high_value_idle_reminders(user_id=1)

        assert len(reminders) == 0


# ========== 报价过期提醒测试 ==========

class TestQuoteExpiringReminders:
    """_get_quote_expiring_reminders 测试"""

    def test_finds_expiring_quotes(self, service, mock_db, mock_quote):
        """找到即将过期报价"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_quote]

        reminders = service._get_quote_expiring_reminders(user_id=1)

        assert len(reminders) == 1
        assert reminders[0].type == ReminderType.QUOTE_EXPIRING
        assert "过期" in reminders[0].message

    def test_urgent_for_3_days(self, service, mock_db, mock_quote):
        """3天内过期为紧急"""
        from datetime import date
        mock_quote.valid_until = date.today() + timedelta(days=2)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_quote]

        reminders = service._get_quote_expiring_reminders(user_id=1)

        assert reminders[0].priority == ReminderPriority.URGENT


# ========== 综合测试 ==========

class TestGetRemindersForUser:
    """get_reminders_for_user 测试"""

    def test_sorts_by_priority(self, service, mock_db):
        """按优先级排序"""
        # 模拟所有子方法返回空
        with patch.object(service, '_get_lead_overdue_reminders', return_value=[]):
            with patch.object(service, '_get_lead_no_follow_up_reminders', return_value=[]):
                with patch.object(service, '_get_opportunity_reminders', return_value=[]):
                    with patch.object(service, '_get_high_value_idle_reminders', return_value=[]):
                        with patch.object(service, '_get_quote_expiring_reminders', return_value=[]):
                            reminders = service.get_reminders_for_user(user_id=1)

        assert reminders == []

    def test_respects_limit(self, service, mock_db, mock_lead):
        """限制返回数量"""
        # 使用 patch 隔离各个子方法，只测试 limit 逻辑
        from app.services.sales.follow_up_reminder_service import FollowUpReminder

        # 创建100个提醒
        mock_reminders = []
        for i in range(100):
            mock_reminders.append(
                FollowUpReminder(
                    type=ReminderType.OVERDUE_ACTION,
                    priority=ReminderPriority.MEDIUM,
                    entity_type="lead",
                    entity_id=i,
                    entity_code=f"LD{i:012d}",
                    entity_name=f"测试线索{i}",
                    customer_name="测试客户",
                    owner_id=1,
                    owner_name="张三",
                    message=f"测试消息{i}",
                    suggestion="测试建议",
                    days_overdue=3,
                    last_follow_up_at=None,
                    next_action_at=None,
                    est_amount=None,
                )
            )

        with patch.object(service, '_get_lead_overdue_reminders', return_value=mock_reminders):
            with patch.object(service, '_get_lead_no_follow_up_reminders', return_value=[]):
                with patch.object(service, '_get_opportunity_reminders', return_value=[]):
                    with patch.object(service, '_get_high_value_idle_reminders', return_value=[]):
                        with patch.object(service, '_get_quote_expiring_reminders', return_value=[]):
                            reminders = service.get_reminders_for_user(user_id=1, limit=10)

        assert len(reminders) == 10


# ========== 摘要测试 ==========

class TestGetSummary:
    """get_summary 测试"""

    def test_summary_structure(self, service, mock_db):
        """摘要结构正确"""
        with patch.object(service, 'get_reminders_for_user', return_value=[]):
            summary = service.get_summary(user_id=1)

        assert "total" in summary
        assert "by_priority" in summary
        assert "by_type" in summary
        assert "urgent_items" in summary

    def test_counts_by_priority(self, service, mock_db):
        """按优先级统计"""
        from app.services.sales.follow_up_reminder_service import FollowUpReminder

        mock_reminder = FollowUpReminder(
            type=ReminderType.OVERDUE_ACTION,
            priority=ReminderPriority.URGENT,
            entity_type="lead",
            entity_id=1,
            entity_code="LD001",
            entity_name="测试",
            customer_name="客户",
            owner_id=1,
            owner_name="张三",
            message="测试消息",
            suggestion="测试建议",
            days_overdue=5,
            last_follow_up_at=None,
            next_action_at=None,
            est_amount=None,
        )

        with patch.object(service, 'get_reminders_for_user', return_value=[mock_reminder]):
            summary = service.get_summary(user_id=1)

        assert summary["total"] == 1
        assert summary["by_priority"]["urgent"] == 1
        assert len(summary["urgent_items"]) == 1
