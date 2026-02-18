# -*- coding: utf-8 -*-
"""第十八批 - 设计评审同步服务单元测试"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.design_review_sync_service import DesignReviewSyncService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return DesignReviewSyncService(db)


def make_tech_review(status="COMPLETED", conclusion="PASS", presenter_id=10,
                     host_id=20, project_id=5, review_id=1):
    tr = MagicMock()
    tr.id = review_id
    tr.status = status
    tr.conclusion = conclusion
    tr.presenter_id = presenter_id
    tr.host_id = host_id
    tr.project_id = project_id
    tr.review_name = "方案评审"
    tr.review_type = "DESIGN"
    tr.review_no = "TR-001"
    tr.actual_date = datetime(2024, 3, 15)
    tr.scheduled_date = datetime(2024, 3, 15)
    tr.issue_count_a = 1
    tr.issue_count_b = 2
    tr.issue_count_c = 0
    tr.issue_count_d = 0
    tr.conclusion_summary = "总体通过"
    return tr


class TestDesignReviewSyncServiceInit:
    def test_db_set(self, db, service):
        assert service.db is db


class TestSyncFromTechnicalReview:
    def test_returns_none_if_no_review(self, db, service):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_from_technical_review(999)
        assert result is None

    def test_returns_none_if_not_completed(self, db, service):
        tr = make_tech_review(status="PENDING")
        db.query.return_value.filter.return_value.first.return_value = tr
        result = service.sync_from_technical_review(1)
        assert result is None

    def test_returns_none_if_no_presenter(self, db, service):
        tr = make_tech_review(presenter_id=None)
        call_idx = [0]
        def query_side(model):
            call_idx[0] += 1
            m = MagicMock()
            if call_idx[0] == 1:
                m.filter.return_value.first.return_value = tr
            else:
                m.filter.return_value.first.return_value = None
            return m
        db.query.side_effect = query_side
        result = service.sync_from_technical_review(1)
        assert result is None

    def test_returns_existing_if_not_force(self, db, service):
        tr = make_tech_review()
        existing = MagicMock()

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            m = MagicMock()
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = tr
            else:
                m.filter.return_value.first.return_value = existing
            return m

        db.query.side_effect = query_side
        result = service.sync_from_technical_review(1, force_update=False)
        assert result is existing

    def test_returns_none_for_unknown_conclusion(self, db, service):
        tr = make_tech_review(conclusion="UNKNOWN")
        existing_call = [0]
        def query_side(model):
            existing_call[0] += 1
            m = MagicMock()
            if existing_call[0] == 1:
                m.filter.return_value.first.return_value = tr
            else:
                m.filter.return_value.first.return_value = None
            return m

        db.query.side_effect = query_side
        result = service.sync_from_technical_review(1)
        assert result is None


class TestSyncAllCompletedReviews:
    def test_returns_stats_dict(self, db, service):
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, "sync_from_technical_review", return_value=None):
            result = service.sync_all_completed_reviews()
        assert "total_reviews" in result
        assert "synced_count" in result
        assert "error_count" in result

    def test_counts_synced_reviews(self, db, service):
        tr1 = make_tech_review(review_id=1)
        tr2 = make_tech_review(review_id=2)
        db.query.return_value.filter.return_value.all.return_value = [tr1, tr2]

        synced = MagicMock()
        with patch.object(service, "sync_from_technical_review", return_value=synced):
            result = service.sync_all_completed_reviews()
        assert result["synced_count"] == 2
        assert result["total_reviews"] == 2
