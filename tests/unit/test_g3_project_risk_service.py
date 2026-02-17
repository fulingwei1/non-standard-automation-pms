# -*- coding: utf-8 -*-
"""
G3组 - 项目风险服务单元测试（扩展）
目标文件: app/services/project/project_risk_service.py
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, call

from app.services.project.project_risk_service import ProjectRiskService


def make_service(db=None):
    if db is None:
        db = MagicMock()
    return ProjectRiskService(db), db


class TestRiskLevelCalculation:
    """测试风险等级计算逻辑"""

    def setup_method(self):
        self.svc, _ = make_service()

    def test_critical_by_high_overdue_ratio(self):
        factors = {
            "overdue_milestone_ratio": 0.6,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 0
        }
        assert self.svc._calculate_risk_level(factors) == "CRITICAL"

    def test_critical_by_critical_risk(self):
        factors = {
            "overdue_milestone_ratio": 0,
            "critical_risks_count": 2,
            "high_risks_count": 0,
            "schedule_variance": 0
        }
        assert self.svc._calculate_risk_level(factors) == "CRITICAL"

    def test_high_by_moderate_overdue_ratio(self):
        factors = {
            "overdue_milestone_ratio": 0.3,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 0
        }
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    def test_high_by_high_schedule_variance(self):
        factors = {
            "overdue_milestone_ratio": 0,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": -25
        }
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    def test_medium_risk(self):
        factors = {
            "overdue_milestone_ratio": 0.15,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 0
        }
        assert self.svc._calculate_risk_level(factors) == "MEDIUM"

    def test_medium_by_high_risks(self):
        factors = {
            "overdue_milestone_ratio": 0,
            "critical_risks_count": 0,
            "high_risks_count": 2,
            "schedule_variance": 0
        }
        assert self.svc._calculate_risk_level(factors) in ("MEDIUM", "HIGH")

    def test_low_risk(self):
        factors = {
            "overdue_milestone_ratio": 0,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 0
        }
        assert self.svc._calculate_risk_level(factors) == "LOW"


class TestIsRiskUpgrade:
    """测试风险升级判断"""

    def setup_method(self):
        self.svc, _ = make_service()

    def test_low_to_high_is_upgrade(self):
        assert self.svc._is_risk_upgrade("LOW", "HIGH") is True

    def test_high_to_low_not_upgrade(self):
        assert self.svc._is_risk_upgrade("HIGH", "LOW") is False

    def test_same_level_not_upgrade(self):
        assert self.svc._is_risk_upgrade("MEDIUM", "MEDIUM") is False

    def test_medium_to_critical_is_upgrade(self):
        assert self.svc._is_risk_upgrade("MEDIUM", "CRITICAL") is True

    def test_critical_to_medium_not_upgrade(self):
        assert self.svc._is_risk_upgrade("CRITICAL", "MEDIUM") is False


class TestCalculateProgressFactors:
    """测试进度风险因子计算"""

    def setup_method(self):
        self.svc, _ = make_service()

    def test_no_planned_end_date(self):
        project = MagicMock()
        project.progress_pct = 40
        project.planned_end_date = None

        result = self.svc._calculate_progress_factors(project)

        assert result["progress_pct"] == 40.0
        assert result["schedule_variance"] == 0

    def test_with_planned_end_date_on_track(self):
        project = MagicMock()
        project.progress_pct = 80
        project.planned_end_date = date.today()

        result = self.svc._calculate_progress_factors(project)
        assert "schedule_variance" in result

    def test_zero_progress(self):
        project = MagicMock()
        project.progress_pct = None
        project.planned_end_date = None

        result = self.svc._calculate_progress_factors(project)
        assert result["progress_pct"] == 0.0


class TestCalculateProjectRisk:
    """测试计算项目风险"""

    def setup_method(self):
        self.svc, self.db = make_service()

    def test_project_not_found_raises(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            self.svc.calculate_project_risk(999)

    def test_project_found_returns_result(self):
        project = MagicMock()
        project.id = 1
        project.project_code = "P-2026-001"
        project.progress_pct = 50
        project.planned_end_date = None

        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.svc.calculate_project_risk(1)

        assert result["project_id"] == 1
        assert result["project_code"] == "P-2026-001"
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert "risk_factors" in result


class TestAutoUpgradeRiskLevel:
    """测试自动升级风险等级"""

    def setup_method(self):
        self.svc, self.db = make_service()

    def test_first_run_defaults_to_low(self):
        """历史记录为空时，默认旧等级为LOW"""
        project = MagicMock()
        project.id = 1
        project.project_code = "P-001"
        project.project_name = "测试项目"
        project.progress_pct = 20
        project.planned_end_date = None

        # 第一次调用 query(Project) 返回项目
        # 之后 query(ProjectRiskHistory) 返回 None
        def query_side_effect(model):
            from app.models.project import Project
            from app.models.project.risk_history import ProjectRiskHistory
            m = MagicMock()
            if model is Project:
                m.filter.return_value.first.return_value = project
                m.filter.return_value.scalar.return_value = 0
                m.filter.return_value.all.return_value = []
            elif model is ProjectRiskHistory:
                m.filter.return_value.order_by.return_value.first.return_value = None
                m.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            else:
                m.filter.return_value.first.return_value = None
                m.filter.return_value.all.return_value = []
                m.filter.return_value.scalar.return_value = 0
            return m

        self.db.query.side_effect = query_side_effect

        with patch.object(self.svc, "_send_risk_upgrade_notification"):
            result = self.svc.auto_upgrade_risk_level(1)

        assert result["old_risk_level"] == "LOW"
        assert "new_risk_level" in result
        assert "is_upgrade" in result


class TestBatchCalculateRisks:
    """测试批量计算风险"""

    def setup_method(self):
        self.svc, self.db = make_service()

    def test_empty_project_ids(self):
        mock_projects = []
        self.db.query.return_value.filter.return_value.all.return_value = mock_projects
        self.db.query.return_value.all.return_value = mock_projects

        result = self.svc.batch_calculate_risks()
        assert result == []

    def test_skips_failed_projects(self):
        project = MagicMock()
        project.id = 1
        project.project_code = "P-001"

        self.db.query.return_value.filter.return_value.all.return_value = [project]
        self.db.query.return_value.all.return_value = [project]

        with patch.object(self.svc, "auto_upgrade_risk_level",
                          side_effect=ValueError("项目不存在: 1")):
            result = self.svc.batch_calculate_risks(project_ids=[1])

        assert len(result) == 1
        assert "error" in result[0]


class TestGetRiskHistory:
    """测试获取风险历史"""

    def setup_method(self):
        self.svc, self.db = make_service()

    def test_empty_history(self):
        (self.db.query.return_value
            .filter.return_value
            .order_by.return_value
            .limit.return_value
            .all.return_value) = []

        result = self.svc.get_risk_history(1)
        assert result == []

    def test_returns_history_records(self):
        mock_record = MagicMock()
        (self.db.query.return_value
            .filter.return_value
            .order_by.return_value
            .limit.return_value
            .all.return_value) = [mock_record]

        result = self.svc.get_risk_history(1, limit=10)
        assert len(result) == 1
        assert result[0] is mock_record


class TestCreateRiskSnapshot:
    """测试创建风险快照"""

    def setup_method(self):
        self.svc, self.db = make_service()

    def test_create_snapshot_success(self):
        project = MagicMock()
        project.id = 1
        project.project_code = "P-002"
        project.progress_pct = 60
        project.planned_end_date = None

        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.return_value.filter.return_value.all.return_value = []

        snapshot = self.svc.create_risk_snapshot(1)

        self.db.add.assert_called_once()
        self.db.commit.assert_called()
        assert snapshot.project_id == 1
