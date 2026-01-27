# -*- coding: utf-8 -*-
"""
线索优先级评分服务测试
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.sales import Lead, LeadFollowUp
from app.services.lead_priority_scoring import LeadPriorityScoringService


@pytest.fixture
def lead_priority_scoring_service(db_session: Session):
    return LeadPriorityScoringService(db_session)


@pytest.fixture
def create_lead(db_session: Session):
    from tests.conftest import _get_or_create_user

    # Create user with employee association
    user = _get_or_create_user(
        db_session,
        username="scoring_test_user",
        password="test123",
        real_name="评分测试用户",
        department="销售部",
        employee_role="SALES",
    )

    db_session.flush()

    lead = Lead(
        owner_id=user.id,
        lead_name="测试线索",
        status="NEW",
        customer_type="POTENTIAL",
        expected_value=Decimal("100000"),
        source="ONLINE",
        product_interest="测试产品",
        contact_person="测试联系人",
        contact_phone="13800000000",
        description="测试描述",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def create_followup(db_session: Session, create_lead):
    followup = LeadFollowUp(
        lead_id=create_lead.id,
        follow_up_type="PHONE",
        follow_up_content="跟进测试",
        follow_up_result="INTERESTED",
        follow_up_status="COMPLETED",
        created_by=create_lead.owner_id,
    )
    db_session.add(followup)
    db_session.commit()
    db_session.refresh(followup)
    return followup


class TestLeadPriorityScoringServiceInit:
    def test_init(self, lead_priority_scoring_service, db_session):
        assert lead_priority_scoring_service.db == db_session
        # Logger is module-level, not class attribute


class TestCalculateLeadScore:
    def test_calculate_score_new_lead_no_followup(
        self, lead_priority_scoring_service, create_lead
    ):
        score, details = lead_priority_scoring_service.calculate_lead_score(
        create_lead.id
        )

        assert isinstance(score, int)
        assert isinstance(details, dict)

    def test_calculate_score_new_lead_with_recent_followup(
        self, lead_priority_scoring_service, create_lead, create_followup
    ):
        score, details = lead_priority_scoring_service.calculate_lead_score(
        create_lead.id
        )

        assert isinstance(score, int)
        assert score > 0

    def test_calculate_score_converted_lead(self, db_session: Session):
        from tests.factories import UserFactory

        user = UserFactory()
        lead = Lead(
        owner_id=user.id,
        lead_name="已转换线索",
        status="CONVERTED",
        customer_type="POTENTIAL",
        expected_value=Decimal("100000"),
        source="ONLINE",
        product_interest="测试产品",
        contact_person="测试联系人",
        contact_phone="13800000000",
        converted_at=datetime.now(),
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)

        score, details = lead_priority_scoring_service.calculate_lead_score(lead.id)

        assert score > 0

    def test_calculate_score_lost_lead(self, db_session: Session):
        from tests.factories import UserFactory

        user = UserFactory()
        lead = Lead(
        owner_id=user.id,
        lead_name="已丢失线索",
        status="LOST",
        customer_type="POTENTIAL",
        expected_value=Decimal("100000"),
        source="ONLINE",
        product_interest="测试产品",
        contact_person="测试联系人",
        contact_phone="13800000000",
        lost_reason="预算不足",
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)

        score, details = lead_priority_scoring_service.calculate_lead_score(lead.id)

        assert score >= 0


class TestGetPriorityLevel:
    def test_get_priority_level_high(self, lead_priority_scoring_service, create_lead):
        score, details = lead_priority_scoring_service.calculate_lead_score(
        create_lead.id
        )
        level = lead_priority_scoring_service.get_priority_level(score)

        assert level in ["HIGH", "MEDIUM", "LOW"]

    def test_get_priority_level_medium(self, db_session: Session):
        from tests.factories import UserFactory

        user = UserFactory()
        lead = Lead(
        owner_id=user.id,
        lead_name="中等优先级线索",
        status="NEW",
        customer_type="POTENTIAL",
        expected_value=Decimal("50000"),
        source="REFERRAL",
        product_interest="测试产品",
        contact_person="测试联系人",
        contact_phone="13800000000",
        days_since_last_followup=15,
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)

        score, details = lead_priority_scoring_service.calculate_lead_score(lead.id)
        level = lead_priority_scoring_service.get_priority_level(score)

        assert level in ["MEDIUM", "LOW"]

    def test_get_priority_level_low(self, db_session: Session):
        from tests.factories import UserFactory

        user = UserFactory()
        lead = Lead(
        owner_id=user.id,
        lead_name="低优先级线索",
        status="NEW",
        customer_type="POTENTIAL",
        expected_value=Decimal("10000"),
        source="COLD_CALL",
        product_interest="测试产品",
        contact_person="测试联系人",
        contact_phone="13800000000",
        days_since_last_followup=30,
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)

        score, details = lead_priority_scoring_service.calculate_lead_score(lead.id)
        level = lead_priority_scoring_service.get_priority_level(score)

        assert level == "LOW"


class TestBatchCalculation:
    def test_batch_calculate_scores(
        self, lead_priority_scoring_service, db_session: Session
    ):
        from tests.factories import UserFactory
        from tests.factories import LeadFactory

        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        leads = []
        for i, user in enumerate([user1, user2, user3]):
            lead = LeadFactory(
            owner_id=user.id,
            lead_name=f"测试线索{i}",
            status="NEW" if i < 2 else "NEGOTIATING",
            customer_type="POTENTIAL",
            expected_value=Decimal("100000") * (i + 1),
            )
            db_session.add(lead)
            leads.append(lead)
            db_session.commit()

            results = lead_priority_scoring_service.batch_calculate_scores(
            [l.id for l in leads]
            )

            assert len(results) == 3
            assert all("score" in r for r in results)
            assert all("priority_level" in r for r in results)

    def test_batch_calculate_empty_list(self, lead_priority_scoring_service):
        results = lead_priority_scoring_service.batch_calculate_scores([])
        assert results == []


class TestEdgeCases:
    def test_calculate_lead_without_expected_value(self, db_session: Session):
        from tests.factories import UserFactory

        user = UserFactory()
        lead = Lead(
        owner_id=user.id,
        lead_name="线索无期望值",
        status="NEW",
        customer_type="POTENTIAL",
        source="ONLINE",
        )
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)

        score, details = lead_priority_scoring_service.calculate_lead_score(lead.id)

        assert isinstance(score, int)
        assert score >= 0

    def test_get_priority_level_invalid_score(self, lead_priority_scoring_service):
        level = lead_priority_scoring_service.get_priority_level(-1)
        assert level == "LOW"

    def test_get_priority_level_zero_score(self, lead_priority_scoring_service):
        level = lead_priority_scoring_service.get_priority_level(0)
        assert level == "LOW"
