# -*- coding: utf-8 -*-
"""排产建议服务测试"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.scheduling_suggestion_service import SchedulingSuggestionService


@pytest.fixture
def db():
    return MagicMock()


class TestCalculatePriorityScore:
    def test_p1_priority(self, db):
        project = MagicMock(
            priority='P1', planned_end_date=date.today() + timedelta(days=5),
            customer_id=1, contract_amount=Decimal("600000")
        )
        readiness = MagicMock(blocking_kit_rate=Decimal("80"))
        customer = MagicMock(credit_level='A')
        db.query.return_value.filter.return_value.first.return_value = customer
        result = SchedulingSuggestionService.calculate_priority_score(db, project, readiness)
        assert result['total_score'] > 0
        assert 'factors' in result

    def test_no_readiness(self, db):
        project = MagicMock(
            priority='P3', planned_end_date=None,
            customer_id=None, contract_amount=Decimal("50000")
        )
        result = SchedulingSuggestionService.calculate_priority_score(db, project)
        assert result['factors']['kit_rate']['score'] == 0

    def test_high_priority_map(self, db):
        project = MagicMock(
            priority='HIGH', planned_end_date=date.today() + timedelta(days=100),
            customer_id=None, contract_amount=Decimal("0")
        )
        result = SchedulingSuggestionService.calculate_priority_score(db, project)
        assert result['factors']['priority']['value'] == 'P1'


class TestDeadlinePressure:
    def test_no_deadline(self):
        project = MagicMock(planned_end_date=None)
        assert SchedulingSuggestionService._calculate_deadline_pressure(project) == 5.0

    def test_urgent_deadline(self):
        project = MagicMock(planned_end_date=date.today() + timedelta(days=3))
        score = SchedulingSuggestionService._calculate_deadline_pressure(project)
        assert score == 25.0

    def test_far_deadline(self):
        project = MagicMock(planned_end_date=date.today() + timedelta(days=90))
        score = SchedulingSuggestionService._calculate_deadline_pressure(project)
        assert score == 5.0


class TestDeadlineDescription:
    def test_no_deadline(self):
        project = MagicMock(planned_end_date=None)
        assert SchedulingSuggestionService._get_deadline_description(project) == '无交期'

    def test_overdue(self):
        project = MagicMock(planned_end_date=date.today() - timedelta(days=5))
        desc = SchedulingSuggestionService._get_deadline_description(project)
        assert '逾期' in desc


class TestCustomerImportance:
    def test_no_customer(self, db):
        project = MagicMock(customer_id=None)
        assert SchedulingSuggestionService._calculate_customer_importance(db, project) == 6.0

    def test_a_level_customer(self, db):
        project = MagicMock(customer_id=1, contract_amount=Decimal("0"))
        customer = MagicMock(credit_level='A')
        db.query.return_value.filter.return_value.first.return_value = customer
        assert SchedulingSuggestionService._calculate_customer_importance(db, project) == 15.0


class TestContractAmountScore:
    def test_high_amount(self):
        project = MagicMock(contract_amount=Decimal("600000"))
        assert SchedulingSuggestionService._calculate_contract_amount_score(project) == 10.0

    def test_low_amount(self):
        project = MagicMock(contract_amount=Decimal("50000"))
        assert SchedulingSuggestionService._calculate_contract_amount_score(project) == 3.0


class TestGetNextStage:
    def test_frame(self):
        assert SchedulingSuggestionService._get_next_stage('FRAME') == 'MECH'

    def test_cosmetic_is_last(self):
        assert SchedulingSuggestionService._get_next_stage('COSMETIC') is None


class TestGenerateSchedulingSuggestions:
    def test_no_projects(self, db):
        db.query.return_value.filter.return_value.all.return_value = []
        result = SchedulingSuggestionService.generate_scheduling_suggestions(db)
        assert result == []
