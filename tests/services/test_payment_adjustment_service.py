# -*- coding: utf-8 -*-
"""
PaymentAdjustmentService 单元测试 - N5组
覆盖：里程碑触发调整、手动调整、历史记录、批量检查
"""

import json
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, call

from app.services.payment_adjustment_service import PaymentAdjustmentService


def _make_mock_query(db):
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.join.return_value = q
    q.all.return_value = []
    q.count.return_value = 0
    return q


class TestAdjustPaymentPlanByMilestone(unittest.TestCase):
    """adjust_payment_plan_by_milestone 主流程测试"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = PaymentAdjustmentService(self.db)

    def test_milestone_not_found_returns_failure(self):
        """里程碑不存在时返回失败"""
        q = _make_mock_query(self.db)
        q.first.return_value = None

        result = self.svc.adjust_payment_plan_by_milestone(999)
        self.assertFalse(result["success"])
        self.assertIn("里程碑不存在", result["message"])
        self.assertEqual(result["adjusted_plans"], [])

    def test_no_payment_plans_returns_empty(self):
        """无关联收款计划时返回空列表（仍成功）"""
        q = _make_mock_query(self.db)
        milestone = MagicMock(id=1, status="DELAYED", actual_date=date(2025, 6, 1))
        q.first.return_value = milestone
        q.all.return_value = []  # no payment plans

        result = self.svc.adjust_payment_plan_by_milestone(1)
        self.assertTrue(result["success"])
        self.assertEqual(result["adjusted_plans"], [])

    def test_delayed_milestone_adjusts_future_plan(self):
        """DELAYED里程碑，实际日期晚于计划，应推迟收款日期"""
        milestone = MagicMock(
            id=1,
            status="DELAYED",
            actual_date=date(2025, 9, 1),
            project=MagicMock(project_code="P-001", pm_id=None, contract_id=None, is_active=True),
            milestone_name="测试里程碑"
        )

        plan = MagicMock(
            id=10,
            planned_date=date(2025, 7, 1),  # 计划日期早于实际日期
            payment_name="首付款",
            status="PENDING",
            remark=None,
            contract=None,
            milestone=milestone,
        )

        call_count = [0]
        def query_side_effect(*args):
            q = MagicMock()
            q.filter.return_value = q
            q.join.return_value = q
            q.all.return_value = []
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = milestone  # milestone query
            elif call_count[0] == 2:
                q.all.return_value = [plan]  # payment plans query
            else:
                q.first.return_value = plan  # history record plan query
            return q

        self.db.query.side_effect = query_side_effect

        with patch.object(self.svc, '_send_adjustment_notifications'):
            result = self.svc.adjust_payment_plan_by_milestone(1)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["adjusted_plans"]), 1)
        self.assertEqual(plan.planned_date, date(2025, 9, 1))

    def test_delayed_milestone_does_not_adjust_if_already_later(self):
        """DELAYED里程碑，计划日期已比实际日期晚，不调整"""
        milestone = MagicMock(
            id=1,
            status="DELAYED",
            actual_date=date(2025, 5, 1),  # 实际早于计划
        )

        plan = MagicMock(
            id=10,
            planned_date=date(2025, 7, 1),  # 计划日期更晚
            payment_name="首付款",
            status="PENDING",
        )

        call_count = [0]
        def query_side_effect(*args):
            q = MagicMock()
            q.filter.return_value = q
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = milestone
            elif call_count[0] == 2:
                q.all.return_value = [plan]
            return q

        self.db.query.side_effect = query_side_effect

        result = self.svc.adjust_payment_plan_by_milestone(1)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["adjusted_plans"]), 0)  # 无需调整

    def test_completed_milestone_advances_plan(self):
        """COMPLETED里程碑提前完成，允许提前开票"""
        milestone = MagicMock(
            id=1,
            status="COMPLETED",
            actual_date=date(2025, 4, 1),  # 实际提前完成
            project=MagicMock(project_code="P-001", pm_id=None, contract_id=None, is_active=True),
            milestone_name="完成里程碑",
        )

        plan = MagicMock(
            id=11,
            planned_date=date(2025, 7, 1),  # 原计划较晚
            payment_name="进度款",
            status="PENDING",
            remark=None,
            contract=None,
            milestone=milestone,
        )

        call_count = [0]
        def query_side_effect(*args):
            q = MagicMock()
            q.filter.return_value = q
            q.join.return_value = q
            q.all.return_value = []
            call_count[0] += 1
            if call_count[0] == 1:
                q.first.return_value = milestone
            elif call_count[0] == 2:
                q.all.return_value = [plan]
            else:
                q.first.return_value = plan
            return q

        self.db.query.side_effect = query_side_effect

        with patch.object(self.svc, '_send_adjustment_notifications'):
            result = self.svc.adjust_payment_plan_by_milestone(1)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["adjusted_plans"]), 1)
        self.assertEqual(plan.planned_date, date(2025, 4, 1))


class TestManualAdjustPaymentPlan(unittest.TestCase):
    """manual_adjust_payment_plan 手动调整测试"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = PaymentAdjustmentService(self.db)

    def test_plan_not_found_returns_failure(self):
        """收款计划不存在时返回失败"""
        q = _make_mock_query(self.db)
        q.first.return_value = None

        result = self.svc.manual_adjust_payment_plan(
            plan_id=999, new_date=date(2025, 8, 1), reason="测试", adjusted_by=1
        )
        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    def test_manual_adjust_success(self):
        """合法调整应成功，返回新旧日期"""
        old_date = date(2025, 5, 1)
        plan = MagicMock(
            id=1,
            planned_date=old_date,
            payment_name="尾款",
            remark=None,
            milestone=None,
        )

        q = _make_mock_query(self.db)
        q.first.return_value = plan

        result = self.svc.manual_adjust_payment_plan(
            plan_id=1, new_date=date(2025, 8, 1), reason="客户要求", adjusted_by=2
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["new_date"], "2025-08-01")
        self.assertEqual(result["old_date"], "2025-05-01")
        self.db.commit.assert_called_once()

    def test_manual_adjust_with_milestone_sends_notification(self):
        """有里程碑时应触发通知"""
        plan = MagicMock(
            id=1,
            planned_date=date(2025, 5, 1),
            payment_name="尾款",
            remark=None,
            milestone=MagicMock(
                milestone_name="交付",
                project=MagicMock(project_code="P-999", is_active=True, pm_id=None, contract_id=None)
            ),
        )

        q = _make_mock_query(self.db)
        q.first.return_value = plan

        with patch.object(self.svc, '_send_adjustment_notifications') as mock_notify:
            result = self.svc.manual_adjust_payment_plan(
                plan_id=1, new_date=date(2025, 8, 1), reason="调整", adjusted_by=2
            )

        mock_notify.assert_called_once()
        self.assertTrue(result["success"])


