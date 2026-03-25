# -*- coding: utf-8 -*-
"""
Sales scope tail tests — Sprint 7

Verifies that the newly-protected tail endpoints correctly enforce
data-scope checks via check_sales_data_permission (entity-level)
or filter_sales_data_by_scope (bulk queries).

Covered endpoints:
- Quote cost breakdown (4 endpoints)
- Quote cost analysis (2 endpoints)
- Quote cost calculations (5 endpoints, 2 bulk)
- Contract payment plans
- Contract enhanced CRUD (list/detail/stats)
- Customer related (projects)
- Contract sign & project creation
"""

import inspect
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. Quote cost breakdown — parent-quote scope gating
# ---------------------------------------------------------------------------

class TestQuoteCostBreakdownScope:
    """GET/PUT/POST cost-breakdown endpoints must gate on parent Quote."""

    def test_get_cost_breakdown_has_scope_check(self):
        from app.api.v1.endpoints.sales.quote_cost_breakdown import get_cost_breakdown
        source = inspect.getsource(get_cost_breakdown)
        assert "_check_quote_scope" in source

    def test_update_cost_item_has_scope_check(self):
        from app.api.v1.endpoints.sales.quote_cost_breakdown import update_cost_item
        source = inspect.getsource(update_cost_item)
        assert "_check_quote_scope" in source

    def test_recalculate_cost_has_scope_check(self):
        from app.api.v1.endpoints.sales.quote_cost_breakdown import recalculate_cost
        source = inspect.getsource(recalculate_cost)
        assert "_check_quote_scope" in source

    def test_recalculate_quote_cost_delegates(self):
        """The compat alias delegates to recalculate_cost which has scope."""
        from app.api.v1.endpoints.sales.quote_cost_breakdown import recalculate_quote_cost
        source = inspect.getsource(recalculate_quote_cost)
        assert "recalculate_cost" in source


# ---------------------------------------------------------------------------
# 2. Quote cost analysis — entity + bulk scope
# ---------------------------------------------------------------------------

class TestQuoteCostAnalysisScope:
    """Cost analysis endpoints must enforce scope."""

    def test_get_cost_analysis_has_scope_check(self):
        from app.api.v1.endpoints.sales.quote_cost_analysis import get_cost_analysis
        source = inspect.getsource(get_cost_analysis)
        assert "check_sales_data_permission" in source

    def test_benchmark_has_scope_filter(self):
        from app.api.v1.endpoints.sales.quote_cost_analysis import get_cost_benchmark
        source = inspect.getsource(get_cost_benchmark)
        assert "filter_sales_data_by_scope" in source


# ---------------------------------------------------------------------------
# 3. Quote cost calculations — entity + bulk scope
# ---------------------------------------------------------------------------

