# -*- coding: utf-8 -*-
"""AS-13: customer 360 must feed all frontend tabs from real records."""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from app.api.v1.endpoints.customers.view360 import get_customer_360_overview
from app.models.business_support import SalesOrder
from app.models.project import Customer, Project, ProjectPaymentPlan
from app.models.service import CustomerSatisfaction, ServiceTicket
from app.models.user import User
from app.services.customer_360_service import Customer360Service


def _seed_customer_360_records(db_session):
    user = User(
        username="as13-user",
        password_hash="x",
        real_name="AS13 User",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS13-CUST", customer_name="AS13 客户")
    db_session.add_all([user, customer])
    db_session.flush()

    project = Project(
        project_code="AS13-PROJ",
        project_name="AS13 项目",
        customer_id=customer.id,
    )
    db_session.add(project)
    db_session.flush()

    order = SalesOrder(
        order_no="SO-AS13-001",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        order_type="standard",
        order_amount=Decimal("12345.67"),
        order_status="confirmed",
        promised_date=date(2026, 8, 1),
    )
    payment = ProjectPaymentPlan(
        project_id=project.id,
        payment_no=1,
        payment_name="首付款",
        payment_type="ADVANCE",
        planned_amount=Decimal("5000.00"),
        actual_amount=Decimal("2000.00"),
        planned_date=date(2026, 7, 10),
        status="PARTIAL",
    )
    ticket = ServiceTicket(
        ticket_no="ST-AS13-001",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="客户现场软件异常",
        urgency="HIGH",
        reported_by=str(user.id),
        reported_time=datetime(2026, 7, 4, 9, 0),
        status="PENDING",
        priority="HIGH",
        satisfaction=4,
    )
    satisfaction = CustomerSatisfaction(
        survey_no="CSAT-AS13-001",
        survey_type="service_feedback",
        customer_name=customer.customer_name,
        survey_date=date(2026, 7, 5),
        status="COMPLETED",
        overall_score=Decimal("4.5"),
        feedback="响应及时",
        suggestions="继续保持",
        created_by=user.id,
        created_by_name=user.real_name,
    )
    db_session.add_all([order, payment, ticket, satisfaction])
    db_session.commit()
    return user, customer


def test_customer_360_overview_includes_frontend_tab_sources(db_session):
    _user, customer = _seed_customer_360_records(db_session)

    overview = Customer360Service(db_session).build_overview(customer.id)

    assert overview["orders"][0].order_no == "SO-AS13-001"
    assert overview["payments"][0].payment_name == "首付款"
    assert overview["services"][0].ticket_no == "ST-AS13-001"
    assert overview["satisfactions"][0].survey_no == "CSAT-AS13-001"


def test_customer_360_api_exposes_frontend_tab_fields(db_session):
    user, customer = _seed_customer_360_records(db_session)

    with patch(
        "app.api.v1.endpoints.customers.view360.DataScopeService.check_customer_access",
        return_value=True,
    ):
        response = get_customer_360_overview(
            db=db_session,
            customer_id=customer.id,
            current_user=user,
        )

    payload = response.model_dump(mode="json")

    assert payload["orders"][0]["id"] == "SO-AS13-001"
    assert payload["payments"][0]["amount"] == "5000.00"
    assert payload["services"][0]["issue"] == "客户现场软件异常"
    assert payload["satisfactions"][0]["score"] == "4.5"
