# -*- coding: utf-8 -*-
"""
funnel_optimization_service 单元测试
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.common.date_range import get_month_range
from app.models.project.customer import Customer
from app.models.sales import FunnelTransitionLog, Lead, Opportunity, SalesTarget
from app.models.user import User
from app.services.sales.funnel_optimization_service import SalesFunnelOptimizationService


def _suffix() -> str:
    return uuid4().hex[:8]


def _create_user(db: Session, *, username_prefix: str, is_superuser: bool = False) -> User:
    user = User(
        username=f"{username_prefix}_{_suffix()}",
        password_hash="hashed-password",
        real_name=f"{username_prefix}_{_suffix()}",
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.flush()
    return user


def _create_customer(db: Session, name: str) -> Customer:
    customer = Customer(
        customer_code=f"CUST-{_suffix()}",
        customer_name=name,
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()
    return customer


def _create_lead(
    db: Session,
    *,
    owner: User,
    customer_name: str,
    created_at: datetime,
) -> Lead:
    lead = Lead(
        lead_code=f"LEAD-{_suffix()}",
        customer_name=customer_name,
        owner_id=owner.id,
        created_at=created_at,
        updated_at=created_at,
    )
    db.add(lead)
    db.flush()
    return lead


def _create_opportunity(
    db: Session,
    *,
    owner: User,
    customer: Customer,
    lead: Lead,
    name: str,
    stage: str,
    created_at: datetime,
    updated_at: datetime,
    amount: str,
    probability: int,
) -> Opportunity:
    opportunity = Opportunity(
        opp_code=f"OPP-{_suffix()}",
        lead_id=lead.id,
        customer_id=customer.id,
        opp_name=name,
        stage=stage,
        est_amount=Decimal(amount),
        probability=probability,
        owner_id=owner.id,
        created_at=created_at,
        updated_at=updated_at,
    )
    db.add(opportunity)
    db.flush()
    return opportunity


def _create_transition_log(
    db: Session,
    *,
    opportunity: Opportunity,
    from_stage: str,
    to_stage: str,
    transitioned_at: datetime,
    dwell_hours: int,
) -> FunnelTransitionLog:
    log = FunnelTransitionLog(
        entity_type="OPPORTUNITY",
        entity_id=opportunity.id,
        entity_code=opportunity.opp_code,
        from_stage=from_stage,
        to_stage=to_stage,
        transitioned_at=transitioned_at,
        dwell_hours=dwell_hours,
    )
    db.add(log)
    db.flush()
    return log


class TestSalesFunnelOptimizationService:

    def test_get_conversion_rates_uses_real_stage_dwell_and_previous_period_trend(
        self,
        db_session: Session,
    ):
        admin = _create_user(db_session, username_prefix="funnel_admin", is_superuser=True)
        customer = _create_customer(db_session, "漏斗测试客户")

        current_start = date(2026, 3, 1)
        current_end = date(2026, 3, 10)

        lead_current_discovery = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=datetime(2026, 3, 6, 0, 0, 0),
        )
        lead_current_qualification = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=datetime(2026, 3, 2, 0, 0, 0),
        )
        lead_previous = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=datetime(2026, 2, 21, 9, 0, 0),
        )
        lead_current_won = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=datetime(2026, 3, 3, 8, 0, 0),
        )

        opp_discovery = _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_current_discovery,
            name="当前阶段停留商机",
            stage="DISCOVERY",
            created_at=datetime(2026, 3, 6, 0, 0, 0),
            updated_at=datetime(2026, 3, 6, 0, 0, 0),
            amount="100000",
            probability=20,
        )
        opp_qualification = _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_current_qualification,
            name="已推进商机",
            stage="QUALIFICATION",
            created_at=datetime(2026, 3, 2, 0, 0, 0),
            updated_at=datetime(2026, 3, 4, 0, 0, 0),
            amount="120000",
            probability=50,
        )
        _create_transition_log(
            db_session,
            opportunity=opp_qualification,
            from_stage="DISCOVERY",
            to_stage="QUALIFICATION",
            transitioned_at=datetime(2026, 3, 4, 0, 0, 0),
            dwell_hours=48,
        )
        _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_current_won,
            name="当前赢单样本",
            stage="WON",
            created_at=datetime(2026, 3, 3, 8, 0, 0),
            updated_at=datetime(2026, 3, 9, 18, 0, 0),
            amount="200000",
            probability=95,
        )
        _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_previous,
            name="上一周期未推进商机",
            stage="DISCOVERY",
            created_at=datetime(2026, 2, 21, 9, 0, 0),
            updated_at=datetime(2026, 2, 21, 9, 0, 0),
            amount="90000",
            probability=20,
        )
        db_session.flush()

        service = SalesFunnelOptimizationService(db_session)
        result = service.get_conversion_rates(
            start_date=current_start.isoformat(),
            end_date=current_end.isoformat(),
            current_user=admin,
        )

        discovery_stage = next(item for item in result["stages"] if item["stage"] == "DISCOVERY")
        qualification_stage = next(
            item for item in result["stages"] if item["stage"] == "QUALIFICATION"
        )

        assert discovery_stage["avg_days_in_stage"] == 3.5
        assert qualification_stage["conversion_to_next"] == 66.7
        assert qualification_stage["trend"] == "up"
        assert opp_discovery.id is not None

    def test_get_health_dashboard_uses_real_month_target_and_computed_trend(
        self,
        db_session: Session,
    ):
        today = date.today()
        admin = _create_user(db_session, username_prefix="health_admin", is_superuser=True)
        customer = _create_customer(db_session, "健康看板客户")

        db_session.add(
            SalesTarget(
                target_scope="PERSONAL",
                user_id=admin.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value=f"{today.year}-{today.month:02d}",
                target_value=Decimal("1000000"),
                status="ACTIVE",
                created_by=admin.id,
            )
        )
        db_session.flush()

        current_specs = [
            ("当前赢单A", "WON", 10, 2, "300000", 100),
            ("当前赢单B", "WON", 9, 1, "200000", 100),
            ("当前成交促成", "CLOSING", 4, 2, "500000", 80),
            ("当前价格谈判", "NEGOTIATION", 6, 2, "400000", 70),
        ]
        previous_specs = [
            ("历史滞留1", "DISCOVERY", 150, 150, "80000", 20),
            ("历史滞留2", "DISCOVERY", 140, 140, "90000", 20),
            ("历史滞留3", "DISCOVERY", 130, 130, "100000", 20),
        ]

        for name, stage, created_days_ago, updated_days_ago, amount, probability in current_specs:
            created_at = datetime.combine(today - timedelta(days=created_days_ago), datetime.min.time())
            updated_at = datetime.combine(today - timedelta(days=updated_days_ago), datetime.min.time())
            lead = _create_lead(
                db_session,
                owner=admin,
                customer_name=customer.customer_name,
                created_at=created_at,
            )
            _create_opportunity(
                db_session,
                owner=admin,
                customer=customer,
                lead=lead,
                name=name,
                stage=stage,
                created_at=created_at,
                updated_at=updated_at,
                amount=amount,
                probability=probability,
            )

        for name, stage, created_days_ago, updated_days_ago, amount, probability in previous_specs:
            created_at = datetime.combine(today - timedelta(days=created_days_ago), datetime.min.time())
            updated_at = datetime.combine(today - timedelta(days=updated_days_ago), datetime.min.time())
            lead = _create_lead(
                db_session,
                owner=admin,
                customer_name=customer.customer_name,
                created_at=created_at,
            )
            _create_opportunity(
                db_session,
                owner=admin,
                customer=customer,
                lead=lead,
                name=name,
                stage=stage,
                created_at=created_at,
                updated_at=updated_at,
                amount=amount,
                probability=probability,
            )

        db_session.flush()

        result = SalesFunnelOptimizationService(db_session).get_health_dashboard(current_user=admin)

        assert result["overall_health"]["trend"] == "up"
        assert result["key_metrics"]["monthly_target"] == 1000000.0
        assert result["key_metrics"]["target_source"] == "sales_targets"
        assert result["key_metrics"]["target_coverage"] == 68.0

    def test_get_trends_uses_closing_stage_for_stage5(self, db_session: Session):
        today = date.today()
        admin = _create_user(db_session, username_prefix="trend_admin", is_superuser=True)
        customer = _create_customer(db_session, "趋势客户")
        month_start, _ = get_month_range(today)

        month_specs = [
            ("谈判商机", "NEGOTIATION", "150000", 70),
            ("成交促成商机", "CLOSING", "180000", 85),
            ("赢单商机", "WON", "220000", 100),
        ]

        for index, (name, stage, amount, probability) in enumerate(month_specs, start=1):
            created_at = datetime.combine(month_start + timedelta(days=index), datetime.min.time())
            lead = _create_lead(
                db_session,
                owner=admin,
                customer_name=customer.customer_name,
                created_at=created_at,
            )
            _create_opportunity(
                db_session,
                owner=admin,
                customer=customer,
                lead=lead,
                name=name,
                stage=stage,
                created_at=created_at,
                updated_at=created_at,
                amount=amount,
                probability=probability,
            )

        db_session.flush()

        result = SalesFunnelOptimizationService(db_session).get_trends(
            period="monthly",
            months=1,
            current_user=admin,
        )

        assert len(result["data"]) == 1
        period_data = result["data"][0]
        assert period_data["stage4"] == 3
        assert period_data["stage5"] == 2
        assert period_data["won"] == 1

    def test_get_prediction_accuracy_uses_real_stage_and_close_window(
        self,
        db_session: Session,
    ):
        today = date.today()
        admin = _create_user(db_session, username_prefix="accuracy_admin", is_superuser=True)
        customer = _create_customer(db_session, "预测准确率客户")
        created_at = datetime.combine(today - timedelta(days=120), datetime.min.time())

        lead_neg_won = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=created_at,
        )
        opp_neg_won = _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_neg_won,
            name="谈判后赢单",
            stage="WON",
            created_at=created_at,
            updated_at=datetime.combine(today - timedelta(days=5), datetime.min.time()),
            amount="300000",
            probability=78,
        )
        _create_transition_log(
            db_session,
            opportunity=opp_neg_won,
            from_stage="NEGOTIATION",
            to_stage="WON",
            transitioned_at=datetime.combine(today - timedelta(days=5), datetime.min.time()),
            dwell_hours=48,
        )

        lead_neg_lost = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=created_at + timedelta(days=1),
        )
        opp_neg_lost = _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_neg_lost,
            name="谈判后输单",
            stage="LOST",
            created_at=created_at + timedelta(days=1),
            updated_at=datetime.combine(today - timedelta(days=4), datetime.min.time()),
            amount="260000",
            probability=82,
        )
        _create_transition_log(
            db_session,
            opportunity=opp_neg_lost,
            from_stage="NEGOTIATION",
            to_stage="LOST",
            transitioned_at=datetime.combine(today - timedelta(days=4), datetime.min.time()),
            dwell_hours=72,
        )

        lead_proposal_lost = _create_lead(
            db_session,
            owner=admin,
            customer_name=customer.customer_name,
            created_at=created_at + timedelta(days=2),
        )
        opp_proposal_lost = _create_opportunity(
            db_session,
            owner=admin,
            customer=customer,
            lead=lead_proposal_lost,
            name="方案阶段输单",
            stage="LOST",
            created_at=created_at + timedelta(days=2),
            updated_at=datetime.combine(today - timedelta(days=3), datetime.min.time()),
            amount="180000",
            probability=62,
        )
        _create_transition_log(
            db_session,
            opportunity=opp_proposal_lost,
            from_stage="PROPOSAL",
            to_stage="LOST",
            transitioned_at=datetime.combine(today - timedelta(days=3), datetime.min.time()),
            dwell_hours=96,
        )

        db_session.flush()

        result = SalesFunnelOptimizationService(db_session).get_prediction_accuracy(
            months=1,
            current_user=admin,
        )

        by_stage = {item["stage"]: item for item in result["by_stage"]}
        negotiation = by_stage["NEGOTIATION"]
        proposal = by_stage["PROPOSAL"]

        assert result["period"]["total_opportunities"] == 3
        assert set(by_stage.keys()) == {
            "DISCOVERY",
            "QUALIFICATION",
            "PROPOSAL",
            "NEGOTIATION",
            "CLOSING",
        }
        assert negotiation["stage_name"] == "价格谈判"
        assert negotiation["sample_size"] == 2
        assert negotiation["actual"] == 50.0
        assert negotiation["predicted"] == 80.0
        assert negotiation["data_source"] == "terminal_transition"
        assert proposal["sample_size"] == 1
        assert proposal["actual"] == 0.0
        assert proposal["predicted"] == 62.0
        assert by_stage["DISCOVERY"]["bias"] == "数据不足"
        assert opp_neg_won.id and opp_neg_lost.id and opp_proposal_lost.id
