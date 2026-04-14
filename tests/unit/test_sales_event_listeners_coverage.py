from decimal import Decimal
from enum import Enum
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch
import sys

import pytest

import app.models.sales.event_listeners as listeners


class _Field:
    def in_(self, values):
        return ("in", tuple(values))


class QuoteStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OpportunityStageEnum(str, Enum):
    DISCOVERY = "DISCOVERY"
    QUALIFICATION = "QUALIFICATION"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    CLOSING = "CLOSING"
    WON = "WON"
    LOST = "LOST"


class ContractStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    SIGNED = "SIGNED"
    CANCELLED = "CANCELLED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class Opportunity:
    id = 1


class Contract:
    id = 1
    opportunity_id = 1
    status = _Field()


class Quote:
    opportunity_id = 1
    status = _Field()


class Invoice:
    contract_id = 1
    paid_amount = 1


@pytest.fixture
def fake_modules(monkeypatch):
    import app.models as models_pkg

    sales_module = SimpleNamespace(
        Opportunity=Opportunity,
        Contract=Contract,
        Quote=Quote,
        Invoice=Invoice,
    )
    enums_module = SimpleNamespace(
        QuoteStatusEnum=QuoteStatusEnum,
        OpportunityStageEnum=OpportunityStageEnum,
        ContractStatusEnum=ContractStatusEnum,
    )
    monkeypatch.setitem(sys.modules, "app.models.sales", sales_module)
    monkeypatch.setitem(sys.modules, "app.models.enums", enums_module)
    monkeypatch.setattr(models_pkg, "sales", sales_module, raising=False)
    monkeypatch.setattr(models_pkg, "enums", enums_module, raising=False)
    return sales_module, enums_module


def _query(first=None, all_result=None):
    q = MagicMock()
    q.filter.return_value = q
    q.with_entities.return_value = q
    q.all.return_value = all_result or []
    q.first.return_value = first
    return q


def test_get_session_delegates_to_sqlalchemy_object_session():
    target = object()
    expected = object()
    with patch("sqlalchemy.orm.object_session", return_value=expected) as mock_object_session:
        assert listeners._get_session(target) is expected
    mock_object_session.assert_called_once_with(target)


def test_sync_opportunity_amount_from_contract_success_and_early_returns(fake_modules):
    session = MagicMock()
    opportunity = SimpleNamespace(id=7, est_amount=Decimal("10.5"))
    session.query.return_value = _query(first=opportunity)

    with patch.object(listeners, "_get_session", return_value=session):
        listeners.sync_opportunity_amount_from_contract(
            None,
            None,
            SimpleNamespace(opportunity_id=7, total_amount=Decimal("88.8")),
        )

    assert opportunity.est_amount == Decimal("88.8")

    session.reset_mock()
    listeners.sync_opportunity_amount_from_contract(None, None, SimpleNamespace(opportunity_id=None, total_amount=1))
    session.query.assert_not_called()

    with patch.object(listeners, "_get_session", return_value=None):
        listeners.sync_opportunity_amount_from_contract(None, None, SimpleNamespace(opportunity_id=1, total_amount=1))
    session.query.assert_not_called()


def test_sync_opportunity_amount_from_contract_logs_error(fake_modules):
    session = MagicMock()
    session.query.side_effect = RuntimeError("boom")

    with patch.object(listeners, "_get_session", return_value=session), patch.object(listeners.logger, "error") as mock_error:
        listeners.sync_opportunity_amount_from_contract(
            None,
            None,
            SimpleNamespace(opportunity_id=1, total_amount=Decimal("5")),
        )

    mock_error.assert_called_once()
    assert "同步商机金额失败" in mock_error.call_args[0][0]


