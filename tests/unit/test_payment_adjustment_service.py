# -*- coding: utf-8 -*-
"""收款计划调整服务测试"""
import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.payment_adjustment_service import PaymentAdjustmentService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return PaymentAdjustmentService(db)


class TestAdjustPaymentPlanByMilestone:
    def test_milestone_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.adjust_payment_plan_by_milestone(999)
        assert result["success"] is False

    def test_no_payment_plans(self, service, db):
        milestone = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = milestone
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.adjust_payment_plan_by_milestone(1)
        assert result["success"] is True
        assert result["adjusted_plans"] == []

    def test_delayed_milestone_adjusts_plan(self, service, db):
        milestone = MagicMock(id=1, status="DELAYED", actual_date=date(2026, 3, 1))
        plan = MagicMock(id=1, payment_name="首付款", planned_date=date(2026, 2, 1), remark=None)
        db.query.return_value.filter.return_value.first.side_effect = [milestone, plan]
        db.query.return_value.filter.return_value.all.return_value = [plan]
        with patch.object(service, '_send_adjustment_notifications'):
            result = service.adjust_payment_plan_by_milestone(1)
            assert result["success"] is True
            assert len(result["adjusted_plans"]) == 1

    def test_completed_early_milestone(self, service, db):
        milestone = MagicMock(id=1, status="COMPLETED", actual_date=date(2026, 1, 15))
        plan = MagicMock(id=1, payment_name="首付款", planned_date=date(2026, 2, 1), remark=None)
        db.query.return_value.filter.return_value.first.side_effect = [milestone, plan]
        db.query.return_value.filter.return_value.all.return_value = [plan]
        with patch.object(service, '_send_adjustment_notifications'):
            result = service.adjust_payment_plan_by_milestone(1)
            assert result["success"] is True


class TestManualAdjust:
    def test_plan_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.manual_adjust_payment_plan(999, date(2026, 3, 1), "reason", 1)
        assert result["success"] is False

    def test_adjust_success(self, service, db):
        plan = MagicMock(id=1, planned_date=date(2026, 2, 1), payment_name="Test", remark=None)
        milestone = MagicMock(project=MagicMock())
        plan.milestone = milestone
        db.query.return_value.filter.return_value.first.return_value = plan
        with patch.object(service, '_send_adjustment_notifications'):
            result = service.manual_adjust_payment_plan(1, date(2026, 3, 1), "延期", 1)
            assert result["success"] is True


class TestGetAdjustmentHistory:
    def test_no_plan(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        assert service.get_adjustment_history(999) == []

    def test_no_remark(self, service, db):
        plan = MagicMock(remark=None)
        db.query.return_value.filter.return_value.first.return_value = plan
        assert service.get_adjustment_history(1) == []

    def test_json_remark(self, service, db):
        history = [{"field": "planned_date", "old_value": "2026-01-01"}]
        plan = MagicMock(remark=json.dumps(history))
        db.query.return_value.filter.return_value.first.return_value = plan
        result = service.get_adjustment_history(1)
        assert len(result) == 1

    def test_invalid_remark(self, service, db):
        plan = MagicMock(remark="not json")
        db.query.return_value.filter.return_value.first.return_value = plan
        assert service.get_adjustment_history(1) == []


class TestCheckAndAdjustAll:
    def test_no_delayed(self, service, db):
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = service.check_and_adjust_all()
        assert result["checked"] == 0
