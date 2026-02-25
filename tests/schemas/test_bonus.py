# -*- coding: utf-8 -*-
"""Tests for app/schemas/bonus.py"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.bonus import (
    BonusRuleBase,
    BonusRuleCreate,
    BonusRuleUpdate,
    BonusRuleResponse,
    BonusCalculationBase,
    BonusCalculationCreate,
    BonusCalculationApprove,
    BonusDistributionBase,
    BonusDistributionCreate,
    BonusDistributionPay,
    TeamBonusAllocationBase,
    TeamBonusAllocationCreate,
    BonusCalculationQuery,
    BonusDistributionQuery,
    MyBonusResponse,
    BonusStatisticsResponse,
    CalculatePerformanceBonusRequest,
    CalculateProjectBonusRequest,
    CalculateSalesBonusRequest,
    BonusAllocationSheetConfirm,
)


class TestBonusRuleBase:
    def test_valid(self):
        r = BonusRuleBase(rule_code="BR001", rule_name="绩效奖金", bonus_type="PERFORMANCE")
        assert r.is_active is True
        assert r.require_approval is True
        assert r.priority == 0

    def test_missing(self):
        with pytest.raises(ValidationError):
            BonusRuleBase()

    def test_full(self):
        r = BonusRuleBase(
            rule_code="BR001", rule_name="项目奖金", bonus_type="PROJECT",
            base_amount=Decimal("5000"), coefficient=Decimal("1.2"),
            trigger_condition={"min_score": 80},
            apply_to_roles=["PM", "ENGINEER"],
            effective_start_date=date(2024, 1, 1),
        )
        assert r.coefficient == Decimal("1.2")


class TestBonusRuleCreate:
    def test_inherits(self):
        r = BonusRuleCreate(rule_code="BR001", rule_name="R", bonus_type="T")
        assert r.rule_code == "BR001"


class TestBonusRuleUpdate:
    def test_all_none(self):
        r = BonusRuleUpdate()
        assert r.rule_name is None

    def test_partial(self):
        r = BonusRuleUpdate(rule_name="新名称", is_active=False)
        assert r.is_active is False


class TestBonusCalculationBase:
    def test_valid(self):
        c = BonusCalculationBase(
            rule_id=1, user_id=1, calculated_amount=Decimal("5000"),
        )
        assert c.project_id is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            BonusCalculationBase()


class TestBonusCalculationApprove:
    def test_approved(self):
        a = BonusCalculationApprove(approved=True, comment="OK")
        assert a.approved is True

    def test_rejected(self):
        a = BonusCalculationApprove(approved=False)
        assert a.comment is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            BonusCalculationApprove()


class TestBonusDistributionBase:
    def test_valid(self):
        d = BonusDistributionBase(
            calculation_id=1, user_id=1,
            distributed_amount=Decimal("5000"),
            distribution_date=date(2024, 6, 30),
        )
        assert d.payment_method is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            BonusDistributionBase()


class TestBonusDistributionPay:
    def test_all_none(self):
        p = BonusDistributionPay()
        assert p.voucher_no is None

    def test_with_data(self):
        p = BonusDistributionPay(voucher_no="V001", payment_account="6222***")
        assert p.voucher_no == "V001"


class TestTeamBonusAllocationBase:
    def test_valid(self):
        t = TeamBonusAllocationBase(
            project_id=1, total_bonus_amount=Decimal("50000"),
            allocation_method="EQUAL",
            allocation_detail=[{"user_id": 1, "amount": 25000}],
        )
        assert len(t.allocation_detail) == 1

    def test_missing(self):
        with pytest.raises(ValidationError):
            TeamBonusAllocationBase()


class TestBonusCalculationQuery:
    def test_defaults(self):
        q = BonusCalculationQuery()
        assert q.page == 1
        assert q.rule_id is None

    def test_with_filters(self):
        q = BonusCalculationQuery(
            rule_id=1, status="APPROVED",
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31),
        )
        assert q.status == "APPROVED"


class TestMyBonusResponse:
    def test_valid(self):
        r = MyBonusResponse(
            total_amount=Decimal("10000"),
            pending_amount=Decimal("5000"),
            paid_amount=Decimal("5000"),
        )
        assert r.calculations == []
        assert r.distributions == []


class TestBonusStatisticsResponse:
    def test_valid(self):
        s = BonusStatisticsResponse(
            total_calculated=Decimal("100000"),
            total_distributed=Decimal("80000"),
            total_pending=Decimal("20000"),
            calculation_count=50,
            distribution_count=40,
        )
        assert s.by_type == {}
        assert s.by_department == {}


class TestCalculatePerformanceBonusRequest:
    def test_valid(self):
        r = CalculatePerformanceBonusRequest(period_id=1)
        assert r.user_id is None
        assert r.rule_id is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            CalculatePerformanceBonusRequest()


class TestCalculateProjectBonusRequest:
    def test_valid(self):
        r = CalculateProjectBonusRequest(project_id=1)
        assert r.rule_id is None


class TestCalculateSalesBonusRequest:
    def test_valid(self):
        r = CalculateSalesBonusRequest(contract_id=1)
        assert r.based_on == "CONTRACT"


class TestBonusAllocationSheetConfirm:
    def test_defaults(self):
        c = BonusAllocationSheetConfirm()
        assert c.finance_confirmed is False
        assert c.hr_confirmed is False
        assert c.manager_confirmed is False

    def test_confirmed(self):
        c = BonusAllocationSheetConfirm(
            finance_confirmed=True, hr_confirmed=True, manager_confirmed=True,
        )
        assert c.finance_confirmed is True