def test_update_opportunity_stage_on_quote_status_advances_only(fake_modules):
    session = MagicMock()
    advancing = SimpleNamespace(id=1, stage=OpportunityStageEnum.DISCOVERY)
    not_rollback = SimpleNamespace(id=2, stage=OpportunityStageEnum.NEGOTIATION)
    session.query.side_effect = [_query(first=advancing), _query(first=not_rollback)]

    with patch.object(listeners, "_get_session", return_value=session):
        listeners.update_opportunity_stage_on_quote_status(
            None,
            None,
            SimpleNamespace(opportunity_id=1, status=QuoteStatusEnum.SUBMITTED),
        )
        listeners.update_opportunity_stage_on_quote_status(
            None,
            None,
            SimpleNamespace(opportunity_id=2, status=QuoteStatusEnum.SUBMITTED),
        )

    assert advancing.stage == OpportunityStageEnum.PROPOSAL.value
    assert not_rollback.stage == OpportunityStageEnum.NEGOTIATION


def test_update_opportunity_stage_on_quote_status_skips_unmapped_or_missing_session(fake_modules):
    session = MagicMock()
    with patch.object(listeners, "_get_session", return_value=session):
        listeners.update_opportunity_stage_on_quote_status(
            None,
            None,
            SimpleNamespace(opportunity_id=1, status=QuoteStatusEnum.REJECTED),
        )
    session.query.assert_not_called()

    with patch.object(listeners, "_get_session", return_value=None):
        listeners.update_opportunity_stage_on_quote_status(
            None,
            None,
            SimpleNamespace(opportunity_id=1, status=QuoteStatusEnum.SUBMITTED),
        )


def test_update_opportunity_stage_on_quote_status_logs_error(fake_modules):
    session = MagicMock()
    session.query.side_effect = RuntimeError("boom")

    with patch.object(listeners, "_get_session", return_value=session), patch.object(listeners.logger, "error") as mock_error:
        listeners.update_opportunity_stage_on_quote_status(
            None,
            None,
            SimpleNamespace(opportunity_id=1, status=QuoteStatusEnum.APPROVED),
        )

    mock_error.assert_called_once()
    assert "同步商机阶段失败" in mock_error.call_args[0][0]


def test_update_contract_payment_stats_on_invoice_success_and_early_returns(fake_modules):
    invoice_query = _query(all_result=[SimpleNamespace(paid_amount=Decimal("10")), SimpleNamespace(paid_amount=None)])
    contract = SimpleNamespace(id=3, total_amount=Decimal("40"), received_amount=Decimal("0"))
    contract_query = _query(first=contract)
    session = MagicMock()
    session.query.side_effect = [invoice_query, contract_query]

    with patch.object(listeners, "_get_session", return_value=session):
        listeners.update_contract_payment_stats_on_invoice(
            None,
            None,
            SimpleNamespace(contract_id=3),
        )

    assert contract.received_amount == Decimal("10")

    session.reset_mock()
    listeners.update_contract_payment_stats_on_invoice(None, None, SimpleNamespace(contract_id=None))
    session.query.assert_not_called()

    with patch.object(listeners, "_get_session", return_value=None):
        listeners.update_contract_payment_stats_on_invoice(None, None, SimpleNamespace(contract_id=3))
    session.query.assert_not_called()


def test_update_contract_payment_stats_on_invoice_logs_error(fake_modules):
    session = MagicMock()
    session.query.side_effect = RuntimeError("boom")

    with patch.object(listeners, "_get_session", return_value=session), patch.object(listeners.logger, "error") as mock_error:
        listeners.update_contract_payment_stats_on_invoice(None, None, SimpleNamespace(contract_id=1))

    mock_error.assert_called_once()
    assert "同步合同收款统计失败" in mock_error.call_args[0][0]


def test_update_opportunity_stage_on_contract_status_handles_signed_cancelled_and_missing(fake_modules):
    signed_opportunity = SimpleNamespace(id=5, stage=OpportunityStageEnum.QUALIFICATION, expected_close_date=None)
    cancelled_opportunity = SimpleNamespace(id=6, stage=OpportunityStageEnum.WON, expected_close_date=None)
    session = MagicMock()
    session.query.side_effect = [_query(first=signed_opportunity), _query(first=cancelled_opportunity), _query(first=None)]

    with patch.object(listeners, "_get_session", return_value=session):
        listeners.update_opportunity_stage_on_contract_status(
            None,
            None,
            SimpleNamespace(opportunity_id=5, status=ContractStatusEnum.SIGNED),
        )
        listeners.update_opportunity_stage_on_contract_status(
            None,
            None,
            SimpleNamespace(opportunity_id=6, status=ContractStatusEnum.CANCELLED),
        )
        listeners.update_opportunity_stage_on_contract_status(
            None,
            None,
            SimpleNamespace(opportunity_id=99, status=ContractStatusEnum.ACTIVE),
        )

    assert signed_opportunity.stage == OpportunityStageEnum.WON
    assert signed_opportunity.expected_close_date is not None
    assert cancelled_opportunity.stage == OpportunityStageEnum.CLOSING


