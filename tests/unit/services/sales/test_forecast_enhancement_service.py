# -*- coding: utf-8 -*-
"""
sales forecast enhancement service 单元测试
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project.customer import Customer
from app.models.sales import (
    Contract,
    Lead,
    LeadFollowUp,
    Opportunity,
    Quote,
    SalesTarget,
    SalesTeam,
    SalesTeamMember,
)
from app.models.user import User
from app.services.sales.forecast_enhancement_service import SalesForecastEnhancementService


def _suffix() -> str:
    return uuid4().hex[:8]


def _create_department(db: Session) -> Department:
    department = Department(
        dept_code=f"DEP-{_suffix()}",
        dept_name=f"销售部-{_suffix()}",
        is_active=True,
    )
    db.add(department)
    db.flush()
    return department


def _create_user(db: Session, department: Department, prefix: str) -> User:
    user = User(
        username=f"{prefix}_{_suffix()}",
        password_hash="hashed-password",
        real_name=f"{prefix}_{_suffix()}",
        department_id=department.id,
        department=department.dept_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _create_customer(db: Session) -> Customer:
    customer = Customer(
        customer_code=f"CUST-{_suffix()}",
        customer_name=f"测试客户-{_suffix()}",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()
    return customer


def _create_team(db: Session, department: Department, leader: User, members: list[User]) -> SalesTeam:
    team = SalesTeam(
        team_code=f"TEAM-{_suffix()}",
        team_name=f"华南大区-{_suffix()}",
        department_id=department.id,
        leader_id=leader.id,
        created_by=leader.id,
        is_active=True,
    )
    db.add(team)
    db.flush()

    for index, member in enumerate(members):
        db.add(
            SalesTeamMember(
                team_id=team.id,
                user_id=member.id,
                is_active=True,
                is_primary=index == 0,
            )
        )

    db.flush()
    return team


def _seed_sales_data(db_session: Session) -> dict[str, User]:
    department = _create_department(db_session)
    good_user = _create_user(db_session, department, "sales_good")
    low_user = _create_user(db_session, department, "sales_low")
    customer = _create_customer(db_session)
    _create_team(db_session, department, good_user, [good_user, low_user])

    good_active_lead = Lead(
        lead_code=f"LEAD-{_suffix()}",
        customer_name="优质线索",
        owner_id=good_user.id,
        created_at=datetime(2026, 3, 1, 10, 0, 0),
    )
    good_won_lead = Lead(
        lead_code=f"LEAD-{_suffix()}",
        customer_name="已成交线索",
        owner_id=good_user.id,
        created_at=datetime(2026, 2, 1, 9, 0, 0),
    )
    low_active_lead = Lead(
        lead_code=f"LEAD-{_suffix()}",
        customer_name="风险线索",
        owner_id=low_user.id,
        created_at=datetime(2026, 2, 1, 8, 0, 0),
    )
    low_lost_lead = Lead(
        lead_code=f"LEAD-{_suffix()}",
        customer_name="输单线索",
        owner_id=low_user.id,
        created_at=datetime(2026, 1, 1, 8, 0, 0),
    )
    db_session.add_all([good_active_lead, good_won_lead, low_active_lead, low_lost_lead])
    db_session.flush()

    db_session.add_all(
        [
            LeadFollowUp(
                lead_id=good_active_lead.id,
                follow_up_type="VISIT",
                content="上门拜访",
                created_by=good_user.id,
                created_at=datetime(2026, 3, 2, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=good_active_lead.id,
                follow_up_type="CALL",
                content="电话沟通",
                created_by=good_user.id,
                created_at=datetime(2026, 3, 3, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=good_active_lead.id,
                follow_up_type="MEETING",
                content="方案评审会议",
                created_by=good_user.id,
                created_at=datetime(2026, 3, 15, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=good_won_lead.id,
                follow_up_type="CALL",
                content="成交确认",
                created_by=good_user.id,
                created_at=datetime(2026, 2, 20, 11, 0, 0),
            ),
            LeadFollowUp(
                lead_id=low_active_lead.id,
                follow_up_type="CALL",
                content="很久以前的跟进",
                created_by=low_user.id,
                created_at=datetime(2026, 2, 20, 9, 0, 0),
            ),
        ]
    )

    good_active_opp = Opportunity(
        opp_code=f"OPP-{_suffix()}",
        lead_id=good_active_lead.id,
        customer_id=customer.id,
        opp_name="优质活跃商机",
        stage="NEGOTIATION",
        est_amount=Decimal("1200000"),
        expected_close_date=date(2026, 3, 28),
        budget_range="100-150万",
        decision_chain="EB/TB/PB",
        risk_level="LOW",
        delivery_window="2026-Q2",
        owner_id=good_user.id,
        updated_at=datetime(2026, 3, 10, 10, 0, 0),
    )
    good_won_opp = Opportunity(
        opp_code=f"OPP-{_suffix()}",
        lead_id=good_won_lead.id,
        customer_id=customer.id,
        opp_name="已成交商机",
        stage="WON",
        est_amount=Decimal("900000"),
        expected_close_date=date(2026, 3, 4),
        budget_range="80-100万",
        decision_chain="EB/TB/PB",
        risk_level="LOW",
        delivery_window="2026-Q2",
        owner_id=good_user.id,
        updated_at=datetime(2026, 3, 4, 10, 0, 0),
    )
    low_active_opp = Opportunity(
        opp_code=f"OPP-{_suffix()}",
        lead_id=low_active_lead.id,
        customer_id=customer.id,
        opp_name="风险活跃商机",
        stage="PROPOSAL",
        est_amount=Decimal("800000"),
        expected_close_date=date(2026, 3, 20),
        owner_id=low_user.id,
        updated_at=datetime(2026, 3, 8, 10, 0, 0),
    )
    low_lost_opp = Opportunity(
        opp_code=f"OPP-{_suffix()}",
        lead_id=low_lost_lead.id,
        customer_id=customer.id,
        opp_name="已输单商机",
        stage="LOST",
        est_amount=Decimal("500000"),
        owner_id=low_user.id,
        updated_at=datetime(2026, 1, 15, 10, 0, 0),
    )
    db_session.add_all([good_active_opp, good_won_opp, low_active_opp, low_lost_opp])
    db_session.flush()

    db_session.add(
        Quote(
            quote_code=f"QT-{_suffix()}",
            opportunity_id=good_active_opp.id,
            customer_id=customer.id,
            owner_id=good_user.id,
            created_at=datetime(2026, 3, 6, 10, 0, 0),
        )
    )

    db_session.add_all(
        [
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="当季签约合同",
                contract_type="sales",
                opportunity_id=good_won_opp.id,
                customer_id=customer.id,
                total_amount=Decimal("1500000"),
                signing_date=date(2026, 3, 4),
                status="SIGNED",
                sales_owner_id=good_user.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="二月签约合同",
                contract_type="sales",
                customer_id=customer.id,
                total_amount=Decimal("800000"),
                signing_date=date(2026, 2, 20),
                status="SIGNED",
                sales_owner_id=good_user.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="一月签约合同",
                contract_type="sales",
                customer_id=customer.id,
                total_amount=Decimal("600000"),
                signing_date=date(2026, 1, 18),
                status="SIGNED",
                sales_owner_id=good_user.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="去年十二月签约合同",
                contract_type="sales",
                customer_id=customer.id,
                total_amount=Decimal("500000"),
                signing_date=date(2025, 12, 20),
                status="SIGNED",
                sales_owner_id=good_user.id,
            ),
        ]
    )

    db_session.add_all(
        [
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2026-Q1",
                target_value=Decimal("5000000"),
                created_by=good_user.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2026-02",
                target_value=Decimal("1000000"),
                created_by=good_user.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2026-01",
                target_value=Decimal("700000"),
                created_by=good_user.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2025-12",
                target_value=Decimal("400000"),
                created_by=good_user.id,
            ),
            SalesTarget(
                target_scope="PERSONAL",
                user_id=good_user.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2026-02",
                target_value=Decimal("1000000"),
                created_by=good_user.id,
            ),
            SalesTarget(
                target_scope="PERSONAL",
                user_id=low_user.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2026-02",
                target_value=Decimal("500000"),
                created_by=good_user.id,
            ),
        ]
    )
    db_session.flush()

    return {"good_user": good_user, "low_user": low_user}


class TestSalesForecastEnhancementService:

    def test_get_enhanced_prediction_uses_real_sales_data(self, db_session: Session):
        _seed_sales_data(db_session)
        service = SalesForecastEnhancementService(db_session)

        result = service.get_enhanced_prediction(period="quarterly")

        assert result["period"] == "2026-Q1"
        assert result["base_prediction"]["completed"] == 2900000.0
        assert result["activity_factor"]["metrics"]["proposals_actual"] == 1
        assert result["opportunity_health_factor"]["at_risk_opportunities"]["count"] == 1
        assert result["historical_accuracy_factor"]["recent_predictions"]
        assert result["key_insights"]

    def test_get_data_quality_score_ranks_real_users(self, db_session: Session):
        users = _seed_sales_data(db_session)
        service = SalesForecastEnhancementService(db_session)

        result = service.get_data_quality_score()

        assert result["company_average"] > 0
        assert len(result["rankings"]) == 2
        assert result["rankings"][0]["sales_id"] == users["good_user"].id
        assert result["rankings"][0]["overall_score"] > result["rankings"][1]["overall_score"]
        assert result["rankings"][1]["alerts"]

    def test_get_activity_tracking_aggregates_follow_ups_and_quotes(self, db_session: Session):
        users = _seed_sales_data(db_session)
        service = SalesForecastEnhancementService(db_session)

        result = service.get_activity_tracking(period="monthly")
        good_profile = next(
            item for item in result["individual_tracking"] if item["sales_id"] == users["good_user"].id
        )

        assert result["period"] == "2026-03"
        assert result["team_summary"]["visits"]["actual"] == 1
        assert result["team_summary"]["calls"]["actual"] == 1
        assert result["team_summary"]["meetings"]["actual"] == 1
        assert result["team_summary"]["proposals"]["actual"] == 1
        assert good_profile["activities"]["proposals"]["actual"] == 1
        assert good_profile["avg_response_time_hours"] == 24.0

    def test_get_accuracy_comparison_groups_by_quality_band(self, db_session: Session):
        _seed_sales_data(db_session)
        service = SalesForecastEnhancementService(db_session)

        result = service.get_accuracy_comparison()

        assert result["high_data_quality"]["sales_count"] == 1
        assert result["low_data_quality"]["sales_count"] == 1
        assert result["high_data_quality"]["avg_win_rate"] > result["low_data_quality"]["avg_win_rate"]
        assert result["key_findings"]
