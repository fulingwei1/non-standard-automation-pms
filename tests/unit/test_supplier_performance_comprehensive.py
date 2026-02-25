# -*- coding: utf-8 -*-
"""SupplierPerformanceEvaluator 综合测试"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def svc(mock_db):
    return SupplierPerformanceEvaluator(mock_db)


class TestInit:
    def test_default_tenant(self, mock_db):
        svc = SupplierPerformanceEvaluator(mock_db)
        assert svc.db is mock_db

    def test_custom_tenant(self, mock_db):
        svc = SupplierPerformanceEvaluator(mock_db, tenant_id=5)
        assert svc.tenant_id == 5


class TestDetermineRating:
    def test_excellent(self, svc):
        r = svc._determine_rating(Decimal("95"))
        assert isinstance(r, str)

    def test_good(self, svc):
        r = svc._determine_rating(Decimal("85"))
        assert isinstance(r, str)

    def test_average(self, svc):
        r = svc._determine_rating(Decimal("70"))
        assert isinstance(r, str)

    def test_poor(self, svc):
        r = svc._determine_rating(Decimal("50"))
        assert isinstance(r, str)

    def test_zero(self, svc):
        r = svc._determine_rating(Decimal("0"))
        assert isinstance(r, str)

    def test_hundred(self, svc):
        r = svc._determine_rating(Decimal("100"))
        assert isinstance(r, str)


class TestBatchEvaluate:
    def test_no_suppliers(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = svc.batch_evaluate_all_suppliers("2024-Q1")
        assert result == 0

    def test_with_suppliers(self, svc, mock_db):
        s1 = MagicMock()
        s1.id = 1
        mock_db.query.return_value.filter.return_value.all.return_value = [s1]
        with patch.object(svc, 'evaluate_supplier', return_value=MagicMock()):
            result = svc.batch_evaluate_all_suppliers("2024-Q1")
            assert result >= 0