def test_update_opportunity_stage_on_contract_status_logs_error(fake_modules):
    session = MagicMock()
    session.query.side_effect = RuntimeError("boom")

    with patch.object(listeners, "_get_session", return_value=session), patch.object(listeners.logger, "error") as mock_error:
        listeners.update_opportunity_stage_on_contract_status(
            None,
            None,
            SimpleNamespace(opportunity_id=1, status=ContractStatusEnum.SIGNED),
        )

    mock_error.assert_called_once()
    assert "同步商机状态失败" in mock_error.call_args[0][0]


def test_sync_related_entities_on_opportunity_lost_updates_quotes_and_contracts(fake_modules):
    quote_a = SimpleNamespace(id=1, status=QuoteStatusEnum.DRAFT.value)
    quote_b = SimpleNamespace(id=2, status=QuoteStatusEnum.SUBMITTED.value)
    contract_a = SimpleNamespace(id=3, status=ContractStatusEnum.DRAFT.value)
    contract_b = SimpleNamespace(id=4, status=ContractStatusEnum.REVIEW.value)
    session = MagicMock()
    session.query.side_effect = [
        _query(all_result=[quote_a, quote_b]),
        _query(all_result=[contract_a, contract_b]),
    ]

    with patch.object(listeners, "_get_session", return_value=session):
        listeners.sync_related_entities_on_opportunity_lost(
            None,
            None,
            SimpleNamespace(id=10, stage=OpportunityStageEnum.LOST),
        )

    assert quote_a.status == QuoteStatusEnum.EXPIRED.value
    assert quote_b.status == QuoteStatusEnum.EXPIRED.value
    assert contract_a.status == ContractStatusEnum.CANCELLED.value
    assert contract_b.status == ContractStatusEnum.CANCELLED.value


def test_sync_related_entities_on_opportunity_lost_skips_or_logs_error(fake_modules):
    session = MagicMock()
    with patch.object(listeners, "_get_session", return_value=session):
        listeners.sync_related_entities_on_opportunity_lost(
            None,
            None,
            SimpleNamespace(id=1, stage=OpportunityStageEnum.PROPOSAL),
        )
    session.query.assert_not_called()

    with patch.object(listeners, "_get_session", return_value=None):
        listeners.sync_related_entities_on_opportunity_lost(
            None,
            None,
            SimpleNamespace(id=1, stage=OpportunityStageEnum.LOST),
        )

    session = MagicMock()
    session.query.side_effect = RuntimeError("boom")
    with patch.object(listeners, "_get_session", return_value=session), patch.object(listeners.logger, "error") as mock_error:
        listeners.sync_related_entities_on_opportunity_lost(
            None,
            None,
            SimpleNamespace(id=1, stage=OpportunityStageEnum.LOST),
        )
    mock_error.assert_called_once()
    assert "处理商机输单联动失败" in mock_error.call_args[0][0]


def test_register_and_unregister_sales_event_listeners(fake_modules):
    with patch.object(listeners.event, "listen") as mock_listen, patch.object(listeners.event, "remove") as mock_remove:
        listeners.register_sales_event_listeners()
        listeners.unregister_sales_event_listeners()

    assert mock_listen.call_count == 6
    assert mock_remove.call_count == 6
    assert mock_listen.call_args_list[:2] == [
        call(Contract, "after_insert", listeners.sync_opportunity_amount_from_contract),
        call(Contract, "after_update", listeners.sync_opportunity_amount_from_contract),
    ]
