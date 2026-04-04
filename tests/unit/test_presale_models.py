# -*- coding: utf-8 -*-
"""
售前模型枚举测试
"""

import pytest


class TestTicketTypeEnum:
    """测试工单类型枚举"""

    def test_ticket_type_values(self):
        """测试枚举值"""
        from app.models.presale import TicketTypeEnum

        assert TicketTypeEnum.CONSULT.value == "CONSULT"
        assert TicketTypeEnum.SURVEY.value == "SURVEY"
        assert TicketTypeEnum.SOLUTION.value == "SOLUTION"
        assert TicketTypeEnum.QUOTATION.value == "QUOTATION"
        assert TicketTypeEnum.TENDER.value == "TENDER"
        assert TicketTypeEnum.MEETING.value == "MEETING"
        assert TicketTypeEnum.SITE_VISIT.value == "SITE_VISIT"

    def test_ticket_type_from_string(self):
        """测试从字符串创建"""
        from app.models.presale import TicketTypeEnum

        assert TicketTypeEnum("CONSULT") == TicketTypeEnum.CONSULT
        assert TicketTypeEnum("SOLUTION") == TicketTypeEnum.SOLUTION


class TestTicketUrgencyEnum:
    """测试紧急程度枚举"""

    def test_urgency_values(self):
        """测试枚举值"""
        from app.models.presale import TicketUrgencyEnum

        assert TicketUrgencyEnum.NORMAL.value == "NORMAL"
        assert TicketUrgencyEnum.URGENT.value == "URGENT"
        assert TicketUrgencyEnum.VERY_URGENT.value == "VERY_URGENT"


class TestTicketStatusEnum:
    """测试工单状态枚举"""

    def test_status_values(self):
        """测试枚举值"""
        from app.models.presale import TicketStatusEnum

        assert TicketStatusEnum.PENDING.value == "PENDING"
        assert TicketStatusEnum.ACCEPTED.value == "ACCEPTED"
        assert TicketStatusEnum.PROCESSING.value == "PROCESSING"
        assert TicketStatusEnum.REVIEW.value == "REVIEW"
        assert TicketStatusEnum.COMPLETED.value == "COMPLETED"
        assert TicketStatusEnum.CLOSED.value == "CLOSED"
        assert TicketStatusEnum.CANCELLED.value == "CANCELLED"