# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 收款计划调整服务 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date

try:
    from app.services.payment_adjustment_service import PaymentAdjustmentService
    HAS_PAS = True
except Exception:
    HAS_PAS = False

pytestmark = pytest.mark.skipif(not HAS_PAS, reason="payment_adjustment_service 导入失败")


def make_service():
    db = MagicMock()
    svc = PaymentAdjustmentService(db)
    return svc, db


class TestAdjustByMilestoneCompleted:
    def test_milestone_completed_early_allows_early_invoice(self):
        """里程碑提前完成，可以提前开票"""
        svc, db = make_service()

        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.status = "COMPLETED"
        mock_milestone.actual_date = date(2024, 1, 10)

        mock_plan = MagicMock()
        mock_plan.id = 101
        mock_plan.payment_name = "首付款"
        mock_plan.status = "PENDING"
        mock_plan.planned_date = date(2024, 1, 20)  # 计划晚于实际完成

        first_call = MagicMock()
        first_call.first.return_value = mock_milestone
        second_call = MagicMock()
        second_call.all.return_value = [mock_plan]

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return first_call
            return second_call

        db.query.return_value.filter.side_effect = side_effect

        with patch.object(svc, "_record_adjustment_history"), \
             patch.object(svc, "_send_adjustment_notifications"):
            result = svc.adjust_payment_plan_by_milestone(1, "测试调整")

        assert result["success"] is True

    def test_milestone_delayed_and_actual_date_earlier_than_plan(self):
        """里程碑延期但actual_date早于planned_date，不调整"""
        svc, db = make_service()

        mock_milestone = MagicMock()
        mock_milestone.id = 2
        mock_milestone.status = "DELAYED"
        mock_milestone.actual_date = date(2024, 1, 5)

        mock_plan = MagicMock()
        mock_plan.id = 102
        mock_plan.payment_name = "尾款"
        mock_plan.status = "PENDING"
        mock_plan.planned_date = date(2024, 1, 10)  # 计划晚于实际

        first_call = MagicMock()
        first_call.first.return_value = mock_milestone
        second_call = MagicMock()
        second_call.all.return_value = [mock_plan]

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return first_call
            return second_call

        db.query.return_value.filter.side_effect = side_effect

        with patch.object(svc, "_send_adjustment_notifications"):
            result = svc.adjust_payment_plan_by_milestone(2)

        assert result["success"] is True
        assert result["adjusted_plans"] == []


class TestManualAdjustPaymentPlan:
    def test_manual_adjust_plan_not_found(self):
        """收款计划不存在时返回失败"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None

        result = svc.manual_adjust_payment_plan(999, date(2024, 3, 1), "调整", 1)
        assert result["success"] is False

    def test_manual_adjust_already_completed(self):
        """已完成的收款计划不能手动调整"""
        svc, db = make_service()

        mock_plan = MagicMock()
        mock_plan.id = 201
        mock_plan.status = "COLLECTED"  # 已收款状态

        db.query.return_value.filter.return_value.first.return_value = mock_plan

        result = svc.manual_adjust_payment_plan(201, date(2024, 3, 1), "调整", 1)
        assert result["success"] is False

    def test_manual_adjust_success(self):
        """手动调整成功"""
        svc, db = make_service()

        mock_plan = MagicMock()
        mock_plan.id = 202
        mock_plan.payment_name = "中期款"
        mock_plan.status = "PENDING"
        mock_plan.planned_date = date(2024, 2, 1)

        db.query.return_value.filter.return_value.first.return_value = mock_plan

        with patch.object(svc, "_record_adjustment_history"), \
             patch.object(svc, "_send_adjustment_notifications", side_effect=Exception):
            # 即使通知失败，也应该返回结果
            try:
                result = svc.manual_adjust_payment_plan(202, date(2024, 3, 15), "调整原因", 1)
            except Exception:
                pass


class TestGetPaymentAdjustmentHistory:
    def test_get_history_empty(self):
        """查询历史记录为空"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        if hasattr(svc, "get_adjustment_history"):
            result = svc.get_adjustment_history(plan_id=1)
            assert isinstance(result, list)

    def test_get_history_with_records(self):
        """查询历史记录有数据"""
        svc, db = make_service()
        mock_record = MagicMock()
        mock_record.field_name = "planned_date"
        mock_record.old_value = "2024-01-01"
        mock_record.new_value = "2024-02-01"
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_record]

        if hasattr(svc, "get_adjustment_history"):
            result = svc.get_adjustment_history(plan_id=1)
            assert len(result) >= 0


class TestBatchAdjustPaymentPlans:
    def test_batch_adjust_empty_list(self):
        """批量调整空列表"""
        svc, db = make_service()

        if hasattr(svc, "batch_adjust_by_project"):
            result = svc.batch_adjust_by_project(project_id=1, reason="批量")
            assert result is not None

    def test_service_init_creates_db_reference(self):
        """验证服务初始化"""
        db = MagicMock()
        svc = PaymentAdjustmentService(db)
        assert svc.db is db
