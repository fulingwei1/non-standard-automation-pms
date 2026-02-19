# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - engineer_performance/ranking_service.py
"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.engineer_performance.ranking_service",
                    reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    from app.services.engineer_performance.ranking_service import RankingService
    return RankingService(mock_db)


def _make_result(user_id, total_score, job_type="mechanical", level="B", rank=None):
    r = MagicMock()
    r.user_id = user_id
    r.total_score = total_score
    r.job_type = job_type
    r.job_level = "L2"
    r.level = level
    r.company_rank = rank
    r.period_id = 1
    return r


_MOCK_PERF_RESULT_MODULE = "app.services.engineer_performance.ranking_service.PerformanceResult"
_MOCK_PERF_PERIOD_MODULE = "app.services.engineer_performance.ranking_service.PerformancePeriod"
_MOCK_DESC_MODULE = "app.services.engineer_performance.ranking_service.desc"


class TestRankingServiceGetRanking:

    def test_get_ranking_returns_items_and_total(self, service, mock_db):
        items = [_make_result(1, 90), _make_result(2, 85)]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = items

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR, \
             patch(_MOCK_DESC_MODULE, return_value=MagicMock()):
            MockPR.period_id = MagicMock()
            MockPR.job_type = MagicMock()
            MockPR.job_level = MagicMock()
            MockPR.department_id = MagicMock()
            MockPR.total_score = MagicMock()
            result_items, total = service.get_ranking(period_id=1)
        assert total == 2

    def test_get_ranking_with_filters(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [_make_result(1, 90, "test")]

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR, \
             patch(_MOCK_DESC_MODULE, return_value=MagicMock()):
            MockPR.period_id = MagicMock()
            MockPR.job_type = MagicMock()
            MockPR.job_level = MagicMock()
            MockPR.department_id = MagicMock()
            MockPR.total_score = MagicMock()
            items, total = service.get_ranking(period_id=1, job_type="test",
                                               job_level="L2", department_id=5)
        assert total == 1


class TestRankingServiceCompanySummary:

    def test_empty_results_returns_empty_dict(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR:
            MockPR.period_id = MagicMock()
            MockPR.job_type = MagicMock()
            result = service.get_company_summary(period_id=1)
        assert result == {}

    def test_summary_with_data(self, service, mock_db):
        results = [
            _make_result(1, 90, "mechanical", "A"),
            _make_result(2, 80, "test", "B"),
            _make_result(3, 70, "electrical", "C"),
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = results

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR:
            MockPR.period_id = MagicMock()
            MockPR.job_type = MagicMock()
            summary = service.get_company_summary(period_id=1)
        assert summary["total_engineers"] == 3
        assert summary["avg_score"] == 80.0

    def test_level_distribution_counted(self, service, mock_db):
        results = [
            _make_result(1, 90, level="A"),
            _make_result(2, 80, level="A"),
            _make_result(3, 70, level="B"),
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = results

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR:
            MockPR.period_id = MagicMock()
            MockPR.job_type = MagicMock()
            summary = service.get_company_summary(period_id=1)
        assert summary["level_distribution"]["A"] == 2
        assert summary["level_distribution"]["B"] == 1

    def test_analyze_by_job_type(self, service):
        results = [
            _make_result(1, 90, "mechanical"),
            _make_result(2, 80, "mechanical"),
            _make_result(3, 70, "test"),
        ]
        result = service._analyze_by_job_type(results)
        assert "mechanical" in result
        assert result["mechanical"]["count"] == 2


class TestRankingServiceEngineerTrend:

    def test_trend_returns_list(self, service, mock_db):
        r = _make_result(1, 85, rank=3)
        period = MagicMock()
        period.period_name = "2024Q1"
        r.period = period
        r.period_id = 1

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [r]

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR, \
             patch(_MOCK_PERF_PERIOD_MODULE) as MockPP, \
             patch(_MOCK_DESC_MODULE, return_value=MagicMock()):
            MockPR.user_id = MagicMock()
            MockPP.start_date = MagicMock()
            MockPP.id = MagicMock()
            MockPR.period_id = MagicMock()
            trends = service.get_engineer_trend(engineer_id=1, periods=6)
        assert len(trends) == 1
        assert trends[0]["total_score"] == 85.0

    def test_trend_empty(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch(_MOCK_PERF_RESULT_MODULE) as MockPR, \
             patch(_MOCK_PERF_PERIOD_MODULE) as MockPP, \
             patch(_MOCK_DESC_MODULE, return_value=MagicMock()):
            MockPR.user_id = MagicMock()
            MockPP.start_date = MagicMock()
            trends = service.get_engineer_trend(engineer_id=99)
        assert trends == []
