# -*- coding: utf-8 -*-
"""
sales target performance service 单元测试
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project.customer import Customer
from app.models.sales import Contract, Invoice, Opportunity, SalesTarget, SalesTeam, SalesTeamMember
from app.models.user import User
from app.services.sales.target_performance_service import SalesTargetPerformanceService


def _suffix() -> str:
    return uuid4().hex[:8]


def _create_department(db: Session, name: str) -> Department:
    dept = Department(
        dept_code=f"DEP-{_suffix()}",
        dept_name=name,
        is_active=True,
    )
    db.add(dept)
    db.flush()
    return dept


def _create_user(
    db: Session,
    *,
    username_prefix: str,
    department: Department | None = None,
    department_name: str | None = None,
) -> User:
    suffix = _suffix()
    user = User(
        username=f"{username_prefix}_{suffix}",
        password_hash="hashed-password",
        real_name=f"{username_prefix}_{suffix}",
        department_id=department.id if department else None,
        department=department_name or (department.dept_name if department else None),
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


class TestSalesTargetPerformanceService:

    def test_calculate_personal_contract_amount_uses_signing_date(self, db_session: Session):
        department = _create_department(db_session, "销售一部")
        owner = _create_user(db_session, username_prefix="sales_contract", department=department)
        customer = _create_customer(db_session)

        db_session.add_all(
            [
                Contract(
                    contract_code=f"CT-{_suffix()}",
                    contract_name="月度签约合同",
                    contract_type="sales",
                    customer_id=customer.id,
                    total_amount=Decimal("100000"),
                    signing_date=date(2026, 1, 10),
                    status="SIGNED",
                    sales_owner_id=owner.id,
                ),
                Contract(
                    contract_code=f"CT-{_suffix()}",
                    contract_name="草稿合同",
                    contract_type="sales",
                    customer_id=customer.id,
                    total_amount=Decimal("90000"),
                    signing_date=date(2026, 1, 15),
                    status="DRAFT",
                    sales_owner_id=owner.id,
                ),
                Contract(
                    contract_code=f"CT-{_suffix()}",
                    contract_name="跨月合同",
                    contract_type="sales",
                    customer_id=customer.id,
                    total_amount=Decimal("60000"),
                    signing_date=date(2026, 2, 1),
                    status="SIGNED",
                    sales_owner_id=owner.id,
                ),
            ]
        )

        target = SalesTarget(
            target_scope="PERSONAL",
            user_id=owner.id,
            target_type="CONTRACT_AMOUNT",
            target_period="MONTHLY",
            period_value="2026-01",
            target_value=Decimal("200000"),
            created_by=owner.id,
        )
        db_session.add(target)
        db_session.flush()

        result = SalesTargetPerformanceService(db_session).calculate_target(target)

        assert result["actual_value"] == Decimal("100000")
        assert result["completion_rate"] == 50.0

    def test_calculate_team_collection_amount_only_counts_active_members(self, db_session: Session):
        department = _create_department(db_session, "销售二部")
        leader = _create_user(db_session, username_prefix="team_leader", department=department)
        active_member = _create_user(
            db_session,
            username_prefix="team_active",
            department=department,
        )
        inactive_member = _create_user(
            db_session,
            username_prefix="team_inactive",
            department=department,
        )
        customer = _create_customer(db_session)

        team = SalesTeam(
            team_code=f"TEAM-{_suffix()}",
            team_name=f"测试团队-{_suffix()}",
            department_id=department.id,
            leader_id=leader.id,
            created_by=leader.id,
            is_active=True,
        )
        db_session.add(team)
        db_session.flush()

        db_session.add_all(
            [
                SalesTeamMember(team_id=team.id, user_id=active_member.id, is_active=True),
                SalesTeamMember(team_id=team.id, user_id=inactive_member.id, is_active=False),
            ]
        )
        db_session.flush()

        active_contract = Contract(
            contract_code=f"CT-{_suffix()}",
            contract_name="活跃成员合同",
            contract_type="sales",
            customer_id=customer.id,
            total_amount=Decimal("80000"),
            signing_date=date(2026, 2, 8),
            status="SIGNED",
            sales_owner_id=active_member.id,
        )
        inactive_contract = Contract(
            contract_code=f"CT-{_suffix()}",
            contract_name="无效成员合同",
            contract_type="sales",
            customer_id=customer.id,
            total_amount=Decimal("70000"),
            signing_date=date(2026, 2, 12),
            status="SIGNED",
            sales_owner_id=inactive_member.id,
        )
        db_session.add_all([active_contract, inactive_contract])
        db_session.flush()

        db_session.add_all(
            [
                Invoice(
                    invoice_code=f"INV-{_suffix()}",
                    contract_id=active_contract.id,
                    total_amount=Decimal("40000"),
                    paid_amount=Decimal("40000"),
                    paid_date=date(2026, 3, 6),
                    payment_status="PAID",
                ),
                Invoice(
                    invoice_code=f"INV-{_suffix()}",
                    contract_id=inactive_contract.id,
                    total_amount=Decimal("30000"),
                    paid_amount=Decimal("30000"),
                    paid_date=date(2026, 3, 9),
                    payment_status="PAID",
                ),
            ]
        )

        target = SalesTarget(
            target_scope="TEAM",
            team_id=team.id,
            target_type="COLLECTION_AMOUNT",
            target_period="QUARTERLY",
            period_value="2026-Q1",
            target_value=Decimal("50000"),
            created_by=leader.id,
        )
        db_session.add(target)
        db_session.flush()

        result = SalesTargetPerformanceService(db_session).calculate_target(target)

        assert result["actual_value"] == Decimal("40000")
        assert result["completion_rate"] == 80.0

    def test_calculate_department_opportunity_count_supports_department_name_fallback(
        self,
        db_session: Session,
    ):
        department = _create_department(db_session, "大客户部")
        owner_by_id = _create_user(
            db_session,
            username_prefix="dept_owner_id",
            department=department,
        )
        owner_by_name = _create_user(
            db_session,
            username_prefix="dept_owner_name",
            department_name=department.dept_name,
        )
        outsider = _create_user(db_session, username_prefix="dept_outsider")
        customer = _create_customer(db_session)

        db_session.add_all(
            [
                Opportunity(
                    opp_code=f"OPP-{_suffix()}",
                    customer_id=customer.id,
                    opp_name="部门内商机-1",
                    owner_id=owner_by_id.id,
                    est_amount=Decimal("100000"),
                    created_at=datetime(2026, 1, 5, 10, 0, 0),
                ),
                Opportunity(
                    opp_code=f"OPP-{_suffix()}",
                    customer_id=customer.id,
                    opp_name="部门内商机-2",
                    owner_id=owner_by_name.id,
                    est_amount=Decimal("120000"),
                    created_at=datetime(2026, 6, 18, 15, 0, 0),
                ),
                Opportunity(
                    opp_code=f"OPP-{_suffix()}",
                    customer_id=customer.id,
                    opp_name="部门外商机",
                    owner_id=outsider.id,
                    est_amount=Decimal("90000"),
                    created_at=datetime(2026, 8, 1, 9, 0, 0),
                ),
            ]
        )

        target = SalesTarget(
            target_scope="DEPARTMENT",
            department_id=department.id,
            target_type="OPPORTUNITY_COUNT",
            target_period="YEARLY",
            period_value="2026",
            target_value=Decimal("4"),
            created_by=owner_by_id.id,
        )
        db_session.add(target)
        db_session.flush()

        result = SalesTargetPerformanceService(db_session).calculate_target(target)

        assert result["actual_value"] == Decimal("2")
        assert result["completion_rate"] == 50.0
