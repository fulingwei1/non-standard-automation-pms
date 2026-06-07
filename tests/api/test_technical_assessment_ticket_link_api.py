# -*- coding: utf-8 -*-
"""技术评估与售前工单绑定的 API 闭环测试。"""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AssessmentStatusEnum
from app.models.presale import PresaleSupportTicket
from app.models.project import Customer
from app.models.sales import Opportunity, TechnicalAssessment
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_apply_opportunity_assessment_binds_explicit_presale_ticket_only(
    client: TestClient, db_session: Session, admin_token: str
):
    """从售前工单进入技术评估时，申请评估必须绑定当前工单。"""
    if not admin_token:
        pytest.skip("Admin token not available")

    headers = _auth_headers(admin_token)
    prefix = settings.API_V1_PREFIX
    unique = uuid4().hex[:8].upper()

    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None

    customer = Customer(
        customer_code=f"CUST-TAL-{unique}",
        customer_name=f"技术评估绑定客户-{unique}",
        industry="电子制造",
        created_by=admin_user.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPPTAL{unique[:6]}",
        customer=customer,
        opp_name=f"技术评估绑定商机-{unique}",
        stage="QUALIFICATION",
        probability=60,
        est_amount=Decimal("360000"),
        owner_id=admin_user.id,
        updated_by=admin_user.id,
        assessment_status=AssessmentStatusEnum.PENDING.value,
    )
    db_session.add_all([customer, opportunity])
    db_session.flush()

    unrelated_ticket = PresaleSupportTicket(
        ticket_no=f"TICKET-TAL-A-{unique}",
        title=f"同商机其他售前工单-{unique}",
        ticket_type="SOLUTION",
        urgency="NORMAL",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        opportunity_id=opportunity.id,
        applicant_id=admin_user.id,
        applicant_name=admin_user.real_name or admin_user.username,
        status="PROCESSING",
        assessment_status=AssessmentStatusEnum.IN_PROGRESS.value,
        created_by=admin_user.id,
    )
    target_ticket = PresaleSupportTicket(
        ticket_no=f"TICKET-TAL-B-{unique}",
        title=f"当前技术评估工单-{unique}",
        ticket_type="FEASIBILITY_ASSESSMENT",
        urgency="NORMAL",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        opportunity_id=opportunity.id,
        applicant_id=admin_user.id,
        applicant_name=admin_user.real_name or admin_user.username,
        status="PROCESSING",
        created_by=admin_user.id,
    )
    db_session.add_all([unrelated_ticket, target_ticket])
    db_session.commit()

    response = client.post(
        f"{prefix}/sales/opportunities/{opportunity.id}/assessments/apply",
        json={"presale_ticket_id": target_ticket.id},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    assessment_id = response.json()["data"]["assessment_id"]
    assert response.json()["data"]["presale_ticket_id"] == target_ticket.id

    db_session.expire_all()
    assessment = db_session.get(TechnicalAssessment, assessment_id)
    refreshed_target_ticket = db_session.get(PresaleSupportTicket, target_ticket.id)
    refreshed_unrelated_ticket = db_session.get(PresaleSupportTicket, unrelated_ticket.id)

    assert assessment is not None
    assert assessment.presale_ticket_id == target_ticket.id
    assert refreshed_target_ticket.current_assessment_id == assessment.id
    assert refreshed_target_ticket.assessment_status == AssessmentStatusEnum.PENDING.value
    assert refreshed_unrelated_ticket.current_assessment_id is None
    assert refreshed_unrelated_ticket.assessment_status == AssessmentStatusEnum.IN_PROGRESS.value
    assert assessment.presale_ticket_id != unrelated_ticket.id


def test_apply_opportunity_assessment_does_not_steal_another_ticket_assessment(
    client: TestClient, db_session: Session, admin_token: str
):
    """已有其他工单的未完成评估时，当前工单应获得自己的评估绑定。"""
    if not admin_token:
        pytest.skip("Admin token not available")

    headers = _auth_headers(admin_token)
    prefix = settings.API_V1_PREFIX
    unique = uuid4().hex[:8].upper()

    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None

    customer = Customer(
        customer_code=f"CUST-TAS-{unique}",
        customer_name=f"技术评估不抢占客户-{unique}",
        industry="电子制造",
        created_by=admin_user.id,
    )
    opportunity = Opportunity(
        opp_code=f"OPPTAS{unique[:6]}",
        customer=customer,
        opp_name=f"技术评估不抢占商机-{unique}",
        stage="QUALIFICATION",
        probability=60,
        est_amount=Decimal("420000"),
        owner_id=admin_user.id,
        updated_by=admin_user.id,
        assessment_status=AssessmentStatusEnum.PENDING.value,
    )
    db_session.add_all([customer, opportunity])
    db_session.flush()

    first_ticket = PresaleSupportTicket(
        ticket_no=f"TICKET-TAS-A-{unique}",
        title=f"已有评估工单-{unique}",
        ticket_type="SOLUTION",
        urgency="NORMAL",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        opportunity_id=opportunity.id,
        applicant_id=admin_user.id,
        applicant_name=admin_user.real_name or admin_user.username,
        status="PROCESSING",
        created_by=admin_user.id,
    )
    second_ticket = PresaleSupportTicket(
        ticket_no=f"TICKET-TAS-B-{unique}",
        title=f"当前申请工单-{unique}",
        ticket_type="FEASIBILITY_ASSESSMENT",
        urgency="NORMAL",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        opportunity_id=opportunity.id,
        applicant_id=admin_user.id,
        applicant_name=admin_user.real_name or admin_user.username,
        status="PROCESSING",
        created_by=admin_user.id,
    )
    db_session.add_all([first_ticket, second_ticket])
    db_session.flush()

    first_assessment = TechnicalAssessment(
        source_type="OPPORTUNITY",
        source_id=opportunity.id,
        evaluator_id=admin_user.id,
        status=AssessmentStatusEnum.PENDING.value,
        presale_ticket_id=first_ticket.id,
    )
    db_session.add(first_assessment)
    db_session.flush()
    first_ticket.current_assessment_id = first_assessment.id
    first_ticket.assessment_status = first_assessment.status
    opportunity.assessment_id = first_assessment.id
    db_session.commit()

    response = client.post(
        f"{prefix}/sales/opportunities/{opportunity.id}/assessments/apply",
        json={"presale_ticket_id": second_ticket.id},
        headers=headers,
    )

    assert response.status_code == 201, response.text
    second_assessment_id = response.json()["data"]["assessment_id"]

    db_session.expire_all()
    refreshed_first_assessment = db_session.get(TechnicalAssessment, first_assessment.id)
    refreshed_first_ticket = db_session.get(PresaleSupportTicket, first_ticket.id)
    refreshed_second_ticket = db_session.get(PresaleSupportTicket, second_ticket.id)

    assert second_assessment_id != first_assessment.id
    assert refreshed_first_assessment.presale_ticket_id == first_ticket.id
    assert refreshed_first_ticket.current_assessment_id == first_assessment.id
    assert refreshed_second_ticket.current_assessment_id == second_assessment_id
