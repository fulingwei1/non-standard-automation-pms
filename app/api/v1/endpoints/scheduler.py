# -*- coding: utf-8 -*-
"""
调度器管理API端点
提供调度器状态查询、任务管理等功能
"""

from typing import Any, List, Optional
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.scheduler_config import SchedulerTaskConfig
from app.schemas.common import ResponseModel
from app.schemas.scheduler_config import (
    SchedulerTaskConfigResponse,
    SchedulerTaskConfigUpdate,
    SchedulerTaskConfigListResponse,
    SchedulerTaskConfigSyncRequest,
)

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
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")

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


# ==================== 定时服务配置管理 ====================

@router.get("/configs", response_model=ResponseModel)
def get_task_configs(
    category: Optional[str] = Query(None, description="按分类筛选"),
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取所有定时任务配置列表
    """
    try:
        # 确保数据库会话有效
        if not db:
            raise HTTPException(status_code=500, detail="数据库连接失败")
        
        query = db.query(SchedulerTaskConfig)
        
        if category:
            query = query.filter(SchedulerTaskConfig.category == category)
        if enabled is not None:
            query = query.filter(SchedulerTaskConfig.is_enabled == enabled)
        
        configs = query.order_by(SchedulerTaskConfig.category, SchedulerTaskConfig.task_name).all()
        
        # 安全地处理 JSON 字段
        items = []
        for config in configs:
            try:
                # 处理 cron_config（JSONType 应该已经处理，但为了安全起见再次检查）
                cron_config = config.cron_config
                if cron_config is None:
                    cron_config = {}
                elif isinstance(cron_config, str):
                    try:
                        cron_config = json.loads(cron_config)
                    except (json.JSONDecodeError, TypeError):
                        cron_config = {}
                
                # 处理 dependencies_tables
                dependencies_tables = config.dependencies_tables
                if dependencies_tables is None:
                    dependencies_tables = []
                elif isinstance(dependencies_tables, str):
                    try:
                        dependencies_tables = json.loads(dependencies_tables)
                    except (json.JSONDecodeError, TypeError):
                        dependencies_tables = []
                
                # 处理 sla_config
                sla_config = config.sla_config
                if sla_config is None:
                    sla_config = {}
                elif isinstance(sla_config, str):
                    try:
                        sla_config = json.loads(sla_config)
                    except (json.JSONDecodeError, TypeError):
                        sla_config = {}
                
                items.append({
                    "id": config.id,
                    "task_id": config.task_id,
                    "task_name": config.task_name,
                    "module": config.module,
                    "callable_name": config.callable_name,
                    "owner": config.owner,
                    "category": config.category,
                    "description": config.description,
                    "is_enabled": config.is_enabled,
                    "cron_config": cron_config,
                    "dependencies_tables": dependencies_tables,
                    "risk_level": config.risk_level,
                    "sla_config": sla_config,
                    "updated_by": config.updated_by,
                    "created_at": config.created_at.isoformat() if config.created_at else None,
                    "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                })
            except Exception as config_error:
                # 如果某个配置项处理失败，记录错误但继续处理其他项
                logger = logging.getLogger(__name__)
                logger.error(f"处理配置项 {config.task_id} 失败: {config_error}", exc_info=True)
                continue
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(items),
                "items": items
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"获取任务配置列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务配置列表失败: {str(e)}")


@router.get("/configs/{task_id}", response_model=ResponseModel)
def get_task_config(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取指定任务的配置
    """
    try:
        config = db.query(SchedulerTaskConfig).filter(
            SchedulerTaskConfig.task_id == task_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"任务配置 {task_id} 不存在")
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "id": config.id,
                "task_id": config.task_id,
                "task_name": config.task_name,
                "module": config.module,
                "callable_name": config.callable_name,
                "owner": config.owner,
                "category": config.category,
                "description": config.description,
                "is_enabled": config.is_enabled,
                "cron_config": config.cron_config if config.cron_config else {},
                "dependencies_tables": config.dependencies_tables if config.dependencies_tables else [],
                "risk_level": config.risk_level,
                "sla_config": config.sla_config if config.sla_config else {},
                "updated_by": config.updated_by,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务配置失败: {str(e)}")


@router.put("/configs/{task_id}", response_model=ResponseModel)
def update_task_config(
    task_id: str,
    config_update: SchedulerTaskConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    更新定时任务配置（频率、启用状态等）
    注意：需要管理员权限
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        config = db.query(SchedulerTaskConfig).filter(
            SchedulerTaskConfig.task_id == task_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"任务配置 {task_id} 不存在")
        
        # 更新配置
        if config_update.is_enabled is not None:
            config.is_enabled = config_update.is_enabled
        if config_update.cron_config is not None:
            config.cron_config = config_update.cron_config
        config.updated_by = current_user.id
        
        db.commit()
        
        # 动态更新调度器中的任务
        try:
            from app.utils.scheduler import scheduler
            job = scheduler.get_job(task_id)
            if job:
                # 更新任务的Cron配置
                if config_update.cron_config:
                    scheduler.reschedule_job(
                        task_id,
                        trigger='cron',
                        **config_update.cron_config
                    )
                # 启用/禁用任务
                if config_update.is_enabled is not None:
                    if config_update.is_enabled:
                        scheduler.resume_job(task_id)
                    else:
                        scheduler.pause_job(task_id)
        except Exception as scheduler_err:
            # 调度器更新失败不影响数据库更新
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"更新调度器任务失败: {str(scheduler_err)}")
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "task_id": task_id,
                "message": "配置已更新"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务配置失败: {str(e)}")


@router.post("/configs/sync", response_model=ResponseModel)
def sync_task_configs(
    sync_request: SchedulerTaskConfigSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    从 scheduler_config.py 同步任务配置到数据库
    用于初始化或更新配置
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        from app.utils.scheduler_config import SCHEDULER_TASKS
        
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for task in SCHEDULER_TASKS:
            config = db.query(SchedulerTaskConfig).filter(
                SchedulerTaskConfig.task_id == task["id"]
            ).first()
            
            # 准备配置数据
            cron_config = task.get("cron", {})
            dependencies_tables = task.get("dependencies_tables", [])
            sla_config = task.get("sla", {})
            
            config_data = {
                "task_id": task["id"],
                "task_name": task["name"],
                "module": task["module"],
                "callable_name": task["callable"],
                "owner": task.get("owner"),
                "category": task.get("category"),
                "description": task.get("description"),
                "is_enabled": task.get("enabled", True),
                "cron_config": cron_config,
                "dependencies_tables": dependencies_tables if dependencies_tables else None,
                "risk_level": task.get("risk_level"),
                "sla_config": sla_config if sla_config else None,
                "updated_by": current_user.id,
            }
            
            if config:
                # 更新现有配置
                if sync_request.force:
                    for key, value in config_data.items():
                        if key != "task_id":  # 不更新task_id
                            setattr(config, key, value)
                    updated_count += 1
            else:
                # 创建新配置
                config = SchedulerTaskConfig(**config_data)
                db.add(config)
                created_count += 1
            
            synced_count += 1
        
        db.commit()
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "synced_count": synced_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "message": f"成功同步 {synced_count} 个任务配置（新建 {created_count} 个，更新 {updated_count} 个）"
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步任务配置失败: {str(e)}")
