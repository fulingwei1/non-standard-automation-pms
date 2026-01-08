# -*- coding: utf-8 -*-
"""
调度器管理API端点
提供调度器状态查询、任务管理等功能
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/status", response_model=ResponseModel)
def get_scheduler_status(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取调度器状态
    返回调度器运行状态和已注册的任务列表
    """
    try:
        from app.utils.scheduler import scheduler
        
        jobs = scheduler.get_jobs()
        
        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger) if job.trigger else None,
            })
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "running": scheduler.running,
                "job_count": len(jobs),
                "jobs": job_list
            }
        )
    except ImportError:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "running": False,
                "job_count": 0,
                "jobs": [],
                "error": "APScheduler未安装"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")


@router.get("/jobs", response_model=ResponseModel)
def get_scheduler_jobs(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取所有已注册的任务列表
    """
    try:
        from app.utils.scheduler import scheduler
        
        jobs = scheduler.get_jobs()
        
        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger) if job.trigger else None,
                "func": job.func.__name__ if job.func else None,
            })
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(jobs),
                "jobs": job_list
            }
        )
    except ImportError:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": 0,
                "jobs": [],
                "error": "APScheduler未安装"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/metrics", response_model=ResponseModel)
def get_scheduler_metrics(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取调度任务运行指标（成功/失败次数、耗时、统计信息）
    包含平均值、P50、P95、P99等聚合数据
    """
    try:
        from app.utils.scheduler_metrics import get_metrics_snapshot, get_metrics_statistics
        from app.utils.scheduler_config import SCHEDULER_TASKS
        
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


@router.post("/jobs/{job_id}/trigger", response_model=ResponseModel)
def trigger_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    手动触发指定任务
    注意：需要管理员权限
    """
    # TODO: 添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        from app.utils.scheduler import scheduler
        
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"任务 {job_id} 不存在")
        
        # 手动触发任务
        job.modify(next_run_time=None)
        scheduler.wakeup()
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "job_id": job_id,
                "job_name": job.name,
                "message": "任务已触发"
            }
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="APScheduler未安装")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发任务失败: {str(e)}")


@router.get("/metrics/prometheus")
def get_scheduler_metrics_prometheus(
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    获取调度器指标（Prometheus 格式）
    返回 Prometheus 文本格式的指标，可用于 Prometheus 抓取
    """
    try:
        from app.utils.scheduler_metrics import get_metrics_snapshot, get_metrics_statistics
        from app.utils.scheduler_config import SCHEDULER_TASKS
        
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
                    dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                    timestamp_seconds = int(dt.timestamp())
                    lines.append(f'scheduler_job_last_run_timestamp{{{labels}}} {timestamp_seconds}')
                except Exception:
                    pass
        
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


@router.get("/services/list", response_model=ResponseModel)
def list_all_services(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    列出所有可用的服务函数
    包含完整的元数据：依赖表、风险级别、SLA 等
    """
    try:
        from app.utils.scheduler_config import SCHEDULER_TASKS
        
        services = []
        for task in SCHEDULER_TASKS:
            services.append({
                "id": task["id"],
                "name": task["name"],
                "module": task["module"],
                "callable": task["callable"],
                "cron": task.get("cron"),
                "owner": task.get("owner"),
                "category": task.get("category"),
                "enabled": task.get("enabled", True),
                "description": task.get("description"),
                "dependencies_tables": task.get("dependencies_tables", []),
                "risk_level": task.get("risk_level", "UNKNOWN"),
                "sla": task.get("sla", {}),
            })
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(services),
                "services": services
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")
