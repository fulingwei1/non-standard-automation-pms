# -*- coding: utf-8 -*-
"""
sales forecast dashboard service 单元测试
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project.customer import Customer
from app.models.sales import Contract, Lead, LeadFollowUp, Opportunity, SalesTarget, SalesTeam, SalesTeamMember
from app.models.user import User
from app.services.sales.forecast_dashboard_service import SalesForecastDashboardService


def _suffix() -> str:
    return uuid4().hex[:8]


def _create_department(db: Session) -> Department:
    department = Department(
        dept_code=f"DEP-{_suffix()}",
        dept_name=f"销售预测部-{_suffix()}",
        is_active=True,
    )
    db.add(department)
    db.flush()
    return department


def _create_user(db: Session, department: Department, prefix: str, real_name: str) -> User:
    user = User(
        username=f"{prefix}_{_suffix()}",
        password_hash="hashed-password",
        real_name=real_name,
        department_id=department.id,
        department=department.dept_name,
        is_active=True,
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


def _create_team(
    db: Session,
    department: Department,
    leader: User,
    team_name: str,
    members: list[tuple[User, bool]],
) -> SalesTeam:
    team = SalesTeam(
        team_code=f"TEAM-{_suffix()}",
        team_name=team_name,
        department_id=department.id,
        leader_id=leader.id,
        created_by=leader.id,
        is_active=True,
    )
    db.add(team)
    db.flush()

    for member, is_primary in members:
        db.add(
            SalesTeamMember(
                team_id=team.id,
                user_id=member.id,
                is_active=True,
                is_primary=is_primary,
            )
        )

    db.flush()
    return team


def _create_lead(
    db: Session,
    owner: User,
    customer_name: str,
    created_at: datetime,
) -> Lead:
    lead = Lead(
        lead_code=f"LEAD-{_suffix()}",
        customer_name=customer_name,
        owner_id=owner.id,
        created_at=created_at,
    )
    db.add(lead)
    db.flush()
    return lead


def _create_opportunity(
    db: Session,
    *,
    lead: Lead,
    customer: Customer,
    owner: User,
    name: str,
    stage: str,
    amount: str,
    expected_close_date: date,
    updated_at: datetime,
    probability: int,
    decision_chain: str | None = "EB/TB/PB",
) -> Opportunity:
    opportunity = Opportunity(
        opp_code=f"OPP-{_suffix()}",
        lead_id=lead.id,
        customer_id=customer.id,
        opp_name=name,
        stage=stage,
        est_amount=Decimal(amount),
        expected_close_date=expected_close_date,
        probability=probability,
        decision_chain=decision_chain,
        risk_level="LOW",
        owner_id=owner.id,
        updated_at=updated_at,
    )
    db.add(opportunity)
    db.flush()
    return opportunity


def _seed_dashboard_data(db_session: Session) -> dict[str, object]:
    department = _create_department(db_session)
    leader_a = _create_user(db_session, department, "leader_a", "华南经理")
    rep_a = _create_user(db_session, department, "rep_a", "张三")
    rep_b = _create_user(db_session, department, "rep_b", "李四")
    leader_b = _create_user(db_session, department, "leader_b", "华北经理")
    rep_c = _create_user(db_session, department, "rep_c", "王五")

    team_a = _create_team(
        db_session,
        department,
        leader_a,
        "华南大区",
        [(rep_a, True), (rep_b, False)],
    )
    team_b = _create_team(
        db_session,
        department,
        leader_b,
        "华北大区",
        [(rep_c, True)],
    )

    customer_existing_a = _create_customer(db_session, "老客户A")
    customer_new_b = _create_customer(db_session, "新客户B")
    customer_existing_c = _create_customer(db_session, "老客户C")
    customer_pipeline_d = _create_customer(db_session, "重点客户D")
    customer_pipeline_e = _create_customer(db_session, "重点客户E")
    customer_pipeline_f = _create_customer(db_session, "重点客户F")

    lead_a_hist = _create_lead(db_session, rep_a, customer_existing_a.customer_name, datetime(2025, 12, 1, 10, 0, 0))
    lead_a_open = _create_lead(db_session, rep_a, customer_pipeline_d.customer_name, datetime(2026, 3, 1, 10, 0, 0))
    lead_b_hist = _create_lead(db_session, rep_b, customer_new_b.customer_name, datetime(2026, 2, 2, 10, 0, 0))
    lead_b_open = _create_lead(db_session, rep_b, customer_pipeline_f.customer_name, datetime(2026, 3, 2, 10, 0, 0))
    lead_c_hist = _create_lead(db_session, rep_c, customer_existing_c.customer_name, datetime(2025, 11, 5, 10, 0, 0))
    lead_c_open = _create_lead(db_session, rep_c, customer_pipeline_e.customer_name, datetime(2026, 3, 3, 10, 0, 0))

    db_session.add_all(
        [
            LeadFollowUp(
                lead_id=lead_a_open.id,
                follow_up_type="VISIT",
                content="现场拜访",
                created_by=rep_a.id,
                created_at=datetime(2026, 3, 10, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=lead_a_open.id,
                follow_up_type="CALL",
                content="电话沟通",
                created_by=rep_a.id,
                created_at=datetime(2026, 3, 12, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=lead_b_open.id,
                follow_up_type="CALL",
                content="初次沟通",
                created_by=rep_b.id,
                created_at=datetime(2026, 3, 5, 10, 0, 0),
            ),
            LeadFollowUp(
                lead_id=lead_c_open.id,
                follow_up_type="MEETING",
                content="线上评审会",
                created_by=rep_c.id,
                created_at=datetime(2026, 3, 11, 10, 0, 0),
            ),
        ]
    )

    opp_a_open = _create_opportunity(
        db_session,
        lead=lead_a_open,
        customer=customer_pipeline_d,
        owner=rep_a,
        name="华南重点项目",
        stage="NEGOTIATION",
        amount="800000",
        expected_close_date=date(2026, 3, 25),
        updated_at=datetime(2026, 3, 12, 10, 0, 0),
        probability=78,
    )
    opp_b_open = _create_opportunity(
        db_session,
        lead=lead_b_open,
        customer=customer_pipeline_f,
        owner=rep_b,
        name="华南培育项目",
        stage="PROPOSAL",
        amount="600000",
        expected_close_date=date(2026, 3, 28),
        updated_at=datetime(2026, 3, 8, 10, 0, 0),
        probability=60,
        decision_chain=None,
    )
    opp_c_open = _create_opportunity(
        db_session,
        lead=lead_c_open,
        customer=customer_pipeline_e,
        owner=rep_c,
        name="华北冲刺项目",
        stage="CLOSING",
        amount="500000",
        expected_close_date=date(2026, 3, 26),
        updated_at=datetime(2026, 3, 14, 10, 0, 0),
        probability=88,
    )

    db_session.add_all(
        [
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华南一月签约",
                contract_type="sales",
                customer_id=customer_existing_a.id,
                total_amount=Decimal("700000"),
                signing_date=date(2026, 1, 15),
                status="SIGNED",
                sales_owner_id=rep_a.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华南三月签约",
                contract_type="sales",
                customer_id=customer_existing_a.id,
                total_amount=Decimal("1200000"),
                signing_date=date(2026, 3, 5),
                status="SIGNED",
                sales_owner_id=rep_a.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华南二月签约",
                contract_type="sales",
                customer_id=customer_new_b.id,
                total_amount=Decimal("300000"),
                signing_date=date(2026, 2, 10),
                status="SIGNED",
                sales_owner_id=rep_b.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华北二月签约",
                contract_type="sales",
                customer_id=customer_existing_c.id,
                total_amount=Decimal("800000"),
                signing_date=date(2026, 2, 20),
                status="SIGNED",
                sales_owner_id=rep_c.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华南十二月签约",
                contract_type="sales",
                customer_id=customer_existing_a.id,
                total_amount=Decimal("400000"),
                signing_date=date(2025, 12, 20),
                status="SIGNED",
                sales_owner_id=rep_a.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华北十二月签约",
                contract_type="sales",
                customer_id=customer_existing_c.id,
                total_amount=Decimal("600000"),
                signing_date=date(2025, 12, 10),
                status="SIGNED",
                sales_owner_id=rep_c.id,
            ),
            Contract(
                contract_code=f"CT-{_suffix()}",
                contract_name="华北十一月签约",
                contract_type="sales",
                customer_id=customer_existing_c.id,
                total_amount=Decimal("500000"),
                signing_date=date(2025, 11, 12),
                status="SIGNED",
                sales_owner_id=rep_c.id,
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
                target_value=Decimal("4500000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2026-02",
                target_value=Decimal("2000000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2026-01",
                target_value=Decimal("1000000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2025-12",
                target_value=Decimal("500000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="DEPARTMENT",
                department_id=department.id,
                target_type="CONTRACT_AMOUNT",
                target_period="MONTHLY",
                period_value="2025-11",
                target_value=Decimal("600000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="TEAM",
                team_id=team_a.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2026-Q1",
                target_value=Decimal("2500000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="TEAM",
                team_id=team_b.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2026-Q1",
                target_value=Decimal("2000000"),
                created_by=leader_b.id,
            ),
            SalesTarget(
                target_scope="TEAM",
                team_id=team_a.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2025-Q4",
                target_value=Decimal("1000000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="TEAM",
                team_id=team_b.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2025-Q4",
                target_value=Decimal("800000"),
                created_by=leader_b.id,
            ),
            SalesTarget(
                target_scope="PERSONAL",
                user_id=rep_a.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2026-Q1",
                target_value=Decimal("2000000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="PERSONAL",
                user_id=rep_b.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2026-Q1",
                target_value=Decimal("1000000"),
                created_by=leader_a.id,
            ),
            SalesTarget(
                target_scope="PERSONAL",
                user_id=rep_c.id,
                target_type="CONTRACT_AMOUNT",
                target_period="QUARTERLY",
                period_value="2026-Q1",
                target_value=Decimal("1500000"),
                created_by=leader_b.id,
            ),
        ]
    )
    db_session.flush()

    return {
        "department": department,
        "team_a": team_a,
        "team_b": team_b,
        "rep_a": rep_a,
        "rep_b": rep_b,
        "rep_c": rep_c,
        "opp_a_open": opp_a_open,
        "opp_b_open": opp_b_open,
        "opp_c_open": opp_c_open,
    }


class TestSalesForecastDashboardService:

    def test_get_team_breakdown_uses_real_team_targets_and_pipeline(self, db_session: Session):
        data = _seed_dashboard_data(db_session)
        service = SalesForecastDashboardService(db_session)

        result = service.get_team_breakdown(period="quarterly")

        assert result["period"] == "2026-Q1"
        assert result["total_teams"] == 2
        assert result["teams_on_track"] == 1
        assert result["teams_at_risk"] == 1
        assert result["teams"][0]["team_name"] == data["team_a"].team_name
        assert result["teams"][0]["members_count"] == 2
        assert result["teams"][0]["actual_revenue"] == 2200000.0
        assert result["teams"][0]["predicted_completion"] > 100
        assert result["teams"][0]["rank_change"] == 1
        assert result["teams"][1]["team_name"] == data["team_b"].team_name
        assert result["teams"][1]["risk_level"] == "HIGH"
        assert result["teams"][1]["rank_change"] == -1

    def test_get_sales_rep_breakdown_filters_team_members_and_keeps_non_primary_member(
        self,
        db_session: Session,
    ):
        data = _seed_dashboard_data(db_session)
        service = SalesForecastDashboardService(db_session)

        result = service.get_sales_rep_breakdown(team_id=data["team_a"].id, period="quarterly")

        assert result["period"] == "2026-Q1"
        assert result["team_id"] == data["team_a"].id
        assert result["total_reps"] == 2
        assert result["sales_reps"][0]["sales_id"] == data["rep_a"].id
        assert result["sales_reps"][0]["actual_revenue"] == 1900000.0
        assert result["sales_reps"][0]["pipeline_value"] == 800000.0
        assert {item["sales_id"] for item in result["sales_reps"]} == {
            data["rep_a"].id,
            data["rep_b"].id,
        }
        assert result["sales_reps"][1]["team_id"] == data["team_a"].id

    def test_get_accuracy_tracking_uses_recent_completed_months(self, db_session: Session):
        _seed_dashboard_data(db_session)
        service = SalesForecastDashboardService(db_session)

        result = service.get_accuracy_tracking(months=4)

        assert result["tracking_period"] == "最近4个月"
        assert [item["period"] for item in result["history"]] == [
            "2025-11",
            "2025-12",
            "2026-01",
            "2026-02",
        ]
        assert result["history"][0]["actual"] == 500000.0
        assert result["history"][-1]["predicted"] == 2000000.0
        assert result["average_accuracy"] > 0
        assert "不再返回固定演示值" in result["model_insights"][2]

    def test_get_executive_dashboard_aggregates_real_metrics(self, db_session: Session):
        _seed_dashboard_data(db_session)
        service = SalesForecastDashboardService(db_session)

        result = service.get_executive_dashboard()

        assert result["period"] == "2026-Q1"
        assert result["kpi_summary"]["revenue"]["target"] == 4500000.0
        assert result["kpi_summary"]["revenue"]["actual"] == 3000000.0
        assert result["kpi_summary"]["revenue"]["predicted"] > 3000000.0
        assert result["traffic_lights"]["overall"] == "YELLOW"
        assert len(result["traffic_lights"]["by_team"]) == 2
        assert result["top_risks"]
        assert result["top_opportunities"]
        assert len(result["trend_data"]) == 3
        assert result["kpi_summary"]["new_customers"]["predicted"] >= result["kpi_summary"]["new_customers"]["actual"]
