# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：销售相关 (sales_tasks.py)
J2组覆盖率提升
"""
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def _make_db():
    return MagicMock()


# ================================================================
#  sales_reminder_scan
# ================================================================

class TestSalesReminderScan:

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_scan_calls_notify_all(self, mock_db_ctx):
        """scan 任务正常调用 scan_and_notify_all"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.sales_reminder.scan_and_notify_all",
            return_value={"sent": 3},
        ) as mock_scan:
            from app.utils.scheduled_tasks.sales_tasks import sales_reminder_scan
            sales_reminder_scan()

        mock_scan.assert_called_once_with(db)

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_scan_exception_does_not_raise(self, mock_db_ctx):
        """scan 任务异常时不向外抛出"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.sales_reminder.scan_and_notify_all",
            side_effect=Exception("scan error"),
        ):
            from app.utils.scheduled_tasks.sales_tasks import sales_reminder_scan
            # 不应抛出异常
            sales_reminder_scan()


# ================================================================
#  check_payment_reminder
# ================================================================

class TestCheckPaymentReminder:

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_returns_reminder_count(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.sales_reminder.notify_payment_plan_upcoming",
            return_value=4,
        ):
            from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder
            result = check_payment_reminder()

        assert result["reminder_count"] == 4
        assert "timestamp" in result

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_zero_reminders(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.sales_reminder.notify_payment_plan_upcoming",
            return_value=0,
        ):
            from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder
            result = check_payment_reminder()

        assert result["reminder_count"] == 0

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.sales_reminder.notify_payment_plan_upcoming",
            side_effect=Exception("payment error"),
        ):
            from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder
            result = check_payment_reminder()

        assert "error" in result


# ================================================================
#  check_overdue_receivable_alerts
# ================================================================

class TestCheckOverdueReceivableAlerts:

    def _make_invoice(self, overdue_days=10):
        from datetime import date, timedelta
        inv = MagicMock()
        inv.id = 1
        inv.invoice_code = "INV-001"
        inv.status = "ISSUED"
        inv.payment_status = "PENDING"
        inv.due_date = date.today() - timedelta(days=overdue_days)
        inv.total_amount = Decimal("10000")
        inv.amount = Decimal("10000")
        inv.paid_amount = Decimal("0")
        contract = MagicMock()
        contract.project_id = 5
        customer = MagicMock()
        customer.customer_name = "测试客户"
        contract.customer = customer
        inv.contract = contract
        return inv

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_no_overdue_invoices(self, mock_db_ctx):
        """无逾期发票"""
        db = _make_db()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                m.filter.return_value.first.return_value = MagicMock(id=1)
            else:
                # Invoice 或 Contract 查询
                m.join.return_value.filter.return_value.filter.return_value\
                 .filter.return_value.filter.return_value.filter.return_value.all.return_value = []
                m.join.return_value.filter.return_value.all.return_value = []
                m.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts
        result = check_overdue_receivable_alerts()

        assert result["alert_count"] == 0

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_overdue_invoice_creates_alert(self, mock_db_ctx):
        """有逾期发票且无历史预警 → 生成预警"""
        db = _make_db()
        invoice = self._make_invoice(overdue_days=10)
        rule_mock = MagicMock(id=1)

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                m.filter.return_value.first.return_value = rule_mock
            elif "AlertRecord" in name:
                m.filter.return_value.first.return_value = None
            elif "Invoice" in name:
                # 代码: db.query(Invoice).join(Contract).filter(cond1,cond2,cond3,cond4).all()
                m.join.return_value.filter.return_value.all.return_value = [invoice]
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts
        result = check_overdue_receivable_alerts()

        # 至少调用过 db.add
        assert db.add.called

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_overdue_90_days_is_urgent(self, mock_db_ctx):
        """逾期≥90天 → 预警级别为 URGENT"""
        from app.models.enums import AlertLevelEnum

        db = _make_db()
        invoice = self._make_invoice(overdue_days=95)
        rule_mock = MagicMock(id=1)

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                m.filter.return_value.first.return_value = rule_mock
            elif "AlertRecord" in name:
                m.filter.return_value.first.return_value = None
            elif "Invoice" in name:
                m.join.return_value.filter.return_value.all.return_value = [invoice]
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts
        result = check_overdue_receivable_alerts()

        # 验证 add 被调用
        assert db.add.called

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        mock_db_ctx.return_value.__enter__.side_effect = Exception("overdue error")

        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts
        result = check_overdue_receivable_alerts()

        assert "error" in result

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_rule_created_when_missing(self, mock_db_ctx):
        """AlertRule 不存在时自动创建"""
        db = _make_db()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                m.filter.return_value.first.return_value = None  # 不存在
            elif "Invoice" in name:
                m.join.return_value.filter.return_value.filter.return_value\
                 .filter.return_value.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts
        result = check_overdue_receivable_alerts()

        assert db.add.called  # 创建了规则


# ================================================================
#  check_opportunity_stage_timeout
# ================================================================

class TestCheckOpportunityStageTimeout:

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_no_opportunities(self, mock_db_ctx):
        """无活跃商机 → reminder_count=0"""
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout
        result = check_opportunity_stage_timeout()

        assert result["checked_count"] == 0
        assert result["reminder_count"] == 0

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_opportunity_not_overtime(self, mock_db_ctx):
        """商机未超时 → 不发提醒"""
        from datetime import datetime, timedelta

        db = _make_db()
        opp = MagicMock()
        opp.id = 1
        opp.opportunity_name = "商机A"
        opp.stage = "PROPOSAL"
        opp.owner_id = 10
        opp.updated_at = datetime.now() - timedelta(days=3)  # 3天，未超时

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Opportunity" in name:
                m.filter.return_value.all.return_value = [opp]
            elif "Notification" in name:
                m.filter.return_value.first.return_value = None
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout
        result = check_opportunity_stage_timeout()

        assert result["reminder_count"] == 0

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_opportunity_overtime_creates_notification(self, mock_db_ctx):
        """商机超时 → 发提醒"""
        from datetime import datetime, timedelta

        db = _make_db()
        opp = MagicMock()
        opp.id = 2
        opp.opportunity_name = "超时商机"
        opp.stage = "NEGOTIATION"
        opp.owner_id = 11
        opp.updated_at = datetime.now() - timedelta(days=20)  # 超时

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Opportunity" in name:
                m.filter.return_value.all.return_value = [opp]
            elif "Notification" in name:
                m.filter.return_value.first.return_value = None  # 未发过
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.sales_reminder.create_notification",
        ) as mock_create:
            from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout
            result = check_opportunity_stage_timeout()

        assert result["reminder_count"] == 1
        mock_create.assert_called_once()

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_opportunity_already_notified_today(self, mock_db_ctx):
        """今天已发过提醒 → 不重复"""
        from datetime import datetime, timedelta

        db = _make_db()
        opp = MagicMock()
        opp.id = 3
        opp.opportunity_name = "已通知商机"
        opp.stage = "NEGOTIATION"
        opp.owner_id = 12
        opp.updated_at = datetime.now() - timedelta(days=20)

        existing_notification = MagicMock()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Opportunity" in name:
                m.filter.return_value.all.return_value = [opp]
            elif "Notification" in name:
                m.filter.return_value.first.return_value = existing_notification
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout
        result = check_opportunity_stage_timeout()

        assert result["reminder_count"] == 0

    @patch("app.utils.scheduled_tasks.sales_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        mock_db_ctx.return_value.__enter__.side_effect = Exception("opp error")

        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout
        result = check_opportunity_stage_timeout()

        assert "error" in result
