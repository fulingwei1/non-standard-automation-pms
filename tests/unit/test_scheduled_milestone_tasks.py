# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：里程碑相关 (milestone_tasks.py)
L2组覆盖率提升
"""
import sys
from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def make_mock_db_ctx(return_data=None):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = return_data or []
    mock_db.query.return_value.all.return_value = return_data or []
    mock_db.query.return_value.filter.return_value.first.return_value = (
        return_data[0] if return_data else None
    )

    @contextmanager
    def ctx():
        yield mock_db

    return ctx, mock_db


# ================================================================
#  check_milestone_alerts
# ================================================================

class TestCheckMilestoneAlerts:

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_zero_alerts(self, mock_get_db):
        """MilestoneAlertService 返回 0 预警"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert.milestone_alert_service.MilestoneAlertService"
        ) as MockSvc:
            instance = MagicMock()
            instance.check_milestone_alerts.return_value = 0
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.milestone_tasks import check_milestone_alerts
            result = check_milestone_alerts()

        assert result["alert_count"] == 0
        assert "timestamp" in result

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_with_alerts(self, mock_get_db):
        """MilestoneAlertService 返回有预警"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert.milestone_alert_service.MilestoneAlertService"
        ) as MockSvc:
            instance = MagicMock()
            instance.check_milestone_alerts.return_value = 5
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.milestone_tasks import check_milestone_alerts
            result = check_milestone_alerts()

        assert result["alert_count"] == 5

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常 → 返回 error 字段"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert.milestone_alert_service.MilestoneAlertService",
            side_effect=Exception("milestone error"),
        ):
            from app.utils.scheduled_tasks.milestone_tasks import check_milestone_alerts
            result = check_milestone_alerts()

        assert "error" in result


# ================================================================
#  check_milestone_status_and_adjust_payments
# ================================================================

class TestCheckMilestoneStatusAndAdjustPayments:

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_nothing_to_adjust(self, mock_get_db):
        """无需调整 → checked=0, adjusted=0"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.payment_adjustment_service.PaymentAdjustmentService"
        ) as MockSvc:
            instance = MagicMock()
            instance.check_and_adjust_all.return_value = {"checked": 0, "adjusted": 0}
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.milestone_tasks import (
                check_milestone_status_and_adjust_payments,
            )
            result = check_milestone_status_and_adjust_payments()

        assert result.get("checked") == 0
        assert result.get("adjusted") == 0

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_with_adjustments(self, mock_get_db):
        """有收款计划需要调整"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.payment_adjustment_service.PaymentAdjustmentService"
        ) as MockSvc:
            instance = MagicMock()
            instance.check_and_adjust_all.return_value = {"checked": 5, "adjusted": 2}
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.milestone_tasks import (
                check_milestone_status_and_adjust_payments,
            )
            result = check_milestone_status_and_adjust_payments()

        assert result["adjusted"] == 2

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常 → 返回 error"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.payment_adjustment_service.PaymentAdjustmentService",
            side_effect=Exception("adjustment error"),
        ):
            from app.utils.scheduled_tasks.milestone_tasks import (
                check_milestone_status_and_adjust_payments,
            )
            result = check_milestone_status_and_adjust_payments()

        assert "error" in result


# ================================================================
#  check_milestone_risk_alerts
# ================================================================

class TestCheckMilestoneRiskAlerts:

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_no_active_projects(self, mock_get_db):
        """无活跃项目 → checked_projects=0"""
        ctx, mock_db = make_mock_db_ctx()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.side_effect = ctx

        from app.utils.scheduled_tasks.milestone_tasks import check_milestone_risk_alerts
        result = check_milestone_risk_alerts()

        assert result["checked_projects"] == 0
        assert result["risk_alerts"] == 0

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_project_no_milestones(self, mock_get_db):
        """项目无里程碑 → 不生成预警"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "项目A"

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Project" in name:
                m.filter.return_value.all.return_value = [project]
            elif "ProjectMilestone" in name:
                m.filter.return_value.all.return_value = []
            return m

        mock_db.query.side_effect = q

        from app.utils.scheduled_tasks.milestone_tasks import check_milestone_risk_alerts
        result = check_milestone_risk_alerts()

        assert result["risk_alerts"] == 0

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_project_high_overdue_ratio_creates_alert(self, mock_get_db):
        """逾期率 ≥ 30% → 生成风险预警"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        today = date.today()
        project = MagicMock()
        project.id = 2
        project.project_code = "P002"
        project.project_name = "高风险项目"

        # 3个里程碑，2个已逾期（66.7% > 30%）
        m1 = MagicMock()
        m1.planned_date = today - timedelta(days=5)  # 逾期
        m2 = MagicMock()
        m2.planned_date = today - timedelta(days=10)  # 逾期
        m3 = MagicMock()
        m3.planned_date = today + timedelta(days=5)   # 未逾期

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Project" in name:
                m.filter.return_value.all.return_value = [project]
            elif "ProjectMilestone" in name:
                m.filter.return_value.all.return_value = [m1, m2, m3]
            elif "AlertRecord" in name:
                m.filter.return_value.first.return_value = None
            return m

        mock_db.query.side_effect = q

        with patch(
            "app.common.query_filters.apply_keyword_filter",
            side_effect=lambda query, *args, **kwargs: query,
        ):
            from app.utils.scheduled_tasks.milestone_tasks import check_milestone_risk_alerts
            result = check_milestone_risk_alerts()

        assert mock_db.add.called
        assert result["risk_alerts"] >= 1

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_project_low_overdue_ratio_no_alert(self, mock_get_db):
        """逾期率 < 30% → 不生成预警"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        today = date.today()
        project = MagicMock()
        project.id = 3
        project.project_code = "P003"
        project.project_name = "健康项目"

        # 10个里程碑，2个逾期（20% < 30%）
        overdue = [MagicMock(planned_date=today - timedelta(days=i)) for i in [1, 2]]
        ok = [MagicMock(planned_date=today + timedelta(days=i)) for i in range(1, 9)]
        milestones = overdue + ok

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Project" in name:
                m.filter.return_value.all.return_value = [project]
            elif "ProjectMilestone" in name:
                m.filter.return_value.all.return_value = milestones
            return m

        mock_db.query.side_effect = q

        from app.utils.scheduled_tasks.milestone_tasks import check_milestone_risk_alerts
        result = check_milestone_risk_alerts()

        assert result["risk_alerts"] == 0

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_existing_alert_not_duplicated(self, mock_get_db):
        """已有 PENDING 预警 → 不重复创建"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        today = date.today()
        project = MagicMock()
        project.id = 4
        project.project_code = "P004"
        project.project_name = "已预警项目"

        m1 = MagicMock(planned_date=today - timedelta(days=5))
        m2 = MagicMock(planned_date=today - timedelta(days=10))
        existing_alert = MagicMock()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Project" in name:
                m.filter.return_value.all.return_value = [project]
            elif "ProjectMilestone" in name:
                m.filter.return_value.all.return_value = [m1, m2]
            elif "AlertRecord" in name:
                m.filter.return_value.first.return_value = existing_alert
            return m

        mock_db.query.side_effect = q

        with patch(
            "app.common.query_filters.apply_keyword_filter",
            side_effect=lambda query, *args, **kwargs: query,
        ):
            from app.utils.scheduled_tasks.milestone_tasks import check_milestone_risk_alerts
            result = check_milestone_risk_alerts()

        assert result["risk_alerts"] == 0

    @patch("app.utils.scheduled_tasks.milestone_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常 → 返回 error"""
        @contextmanager
        def bad_ctx():
            raise Exception("milestone risk error")
            yield  # noqa

        mock_get_db.side_effect = bad_ctx

        from app.utils.scheduled_tasks.milestone_tasks import check_milestone_risk_alerts
        result = check_milestone_risk_alerts()

        assert "error" in result
