# -*- coding: utf-8 -*-
"""AI 报价对账契约（持续优化环节的数据地基第一块）。

AI 三档报价与最终成交合同金额定期勾稽：
1. 按 售前工单→商机→已签合同 链路配对，报出各档偏差与最贴近档位。
2. 同一工单同档多次生成只取最新一次。
3. 未成交（无已签合同）的计入 unmatched，不进偏差统计。
"""
import uuid
from decimal import Decimal

from app.models.presale.core import PresaleSupportTicket
from app.models.presale_ai_quotation import PresaleAIQuotation, QuotationType
from app.models.sales import Customer
from app.models.sales.leads import Opportunity
from app.models.sales.contracts import Contract
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _quotation(ticket_id, qtype, total, user_id=1):
    return PresaleAIQuotation(
        presale_ticket_id=ticket_id,
        quotation_number=_unique("AIQ"),
        quotation_type=qtype,
        items=[],
        subtotal=Decimal(str(total)),
        tax=Decimal("0"),
        discount=Decimal("0"),
        total=Decimal(str(total)),
        validity_days=30,
        created_by=user_id,
    )


def _seed_chain(db, contract_status="signed", contract_amount="1000000"):
    user = _get_or_create_user(
        db,
        username=_unique("aiqc").lower(),
        password="test123",
        real_name="对账用户",
        department="售前部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="对账客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db.add(customer)
    db.flush()
    opp = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="对账商机",
        stage="NEGOTIATION",
        owner_id=user.id,
    )
    db.add(opp)
    db.flush()
    ticket = PresaleSupportTicket(
        ticket_no=_unique("PST"),
        title="对账工单",
        ticket_type="QUOTATION",
        applicant_id=user.id,
        opportunity_id=opp.id,
    )
    db.add(ticket)
    db.flush()
    db.add_all(
        [
            _quotation(ticket.id, QuotationType.BASIC, "850000", user.id),
            _quotation(ticket.id, QuotationType.STANDARD, "1050000", user.id),
            _quotation(ticket.id, QuotationType.PREMIUM, "1400000", user.id),
        ]
    )
    contract = None
    if contract_status:
        contract = Contract(
            contract_code=_unique("CT"),
            contract_name="对账合同",
            contract_type="sales",
            opportunity_id=opp.id,
            customer_id=customer.id,
            total_amount=Decimal(contract_amount),
            status=contract_status,
        )
        db.add(contract)
    db.commit()
    return ticket, opp, contract


def test_calibration_matches_signed_contract_and_finds_closest_tier(db_session):
    from app.services import ai_quote_calibration_service as svc

    ticket, opp, contract = _seed_chain(db_session)

    report = svc.quote_calibration(db_session)
    matched = [r for r in report["items"] if r["presale_ticket_id"] == ticket.id]
    assert matched, "已签合同的报价链路未进对账"
    row = matched[0]
    assert row["contract_amount"] == 1000000.0
    assert row["closest_tier"] == "standard"
    assert abs(row["deviations"]["standard"] - 0.05) < 1e-6
    assert abs(row["deviations"]["basic"] + 0.15) < 1e-6


def test_calibration_takes_latest_quotation_per_tier(db_session):
    from app.services import ai_quote_calibration_service as svc

    ticket, _, _ = _seed_chain(db_session)
    # 同档重新生成：以最新为准
    db_session.add(_quotation(ticket.id, QuotationType.STANDARD, "990000", ticket.applicant_id))
    db_session.commit()

    report = svc.quote_calibration(db_session)
    row = next(r for r in report["items"] if r["presale_ticket_id"] == ticket.id)
    assert row["tiers"]["standard"] == 990000.0
    assert abs(row["deviations"]["standard"] + 0.01) < 1e-6


def test_calibration_excludes_unsigned_and_counts_unmatched(db_session):
    from app.services import ai_quote_calibration_service as svc

    ticket, _, _ = _seed_chain(db_session, contract_status="draft")

    report = svc.quote_calibration(db_session)
    assert all(r["presale_ticket_id"] != ticket.id for r in report["items"]), "草稿合同不算成交"
    assert report["summary"]["unmatched"] >= 1


def test_calibration_summary_has_tier_mean_abs_deviation(db_session):
    from app.services import ai_quote_calibration_service as svc

    _seed_chain(db_session)
    report = svc.quote_calibration(db_session)
    summary = report["summary"]
    assert summary["matched"] >= 1
    assert "mean_abs_deviation" in summary
    assert summary["mean_abs_deviation"].get("standard") is not None
