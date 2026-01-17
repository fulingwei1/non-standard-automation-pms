# -*- coding: utf-8 -*-
"""
调度器指标监控端点
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics", response_model=ResponseModel)
def get_scheduler_metrics(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取调度任务运行指标（成功/失败次数、耗时、统计信息）
    包含平均值、P50、P95、P99等聚合数据
    """
    try:
        from app.utils.scheduler_config import SCHEDULER_TASKS
        from app.utils.scheduler_metrics import (
            get_metrics_snapshot,
            get_metrics_statistics,
        )

        snapshot = get_metrics_snapshot()
        statistics = get_metrics_statistics()

        task_metadata = {task["id"]: task for task in SCHEDULER_TASKS}
        job_snapshot = snapshot.get("jobs", {})
        notification_snapshot = snapshot.get("notifications", {})

        formatted = []
        for job_id, stats in job_snapshot.items():
            job_stats = statistics.get(job_id, {})
            task_info = task_metadata.get(job_id, {})

            total_runs = stats.get("success_count", 0) + stats.get("failure_count", 0)
            avg_duration = None
            if total_runs > 0 and stats.get("total_duration_ms"):
                avg_duration = stats["total_duration_ms"] / total_runs

            formatted.append({
                "job_id": job_id,
                "job_name": task_info.get("name", job_id),
                "owner": task_info.get("owner"),
                "category": task_info.get("category"),
                "success_count": stats.get("success_count", 0),
                "failure_count": stats.get("failure_count", 0),
                "total_runs": total_runs,
                "last_duration_ms": stats.get("last_duration_ms"),
                "avg_duration_ms": avg_duration,
                "total_duration_ms": stats.get("total_duration_ms"),
                "last_status": stats.get("last_status"),
                "last_timestamp": stats.get("last_timestamp"),
                # Statistics from history
                "p50_duration_ms": job_stats.get("p50_duration_ms"),
                "p95_duration_ms": job_stats.get("p95_duration_ms"),
                "p99_duration_ms": job_stats.get("p99_duration_ms"),
                "min_duration_ms": job_stats.get("min_duration_ms"),
                "max_duration_ms": job_stats.get("max_duration_ms"),
                "sample_count": job_stats.get("sample_count", 0),
            })

        notification_channels = []
        for channel, stats in notification_snapshot.items():
            notification_channels.append({
                "channel": channel,
                "success_count": stats.get("success_count", 0),
                "failure_count": stats.get("failure_count", 0),
            })

        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(formatted),
                "metrics": formatted,
                "notification_channels": notification_channels
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调度指标失败: {str(e)}")


