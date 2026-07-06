# -*- coding: utf-8 -*-
"""
OTDMetricsService 单元测试

验证 7 个核心指标的计算口径：
  1. 项目准时交付率（stage=S9 + actual<=planned）
  2. 项目延期天数（已完成 + 在途超期）
  3. 返工次数（代理：AcceptanceOrderItem.retry_count）
  4. 变更次数（ChangeRequest + Ecn）
  5. 项目毛利偏差（复用 ProfitAnalysisService，mock 隔离）
  6. 验收周期（actual_end - actual_start）
  7. 客户投诉率（COMPLAINT 占比）

以及聚合入口 get_metrics / get_project_metrics 的结构。
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem
from app.models.after_sales import AfterSalesFeedback
from app.models.change_request import ChangeRequest
from app.models.ecn.core import Ecn
from app.models.project import Project


# ============================================================
# 辅助：造项目
# ============================================================


def _make_project(
    db,
    code="OTD-METRIC-001",
    stage="S5",
    planned_end=None,
    actual_end=None,
    **overrides,
):
    """造一个项目，日期可控。"""
    defaults = dict(
        project_code=code,
        project_name=f"指标测试 {code}",
        stage=stage,
        status="ST01",
        health="H1",
        progress_pct=30,
        is_active=True,
        is_archived=False,
        planned_start_date=date.today() - timedelta(days=90),
        planned_end_date=planned_end or (date.today() + timedelta(days=30)),
    )
    if actual_end is not None:
        defaults["actual_end_date"] = actual_end
    defaults.update(overrides)
    p = Project(**defaults)
    db.add(p)
    db.flush()
    return p


# ============================================================
# 1. 项目准时交付率
# ============================================================


class TestOnTimeDeliveryRate:
    def test_no_completed_returns_zero(self, db_session):
        """无已完成项目时 rate=0。"""
        from app.services.otd import OTDMetricsService

        # 只造在途项目
        _make_project(db_session, "METRIC-NOCOMP", stage="S5")
        result = OTDMetricsService(db_session)._on_time_delivery_rate()
        assert result["total_completed"] == 0
        assert result["rate_pct"] == 0.0

    def test_completed_on_time(self, db_session):
        """按时完成（actual <= planned）计入 on_time。"""
        from app.services.otd import OTDMetricsService

        planned = date.today() - timedelta(days=10)
        _make_project(
            db_session,
            "METRIC-ONTIME",
            stage="S9",
            planned_end=planned,
            actual_end=planned,  # 正好按时
        )
        result = OTDMetricsService(db_session)._on_time_delivery_rate()
        assert result["total_completed"] == 1
        assert result["on_time"] == 1
        assert result["rate_pct"] == 100.0

    def test_completed_late_not_counted(self, db_session):
        """逾期完成（actual > planned）不计入 on_time。"""
        from app.services.otd import OTDMetricsService

        planned = date.today() - timedelta(days=10)
        _make_project(
            db_session,
            "METRIC-LATE",
            stage="S9",
            planned_end=planned,
            actual_end=date.today(),  # 晚 10 天
        )
        result = OTDMetricsService(db_session)._on_time_delivery_rate()
        assert result["total_completed"] == 1
        assert result["on_time"] == 0
        assert result["rate_pct"] == 0.0


# ============================================================
# 2. 项目延期天数
# ============================================================


class TestDelayDays:
    def test_no_overdue_returns_zeros(self, db_session):
        """无延期项目时全 0。"""
        from app.services.otd import OTDMetricsService

        _make_project(
            db_session, "METRIC-NODELAY", planned_end=date.today() + timedelta(days=30)
        )
        result = OTDMetricsService(db_session)._delay_days_distribution()
        assert result["avg_delay_days"] == 0
        assert result["completed_overdue_count"] == 0
        assert result["in_progress_overdue_count"] == 0

    def test_in_progress_overdue_counted(self, db_session):
        """在途项目已过计划交付日，计入延期。"""
        from app.services.otd import OTDMetricsService

        _make_project(
            db_session,
            "METRIC-INPROG-OVERDUE",
            stage="S5",
            planned_end=date.today() - timedelta(days=20),  # 已逾期 20 天
        )
        result = OTDMetricsService(db_session)._delay_days_distribution()
        assert result["in_progress_overdue_count"] == 1
        assert result["avg_delay_days"] == 20.0
        assert result["max_delay_days"] == 20


# ============================================================
# 3. 返工次数（代理：retry_count）
# ============================================================


class TestReworkCount:
    def test_no_acceptance_returns_zero(self, db_session):
        """无验收单时返工 0。"""
        from app.services.otd import OTDMetricsService

        _make_project(db_session, "METRIC-NOREWORK")
        result = OTDMetricsService(db_session)._rework_count()
        assert result["total_retry_count"] == 0
        assert result["items_with_retry"] == 0

    def test_retry_count_summed(self, db_session):
        """retry_count 之和 + 有复验的项数。"""
        from app.services.otd import OTDMetricsService

        project = _make_project(db_session, "METRIC-REWORK")
        # 建验收单 + 2 个明细（retry_count 分别 2 和 0）
        order = AcceptanceOrder(
            order_no="AO-REWORK-001",
            project_id=project.id,
            acceptance_type="FAT",
            status="COMPLETED",
        )
        db_session.add(order)
        db_session.flush()
        db_session.add(
            AcceptanceOrderItem(
                order_id=order.id,
                category_code="C1",
                category_name="分类1",
                item_code="I1",
                item_name="项1",
                retry_count=2,  # 有复验
            )
        )
        db_session.add(
            AcceptanceOrderItem(
                order_id=order.id,
                category_code="C1",
                category_name="分类1",
                item_code="I2",
                item_name="项2",
                retry_count=0,  # 无复验
            )
        )
        db_session.flush()

        result = OTDMetricsService(db_session)._rework_count()
        assert result["total_retry_count"] == 2  # 2 + 0
        assert result["items_with_retry"] == 1  # 只有 1 项 > 0


# ============================================================
# 4. 变更次数（ChangeRequest + Ecn）
# ============================================================


class TestChangeCount:
    def test_no_change_returns_zero(self, db_session):
        from app.services.otd import OTDMetricsService

        _make_project(db_session, "METRIC-NOCHANGE")
        result = OTDMetricsService(db_session)._change_count(
            date.today() - timedelta(days=30), date.today() + timedelta(days=1)
        )
        assert result["grand_total"] == 0

    def test_counts_change_request_and_ecn(self, db_session):
        """ChangeRequest（含客户/内部）+ Ecn 都计入。"""
        from datetime import datetime

        from app.services.otd import OTDMetricsService
        from app.models.user import User

        project = _make_project(db_session, "METRIC-CHANGE")
        # 需要一个 submitter（FK）
        user = User(
            username="metric-submitter",
            password_hash="dummy",
            real_name="提交人",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        db_session.add(
            ChangeRequest(
                change_code="CR-M-001",
                project_id=project.id,
                title="客户变更",
                change_type="REQUIREMENT",
                change_source="CUSTOMER",
                submitter_id=user.id,
                status="PENDING",
                created_at=datetime.now(),
            )
        )
        db_session.add(
            ChangeRequest(
                change_code="CR-M-002",
                project_id=project.id,
                title="内部变更",
                change_type="DESIGN",
                change_source="INTERNAL",
                submitter_id=user.id,
                status="APPROVED",
                created_at=datetime.now(),
            )
        )
        db_session.add(Ecn(ecn_no="ECN-M-001", ecn_title="工程变更", project_id=project.id))
        db_session.flush()

        result = OTDMetricsService(db_session)._change_count(
            date.today() - timedelta(days=1), date.today() + timedelta(days=1)
        )
        assert result["change_request_total"] == 2
        assert result["change_request_customer"] == 1
        assert result["change_request_internal"] == 1
        assert result["ecn_total"] == 1
        assert result["grand_total"] == 3


# ============================================================
# 5. 验收周期
# ============================================================


class TestAcceptanceCycle:
    def test_no_completed_returns_zero(self, db_session):
        from app.services.otd import OTDMetricsService

        _make_project(db_session, "METRIC-NOCYCLE")
        result = OTDMetricsService(db_session)._acceptance_cycle_days()
        assert result["avg_cycle_days"] == 0.0
        assert result["completed_acceptance_count"] == 0

    def test_cycle_computed(self, db_session):
        """周期 = (actual_end - actual_start).days。"""
        from datetime import datetime

        from app.services.otd import OTDMetricsService

        project = _make_project(db_session, "METRIC-CYCLE")
        start = datetime.now() - timedelta(days=10)
        end = datetime.now()
        db_session.add(
            AcceptanceOrder(
                order_no="AO-CYC-001",
                project_id=project.id,
                acceptance_type="FAT",
                status="COMPLETED",
                actual_start_date=start,
                actual_end_date=end,
            )
        )
        db_session.flush()

        result = OTDMetricsService(db_session)._acceptance_cycle_days()
        assert result["completed_acceptance_count"] == 1
        assert result["avg_cycle_days"] == 10.0
        assert "FAT" in result["avg_by_type"]


# ============================================================
# 6. 客户投诉率
# ============================================================


class TestComplaintRate:
    def test_no_feedback_returns_zero(self, db_session):
        from app.services.otd import OTDMetricsService

        _make_project(db_session, "METRIC-NOFEEDBACK")
        result = OTDMetricsService(db_session)._customer_complaint_rate(
            date.today() - timedelta(days=30), date.today() + timedelta(days=1)
        )
        assert result["complaint_count"] == 0
        assert result["complaint_rate_pct"] == 0.0

    def test_complaint_rate_computed(self, db_session):
        """投诉率 = COMPLAINT / 总反馈。"""
        from datetime import datetime

        from app.services.otd import OTDMetricsService

        project = _make_project(db_session, "METRIC-COMPLAINT")
        for i, ftype in enumerate(["COMPLAINT", "SUGGESTION", "PRAISE", "COMPLAINT"]):
            db_session.add(
                AfterSalesFeedback(
                    project_id=project.id,
                    feedback_type=ftype,
                    created_at=datetime.now(),
                )
            )
        db_session.flush()

        result = OTDMetricsService(db_session)._customer_complaint_rate(
            date.today() - timedelta(days=1), date.today() + timedelta(days=1)
        )
        assert result["total_feedback"] == 4
        assert result["complaint_count"] == 2
        assert result["complaint_rate_pct"] == 50.0


# ============================================================
# 7. 毛利偏差（mock ProfitAnalysisService 隔离外部依赖）
# ============================================================


class TestMarginDeviation:
    def test_returns_structure(self, db_session):
        """返回结构正确（含 note 说明）。

        不硬断言 project_count=0——_margin_deviation 查全局活跃项目，
        同 module 其他测试可能已造了活跃项目（in-memory DB 累积）。
        """
        from app.services.otd import OTDMetricsService

        result = OTDMetricsService(db_session)._margin_deviation()
        assert "avg_margin_gap_pct" in result
        assert "project_count" in result
        assert "below_target_count" in result
        assert "seriously_below_count" in result
        assert "note" in result
        assert isinstance(result["project_count"], int)

    def test_mocks_margin_gap_aggregation(self, db_session):
        """mock batch_margin_analysis 返回固定 gap，验证聚合 + 下钻。"""
        from app.services.otd import OTDMetricsService

        project = _make_project(db_session, "METRIC-MARGIN-A", is_active=True)

        def fake_batch(self_inner, target_margin=25.0, project_ids=None):
            return [
                {
                    "project_id": project.id,
                    "project_code": "METRIC-MARGIN-A",
                    "project_name": "测试",
                    "margin_gap": -8.0,
                    "current_margin_rate": 17.0,
                    "health": "critical",
                }
            ]

        with patch(
            "app.services.profit_analysis_service.ProfitAnalysisService.batch_margin_analysis",
            fake_batch,
        ):
            result = OTDMetricsService(db_session)._margin_deviation(project.id)

        assert result["project_count"] == 1
        assert result["avg_margin_gap_pct"] == -8.0
        assert result["below_target_count"] == 1
        assert result["seriously_below_count"] == 1
        # 下钻：top_offenders 含该项目
        assert len(result["top_offenders"]) == 1
        assert result["top_offenders"][0]["project_code"] == "METRIC-MARGIN-A"
        assert result["top_offenders"][0]["margin_gap"] == -8.0


# ============================================================
# 聚合入口
# ============================================================


class TestMetricsAggregation:
    def test_get_metrics_returns_7_indicators(self, db_session):
        """get_metrics 返回 7 个指标的完整结构。"""
        from app.services.otd import OTDMetricsService

        result = OTDMetricsService(db_session).get_metrics()
        assert "window" in result
        assert "metrics" in result
        assert "generated_at" in result
        expected = {
            "on_time_delivery_rate",
            "delay_days",
            "rework_count",
            "change_count",
            "margin_deviation",
            "acceptance_cycle_days",
            "customer_complaint_rate",
        }
        assert set(result["metrics"].keys()) == expected

    def test_get_project_metrics_not_found(self, db_session):
        """不存在的项目返回 error。"""
        from app.services.otd import OTDMetricsService

        result = OTDMetricsService(db_session).get_project_metrics(999999)
        assert "error" in result

    def test_get_project_metrics_returns_structure(self, db_session):
        """单项目指标结构正确。"""
        from app.services.otd import OTDMetricsService

        project = _make_project(db_session, "METRIC-PROJ")
        result = OTDMetricsService(db_session).get_project_metrics(project.id)
        assert result["project_id"] == project.id
        assert "metrics" in result
        assert set(result["metrics"].keys()) == {
            "on_time_delivery_rate",
            "delay_days",
            "rework_count",
            "change_count",
            "margin_deviation",
            "acceptance_cycle_days",
            "customer_complaint_rate",
        }

    def test_get_metrics_with_explicit_window(self, db_session):
        """显式时间窗生效。"""
        from app.services.otd import OTDMetricsService

        start = date.today() - timedelta(days=90)
        end = date.today() + timedelta(days=90)
        result = OTDMetricsService(db_session).get_metrics(start, end)
        assert result["window"]["start"] == start.isoformat()
        assert result["window"]["end"] == end.isoformat()


# ============================================================
# 下钻：top_offenders（B3）
# ============================================================


class TestMetricsDrillDown:
    """每个指标的 top_offenders 下钻。"""

    def test_offenders_included_by_default(self, db_session):
        """默认 include_offenders=True，每个指标都有 top_offenders 字段。"""
        from app.services.otd import OTDMetricsService

        result = OTDMetricsService(db_session).get_metrics()
        for name, val in result["metrics"].items():
            assert "top_offenders" in val, f"{name} 缺 top_offenders"
            assert isinstance(val["top_offenders"], list)

    def test_offenders_excluded_when_disabled(self, db_session):
        """include_offenders=False 时 top_offenders 为空列表（响应更小）。"""
        from app.services.otd import OTDMetricsService

        result = OTDMetricsService(db_session).get_metrics(
            include_offenders=False
        )
        for name, val in result["metrics"].items():
            assert val["top_offenders"] == []

    def test_on_time_offenders_sorted_by_delay(self, db_session):
        """准时交付率 offenders 按延期天数降序。"""
        from app.services.otd import OTDMetricsService

        # 造两个逾期完成的项目
        planned = date.today() - timedelta(days=20)
        _make_project(
            db_session, "METRIC-DRILL-LATE1", stage="S9",
            planned_end=planned, actual_end=date.today() - timedelta(days=5),  # 延期15天
        )
        _make_project(
            db_session, "METRIC-DRILL-LATE2", stage="S9",
            planned_end=planned, actual_end=date.today(),  # 延期20天
        )

        result = OTDMetricsService(db_session)._on_time_delivery_rate()
        offenders = result["top_offenders"]
        assert len(offenders) >= 2
        # 降序：第一个 delay_days >= 第二个
        assert offenders[0]["delay_days"] >= offenders[1]["delay_days"]
        # 含项目标识
        assert "project_code" in offenders[0]

    def test_delay_offenders_with_status(self, db_session):
        """延期天数 offenders 含 status 字段（已完成/在途）。"""
        from app.services.otd import OTDMetricsService

        _make_project(
            db_session, "METRIC-DRILL-INPROG", stage="S5",
            planned_end=date.today() - timedelta(days=30),
        )
        result = OTDMetricsService(db_session)._delay_days_distribution()
        if result["top_offenders"]:
            assert "status" in result["top_offenders"][0]
            assert result["top_offenders"][0]["status"] in ("已完成", "在途")
