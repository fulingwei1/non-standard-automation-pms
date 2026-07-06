# -*- coding: utf-8 -*-
"""
In-memory scheduler metrics collector.
Supports historical duration tracking for percentile calculations.
"""

from __future__ import annotations

import threading
import json
import logging
import os
from collections import defaultdict, deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SchedulerMetrics:
    def __init__(self, max_history_size: int = 1000, persistence_path: Optional[str | Path] = None):
        """
        Initialize metrics collector.

        Args:
            max_history_size: Maximum number of duration samples to keep per job
            persistence_path: Optional JSON file used to persist metrics across restarts
        """
        self._lock = threading.Lock()
        self._max_history_size = max_history_size
        self._persistence_path = Path(persistence_path) if persistence_path else None
        # Main metrics data
        self._data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "success_count": 0,
                "failure_count": 0,
                "last_duration_ms": 0.0,
                "total_duration_ms": 0.0,
                "last_status": None,
                "last_timestamp": None,
            }
        )
        # Historical duration samples for percentile calculations
        self._duration_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history_size)
        )
        # Notification channel statistics
        self._notification_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"success_count": 0, "failure_count": 0}
        )
        self._load_from_disk()

    def record_success(self, job_id: str, duration_ms: float, timestamp: str) -> None:
        with self._lock:
            entry = self._data[job_id]
            entry["success_count"] += 1
            entry["last_duration_ms"] = duration_ms
            entry["total_duration_ms"] += duration_ms
            entry["last_status"] = "success"
            entry["last_timestamp"] = timestamp
            # Add to history
            self._duration_history[job_id].append(duration_ms)
            self._persist_locked()

    def record_failure(self, job_id: str, duration_ms: float, timestamp: str) -> None:
        with self._lock:
            entry = self._data[job_id]
            entry["failure_count"] += 1
            entry["last_duration_ms"] = duration_ms
            entry["total_duration_ms"] += duration_ms
            entry["last_status"] = "failed"
            entry["last_timestamp"] = timestamp
            # Add to history (failures also have duration)
            self._duration_history[job_id].append(duration_ms)
            self._persist_locked()

    def reset(self) -> None:
        with self._lock:
            self._data.clear()
            self._duration_history.clear()
            self._notification_stats.clear()
            self._persist_locked()

    def record_notification(self, channel: str, success: bool) -> None:
        with self._lock:
            entry = self._notification_stats[channel.upper()]
            if success:
                entry["success_count"] += 1
            else:
                entry["failure_count"] += 1
            self._persist_locked()

    def _load_from_disk(self) -> None:
        if not self._persistence_path or not self._persistence_path.exists():
            return

        try:
            payload = json.loads(self._persistence_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scheduler metrics persistence load failed: %s", exc)
            return

        for job_id, stats in payload.get("jobs", {}).items():
            self._data[job_id].update(stats)

        for job_id, history in payload.get("duration_history", {}).items():
            self._duration_history[job_id].extend(history[-self._max_history_size:])

        for channel, stats in payload.get("notifications", {}).items():
            self._notification_stats[channel].update(stats)

    def _persist_locked(self) -> None:
        if not self._persistence_path:
            return

        payload = {
            "jobs": {job_id: dict(stats) for job_id, stats in self._data.items()},
            "duration_history": {
                job_id: list(history) for job_id, history in self._duration_history.items()
            },
            "notifications": {
                channel: dict(stats) for channel, stats in self._notification_stats.items()
            },
        }

        try:
            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._persistence_path.with_suffix(f"{self._persistence_path.suffix}.tmp")
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(self._persistence_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scheduler metrics persistence write failed: %s", exc)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Get a snapshot of current metrics."""
        with self._lock:
            return {
                "jobs": deepcopy(self._data),
                "notifications": deepcopy(self._notification_stats),
            }

    def _calculate_statistics(self, history: List[float]) -> Dict[str, Optional[float]]:
        """Calculate statistics from duration history."""
        if not history:
            return {
                "avg_duration_ms": None,
                "p50_duration_ms": None,
                "p95_duration_ms": None,
                "p99_duration_ms": None,
                "min_duration_ms": None,
                "max_duration_ms": None,
                "sample_count": 0,
            }

        sorted_history = sorted(history)
        count = len(sorted_history)

        def percentile(data: List[float], p: float) -> float:
            """Calculate percentile value."""
            if not data:
                return 0.0
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + c * (data[f + 1] - data[f])
            return data[f]

        return {
            "avg_duration_ms": sum(sorted_history) / count,
            "p50_duration_ms": percentile(sorted_history, 0.50),
            "p95_duration_ms": percentile(sorted_history, 0.95),
            "p99_duration_ms": percentile(sorted_history, 0.99),
            "min_duration_ms": sorted_history[0],
            "max_duration_ms": sorted_history[-1],
            "sample_count": count,
        }

    def get_statistics(self, job_id: str) -> Dict[str, Optional[float]]:
        """
        Calculate statistics for a job (avg, p50, p95, p99).

        Returns:
            Dictionary with avg_duration_ms, p50_duration_ms, p95_duration_ms, p99_duration_ms
        """
        with self._lock:
            history = list(self._duration_history.get(job_id, []))
        return self._calculate_statistics(history)

    def get_all_statistics(self) -> Dict[str, Dict[str, Optional[float]]]:
        """Get statistics for all jobs."""
        with self._lock:
            # Copy history data while holding lock
            history_snapshots = {
                job_id: list(history) for job_id, history in self._duration_history.items()
            }
            job_ids = set(self._data.keys()) | set(self._duration_history.keys())

        # Calculate statistics outside lock
        return {
            job_id: self._calculate_statistics(history_snapshots.get(job_id, []))
            for job_id in job_ids
        }


METRICS = SchedulerMetrics(
    persistence_path=os.getenv("SCHEDULER_METRICS_PATH", "data/scheduler_metrics.json")
)


def record_job_success(job_id: str, duration_ms: float, timestamp: str) -> None:
    METRICS.record_success(job_id, duration_ms, timestamp)


def record_job_failure(job_id: str, duration_ms: float, timestamp: str) -> None:
    METRICS.record_failure(job_id, duration_ms, timestamp)


def record_notification_success(channel: str) -> None:
    METRICS.record_notification(channel, True)


def record_notification_failure(channel: str) -> None:
    METRICS.record_notification(channel, False)


def get_metrics_snapshot() -> Dict[str, Dict[str, Any]]:
    return METRICS.snapshot()


def get_metrics_statistics() -> Dict[str, Dict[str, Optional[float]]]:
    """Get statistics (avg, p50, p95, p99) for all jobs."""
    return METRICS.get_all_statistics()
