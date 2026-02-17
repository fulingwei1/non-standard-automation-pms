# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：项目风险服务
Coverage target: app/services/project/project_risk_service.py

测试重点：
- 风险等级计算（概率×影响矩阵）
- 边界值处理（0%, 10%, 30%, 50% 逾期比例）
- 进度偏差风险联动
- 多因子复合场景
- 批量风险计算
- 风险快照生成
- 通知流程（send_notification path）
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.services.project.project_risk_service import ProjectRiskService


# ─────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────

def make_project(
    pid=1,
    code="P001",
    name="测试项目",
    progress_pct=50,
    planned_start_date=None,
    planned_end_date=None,
    actual_start_date=None,
    contract_date=None,
    is_active=True,
):
    p = MagicMock()
    p.id = pid
    p.project_code = code
    p.project_name = name
    p.progress_pct = progress_pct
    p.planned_start_date = planned_start_date
    p.planned_end_date = planned_end_date
    p.actual_start_date = actual_start_date
    p.contract_date = contract_date
    p.is_active = is_active
    return p


# ─────────────────────────────────────────────────
# 1. _calculate_risk_level — 全边界矩阵
# ─────────────────────────────────────────────────

class TestCalculateRiskLevelMatrix:
    """风险等级矩阵完整边界测试"""

    def setup_method(self):
        self.svc = ProjectRiskService(MagicMock())

    # ── CRITICAL 分支 ──────────────────────────────
    def test_critical_by_overdue_ratio_exactly_50pct(self):
        """边界：逾期比例恰好 50% → CRITICAL"""
        factors = {"overdue_milestone_ratio": 0.50, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "CRITICAL"

    def test_critical_by_overdue_ratio_over_50pct(self):
        factors = {"overdue_milestone_ratio": 0.75, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "CRITICAL"

    def test_critical_by_single_critical_risk(self):
        """存在 1 个 CRITICAL 风险 → CRITICAL"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 1,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "CRITICAL"

    def test_critical_by_multiple_critical_risks(self):
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 3,
                   "high_risks_count": 5, "schedule_variance": -5}
        assert self.svc._calculate_risk_level(factors) == "CRITICAL"

    # ── HIGH 分支 ──────────────────────────────────
    def test_high_by_overdue_ratio_exactly_30pct(self):
        """边界：逾期比例恰好 30% → HIGH"""
        factors = {"overdue_milestone_ratio": 0.30, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    def test_high_by_overdue_ratio_between_30_and_50(self):
        factors = {"overdue_milestone_ratio": 0.40, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    def test_high_by_two_high_risks(self):
        """2 个 HIGH 风险 → HIGH"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 2, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    def test_high_by_schedule_variance_exactly_minus20(self):
        """进度偏差恰好 -20% → HIGH"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": -20}
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    def test_high_by_schedule_variance_below_minus20(self):
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": -35}
        assert self.svc._calculate_risk_level(factors) == "HIGH"

    # ── MEDIUM 分支 ─────────────────────────────────
    def test_medium_by_overdue_ratio_exactly_10pct(self):
        """边界：逾期比例恰好 10% → MEDIUM"""
        factors = {"overdue_milestone_ratio": 0.10, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "MEDIUM"

    def test_medium_by_single_high_risk(self):
        """1 个 HIGH 风险 → MEDIUM（不满足 HIGH 所需的 >=2）"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 1, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "MEDIUM"

    def test_medium_by_schedule_variance_minus15(self):
        """进度偏差 -15%（介于 -10% 和 -20% 之间）→ MEDIUM"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": -15}
        assert self.svc._calculate_risk_level(factors) == "MEDIUM"

    def test_medium_by_schedule_variance_exactly_minus10(self):
        """进度偏差恰好 -10% → MEDIUM"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": -10}
        assert self.svc._calculate_risk_level(factors) == "MEDIUM"

    # ── LOW 分支 ────────────────────────────────────
    def test_low_all_zeros(self):
        """零风险 → LOW"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "LOW"

    def test_low_positive_schedule_variance(self):
        """进度超前 → LOW"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 15}
        assert self.svc._calculate_risk_level(factors) == "LOW"

    def test_low_small_overdue_ratio(self):
        """逾期比例 < 10% → LOW（刚好低于 MEDIUM 阈值）"""
        factors = {"overdue_milestone_ratio": 0.09, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": 0}
        assert self.svc._calculate_risk_level(factors) == "LOW"

    def test_low_schedule_variance_just_above_minus10(self):
        """偏差 -9.99% → LOW（刚好不触发 MEDIUM）"""
        factors = {"overdue_milestone_ratio": 0, "critical_risks_count": 0,
                   "high_risks_count": 0, "schedule_variance": -9.99}
        assert self.svc._calculate_risk_level(factors) == "LOW"


# ─────────────────────────────────────────────────
# 2. _is_risk_upgrade — 升降级判断
# ─────────────────────────────────────────────────

class TestIsRiskUpgrade:
    def setup_method(self):
        self.svc = ProjectRiskService(MagicMock())

    def test_upgrade_low_to_critical(self):
        assert self.svc._is_risk_upgrade("LOW", "CRITICAL") is True

    def test_upgrade_medium_to_high(self):
        assert self.svc._is_risk_upgrade("MEDIUM", "HIGH") is True

    def test_same_level_not_upgrade(self):
        assert self.svc._is_risk_upgrade("HIGH", "HIGH") is False

    def test_downgrade_critical_to_low(self):
        assert self.svc._is_risk_upgrade("CRITICAL", "LOW") is False

    def test_unknown_level_treated_as_zero(self):
        """未知等级 → 视为 0，升到 LOW 算升级"""
        assert self.svc._is_risk_upgrade("UNKNOWN", "LOW") is True


# ─────────────────────────────────────────────────
# 3. _calculate_progress_factors — 进度偏差计算
# ─────────────────────────────────────────────────

class TestCalculateProgressFactors:
    def setup_method(self):
        self.svc = ProjectRiskService(MagicMock())

    def test_no_planned_end_date(self):
        """无计划结束日期 → 偏差为 0"""
        project = make_project(progress_pct=60, planned_end_date=None)
        result = self.svc._calculate_progress_factors(project)
        assert result["progress_pct"] == 60.0
        assert result["schedule_variance"] == 0

    def test_progress_on_track(self):
        """进度符合计划 → 偏差接近 0"""
        today = date.today()
        project = make_project(
            progress_pct=50,
            planned_start_date=today - timedelta(days=100),
            planned_end_date=today + timedelta(days=100),
            actual_start_date=today - timedelta(days=100),
        )
        result = self.svc._calculate_progress_factors(project)
        # 经过 100/200 天，期望 50%，实际 50%，偏差约为 0
        assert abs(result["schedule_variance"]) < 5

    def test_progress_behind_schedule(self):
        """进度落后 → 负偏差"""
        today = date.today()
        project = make_project(
            progress_pct=20,   # 实际只做了 20%
            planned_start_date=today - timedelta(days=150),
            planned_end_date=today + timedelta(days=50),   # 已过 75% 时间
            actual_start_date=today - timedelta(days=150),
        )
        result = self.svc._calculate_progress_factors(project)
        assert result["schedule_variance"] < 0

    def test_progress_ahead_of_schedule(self):
        """进度超前 → 正偏差"""
        today = date.today()
        project = make_project(
            progress_pct=90,   # 实际完成 90%
            planned_start_date=today - timedelta(days=50),
            planned_end_date=today + timedelta(days=150),  # 才过 25% 时间
            actual_start_date=today - timedelta(days=50),
        )
        result = self.svc._calculate_progress_factors(project)
        assert result["schedule_variance"] > 0

    def test_zero_duration_no_crash(self):
        """计划总工期为 0 → 不崩溃，偏差为 0"""
        today = date.today()
        project = make_project(
            progress_pct=0,
            planned_start_date=today,
            planned_end_date=today,   # start == end → duration = 0
        )
        result = self.svc._calculate_progress_factors(project)
        assert result["schedule_variance"] == 0


# ─────────────────────────────────────────────────
# 4. calculate_project_risk — 完整流程
# ─────────────────────────────────────────────────

class TestCalculateProjectRisk:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ProjectRiskService(self.db)

    def _setup_db_for_project(self, project, overdue_milestones=None, open_risks=None):
        """通用：配置 db.query().filter() 返回值"""
        from app.models.project import ProjectMilestone, Project
        from app.models.pmo import PmoProjectRisk

        def side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.filter.return_value.filter.return_value = q
            if model is Project:
                q.first.return_value = project
            elif model is ProjectMilestone:
                q.scalar.return_value = len(overdue_milestones or []) + 5
                q.all.return_value = overdue_milestones or []
                mock_count = MagicMock()
                mock_count.filter.return_value.scalar.return_value = len(overdue_milestones or []) + 5
                mock_count.filter.return_value.all.return_value = overdue_milestones or []
            elif model is PmoProjectRisk:
                q.all.return_value = open_risks or []
            else:
                q.all.return_value = []
                q.first.return_value = None
                q.scalar.return_value = 0
            return q

        self.db.query.side_effect = side_effect

    def test_project_not_found_raises_value_error(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            self.svc.calculate_project_risk(999)

    def test_returns_dict_with_required_keys(self):
        project = make_project()
        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.svc.calculate_project_risk(1)
        assert "project_id" in result
        assert "risk_level" in result
        assert "risk_factors" in result
        assert result["project_id"] == 1
        assert result["project_code"] == "P001"

    def test_risk_factors_contain_milestone_data(self):
        project = make_project()
        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.scalar.return_value = 10
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.svc.calculate_project_risk(1)
        rf = result["risk_factors"]
        assert "overdue_milestones_count" in rf
        assert "overdue_milestone_ratio" in rf
        assert "open_risks_count" in rf

    def test_risk_factors_contain_calculated_at(self):
        project = make_project()
        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.svc.calculate_project_risk(1)
        assert "calculated_at" in result["risk_factors"]


# ─────────────────────────────────────────────────
# 5. auto_upgrade_risk_level — 风险升级流程
# ─────────────────────────────────────────────────

class TestAutoUpgradeRiskLevel:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ProjectRiskService(self.db)

    def _mock_calculate(self, risk_level="MEDIUM"):
        self.svc.calculate_project_risk = MagicMock(return_value={
            "project_id": 1,
            "project_code": "P001",
            "risk_level": risk_level,
            "risk_factors": {"overdue_milestones_count": 1, "high_risks_count": 0, "schedule_variance": 0},
        })

    def test_no_prior_history_defaults_to_low(self):
        self._mock_calculate("MEDIUM")
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        project_mock = MagicMock()
        project_mock.project_name = "测试项目"
        # for get_project inside _send_risk_upgrade_notification
        self.db.query.return_value.filter.return_value.first.return_value = project_mock

        with patch.object(self.svc, '_send_risk_upgrade_notification') as mock_notify:
            result = self.svc.auto_upgrade_risk_level(1)

        assert result["old_risk_level"] == "LOW"
        assert result["new_risk_level"] == "MEDIUM"
        assert result["is_upgrade"] is True
        mock_notify.assert_called_once()

    def test_same_risk_level_no_upgrade(self):
        self._mock_calculate("HIGH")
        last_hist = MagicMock()
        last_hist.new_risk_level = "HIGH"
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_hist
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch.object(self.svc, '_send_risk_upgrade_notification') as mock_notify:
            result = self.svc.auto_upgrade_risk_level(1)

        assert result["is_upgrade"] is False
        mock_notify.assert_not_called()

    def test_downgrade_no_notification(self):
        self._mock_calculate("LOW")
        last_hist = MagicMock()
        last_hist.new_risk_level = "CRITICAL"
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last_hist
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch.object(self.svc, '_send_risk_upgrade_notification') as mock_notify:
            result = self.svc.auto_upgrade_risk_level(1)

        assert result["is_upgrade"] is False
        mock_notify.assert_not_called()

    def test_db_commit_called(self):
        self._mock_calculate("LOW")
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch.object(self.svc, '_send_risk_upgrade_notification'):
            self.svc.auto_upgrade_risk_level(1)

        self.db.commit.assert_called()

    def test_history_record_added(self):
        self._mock_calculate("HIGH")
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch.object(self.svc, '_send_risk_upgrade_notification'):
            self.svc.auto_upgrade_risk_level(1)

        self.db.add.assert_called()


# ─────────────────────────────────────────────────
# 6. batch_calculate_risks — 批量计算
# ─────────────────────────────────────────────────

class TestBatchCalculateRisks:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ProjectRiskService(self.db)

    def test_empty_project_list(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc.batch_calculate_risks(active_only=True)
        assert result == []

    def test_processes_all_active_projects(self):
        p1 = make_project(pid=1, code="P001")
        p2 = make_project(pid=2, code="P002")
        self.db.query.return_value.filter.return_value.all.return_value = [p1, p2]

        success_result = {
            "project_id": 1, "project_code": "P001",
            "old_risk_level": "LOW", "new_risk_level": "LOW",
            "is_upgrade": False, "risk_factors": {}
        }
        with patch.object(self.svc, 'auto_upgrade_risk_level', return_value=success_result):
            result = self.svc.batch_calculate_risks()

        assert len(result) == 2

    def test_error_in_single_project_does_not_stop_batch(self):
        p1 = make_project(pid=1, code="P001")
        p2 = make_project(pid=2, code="P002")
        self.db.query.return_value.filter.return_value.all.return_value = [p1, p2]

        def side_effect(project_id):
            if project_id == 1:
                raise RuntimeError("DB error")
            return {"project_id": 2, "project_code": "P002",
                    "old_risk_level": "LOW", "new_risk_level": "LOW",
                    "is_upgrade": False, "risk_factors": {}}

        with patch.object(self.svc, 'auto_upgrade_risk_level', side_effect=side_effect):
            result = self.svc.batch_calculate_risks()

        # P1 应有 error 键，P2 应成功
        assert len(result) == 2
        assert "error" in result[0]
        assert result[1]["project_id"] == 2

    def test_filter_by_project_ids(self):
        """传入 project_ids 时应过滤"""
        p1 = make_project(pid=5, code="P005")
        self.db.query.return_value.filter.return_value.all.return_value = [p1]

        with patch.object(self.svc, 'auto_upgrade_risk_level', return_value={
            "project_id": 5, "is_upgrade": False, "risk_factors": {}
        }):
            result = self.svc.batch_calculate_risks(project_ids=[5])

        assert len(result) == 1


# ─────────────────────────────────────────────────
# 7. create_risk_snapshot — 快照生成
# ─────────────────────────────────────────────────

class TestCreateRiskSnapshot:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ProjectRiskService(self.db)

    def test_snapshot_created_and_committed(self):
        self.svc.calculate_project_risk = MagicMock(return_value={
            "project_id": 1,
            "project_code": "P001",
            "risk_level": "MEDIUM",
            "risk_factors": {
                "overdue_milestones_count": 2,
                "total_milestones_count": 10,
                "overdue_tasks_count": 0,
                "open_risks_count": 1,
                "high_risks_count": 1,
            }
        })

        snapshot = self.svc.create_risk_snapshot(1)

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_snapshot_has_correct_risk_level(self):
        self.svc.calculate_project_risk = MagicMock(return_value={
            "project_id": 1,
            "project_code": "P001",
            "risk_level": "HIGH",
            "risk_factors": {
                "overdue_milestones_count": 3,
                "total_milestones_count": 10,
                "overdue_tasks_count": 0,
                "open_risks_count": 2,
                "high_risks_count": 2,
            }
        })

        # Capture what was added to db
        added_objects = []
        self.db.add.side_effect = lambda obj: added_objects.append(obj)

        self.svc.create_risk_snapshot(1)

        assert len(added_objects) == 1
        snapshot = added_objects[0]
        assert snapshot.risk_level == "HIGH"
        assert snapshot.overdue_milestones_count == 3
        assert snapshot.high_risks_count == 2


# ─────────────────────────────────────────────────
# 8. get_risk_trend — 趋势查询
# ─────────────────────────────────────────────────

class TestGetRiskTrend:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ProjectRiskService(self.db)

    def test_empty_snapshots_returns_empty_list(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = self.svc.get_risk_trend(1, days=30)
        assert result == []

    def test_trend_items_have_required_keys(self):
        snap = MagicMock()
        snap.snapshot_date = datetime(2026, 1, 1)
        snap.risk_level = "MEDIUM"
        snap.overdue_milestones_count = 2
        snap.open_risks_count = 1
        snap.high_risks_count = 1
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [snap]

        result = self.svc.get_risk_trend(1, days=30)
        assert len(result) == 1
        assert "date" in result[0]
        assert "risk_level" in result[0]
        assert result[0]["risk_level"] == "MEDIUM"


# ─────────────────────────────────────────────────
# 9. _calculate_pmo_risk_factors — PMO 风险因子
# ─────────────────────────────────────────────────

class TestCalculatePmoRiskFactors:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ProjectRiskService(self.db)

    def test_no_open_risks(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc._calculate_pmo_risk_factors(1)
        assert result["open_risks_count"] == 0
        assert result["high_risks_count"] == 0
        assert result["critical_risks_count"] == 0

    def test_counts_high_and_critical_correctly(self):
        r1 = MagicMock(); r1.risk_level = "HIGH"
        r2 = MagicMock(); r2.risk_level = "CRITICAL"
        r3 = MagicMock(); r3.risk_level = "MEDIUM"
        r4 = MagicMock(); r4.risk_level = "HIGH"
        self.db.query.return_value.filter.return_value.all.return_value = [r1, r2, r3, r4]

        result = self.svc._calculate_pmo_risk_factors(1)
        # high_risks_count 包含 HIGH 和 CRITICAL（前者是 HIGH|CRITICAL，后者仅 CRITICAL）
        assert result["open_risks_count"] == 4
        assert result["critical_risks_count"] == 1
        # HIGH + CRITICAL = 3
        assert result["high_risks_count"] == 3

    def test_only_critical_risks(self):
        r1 = MagicMock(); r1.risk_level = "CRITICAL"
        r2 = MagicMock(); r2.risk_level = "CRITICAL"
        self.db.query.return_value.filter.return_value.all.return_value = [r1, r2]

        result = self.svc._calculate_pmo_risk_factors(1)
        assert result["critical_risks_count"] == 2
        assert result["high_risks_count"] == 2  # CRITICAL 也计入 high_risks
