from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.project import Customer
from app.models.sales.leads import Opportunity
from app.models.sales.quotes import Quote, QuoteVersion
from app.models.sales.sales_funnel import FunnelEntityTypeEnum
from app.services.sales.funnel_state_machine import FunnelStateMachine
from app.services.sales.gate_validators import G3Validator, ValidationResult


def test_coerce_entity_type_accepts_case_insensitive_string():
    assert FunnelStateMachine._coerce_entity_type("lead") == FunnelEntityTypeEnum.LEAD
    assert FunnelStateMachine._coerce_entity_type("OPPORTUNITY") == FunnelEntityTypeEnum.OPPORTUNITY


def test_coerce_entity_type_rejects_invalid_value():
    with pytest.raises(ValueError):
        FunnelStateMachine._coerce_entity_type("unknown")


def test_transition_accepts_string_entity_type_when_skipping_gate_validation(monkeypatch):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    state_machine = FunnelStateMachine(db)
    entity = SimpleNamespace(
        id=1,
        created_at=datetime(2026, 3, 1, 10, 0, 0),
        updated_at=None,
        lead_code="LD-001",
    )

    monkeypatch.setattr(state_machine, "_get_entity", lambda entity_type, entity_id: entity)
    monkeypatch.setattr(state_machine, "get_entity_stage", lambda entity_type, entity_id: "NEW")
    monkeypatch.setattr(state_machine, "_calculate_dwell_hours", lambda entity_type, entity: 6)
    monkeypatch.setattr(
        state_machine,
        "_update_entity_stage",
        lambda entity_type, entity, to_stage: None,
    )

    success, log, errors = state_machine.transition(
        entity_type="lead",
        entity_id=1,
        to_stage="QUALIFIED",
        validate_gate=False,
    )

    assert success is True
    assert errors == ["状态已从 NEW 转换为 QUALIFIED"]
    assert log is not None
    assert log.entity_type == FunnelEntityTypeEnum.LEAD.value
    assert log.from_stage == "NEW"
    assert log.to_stage == "QUALIFIED"


def test_opportunity_to_quote_creates_usable_quote_after_g2_passes(db_session, monkeypatch):
    customer = Customer(
        customer_code=f"CUST-G2-{datetime.now().strftime('%H%M%S%f')}",
        customer_name="G2测试客户",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-G2-{datetime.now().strftime('%H%M%S%f')}",
        opp_name="G2测试商机",
        customer_id=customer.id,
        stage="QUALIFICATION",
        owner_id=42,
        est_amount=Decimal("120000.00"),
        expected_close_date=date.today() + timedelta(days=30),
    )
    db_session.add(opportunity)
    db_session.commit()

    monkeypatch.setattr(
        "app.services.sales.funnel_state_machine.GateValidatorFactory.validate_gate",
        lambda **kwargs: (
            ValidationResult(passed=True, score=100, threshold=70),
            None,
        ),
    )

    state_machine = FunnelStateMachine(db_session)
    success, quote, errors = state_machine.opportunity_to_quote(
        opportunity_id=opportunity.id,
        quote_data={"validity_days": 45},
        transitioned_by=42,
    )

    assert success is True
    assert errors == ["商机已成功转换为报价"]
    assert quote is not None
    assert quote.opportunity_id == opportunity.id
    assert quote.customer_id == customer.id
    assert quote.owner_id == 42
    assert quote.valid_until == date.today() + timedelta(days=45)

    db_session.refresh(opportunity)
    assert opportunity.stage == "PROPOSAL"


def test_g3_validator_accepts_current_quote_version_model_fields(db_session):
    customer = Customer(
        customer_code=f"CUST-G3-{datetime.now().strftime('%H%M%S%f')}",
        customer_name="G3测试客户",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-G3-{datetime.now().strftime('%H%M%S%f')}",
        opp_name="G3测试商机",
        customer_id=customer.id,
        stage="PROPOSAL",
        owner_id=42,
        est_amount=Decimal("180000.00"),
    )
    db_session.add(opportunity)
    db_session.flush()

    quote = Quote(
        quote_code=f"QT-G3-{datetime.now().strftime('%H%M%S%f')}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        valid_until=date.today() + timedelta(days=15),
        owner_id=42,
    )
    db_session.add(quote)
    db_session.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("180000.00"),
        gross_margin=Decimal("25.00"),
        created_by=42,
    )
    db_session.add(version)
    db_session.flush()

    quote.current_version_id = version.id
    db_session.commit()

    result = G3Validator(db_session).validate(quote.id)

    assert result.passed is True
    assert "报价金额有效" in result.passed_rules
    assert "报价在有效期内" in result.passed_rules


def test_quote_to_contract_uses_current_quote_version_fields_after_g3_passes(db_session):
    customer = Customer(
        customer_code=f"CUST-CT-{datetime.now().strftime('%H%M%S%f')}",
        customer_name="合同转换测试客户",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-CT-{datetime.now().strftime('%H%M%S%f')}",
        opp_name="合同转换测试商机",
        customer_id=customer.id,
        stage="PROPOSAL",
        owner_id=42,
        est_amount=Decimal("260000.00"),
    )
    db_session.add(opportunity)
    db_session.flush()

    quote = Quote(
        quote_code=f"QT-CT-{datetime.now().strftime('%H%M%S%f')}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        valid_until=date.today() + timedelta(days=20),
        owner_id=42,
    )
    db_session.add(quote)
    db_session.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("260000.00"),
        gross_margin=Decimal("28.00"),
        created_by=42,
    )
    db_session.add(version)
    db_session.flush()

    quote.current_version_id = version.id
    db_session.commit()

    state_machine = FunnelStateMachine(db_session)
    success, contract, errors = state_machine.quote_to_contract(
        quote_id=quote.id,
        contract_data={"contract_name": "合同转换测试合同", "contract_type": "sales"},
        transitioned_by=42,
    )

    assert success is True
    assert errors == ["报价已成功转换为合同"]
    assert contract is not None
    assert contract.quote_id == version.id
    assert contract.total_amount == Decimal("260000.00")
    assert contract.opportunity_id == opportunity.id
    assert contract.customer_id == customer.id

    db_session.refresh(quote)
    assert quote.status == "ACCEPTED"


def test_quote_stage_uses_quote_status_not_version_shadow_status(db_session):
    customer = Customer(
        customer_code=f"CUST-QS-{datetime.now().strftime('%H%M%S%f')}",
        customer_name="报价状态测试客户",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-QS-{datetime.now().strftime('%H%M%S%f')}",
        opp_name="报价状态测试商机",
        customer_id=customer.id,
        stage="PROPOSAL",
        owner_id=42,
    )
    db_session.add(opportunity)
    db_session.flush()

    quote = Quote(
        quote_code=f"QT-QS-{datetime.now().strftime('%H%M%S%f')}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        valid_until=date.today() + timedelta(days=20),
        owner_id=42,
    )
    db_session.add(quote)
    db_session.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("100000.00"),
        gross_margin=Decimal("22.00"),
        created_by=42,
    )
    db_session.add(version)
    db_session.flush()
    quote.current_version_id = version.id
    db_session.commit()

    state_machine = FunnelStateMachine(db_session)

    assert state_machine.get_entity_stage(FunnelEntityTypeEnum.QUOTE, quote.id) == "APPROVED"

    state_machine._update_entity_stage(FunnelEntityTypeEnum.QUOTE, quote, "ACCEPTED")

    db_session.refresh(quote)
    assert quote.status == "ACCEPTED"
