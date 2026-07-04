# -*- coding: utf-8 -*-
"""APPR-13: contract status writes must go through canonical status semantics."""

from datetime import date, timedelta
from decimal import Decimal
import uuid
from unittest.mock import patch

from app.models.project import Customer
from app.models.sales import Contract, Opportunity
from app.services.sales.contract.analyzer import ContractAnalyzer
from app.services.sales.contract.status_service import ContractStatusService


def _code(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


def _customer(db_session) -> Customer:
    customer = Customer(
        customer_code=_code("CUST"),
        customer_name="APPR13 状态机客户",
    )
    db_session.add(customer)
    db_session.flush()
    return customer


def _contract(db_session, customer: Customer, status: str) -> Contract:
    contract = Contract(
        contract_code=_code("CT"),
        contract_name=f"APPR13 {status}",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("100000"),
        status=status,
    )
    db_session.add(contract)
    db_session.flush()
    return contract


def test_status_service_writes_canonical_uppercase_statuses(db_session):
    customer = _customer(db_session)
    contract = _contract(db_session, customer, "approved")
    db_session.commit()

    service = ContractStatusService(db_session)

    assert service.mark_as_signed(contract.id).status == "SIGNED"
    assert service.mark_as_executing(contract.id).status == "EXECUTING"
    assert service.mark_as_completed(contract.id).status == "COMPLETED"


def test_contract_model_default_status_is_canonical_uppercase(db_session):
    customer = _customer(db_session)
    contract = Contract(
        contract_code=_code("CT"),
        contract_name="APPR13 default",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("100000"),
    )
    db_session.add(contract)
    db_session.flush()

    assert contract.status == "DRAFT"


def test_status_service_voids_to_cancelled_canonical_status(db_session):
    customer = _customer(db_session)
    contract = _contract(db_session, customer, "draft")
    db_session.commit()

    assert ContractStatusService(db_session).void_contract(contract.id).status == "CANCELLED"


def test_opportunity_lost_cancels_legacy_lowercase_draft_contract(db_session):
    from app.models.enums import OpportunityStageEnum
    from app.models.sales.event_listeners import sync_related_entities_on_opportunity_lost

    customer = _customer(db_session)
    opportunity = Opportunity(
        opp_code=_code("OPP"),
        opp_name="APPR13 lost opportunity",
        customer_id=customer.id,
        stage=OpportunityStageEnum.LOST.value,
    )
    db_session.add(opportunity)
    db_session.flush()
    contract = _contract(db_session, customer, "draft")
    contract.opportunity_id = opportunity.id
    db_session.commit()

    sync_related_entities_on_opportunity_lost(None, None, opportunity)
    db_session.flush()

    assert contract.status == "CANCELLED"


def test_s3_to_s4_transition_accepts_legacy_lowercase_signed_status():
    from unittest.mock import MagicMock

    from app.services.stage_transition_checks import check_s3_to_s4_transition

    db = MagicMock()
    project = MagicMock(contract_no="CT-APPR13", contract_date=date.today(), contract_amount=100)
    contract = MagicMock(status="signed")
    db.query.return_value.filter.return_value.first.return_value = contract

    can_advance, target, missing = check_s3_to_s4_transition(db, project)

    assert can_advance is True
    assert target == "S4"
    assert missing == []


@patch("app.services.sales_reminder.contract_reminders.create_notification")
@patch("app.services.sales_reminder.contract_reminders.settings")
def test_contract_expiring_reminder_includes_canonical_executing_status(
    mock_settings, mock_create_notification, db_session
):
    from app.services.sales_reminder.contract_reminders import notify_contract_expiring

    mock_settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS = [30]
    mock_create_notification.return_value = object()

    customer = _customer(db_session)
    contract = _contract(db_session, customer, "EXECUTING")
    contract.sales_owner_id = 12345
    contract.delivery_deadline = date.today() + timedelta(days=30)
    db_session.commit()

    assert notify_contract_expiring(db_session) == 1


def test_contract_health_treats_legacy_voided_as_cancelled(db_session):
    from app.services.pipeline_health_service import PipelineHealthService

    customer = _customer(db_session)
    contract = _contract(db_session, customer, "voided")
    db_session.commit()

    result = PipelineHealthService(db_session).calculate_contract_health(contract.id)

    assert result["health_status"] == "H4"
    assert "已取消" in result["risk_factors"]


def test_contract_stats_fold_legacy_and_canonical_statuses(db_session):
    customer = _customer(db_session)
    for status in [
        "DRAFT",
        "draft",
        "PENDING_APPROVAL",
        "approving",
        "SIGNED",
        "signed",
        "EXECUTING",
        "ACTIVE",
        "executing",
        "COMPLETED",
        "completed",
        "CANCELLED",
        "voided",
    ]:
        _contract(db_session, customer, status)
    db_session.commit()

    stats = ContractAnalyzer(db_session).get_stats()

    assert stats.draft_count == 2
    assert stats.approving_count == 2
    assert stats.signed_count == 2
    assert stats.executing_count == 3
    assert stats.completed_count == 2
    assert stats.voided_count == 2
