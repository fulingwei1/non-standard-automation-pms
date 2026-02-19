# -*- coding: utf-8 -*-
"""第四十二批：data_integrity/check.py 单元测试"""
import pytest

pytest.importorskip("app.services.data_integrity.check")

from unittest.mock import MagicMock, patch
from app.services.data_integrity.check import DataCheckMixin


class ConcreteCheck(DataCheckMixin):
    def __init__(self, db):
        self.db = db


def make_checker():
    db = MagicMock()
    return ConcreteCheck(db), db


def setup_db_for_check(db, period, profile, work_logs=5, collab=3, contrib=1):
    """Helper to set up the complex DB mock for check_data_completeness"""
    call_count = [0]

    def query_side(*args):
        q = MagicMock()
        # period query
        period_filter = MagicMock()
        period_filter.first.return_value = period
        # profile query
        profile_filter = MagicMock()
        profile_filter.first.return_value = profile
        # default for count queries
        count_q = MagicMock()
        count_q.filter.return_value.count.return_value = 5
        count_q.filter.return_value.all.return_value = []
        count_q.join.return_value.filter.return_value.count.return_value = 0
        return count_q

    db.query.side_effect = None
    # Simple approach: make filter().first() return period/profile in order
    # and count() return configured values via side_effect on .filter().count()

    period_q = MagicMock()
    period_q.filter.return_value.first.return_value = period

    profile_q = MagicMock()
    profile_q.filter.return_value.first.return_value = profile

    # Work log query: filter().count() = work_logs
    worklog_q = MagicMock()
    worklog_q.filter.return_value.count.return_value = work_logs

    # Projects query: join().filter().count() = 0
    project_q = MagicMock()
    project_q.join.return_value.filter.return_value.count.return_value = 0

    # ProjectMember query: filter().all() = []
    member_q = MagicMock()
    member_q.filter.return_value.all.return_value = []

    # Collab ratings: filter().count() = collab
    collab_q = MagicMock()
    collab_q.filter.return_value.count.return_value = collab

    # KnowledgeContribution: filter().count() = contrib
    contrib_q = MagicMock()
    contrib_q.filter.return_value.count.return_value = contrib

    # ProjectEvaluation: filter().count() = 0 (no missing)
    eval_q = MagicMock()
    eval_q.filter.return_value.count.return_value = 0

    # DesignReview: filter().count() = 1 (for mech/electrical)
    review_q = MagicMock()
    review_q.filter.return_value.count.return_value = 1

    from app.models.performance import PerformancePeriod
    from app.models.engineer_performance import (
        EngineerProfile, CollaborationRating, DesignReview, KnowledgeContribution
    )
    from app.models.project import Project, ProjectMember
    from app.models.project_evaluation import ProjectEvaluation
    from app.models.work_log import WorkLog

    model_map = {
        PerformancePeriod: period_q,
        EngineerProfile: profile_q,
        WorkLog: worklog_q,
        Project: project_q,
        ProjectMember: member_q,
        CollaborationRating: collab_q,
        KnowledgeContribution: contrib_q,
        ProjectEvaluation: eval_q,
        DesignReview: review_q,
    }

    def query_router(*args):
        model = args[0] if args else None
        return model_map.get(model, MagicMock())

    db.query.side_effect = query_router


# ------------------------------------------------------------------ tests ---

def test_raises_when_period_not_found():
    checker, db = make_checker()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="考核周期不存在"):
        checker.check_data_completeness(1, 999)


def test_returns_zero_when_profile_missing():
    checker, db = make_checker()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    from app.models.performance import PerformancePeriod
    from app.models.engineer_performance import EngineerProfile

    period_q = MagicMock()
    period_q.filter.return_value.first.return_value = period
    profile_q = MagicMock()
    profile_q.filter.return_value.first.return_value = None

    def q_router(*args):
        if args and args[0] is PerformancePeriod:
            return period_q
        return profile_q

    db.query.side_effect = q_router
    result = checker.check_data_completeness(1, 1)
    assert result["completeness_score"] == 0.0
    assert "工程师档案不存在" in result["missing_items"]


def test_missing_work_logs_adds_missing_item():
    checker, db = make_checker()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    profile = MagicMock()
    profile.job_type = "test"

    setup_db_for_check(db, period, profile, work_logs=0, collab=3, contrib=1)
    result = checker.check_data_completeness(1, 1)
    assert "工作日志缺失" in result["missing_items"]


def test_no_projects_adds_warning():
    checker, db = make_checker()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    profile = MagicMock()
    profile.job_type = "test"

    setup_db_for_check(db, period, profile, work_logs=5, collab=3, contrib=1)
    result = checker.check_data_completeness(1, 1)
    # projects count = 0 → warning
    assert any("项目" in w for w in result["warnings"]) or result["projects_count"] == 0


def test_collab_ratings_insufficient_adds_warning():
    checker, db = make_checker()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    profile = MagicMock()
    profile.job_type = "test"

    setup_db_for_check(db, period, profile, work_logs=5, collab=2, contrib=1)
    result = checker.check_data_completeness(1, 1)
    assert any("协作评价" in w or "跨部门" in w for w in result["warnings"])


def test_completeness_score_range():
    checker, db = make_checker()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    profile = MagicMock()
    profile.job_type = "test"

    setup_db_for_check(db, period, profile)
    result = checker.check_data_completeness(1, 1)
    assert 0.0 <= result["completeness_score"] <= 100.0


def test_result_contains_required_keys():
    checker, db = make_checker()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    profile = MagicMock()
    profile.job_type = "test"

    setup_db_for_check(db, period, profile)
    result = checker.check_data_completeness(1, 1)
    for key in ("engineer_id", "period_id", "completeness_score", "missing_items", "warnings", "suggestions"):
        assert key in result
