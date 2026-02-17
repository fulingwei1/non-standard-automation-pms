# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：生产相关 (production_tasks.py)
J2组覆盖率提升
"""
import sys
from unittest.mock import MagicMock, patch

# --------------- 隔离所有外部依赖 ---------------
sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


# ================================================================
#  辅助函数：构造 mock db
# ================================================================

def _make_db():
    db = MagicMock()
    return db


# ================================================================
#  check_production_plan_alerts (直接注入 db 的内部逻辑)
# ================================================================

class TestCheckProductionPlanAlerts:
    """
    check_production_plan_alerts 使用 get_db_session() 上下文管理器，
    因此需要 patch get_db_session 和可能用到的 models。
    """

    def _make_patch_context(self, active_plans=None, rule_exists=True):
        """构造通用 patch 上下文"""
        db = _make_db()

        # AlertRule 查询
        rule_mock = MagicMock()
        rule_mock.id = 1

        def query_side_effect(model_cls):
            q = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                q.filter.return_value.first.return_value = rule_mock if rule_exists else None
            elif "AlertRecord" in name:
                q.filter.return_value.first.return_value = None  # no existing alert
            elif "ProductionPlan" in name:
                q.filter.return_value.all.return_value = active_plans or []
            return q

        db.query.side_effect = query_side_effect
        return db

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_no_active_plans(self, mock_notify, mock_db_ctx):
        """无执行中计划 → alert_count=0"""
        db = self._make_patch_context(active_plans=[])
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts
        result = check_production_plan_alerts()

        assert result["checked_count"] == 0
        assert result["alert_count"] == 0

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_plan_with_low_progress_near_deadline(self, mock_notify, mock_db_ctx):
        """进度<80% 且接近截止日期 → 生成预警"""
        from datetime import date, timedelta

        plan = MagicMock()
        plan.id = 10
        plan.plan_no = "PP-001"
        plan.plan_name = "生产计划A"
        plan.project_id = 5
        plan.progress = 50
        plan.plan_end_date = date.today() + timedelta(days=3)

        db = self._make_patch_context(active_plans=[plan])
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts
        result = check_production_plan_alerts()

        assert result["checked_count"] == 1
        assert result["alert_count"] == 1
        mock_notify.assert_called_once()

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_plan_with_overdue_deadline(self, mock_notify, mock_db_ctx):
        """计划已逾期（days_left < 0） → 预警级别为 CRITICAL"""
        from datetime import date, timedelta

        plan = MagicMock()
        plan.id = 11
        plan.plan_no = "PP-002"
        plan.plan_name = "逾期计划"
        plan.project_id = 6
        plan.progress = 30
        plan.plan_end_date = date.today() - timedelta(days=2)

        db = self._make_patch_context(active_plans=[plan])
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts
        result = check_production_plan_alerts()

        assert result["alert_count"] == 1

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_plan_rule_created_when_missing(self, mock_notify, mock_db_ctx):
        """AlertRule 不存在时应自动创建规则"""
        from datetime import date, timedelta

        plan = MagicMock()
        plan.id = 12
        plan.plan_no = "PP-003"
        plan.plan_name = "新计划"
        plan.project_id = 7
        plan.progress = 60
        plan.plan_end_date = date.today() + timedelta(days=5)

        db = self._make_patch_context(active_plans=[plan], rule_exists=False)

        # 当规则不存在，query filter first 返回 None，flush 后规则有 id
        rule_mock = MagicMock()
        rule_mock.id = 99

        def query_side_effect(model_cls):
            q = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                q.filter.return_value.first.return_value = None
            elif "AlertRecord" in name:
                q.filter.return_value.first.return_value = None
            elif "ProductionPlan" in name:
                q.filter.return_value.all.return_value = [plan]
            return q

        db.query.side_effect = query_side_effect
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts
        result = check_production_plan_alerts()

        # 应该调用 db.add (添加规则 + 添加预警记录)
        assert db.add.called

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_plan_already_has_pending_alert(self, mock_notify, mock_db_ctx):
        """已有 PENDING 预警 → 跳过，不重复创建"""
        from datetime import date, timedelta

        plan = MagicMock()
        plan.id = 13
        plan.plan_no = "PP-004"
        plan.plan_name = "已预警计划"
        plan.project_id = 8
        plan.progress = 50
        plan.plan_end_date = date.today() + timedelta(days=2)

        db = _make_db()
        rule_mock = MagicMock()
        rule_mock.id = 1
        existing_alert = MagicMock()  # 已存在预警

        def query_side_effect(model_cls):
            q = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                q.filter.return_value.first.return_value = rule_mock
            elif "AlertRecord" in name:
                q.filter.return_value.first.return_value = existing_alert
            elif "ProductionPlan" in name:
                q.filter.return_value.all.return_value = [plan]
            return q

        db.query.side_effect = query_side_effect
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts
        result = check_production_plan_alerts()

        assert result["alert_count"] == 0
        mock_notify.assert_not_called()

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_exception_returns_error_key(self, mock_notify, mock_db_ctx):
        """发生异常时返回 {'error': ...}"""
        mock_db_ctx.return_value.__enter__.side_effect = Exception("DB连接失败")

        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts
        result = check_production_plan_alerts()

        assert "error" in result


# ================================================================
#  check_work_report_timeout
# ================================================================

class TestCheckWorkReportTimeout:

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_no_active_orders(self, mock_notify, mock_db_ctx):
        """无进行中工单 → alert_count=0"""
        db = _make_db()

        def query_side_effect(model_cls):
            q = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                q.filter.return_value.first.return_value = MagicMock(id=1)
            elif "WorkOrder" in name:
                q.filter.return_value.all.return_value = []
            return q

        db.query.side_effect = query_side_effect
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout
        result = check_work_report_timeout()

        assert result["checked_count"] == 0
        assert result["alert_count"] == 0

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_order_with_recent_report(self, mock_notify, mock_db_ctx):
        """最近有报工（未超时） → 不生成预警"""
        from datetime import datetime, timedelta

        db = _make_db()
        order = MagicMock()
        order.id = 1
        order.work_order_no = "WO-001"
        order.task_name = "任务A"
        order.project_id = 1
        order.actual_start_time = datetime.now() - timedelta(hours=30)

        recent_report = MagicMock()
        recent_report.report_time = datetime.now() - timedelta(hours=2)  # 2小时前，未超时

        def query_side_effect(model_cls):
            q = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                q.filter.return_value.first.return_value = MagicMock(id=1)
            elif "WorkOrder" in name:
                q.filter.return_value.all.return_value = [order]
            elif "WorkReport" in name:
                q.filter.return_value.order_by.return_value.first.return_value = recent_report
            return q

        db.query.side_effect = query_side_effect
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout
        result = check_work_report_timeout()

        assert result["alert_count"] == 0

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_order_with_timeout_no_report(self, mock_notify, mock_db_ctx):
        """工单无报工 + 开始时间超过24h → 生成预警"""
        from datetime import datetime, timedelta

        db = _make_db()
        order = MagicMock()
        order.id = 2
        order.work_order_no = "WO-002"
        order.task_name = "超时任务"
        order.project_id = 1
        order.actual_start_time = datetime.now() - timedelta(hours=30)

        def query_side_effect(model_cls):
            q = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "AlertRule" in name:
                q.filter.return_value.first.return_value = MagicMock(id=1)
            elif "WorkOrder" in name:
                q.filter.return_value.all.return_value = [order]
            elif "WorkReport" in name:
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif "AlertRecord" in name:
                q.filter.return_value.first.return_value = None
            return q

        db.query.side_effect = query_side_effect
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout
        result = check_work_report_timeout()

        assert result["alert_count"] == 1
        mock_notify.assert_called_once()

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks.send_notification_for_alert")
    def test_exception_returns_error(self, mock_notify, mock_db_ctx):
        """异常时返回 error 字典"""
        mock_db_ctx.return_value.__enter__.side_effect = RuntimeError("timeout")

        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout
        result = check_work_report_timeout()

        assert "error" in result


# ================================================================
#  generate_production_daily_reports
# ================================================================

class TestGenerateProductionDailyReports:

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks._calculate_production_daily_stats")
    def test_report_already_exists(self, mock_calc, mock_db_ctx):
        """日报已存在 → 跳过生成"""
        db = _make_db()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from datetime import date
        from app.utils.scheduled_tasks.production_tasks import generate_production_daily_reports
        result = generate_production_daily_reports(target_date=date(2025, 1, 1))

        assert "message" in result
        mock_calc.assert_not_called()

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    @patch("app.utils.scheduled_tasks.production_tasks._calculate_production_daily_stats")
    def test_report_created_successfully(self, mock_calc, mock_db_ctx):
        """日报不存在 → 调用统计并创建"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None  # 不存在

        mock_calc.return_value = {
            "total_work_orders": 10,
            "completed_work_orders": 8,
            "total_output": 100,
            "qualified_output": 95,
            "defect_rate": 5.0,
            "efficiency_rate": 80.0,
        }

        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from datetime import date
        from app.utils.scheduled_tasks.production_tasks import generate_production_daily_reports
        result = generate_production_daily_reports(target_date=date(2025, 1, 2))

        assert "report_date" in result
        assert "stats" in result
        assert db.add.called

    @patch("app.utils.scheduled_tasks.production_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        """异常时返回 error"""
        mock_db_ctx.return_value.__enter__.side_effect = Exception("模拟错误")

        from datetime import date
        from app.utils.scheduled_tasks.production_tasks import generate_production_daily_reports
        result = generate_production_daily_reports(target_date=date(2025, 1, 3))

        assert "error" in result


# ================================================================
#  _calculate_production_daily_stats (纯函数，无 db session 包装)
# ================================================================

class TestCalculateProductionDailyStats:

    def test_empty_work_orders(self):
        """无工单时各统计字段均为 0"""
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        from datetime import date
        from app.utils.scheduled_tasks.production_tasks import _calculate_production_daily_stats
        result = _calculate_production_daily_stats(db, date(2025, 1, 1), None)

        assert result["total_work_orders"] == 0
        assert result["efficiency_rate"] == 0

    def test_with_work_orders(self):
        """有工单时正确计算效率和缺陷率"""
        db = _make_db()

        wo1 = MagicMock()
        wo1.status = "COMPLETED"
        wo1.completed_qty = 10
        wo1.qualified_qty = 9

        wo2 = MagicMock()
        wo2.status = "IN_PROGRESS"
        wo2.completed_qty = 5
        wo2.qualified_qty = 5

        # 代码用单次 .filter(cond1, cond2) → chain: query().filter().all()
        db.query.return_value.filter.return_value.all.return_value = [wo1, wo2]

        from datetime import date
        from app.utils.scheduled_tasks.production_tasks import _calculate_production_daily_stats
        result = _calculate_production_daily_stats(db, date(2025, 1, 1), None)

        assert result["total_work_orders"] == 2
        assert result["completed_work_orders"] == 1
        assert result["total_output"] == 15
        assert result["qualified_output"] == 14
        assert result["defect_rate"] > 0
        assert result["efficiency_rate"] == 50.0
