# -*- coding: utf-8 -*-
"""Sales team aggregation contract tests."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.sales import Customer, Lead, LeadFollowUp, Opportunity, SalesTarget
from app.services.sales_ranking_service import SalesRankingService
from app.services.sales_team_service import SalesTeamService
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def _sales_user(db: Session, username_prefix: str):
    return _get_or_create_user(
        db,
        username=_unique(username_prefix).lower(),
        password="test123",
        real_name=f"{username_prefix} 用户",
        department="销售部",
        employee_role="SALES",
    )


def test_sales_team_maps_aggregate_real_sales_activity(db_session: Session):
    user = _sales_user(db_session, "team-agg")
    other_user = _sales_user(db_session, "team-other")
    created_at = datetime(2026, 3, 15, 10, 0, 0)

    customer = Customer(
        customer_code=_unique("CUST-TEAM"),
        customer_name="团队聚合客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
        created_at=created_at,
    )
    db_session.add(customer)
    db_session.flush()

    converted_lead = Lead(
        lead_code=_unique("LD-TEAM"),
        customer_name="团队聚合客户",
        owner_id=user.id,
        status="CONVERTED",
        completeness=80,
        created_at=created_at,
    )
    open_lead = Lead(
        lead_code=_unique("LD-TEAM"),
        customer_name="团队聚合客户二",
        owner_id=user.id,
        status="NEW",
        completeness=40,
        created_at=created_at,
    )
    other_lead = Lead(
        lead_code=_unique("LD-TEAM"),
        customer_name="其他销售客户",
        owner_id=other_user.id,
        status="NEW",
        created_at=created_at,
    )
    db_session.add_all([converted_lead, open_lead, other_lead])
    db_session.flush()

    db_session.add(
        LeadFollowUp(
            lead_id=converted_lead.id,
            follow_up_type="VISIT",
            content="拜访客户并确认预算",
            created_by=user.id,
            created_at=created_at,
        )
    )
    db_session.add_all(
        [
            Opportunity(
                opp_code=_unique("OPP-TEAM"),
                customer_id=customer.id,
                opp_name="已赢单商机",
                stage="WON",
                est_amount=Decimal("200000.00"),
                est_margin=Decimal("0.30"),
                owner_id=user.id,
                created_at=created_at,
            ),
            Opportunity(
                opp_code=_unique("OPP-TEAM"),
                customer_id=customer.id,
                opp_name="推进中商机",
                stage="PROPOSAL",
                est_amount=Decimal("150000.00"),
                est_margin=Decimal("0.20"),
                owner_id=user.id,
                created_at=created_at,
            ),
        ]
    )
    db_session.add(
        SalesTarget(
            target_scope="PERSONAL",
            user_id=user.id,
            target_type="LEAD_COUNT",
            target_period="MONTHLY",
            period_value="2026-03",
            target_value=Decimal("4"),
            status="ACTIVE",
            created_by=user.id,
        )
    )
    db_session.commit()

    service = SalesTeamService(db_session)
    user_ids = [user.id, other_user.id]
    start = datetime(2026, 3, 1)
    end = datetime(2026, 3, 31, 23, 59, 59)

    targets = service.build_personal_target_map(user_ids, "2026-03", None)
    recent = service.get_recent_followups_map(user_ids, start, end)
    customers = service.get_customer_distribution_map(user_ids, date(2026, 3, 1), date(2026, 3, 31))
    followups = service.get_followup_statistics_map(user_ids, start, end)
    leads = service.get_lead_quality_stats_map(user_ids, start, end)
    opportunities = service.get_opportunity_stats_map(user_ids, start, end)

    assert targets[user.id]["monthly"]["target_value"] == 4.0
    assert targets[user.id]["monthly"]["actual_value"] == 2.0
    assert targets[user.id]["monthly"]["completion_rate"] == 50.0
    assert recent[user.id][0]["content"] == "拜访客户并确认预算"
    assert customers[user.id]["total"] == 1
    assert customers[user.id]["new_customers"] == 1
    assert followups[user.id]["total"] == 1
    assert followups[user.id]["VISIT"] == 1
    assert leads[user.id]["total_leads"] == 2
    assert leads[user.id]["converted"] == 1
    assert leads[user.id]["conversion_rate"] == 50.0
    assert opportunities[user.id]["opportunity_count"] == 2
    assert opportunities[user.id]["won"] == 1
    assert opportunities[user.id]["pipeline_amount"] == 350000.0

    assert leads[other_user.id]["total_leads"] == 1
    assert opportunities[other_user.id]["opportunity_count"] == 0


def test_sales_ranking_uses_real_opportunity_statistics(db_session: Session):
    first = _sales_user(db_session, "rank-first")
    second = _sales_user(db_session, "rank-second")
    created_at = datetime(2026, 4, 10, 9, 0, 0)

    customer = Customer(
        customer_code=_unique("CUST-RANK"),
        customer_name="排名客户",
        sales_owner_id=first.id,
        created_by=first.id,
        created_at=created_at,
    )
    db_session.add(customer)
    db_session.flush()

    for idx, owner_id in enumerate([first.id, first.id, second.id], start=1):
        db_session.add(
            Opportunity(
                opp_code=_unique(f"OPP-RANK-{idx}"),
                customer_id=customer.id,
                opp_name=f"排名商机 {idx}",
                stage="PROPOSAL",
                est_amount=Decimal("100000.00"),
                est_margin=Decimal("0.20"),
                owner_id=owner_id,
                created_at=created_at,
            )
        )
    db_session.commit()

    ranking = SalesRankingService(db_session).calculate_rankings(
        [first, second],
        datetime(2026, 4, 1),
        datetime(2026, 4, 30, 23, 59, 59),
        ranking_type="opportunity_count",
    )

    assert ranking["rankings"][0]["user_id"] == first.id
    assert ranking["rankings"][0]["metrics"][3]["value"] == 2.0
    assert ranking["rankings"][1]["user_id"] == second.id
