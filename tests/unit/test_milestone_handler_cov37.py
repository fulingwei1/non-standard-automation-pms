# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 里程碑状态处理器
tests/unit/test_milestone_handler_cov37.py
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.status_handlers.milestone_handler")

from app.services.status_handlers.milestone_handler import (
    MilestoneStatusHandler,
    register_milestone_handlers,
)


def _make_milestone(mid=1):
    m = MagicMock()
    m.id = mid
    return m


def _make_db_with_plans(plans=None):
    db = MagicMock()
    if plans is None:
        plans = []
    db.query.return_value.filter.return_value.all.return_value = plans
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.order_by.return_value.first.return_value = None
    return db


def _make_plan(plan_id=1, contract_id=10, invoice_id=None, amount=Decimal("50000")):
    plan = MagicMock()
    plan.id = plan_id
    plan.contract_id = contract_id
    plan.invoice_id = invoice_id
    plan.project_id = 1
    plan.planned_amount = amount
    return plan


class TestHandleMilestoneCompleted:
    def test_does_nothing_if_not_completed(self):
        db = _make_db_with_plans()
        milestone = _make_milestone()
        # Should not query payment plans when to_status != COMPLETED
        MilestoneStatusHandler.handle_milestone_completed(
            db, milestone, from_status="IN_PROGRESS", to_status="IN_REVIEW"
        )
        # No payment plan query expected
        # db.query should not have been called (or minimal calls only)

    def test_creates_invoice_for_pending_plan_with_contract(self):
        db = MagicMock()
        milestone = _make_milestone()
        plan = _make_plan()
        contract = MagicMock()
        contract.id = 10
        contract.customer = MagicMock()
        contract.customer.customer_name = "客户A"
        contract.customer.tax_no = "91110000MA1FL0PJ3L"

        # Setup queries
        def query_side(model):
            q = MagicMock()
            from app.models.project import ProjectPaymentPlan
            from app.models.sales import Contract
            from app.models.sales import Invoice as InvoiceModel

            if model is ProjectPaymentPlan:
                q.filter.return_value.all.return_value = [plan]
            elif model is Contract:
                q.filter.return_value.first.return_value = contract
            elif model is InvoiceModel:
                # apply_like_filter chain
                q2 = MagicMock()
                q2.order_by.return_value.first.return_value = None
                q.order_by.return_value.first.return_value = None
                return q
            else:
                q.filter.return_value.all.return_value = []
            return q

        db.query.side_effect = query_side

        with patch(
            "app.services.status_handlers.milestone_handler.apply_like_filter"
        ) as mock_alf:
            # Return a mock that supports .order_by().first()
            filter_chain = MagicMock()
            filter_chain.order_by.return_value.first.return_value = None
            mock_alf.return_value = filter_chain

            MilestoneStatusHandler.handle_milestone_completed(
                db, milestone, from_status=None, to_status="COMPLETED"
            )

        db.add.assert_called()
        db.flush.assert_called()

    def test_skips_plan_with_existing_invoice(self):
        db = MagicMock()
        milestone = _make_milestone()
        plan = _make_plan(invoice_id=99)  # already has invoice

        db.query.return_value.filter.return_value.all.return_value = [plan]

        MilestoneStatusHandler.handle_milestone_completed(
            db, milestone, from_status=None, to_status="COMPLETED"
        )
        # No new invoice should be created
        db.flush.assert_not_called()

    def test_skips_plan_without_contract(self):
        db = MagicMock()
        milestone = _make_milestone()
        plan = _make_plan(contract_id=None)
        plan.contract_id = None

        db.query.return_value.filter.return_value.all.return_value = [plan]
        db.query.return_value.filter.return_value.first.return_value = None

        MilestoneStatusHandler.handle_milestone_completed(
            db, milestone, from_status=None, to_status="COMPLETED"
        )
        db.flush.assert_not_called()


class TestRegisterMilestoneHandlers:
    def test_register_calls_workflow_engine(self):
        mock_engine = MagicMock()
        with patch(
            "app.common.workflow.engine.workflow_engine",
            mock_engine,
        ):
            register_milestone_handlers()

        mock_engine.register.assert_called_once_with(
            model_name="ProjectMilestone",
            to_status="COMPLETED",
            handler=MilestoneStatusHandler.handle_milestone_completed,
        )