@router.get("/metrics/prometheus")
def get_scheduler_metrics_prometheus(
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    获取调度器指标（Prometheus 格式）
    返回 Prometheus 文本格式的指标，可用于 Prometheus 抓取
    """
    try:
        from app.utils.scheduler_config import SCHEDULER_TASKS
        from app.utils.scheduler_metrics import (
            get_metrics_snapshot,
            get_metrics_statistics,
        )

        snapshot = get_metrics_snapshot()
        statistics = get_metrics_statistics()
        task_metadata = {task["id"]: task for task in SCHEDULER_TASKS}
        job_snapshot = snapshot.get("jobs", {})
        notification_snapshot = snapshot.get("notifications", {})

        lines = []

        # Counter metrics: success_count, failure_count
        for job_id, stats in job_snapshot.items():
            task_info = task_metadata.get(job_id, {})
            job_name = task_info.get("name", job_id).replace('"', '\\"')
            owner = task_info.get("owner", "unknown").replace('"', '\\"')
            category = task_info.get("category", "unknown").replace('"', '\\"')

            labels = f'job_id="{job_id}",job_name="{job_name}",owner="{owner}",category="{category}"'

            lines.append(f'scheduler_job_success_total{{{labels}}} {stats.get("success_count", 0)}')
            lines.append(f'scheduler_job_failure_total{{{labels}}} {stats.get("failure_count", 0)}')

            # Gauge metrics: last duration, last run timestamp
            last_duration = stats.get("last_duration_ms", 0)
            lines.append(f'scheduler_job_last_duration_ms{{{labels}}} {last_duration}')

            # Last run timestamp (Unix timestamp in seconds)
            last_timestamp = stats.get("last_timestamp")
            if last_timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
                    timestamp_seconds = int(dt.timestamp())
                    lines.append(
                        f'scheduler_job_last_run_timestamp{{{labels}}} {timestamp_seconds}'
                    )
                except Exception:
                    logger.debug("解析调度任务 last_timestamp 失败，已忽略", exc_info=True)

        # Histogram-like metrics: avg, p50, p95, p99
        for job_id, stats in statistics.items():
            if stats.get("sample_count", 0) == 0:
                continue

            task_info = task_metadata.get(job_id, {})
            job_name = task_info.get("name", job_id).replace('"', '\\"')
            owner = task_info.get("owner", "unknown").replace('"', '\\"')
            category = task_info.get("category", "unknown").replace('"', '\\"')

            labels = f'job_id="{job_id}",job_name="{job_name}",owner="{owner}",category="{category}"'

            if stats.get("avg_duration_ms") is not None:
                lines.append(f'scheduler_job_duration_avg_ms{{{labels}}} {stats["avg_duration_ms"]:.2f}')
            if stats.get("p50_duration_ms") is not None:
                lines.append(f'scheduler_job_duration_p50_ms{{{labels}}} {stats["p50_duration_ms"]:.2f}')
            if stats.get("p95_duration_ms") is not None:
                lines.append(f'scheduler_job_duration_p95_ms{{{labels}}} {stats["p95_duration_ms"]:.2f}')
            if stats.get("p99_duration_ms") is not None:
                lines.append(f'scheduler_job_duration_p99_ms{{{labels}}} {stats["p99_duration_ms"]:.2f}')
            if stats.get("min_duration_ms") is not None:
                lines.append(f'scheduler_job_duration_min_ms{{{labels}}} {stats["min_duration_ms"]:.2f}')
            if stats.get("max_duration_ms") is not None:
                lines.append(f'scheduler_job_duration_max_ms{{{labels}}} {stats["max_duration_ms"]:.2f}')

        # Notification channel counters
        for channel, stats in notification_snapshot.items():
            labels = f'channel="{channel}"'
            lines.append(f'scheduler_notification_success_total{{{labels}}} {stats.get("success_count", 0)}')
            lines.append(f'scheduler_notification_failure_total{{{labels}}} {stats.get("failure_count", 0)}')

        # Add a comment header
        prometheus_text = "# HELP scheduler_job_success_total Total number of successful job runs\n"
        prometheus_text += "# TYPE scheduler_job_success_total counter\n"
        prometheus_text += "# HELP scheduler_job_failure_total Total number of failed job runs\n"
        prometheus_text += "# TYPE scheduler_job_failure_total counter\n"
        prometheus_text += "# HELP scheduler_job_last_duration_ms Duration of the last job run in milliseconds\n"
        prometheus_text += "# TYPE scheduler_job_last_duration_ms gauge\n"
        prometheus_text += "# HELP scheduler_job_last_run_timestamp Unix timestamp of the last job run\n"
        prometheus_text += "# TYPE scheduler_job_last_run_timestamp gauge\n"
        prometheus_text += "# HELP scheduler_job_duration_avg_ms Average duration of job runs in milliseconds\n"
        prometheus_text += "# TYPE scheduler_job_duration_avg_ms gauge\n"
        prometheus_text += "# HELP scheduler_job_duration_p50_ms P50 duration of job runs in milliseconds\n"
        prometheus_text += "# TYPE scheduler_job_duration_p50_ms gauge\n"
        prometheus_text += "# HELP scheduler_job_duration_p95_ms P95 duration of job runs in milliseconds\n"
        prometheus_text += "# TYPE scheduler_job_duration_p95_ms gauge\n"
        prometheus_text += "# HELP scheduler_job_duration_p99_ms P99 duration of job runs in milliseconds\n"
        prometheus_text += "# TYPE scheduler_job_duration_p99_ms gauge\n"
        prometheus_text += "# HELP scheduler_notification_success_total Successful alert notifications per channel\n"
        prometheus_text += "# TYPE scheduler_notification_success_total counter\n"
        prometheus_text += "# HELP scheduler_notification_failure_total Failed alert notifications per channel\n"
        prometheus_text += "# TYPE scheduler_notification_failure_total counter\n"
        prometheus_text += "\n".join(lines)

        return Response(
            content=prometheus_text,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Prometheus 指标失败: {str(e)}")
