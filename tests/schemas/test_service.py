# -*- coding: utf-8 -*-
"""Tests for app/schemas/service.py"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.service import (
    ServiceTicketCreate,
    ServiceTicketUpdate,
    ServiceTicketAssign,
    ServiceTicketClose,
    ServiceTicketResponse,
    ServiceRecordCreate,
    ServiceRecordUpdate,
    ServiceRecordResponse,
    CustomerCommunicationCreate,
    CustomerCommunicationUpdate,
    CustomerSatisfactionCreate,
    CustomerSatisfactionUpdate,
    ServiceDashboardStatistics,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    SatisfactionSurveyTemplateCreate,
)


class TestServiceTicketCreate:
    def test_valid(self):
        t = ServiceTicketCreate(
            project_id=1, customer_id=1,
            problem_type="MECHANICAL", problem_desc="设备异响",
            urgency="HIGH", reported_by="客户张三",
            reported_time=datetime.now(),
        )
        assert t.assignee_id is None
        assert t.cc_user_ids is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            ServiceTicketCreate()

    def test_with_assignee(self):
        t = ServiceTicketCreate(
            project_id=1, customer_id=1,
            problem_type="ELECTRICAL", problem_desc="D",
            urgency="LOW", reported_by="R",
            reported_time=datetime.now(),
            assignee_id=5, cc_user_ids=[6, 7],
        )
        assert t.assignee_id == 5


class TestServiceTicketUpdate:
    def test_all_none(self):
        t = ServiceTicketUpdate()
        assert t.problem_desc is None

    def test_partial(self):
        t = ServiceTicketUpdate(urgency="CRITICAL", status="IN_PROGRESS")
        assert t.urgency == "CRITICAL"


class TestServiceTicketAssign:
    def test_valid(self):
        a = ServiceTicketAssign(assignee_id=1)
        assert a.cc_user_ids is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            ServiceTicketAssign()


class TestServiceTicketClose:
    def test_valid(self):
        c = ServiceTicketClose(solution="更换轴承")
        assert c.satisfaction is None

    def test_satisfaction_bounds(self):
        ServiceTicketClose(solution="S", satisfaction=1)
        ServiceTicketClose(solution="S", satisfaction=5)

    def test_satisfaction_out_of_range(self):
        with pytest.raises(ValidationError):
            ServiceTicketClose(solution="S", satisfaction=0)
        with pytest.raises(ValidationError):
            ServiceTicketClose(solution="S", satisfaction=6)

    def test_missing(self):
        with pytest.raises(ValidationError):
            ServiceTicketClose()


class TestServiceRecordCreate:
    def test_valid(self):
        r = ServiceRecordCreate(
            service_type="INSTALLATION",
            project_id=1, customer_id=1,
            service_date=date(2024, 6, 1),
            service_engineer_id=1,
            service_content="安装调试",
        )
        assert r.status == "SCHEDULED"
        assert r.customer_signed is False

    def test_satisfaction_bounds(self):
        r = ServiceRecordCreate(
            service_type="T", project_id=1, customer_id=1,
            service_date=date(2024, 1, 1), service_engineer_id=1,
            service_content="C", customer_satisfaction=1,
        )
        assert r.customer_satisfaction == 1

    def test_satisfaction_invalid(self):
        with pytest.raises(ValidationError):
            ServiceRecordCreate(
                service_type="T", project_id=1, customer_id=1,
                service_date=date(2024, 1, 1), service_engineer_id=1,
                service_content="C", customer_satisfaction=6,
            )

    def test_missing(self):
        with pytest.raises(ValidationError):
            ServiceRecordCreate()


class TestCustomerCommunicationCreate:
    def test_valid(self):
        c = CustomerCommunicationCreate(
            communication_type="PHONE",
            customer_name="客户A",
            communication_date=date(2024, 6, 1),
            topic="项目进展", subject="进度沟通",
            content="讨论了项目进度",
        )
        assert c.follow_up_required is False
        assert c.importance == "中"

    def test_missing(self):
        with pytest.raises(ValidationError):
            CustomerCommunicationCreate()


class TestCustomerSatisfactionCreate:
    def test_valid(self):
        s = CustomerSatisfactionCreate(
            survey_type="PROJECT",
            customer_name="客户A",
            survey_date=date(2024, 6, 1),
            send_method="EMAIL",
        )
        assert s.deadline is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            CustomerSatisfactionCreate()


class TestServiceDashboardStatistics:
    def test_defaults(self):
        d = ServiceDashboardStatistics()
        assert d.active_cases == 0
        assert d.customer_satisfaction == 0.0
        assert d.today_new_tickets is None

    def test_with_data(self):
        d = ServiceDashboardStatistics(
            active_cases=10, resolved_today=5,
            avg_response_time=2.5, customer_satisfaction=4.5,
        )
        assert d.avg_response_time == 2.5


class TestKnowledgeBaseCreate:
    def test_valid(self):
        k = KnowledgeBaseCreate(title="常见问题", category="FAQ")
        assert k.is_faq is False
        assert k.is_featured is False
        assert k.status == "DRAFT"
        assert k.allow_download is True

    def test_missing(self):
        with pytest.raises(ValidationError):
            KnowledgeBaseCreate()


class TestKnowledgeBaseUpdate:
    def test_all_none(self):
        k = KnowledgeBaseUpdate()
        assert k.title is None

    def test_partial(self):
        k = KnowledgeBaseUpdate(title="新标题", is_faq=True)
        assert k.is_faq is True


class TestKnowledgeBaseResponse:
    def test_valid(self):
        now = datetime.now()
        k = KnowledgeBaseResponse(
            id=1, article_no="KB001", title="T", category="C",
            is_faq=False, is_featured=False, status="PUBLISHED",
            view_count=10, like_count=5, helpful_count=3,
            author_id=1, created_at=now, updated_at=now,
        )
        assert k.download_count == 0
        assert k.adopt_count == 0
        assert k.allow_download is True


class TestSatisfactionSurveyTemplateCreate:
    def test_valid(self):
        t = SatisfactionSurveyTemplateCreate(
            template_name="项目满意度",
            template_code="TPL001",
            survey_type="PROJECT",
            questions=[{"q": "满意度如何?", "type": "rating"}],
        )
        assert t.default_deadline_days == 7

    def test_missing(self):
        with pytest.raises(ValidationError):
            SatisfactionSurveyTemplateCreate()
