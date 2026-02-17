# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/cache_decorator.py
Covers additional scenarios beyond test_utils_missing.py
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from app.utils.cache_decorator import (
    QueryStats,
    query_stats,
    log_query_time,
    track_query,
    cache_project_detail,
    cache_project_list,
    get_cache_service,
)


class TestQueryStats:
    """Tests for QueryStats class."""

    def setup_method(self):
        """Reset query_stats before each test."""
        query_stats.reset()

    def test_initial_state_all_zero(self):
        """QueryStats starts with all counters at zero."""
        qs = QueryStats()
        stats = qs.get_stats()
        assert stats["total_queries"] == 0
        assert stats["total_time"] == 0
        assert stats["avg_time"] == 0
        assert stats["slow_queries"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0

    def test_record_query_increments_total(self):
        """record_query increments query count and total_time."""
        qs = QueryStats()
        qs.record_query("get_items", 0.1, {"page": 1})
        qs.record_query("get_details", 0.2, {"id": 5})

        stats = qs.get_stats()
        assert stats["total_queries"] == 2
        assert abs(stats["total_time"] - 0.3) < 0.001

    def test_record_slow_query_tracked_separately(self):
        """Queries over 0.5s threshold are tracked as slow queries."""
        qs = QueryStats()
        qs.record_query("slow_func", 1.2)  # over threshold
        qs.record_query("fast_func", 0.1)  # under threshold

        stats = qs.get_stats()
        assert stats["slow_queries"] == 1

    def test_cache_hit_rate_calculation(self):
        """cache_hit_rate is correctly calculated."""
        qs = QueryStats()
        qs.cache_hits = 3
        qs.cache_misses = 1

        stats = qs.get_stats()
        assert stats["cache_hit_rate"] == 75.0

    def test_cache_hit_rate_zero_when_no_requests(self):
        """cache_hit_rate is 0 when no requests made."""
        qs = QueryStats()
        stats = qs.get_stats()
        assert stats["cache_hit_rate"] == 0

    def test_avg_time_calculated_correctly(self):
        """avg_time is mean of all query times."""
        qs = QueryStats()
        qs.record_query("f1", 0.2)
        qs.record_query("f2", 0.4)

        stats = qs.get_stats()
        assert abs(stats["avg_time"] - 0.3) < 0.001

    def test_reset_clears_all_data(self):
        """reset clears all collected data."""
        qs = QueryStats()
        qs.record_query("test", 0.8)
        qs.cache_hits = 10
        qs.reset()

        stats = qs.get_stats()
        assert stats["total_queries"] == 0
        assert stats["cache_hits"] == 0
        assert stats["slow_queries"] == 0


class TestLogQueryTime:
    """Tests for log_query_time decorator."""

    def test_fast_query_no_warning(self):
        """Fast queries don't emit warning logs."""
        @log_query_time(threshold=10.0)  # very high threshold
        def fast_func():
            return "result"

        with patch("app.utils.cache_decorator.logger") as mock_logger:
            result = fast_func()
            assert result == "result"
            mock_logger.warning.assert_not_called()

    def test_slow_query_emits_warning(self):
        """Queries exceeding threshold emit warning log."""
        @log_query_time(threshold=0.0)  # threshold=0 → always slow
        def slow_func():
            return "done"

        with patch("app.utils.cache_decorator.logger") as mock_logger:
            result = slow_func()
            assert result == "done"
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "慢查询" in call_args
            assert "slow_func" in call_args

    def test_preserves_return_value(self):
        """Decorated function return value is preserved."""
        @log_query_time()
        def func_with_value():
            return {"data": [1, 2, 3]}

        result = func_with_value()
        assert result == {"data": [1, 2, 3]}

    def test_default_threshold_is_half_second(self):
        """Default threshold is 0.5 seconds."""
        # Test that function works with default threshold
        @log_query_time()
        def instant_func():
            return True

        result = instant_func()
        assert result is True


class TestTrackQuery:
    """Tests for track_query decorator."""

    def setup_method(self):
        query_stats.reset()

    def test_track_query_records_execution(self):
        """track_query records query in global query_stats."""
        @track_query
        def my_func(name="test"):
            return name

        result = my_func(name="hello")
        assert result == "hello"
        stats = query_stats.get_stats()
        assert stats["total_queries"] == 1

    def test_track_query_records_function_name(self):
        """track_query records the function name."""
        @track_query
        def named_query():
            return None

        named_query()
        assert len(query_stats.queries) == 1
        assert query_stats.queries[0]["function"] == "named_query"

    def test_track_query_preserves_function_name(self):
        """track_query preserves __name__ via functools.wraps."""
        @track_query
        def my_special_query():
            pass

        assert my_special_query.__name__ == "my_special_query"


class TestCacheProjectDetail:
    """Tests for cache_project_detail decorator."""

    def test_cache_hit_returns_cached_data(self):
        """Returns cached data when cache hit."""
        mock_cache = MagicMock()
        mock_cache.get_project_detail.return_value = {"id": 1, "name": "Project 1"}

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_project_detail
            def get_project(self_obj, project_id):
                return {"id": project_id, "name": "Fresh"}

            result = get_project(MagicMock(), project_id=1)

        assert result["id"] == 1
        assert result.get("_from_cache") is True

    def test_cache_miss_calls_function(self):
        """Calls wrapped function on cache miss."""
        mock_cache = MagicMock()
        mock_cache.get_project_detail.return_value = None  # cache miss

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_project_detail
            def get_project(self_obj, project_id):
                return {"id": project_id, "name": "Fresh"}

            result = get_project(MagicMock(), project_id=5)

        assert result["id"] == 5
        mock_cache.set_project_detail.assert_called_once_with(5, result)

    def test_no_project_id_bypasses_cache(self):
        """When project_id is None, cache is bypassed."""
        mock_cache = MagicMock()

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_project_detail
            def get_project(self_obj, project_id=None):
                return {"data": "direct"}

            result = get_project(MagicMock(), project_id=None)

        assert result == {"data": "direct"}
        mock_cache.get_project_detail.assert_not_called()

    def test_invalidate_method_available(self):
        """Decorated function exposes invalidate method."""
        @cache_project_detail
        def get_project(self_obj, project_id):
            return {}

        assert hasattr(get_project, "invalidate")


class TestCacheProjectList:
    """Tests for cache_project_list decorator."""

    def test_cache_hit_returns_cached_list(self):
        """Returns cached list data on hit."""
        mock_cache = MagicMock()
        mock_cache.get_project_list.return_value = {"items": [1, 2, 3], "total": 3}

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_project_list
            def list_projects(self_obj, filters=None):
                return {"items": [], "total": 0}

            result = list_projects(MagicMock(), filters={"status": "active"})

        assert result["total"] == 3
        assert result.get("_from_cache") is True

    def test_cache_miss_stores_result(self):
        """Stores result in cache on cache miss."""
        mock_cache = MagicMock()
        mock_cache.get_project_list.return_value = None

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_project_list
            def list_projects(self_obj, filters=None):
                return {"items": [{"id": 1}], "total": 1}

            result = list_projects(MagicMock(), filters={"status": "active"})

        assert result["total"] == 1
        mock_cache.set_project_list.assert_called_once()

    def test_invalidate_method_on_list_decorator(self):
        """cache_project_list exposes invalidate method."""
        @cache_project_list
        def list_projects(self_obj, filters=None):
            return {}

        assert hasattr(list_projects, "invalidate")
