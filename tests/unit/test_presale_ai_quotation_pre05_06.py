# -*- coding: utf-8 -*-
"""PRE-05/PRE-06: three-tier quotations need ordered prices and domain fallbacks."""

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.presale_ai_quotation import (
    PresaleAIQuotation,
    QuotationType,
    QuotationVersion,
)
from app.schemas.presale_ai_quotation import QuotationItem, ThreeTierQuotationRequest
from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    PresaleAIQuotation.__table__.create(bind=engine)
    QuotationVersion.__table__.create(bind=engine)
    return sessionmaker(bind=engine)()


def _item(name: str, price: str, category: str = "设备") -> QuotationItem:
    return QuotationItem(
        name=name,
        description=f"{name}范围",
        quantity=Decimal("1"),
        unit="套",
        unit_price=Decimal(price),
        total_price=Decimal(price),
        category=category,
    )


def test_three_tier_generation_enforces_basic_standard_premium_order(monkeypatch):
    db = _make_session()
    service = AIQuotationGeneratorService(db)
    monkeypatch.setattr(
        service,
        "_generate_payment_terms",
        lambda total, quotation_type: f"{quotation_type.value}付款条款",
    )

    def lowball_ai_items(requirements, quotation_type, reference_items=None):
        if quotation_type == QuotationType.BASIC:
            return [_item("基础检测工装与控制单元", "100000")]
        if quotation_type == QuotationType.STANDARD:
            return [_item("标准视觉检测模块", "80000", "视觉检测")]
        return [_item("高级自动上下料模块", "90000", "自动化集成")]

    monkeypatch.setattr(service, "_generate_items_with_ai", lowball_ai_items)

    basic, standard, premium = service.generate_three_tier_quotations(
        ThreeTierQuotationRequest(
            presale_ticket_id=1501,
            customer_id=15,
            base_requirements="FCT测试工站，含夹治具、视觉检测、数据追溯和现场调试",
        ),
        user_id=7,
    )

    assert basic.total < standard.total < premium.total
    assert standard.subtotal >= basic.subtotal * Decimal("1.18")
    assert premium.subtotal >= standard.subtotal * Decimal("1.22")


def test_static_fallback_items_are_non_standard_automation_domain(monkeypatch):
    db = _make_session()
    service = AIQuotationGeneratorService(db)
    monkeypatch.setattr(service, "_generate_items_with_ai", lambda *args, **kwargs: None)

    basic_items = service._generate_basic_items("FCT测试工站，含夹治具、视觉检测和数据追溯")
    standard_items = service._generate_standard_items("FCT测试工站，标准自动化检测", basic_items)
    premium_items = service._generate_premium_items("FCT测试工站，高节拍自动化产线", standard_items)

    combined_text = " ".join(
        str(value)
        for item in [*basic_items, *standard_items, *premium_items]
        for value in [item.name, item.description, item.category]
        if value
    )

    for forbidden in ["ERP", "进销存", "财务管理", "人力资源", "移动端APP"]:
        assert forbidden not in combined_text

    for expected in ["检测", "夹治具", "自动化", "视觉", "追溯"]:
        assert expected in combined_text