class TestGetAdjustmentHistory(unittest.TestCase):
    """get_adjustment_history 调整历史读取"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = PaymentAdjustmentService(self.db)

    def test_plan_not_found_returns_empty(self):
        """计划不存在时返回空列表"""
        q = _make_mock_query(self.db)
        q.first.return_value = None

        result = self.svc.get_adjustment_history(999)
        self.assertEqual(result, [])

    def test_plan_with_no_remark_returns_empty(self):
        """无 remark 时返回空列表"""
        plan = MagicMock(id=1, remark=None)
        q = _make_mock_query(self.db)
        q.first.return_value = plan

        result = self.svc.get_adjustment_history(1)
        self.assertEqual(result, [])

    def test_plan_with_json_history(self):
        """有 JSON 格式历史记录时正确返回"""
        history = [
            {"field": "planned_date", "old_value": "2025-05-01", "new_value": "2025-08-01",
             "reason": "延期", "adjusted_by": 1, "adjusted_at": "2025-04-10T10:00:00"}
        ]
        plan = MagicMock(id=1, remark=json.dumps(history))
        q = _make_mock_query(self.db)
        q.first.return_value = plan

        result = self.svc.get_adjustment_history(1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reason"], "延期")

    def test_plan_with_invalid_json_returns_empty(self):
        """非法 JSON remark 时返回空列表"""
        plan = MagicMock(id=1, remark="这不是JSON格式")
        q = _make_mock_query(self.db)
        q.first.return_value = plan

        result = self.svc.get_adjustment_history(1)
        self.assertEqual(result, [])


class TestRecordAdjustmentHistory(unittest.TestCase):
    """_record_adjustment_history 历史记录写入"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = PaymentAdjustmentService(self.db)

    def test_record_to_empty_remark(self):
        """空 remark 时写入新记录"""
        plan = MagicMock(id=1, remark=None)
        q = _make_mock_query(self.db)
        q.first.return_value = plan

        self.svc._record_adjustment_history(1, "planned_date", "2025-05-01", "2025-08-01", "延期", 1)

        history = json.loads(plan.remark)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["new_value"], "2025-08-01")

    def test_record_appends_to_existing_history(self):
        """已有历史时追加新记录"""
        existing_history = [{"field": "planned_date", "old_value": "2025-03-01",
                             "new_value": "2025-05-01", "reason": "首次调整",
                             "adjusted_by": 1, "adjusted_at": "2025-02-01T10:00:00"}]
        plan = MagicMock(id=1, remark=json.dumps(existing_history))
        q = _make_mock_query(self.db)
        q.first.return_value = plan

        self.svc._record_adjustment_history(1, "planned_date", "2025-05-01", "2025-08-01", "二次调整", 2)

        history = json.loads(plan.remark)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["reason"], "二次调整")

    def test_record_plan_not_found_does_nothing(self):
        """计划不存在时静默退出"""
        q = _make_mock_query(self.db)
        q.first.return_value = None

        # 不应抛出异常
        self.svc._record_adjustment_history(999, "planned_date", None, "2025-08-01", "测试", None)


class TestCheckAndAdjustAll(unittest.TestCase):
    """check_and_adjust_all 批量检查测试"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = PaymentAdjustmentService(self.db)

    def test_no_delayed_milestones(self):
        """无延期里程碑时 checked=0"""
        q = _make_mock_query(self.db)
        q.all.return_value = []

        result = self.svc.check_and_adjust_all()
        self.assertEqual(result["checked"], 0)
        self.assertEqual(result["adjusted"], 0)
        self.assertEqual(result["errors"], [])

    def test_with_delayed_milestones_calls_adjust(self):
        """有延期里程碑时调用逐个调整"""
        milestone1 = MagicMock(id=1)
        milestone2 = MagicMock(id=2)

        q = _make_mock_query(self.db)
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = [milestone1, milestone2]

        with patch.object(self.svc, 'adjust_payment_plan_by_milestone') as mock_adjust:
            mock_adjust.return_value = {"success": True, "adjusted_plans": [], "adjusted_count": 0}
            result = self.svc.check_and_adjust_all()

        self.assertEqual(result["checked"], 2)
        self.assertEqual(mock_adjust.call_count, 2)


if __name__ == "__main__":
    unittest.main()
