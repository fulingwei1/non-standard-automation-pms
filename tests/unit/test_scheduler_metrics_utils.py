# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/scheduler_metrics.py
Covers: SchedulerMetrics class (additional/edge cases)
"""

import pytest
import threading
from app.utils.scheduler_metrics import (
    SchedulerMetrics,
    record_job_success,
    record_job_failure,
    record_notification_success,
    record_notification_failure,
    get_metrics_snapshot,
    get_metrics_statistics,
    METRICS,
)


class TestSchedulerMetricsAdvanced:
    """Advanced tests for SchedulerMetrics."""

    def setup_method(self):
        METRICS.reset()

    def test_percentile_calculations_with_multiple_samples(self):
        """p50, p95, p99 are correctly calculated."""
        m = SchedulerMetrics()
        for i in range(1, 101):  # 100 samples: 1.0..100.0 ms
            m.record_success("job_p", float(i), "2026-01-01T00:00:00Z")

        stats = m.get_statistics("job_p")
        assert abs(stats["p50_duration_ms"] - 50.0) < 2.0
        assert stats["p95_duration_ms"] >= 90.0
        assert stats["p99_duration_ms"] >= 98.0
        assert stats["min_duration_ms"] == 1.0
        assert stats["max_duration_ms"] == 100.0
        assert stats["sample_count"] == 100

    def test_max_history_size_limits_samples(self):
        """History is capped at max_history_size."""
        m = SchedulerMetrics(max_history_size=5)
        for i in range(10):
            m.record_success("capped_job", float(i), "2026-01-01T00:00:00Z")

        stats = m.get_statistics("capped_job")
        assert stats["sample_count"] == 5  # only last 5

    def test_failure_also_contributes_to_history(self):
        """Failures are included in duration history for statistics."""
        m = SchedulerMetrics()
        m.record_success("j", 100.0, "2026-01-01T00:00:00Z")
        m.record_failure("j", 200.0, "2026-01-01T00:00:00Z")

        stats = m.get_statistics("j")
        assert stats["sample_count"] == 2
        assert stats["avg_duration_ms"] == 150.0

    def test_get_all_statistics_covers_all_jobs(self):
        """get_all_statistics returns stats for every job seen."""
        m = SchedulerMetrics()
        m.record_success("job_a", 50.0, "ts1")
        m.record_failure("job_b", 75.0, "ts2")

        all_stats = m.get_all_statistics()
        assert "job_a" in all_stats
        assert "job_b" in all_stats

    def test_snapshot_is_deep_copy(self):
        """snapshot returns a deep copy, not live references."""
        m = SchedulerMetrics()
        m.record_success("snap_job", 10.0, "ts")

        snap = m.snapshot()
        # Mutate the snapshot
        snap["jobs"]["snap_job"]["success_count"] = 999

        # Original should be unchanged
        live_snap = m.snapshot()
        assert live_snap["jobs"]["snap_job"]["success_count"] == 1

    def test_total_duration_accumulates(self):
        """total_duration_ms accumulates across calls."""
        m = SchedulerMetrics()
        m.record_success("acc_job", 100.0, "ts1")
        m.record_success("acc_job", 200.0, "ts2")

        snap = m.snapshot()
        assert snap["jobs"]["acc_job"]["total_duration_ms"] == 300.0

    def test_last_status_updated_on_failure_after_success(self):
        """last_status reflects the most recent call."""
        m = SchedulerMetrics()
        m.record_success("status_job", 10.0, "ts1")
        m.record_failure("status_job", 20.0, "ts2")

        snap = m.snapshot()
        assert snap["jobs"]["status_job"]["last_status"] == "failed"

    def test_thread_safety_concurrent_writes(self):
        """Concurrent writes from multiple threads do not corrupt counts."""
        m = SchedulerMetrics()
        errors = []

        def worker():
            try:
                for _ in range(50):
                    m.record_success("thread_job", 1.0, "ts")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        snap = m.snapshot()
        assert snap["jobs"]["thread_job"]["success_count"] == 500

    def test_reset_clears_everything(self):
        """reset() clears jobs, history, and notifications."""
        m = SchedulerMetrics()
        m.record_success("j1", 10.0, "ts")
        m.record_notification("EMAIL", True)
        m.reset()

        snap = m.snapshot()
        assert len(snap["jobs"]) == 0
        assert len(snap["notifications"]) == 0


class TestModuleLevelFunctions:
    """Tests for module-level helper functions."""

    def setup_method(self):
        METRICS.reset()

    def test_record_job_success_updates_global_metrics(self):
        """record_job_success updates the global METRICS object."""
        record_job_success("mod_job", 55.0, "2026-01-01T00:00:00Z")
        snap = get_metrics_snapshot()
        assert snap["jobs"]["mod_job"]["success_count"] == 1
        assert snap["jobs"]["mod_job"]["last_duration_ms"] == 55.0

    def test_record_job_failure_updates_global_metrics(self):
        """record_job_failure updates the global METRICS object."""
        record_job_failure("fail_mod_job", 88.0, "2026-01-01T00:00:00Z")
        snap = get_metrics_snapshot()
        assert snap["jobs"]["fail_mod_job"]["failure_count"] == 1
        assert snap["jobs"]["fail_mod_job"]["last_status"] == "failed"

    def test_record_notification_success_and_failure(self):
        """record_notification_success and failure update notification stats."""
        record_notification_success("WECHAT")
        record_notification_success("WECHAT")
        record_notification_failure("WECHAT")

        snap = get_metrics_snapshot()
        stats = snap["notifications"]["WECHAT"]
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 1

    def test_get_metrics_statistics_returns_dict(self):
        """get_metrics_statistics returns a dictionary of job stats."""
        record_job_success("stat_job", 100.0, "ts")
        all_stats = get_metrics_statistics()
        assert isinstance(all_stats, dict)
        assert "stat_job" in all_stats

    def test_statistics_empty_job_all_none(self):
        """Statistics for unknown job returns None values."""
        stats = METRICS.get_statistics("unknown_job_xyz")
        assert stats["avg_duration_ms"] is None
        assert stats["sample_count"] == 0
