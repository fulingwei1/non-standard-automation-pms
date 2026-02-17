# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：项目风险 (risk_tasks.py)
L2组覆盖率提升
"""
import sys
from contextlib import contextmanager
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
#  calculate_all_project_risks
# ================================================================

class TestCalculateAllProjectRisks:

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_empty_results(self, mock_get_db):
        """batch_calculate_risks 返回空列表"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.project.project_risk_service.ProjectRiskService"
        ) as MockSvc:
            instance = MagicMock()
            instance.batch_calculate_risks.return_value = []
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.risk_tasks import calculate_all_project_risks
            result = calculate_all_project_risks()

        assert result["total"] == 0
        assert result["success"] == 0
        assert result["errors"] == 0
        assert result["upgrades"] == 0

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_with_risk_upgrades(self, mock_get_db):
        """有风险升级的项目"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.project.project_risk_service.ProjectRiskService"
        ) as MockSvc:
            instance = MagicMock()
            instance.batch_calculate_risks.return_value = [
                {"project_id": 1, "is_upgrade": True},
                {"project_id": 2, "is_upgrade": False},
                {"project_id": 3, "error": "计算失败"},
            ]
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.risk_tasks import calculate_all_project_risks
            result = calculate_all_project_risks()

        assert result["total"] == 3
        assert result["success"] == 2
        assert result["errors"] == 1
        assert result["upgrades"] == 1

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """整体异常 → 返回 error 字段"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.project.project_risk_service.ProjectRiskService",
            side_effect=Exception("risk calc error"),
        ):
            from app.utils.scheduled_tasks.risk_tasks import calculate_all_project_risks
            result = calculate_all_project_risks()

        assert "error" in result


# ================================================================
#  create_daily_risk_snapshots
# ================================================================

class TestCreateDailyRiskSnapshots:

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_no_active_projects(self, mock_get_db):
        """无活跃项目 → total=0"""
        ctx, mock_db = make_mock_db_ctx()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.side_effect = ctx

        with patch("app.services.project.project_risk_service.ProjectRiskService") as MockSvc:
            instance = MagicMock()
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.risk_tasks import create_daily_risk_snapshots
            result = create_daily_risk_snapshots()

        assert result["total"] == 0
        assert result["success"] == 0

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_creates_snapshots_for_projects(self, mock_get_db):
        """有活跃项目 → create_risk_snapshot 被调用"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        p1 = MagicMock(id=1)
        p2 = MagicMock(id=2)
        mock_db.query.return_value.filter.return_value.all.return_value = [p1, p2]

        with patch("app.services.project.project_risk_service.ProjectRiskService") as MockSvc:
            instance = MagicMock()
            instance.create_risk_snapshot.return_value = MagicMock()
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.risk_tasks import create_daily_risk_snapshots
            result = create_daily_risk_snapshots()

        assert result["total"] == 2
        assert result["success"] == 2
        assert result["errors"] == 0

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_single_project_exception_counted(self, mock_get_db):
        """单个项目快照失败 → errors 增加，不影响其他项目"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        p1 = MagicMock(id=1)
        mock_db.query.return_value.filter.return_value.all.return_value = [p1]

        with patch("app.services.project.project_risk_service.ProjectRiskService") as MockSvc:
            instance = MagicMock()
            instance.create_risk_snapshot.side_effect = Exception("snapshot error")
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.risk_tasks import create_daily_risk_snapshots
            result = create_daily_risk_snapshots()

        assert result["errors"] == 1
        assert result["success"] == 0

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_session_exception_returns_error(self, mock_get_db):
        """session 异常 → 返回 error"""
        @contextmanager
        def bad_ctx():
            raise Exception("session error")
            yield  # noqa

        mock_get_db.side_effect = bad_ctx

        from app.utils.scheduled_tasks.risk_tasks import create_daily_risk_snapshots
        result = create_daily_risk_snapshots()

        assert "error" in result


# ================================================================
#  check_high_risk_projects
# ================================================================

class TestCheckHighRiskProjects:

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_no_high_risk_upgrades(self, mock_get_db):
        """无高风险升级 → alerts_created=0"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        # ProjectRiskHistory 查询返回空
        mock_db.query.return_value.filter.return_value.all.return_value = []

        from app.utils.scheduled_tasks.risk_tasks import check_high_risk_projects
        result = check_high_risk_projects()

        assert result["checked"] == 0
        assert result["alerts_created"] == 0

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_creates_alert_for_critical_project(self, mock_get_db):
        """发现 CRITICAL 级别风险升级 → 创建预警"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        history = MagicMock()
        history.project_id = 10
        history.new_risk_level = "CRITICAL"
        history.old_risk_level = "HIGH"

        project = MagicMock()
        project.id = 10
        project.project_code = "P001"
        project.project_name = "高风险项目"

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "ProjectRiskHistory" in name:
                m.filter.return_value.all.return_value = [history]
            elif "AlertRecord" in name:
                # apply_keyword_filter 后的 .first() → None（无已有预警）
                m.filter.return_value.filter.return_value.first.return_value = None
                m.filter.return_value.first.return_value = None
            elif "Project" in name:
                m.filter.return_value.first.return_value = project
            return m

        mock_db.query.side_effect = q

        with patch(
            "app.common.query_filters.apply_keyword_filter",
            side_effect=lambda query, *args, **kwargs: query,
        ):
            from app.utils.scheduled_tasks.risk_tasks import check_high_risk_projects
            result = check_high_risk_projects()

        assert mock_db.add.called
        assert result["alerts_created"] >= 1

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_existing_alert_not_duplicated(self, mock_get_db):
        """已有 PENDING 预警 → 不重复创建"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        history = MagicMock()
        history.project_id = 11
        history.new_risk_level = "HIGH"
        history.old_risk_level = "MEDIUM"

        existing_alert = MagicMock()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "ProjectRiskHistory" in name:
                m.filter.return_value.all.return_value = [history]
            elif "AlertRecord" in name:
                m.filter.return_value.first.return_value = existing_alert
            return m

        mock_db.query.side_effect = q

        with patch(
            "app.common.query_filters.apply_keyword_filter",
            side_effect=lambda query, *args, **kwargs: query,
        ):
            from app.utils.scheduled_tasks.risk_tasks import check_high_risk_projects
            result = check_high_risk_projects()

        assert result["alerts_created"] == 0

    @patch("app.utils.scheduled_tasks.risk_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常 → 返回 error"""
        @contextmanager
        def bad_ctx():
            raise Exception("risk check error")
            yield  # noqa

        mock_get_db.side_effect = bad_ctx

        from app.utils.scheduled_tasks.risk_tasks import check_high_risk_projects
        result = check_high_risk_projects()

        assert "error" in result