class TestQuoteCostCalculationsScope:
    """Cost calculation endpoints must enforce scope."""

    def test_get_cost_calculations_has_scope_check(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import get_cost_calculations
        source = inspect.getsource(get_cost_calculations)
        assert "_check_quote_scope" in source

    def test_batch_update_prices_has_scope_check(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import batch_update_prices
        source = inspect.getsource(batch_update_prices)
        assert "_check_quote_scope" in source

    def test_margin_analysis_has_scope_filter(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import get_margin_analysis
        source = inspect.getsource(get_margin_analysis)
        assert "filter_sales_data_by_scope" in source


# ---------------------------------------------------------------------------
# 4. Contract payment plans — parent-contract scope gating
# ---------------------------------------------------------------------------

class TestContractPaymentPlansScope:
    """GET /contracts/{id}/payment-plans must gate on parent Contract."""

    def test_payment_plans_has_scope_check(self):
        from app.api.v1.endpoints.sales.contracts.payment_plans import (
            get_contract_payment_plans,
        )
        source = inspect.getsource(get_contract_payment_plans)
        assert "check_sales_data_permission" in source


# ---------------------------------------------------------------------------
# 5. Contract enhanced — list/detail/stats scope
# ---------------------------------------------------------------------------

class TestContractEnhancedScope:
    """Enhanced contract endpoints must enforce scope."""

    def test_list_has_scope_check(self):
        from app.api.v1.endpoints.sales.contracts.enhanced import get_contracts
        source = inspect.getsource(get_contracts)
        assert "check_sales_data_permission" in source

    def test_detail_has_scope_check(self):
        from app.api.v1.endpoints.sales.contracts.enhanced import get_contract
        source = inspect.getsource(get_contract)
        assert "check_sales_data_permission" in source

    def test_stats_has_scope_filter(self):
        from app.api.v1.endpoints.sales.contracts.enhanced import get_contract_statistics
        source = inspect.getsource(get_contract_statistics)
        assert "filter_sales_data_by_scope" in source


# ---------------------------------------------------------------------------
# 6. Customer related — parent-customer scope gating
# ---------------------------------------------------------------------------

class TestCustomerRelatedScope:
    """GET /customers/{id}/projects must gate on parent Customer."""

    def test_customer_projects_has_scope_check(self):
        from app.api.v1.endpoints.customers.related import get_customer_projects
        source = inspect.getsource(get_customer_projects)
        assert "check_sales_data_permission" in source


# ---------------------------------------------------------------------------
# 7. Contract sign & project — scope gating
# ---------------------------------------------------------------------------

class TestContractSignProjectScope:
    """Contract sign and project creation must gate on contract scope."""

    def test_sign_contract_has_scope_check(self):
        from app.api.v1.endpoints.sales.contracts.sign_project import sign_contract
        source = inspect.getsource(sign_contract)
        assert "check_sales_data_permission" in source

    def test_create_contract_project_has_scope_check(self):
        from app.api.v1.endpoints.sales.contracts.sign_project import (
            create_contract_project,
        )
        source = inspect.getsource(create_contract_project)
        assert "check_sales_data_permission" in source


# ---------------------------------------------------------------------------
# 8. Behavioral: check_sales_data_permission blocks cross-user access
# ---------------------------------------------------------------------------

class FakeUser:
    def __init__(self, uid=1, department="sales", is_superuser=False):
        self.id = uid
        self.department = department
        self.is_superuser = is_superuser
        self.roles = []
        self.username = f"user_{uid}"
        self.tenant_id = None
        self.password_hash = None


class FakeQuote:
    def __init__(self, owner_id=1):
        self.id = 20
        self.owner_id = owner_id


class FakeContract:
    def __init__(self, sales_owner_id=1):
        self.id = 30
        self.sales_owner_id = sales_owner_id


class TestScopeBehavior:
    """Behavioral tests for scope enforcement on new entities."""

    @patch("app.core.sales_permissions.is_superuser", return_value=False)
    @patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN")
    def test_own_scope_blocks_other_quote(self, *_):
        from app.core.sales_permissions import check_sales_data_permission

        quote = FakeQuote(owner_id=999)
        user = FakeUser(uid=1)
        db = MagicMock()
        assert check_sales_data_permission(quote, user, db, "owner_id") is False

    @patch("app.core.sales_permissions.is_superuser", return_value=False)
    @patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN")
    def test_own_scope_allows_own_quote(self, *_):
        from app.core.sales_permissions import check_sales_data_permission

        quote = FakeQuote(owner_id=1)
        user = FakeUser(uid=1)
        db = MagicMock()
        assert check_sales_data_permission(quote, user, db, "owner_id") is True

    @patch("app.core.sales_permissions.is_superuser", return_value=False)
    @patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN")
    def test_own_scope_blocks_other_contract(self, *_):
        from app.core.sales_permissions import check_sales_data_permission

        contract = FakeContract(sales_owner_id=999)
        user = FakeUser(uid=1)
        db = MagicMock()
        assert check_sales_data_permission(contract, user, db, "sales_owner_id") is False

    @patch("app.core.sales_permissions.is_superuser", return_value=False)
    @patch("app.core.sales_permissions.get_sales_data_scope", return_value="ALL")
    def test_all_scope_allows_any_contract(self, *_):
        from app.core.sales_permissions import check_sales_data_permission

        contract = FakeContract(sales_owner_id=999)
        user = FakeUser(uid=1)
        db = MagicMock()
        assert check_sales_data_permission(contract, user, db, "sales_owner_id") is True
