# -*- coding: utf-8 -*-
"""
定时任务调度器
使用 APScheduler 管理所有后台定时任务
"""

import json
import logging
import time
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Callable, Dict, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings  # noqa: F401
from app.models.base import get_db_session  # noqa: F401
from app.utils.scheduler_config import SCHEDULER_TASKS
from app.utils.scheduler_metrics import (
    record_job_failure,
    record_job_success,
)

logger = logging.getLogger(__name__)

# 配置任务存储和执行器
jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': ThreadPoolExecutor(5)
}

job_defaults = {
    'coalesce': True,  # 如果任务堆积，只执行一次
    'max_instances': 1,  # 同一任务最多1个实例
    'misfire_grace_time': 300  # 错过执行时间后5分钟内仍可执行
}

# 创建调度器
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Shanghai'
)


def job_listener(event):
    """任务执行监听器"""
    payload = {
        "job_id": event.job_id,
        "jobstore": event.jobstore,
        "scheduled_time": event.scheduled_run_time.isoformat() if event.scheduled_run_time else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if event.exception:
        payload["status"] = "failed"
        payload["error"] = str(event.exception)
        logger.error(f"[scheduler] {json.dumps(payload, ensure_ascii=False)}")
    else:
        payload["status"] = "success"
        logger.info(f"[scheduler] {json.dumps(payload, ensure_ascii=False)}")


def _resolve_callable(task: Dict[str, Any]) -> Callable[..., Any]:
    module = import_module(task["module"])
    return getattr(module, task["callable"])


def _wrap_job_callable(func: Callable[..., Any], task: Dict[str, Any]) -> Callable[..., Any]:
    """Wrap actual task function to emit structured start/end logs with duration."""
    task_context = {
        "job_id": task["id"],
        "job_name": task["name"],
        "owner": task.get("owner"),
        "category": task.get("category"),
    }

    def _job_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(
            "[scheduler] "
            + json.dumps(
                {
                    **task_context,
                    "event": "job_run_start",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
            )
        )
        try:
            result = func(*args, **kwargs)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(
                "[scheduler] "
                + json.dumps(
                    {
                        **task_context,
                        "event": "job_run_success",
                        "duration_ms": duration_ms,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    ensure_ascii=False,
                )
            )
            record_job_success(task["id"], duration_ms, datetime.now(timezone.utc).isoformat())
            return result
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "[scheduler] "
                + json.dumps(
                    {
                        **task_context,
                        "event": "job_run_failed",
                        "duration_ms": duration_ms,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
            record_job_failure(task["id"], duration_ms, datetime.now(timezone.utc).isoformat())
            raise

    return _job_wrapper


def _load_task_config_from_db(task_id: str) -> Optional[Dict[str, Any]]:
    """从数据库加载任务配置"""
    try:
        from app.models.base import get_db_session
        from app.models.scheduler_config import SchedulerTaskConfig

        with get_db_session() as db:
            config = db.query(SchedulerTaskConfig).filter(
                SchedulerTaskConfig.task_id == task_id,
                SchedulerTaskConfig.is_enabled
            ).first()

            if config:
                # JSONType会自动处理JSON序列化/反序列化
                cron_config = config.cron_config if config.cron_config else {}
                return {
                    "enabled": config.is_enabled,
                    "cron": cron_config
                }
    except Exception as e:
        logger.warning(f"从数据库加载任务配置失败 ({task_id}): {str(e)}")
    return None


def init_scheduler():
    """初始化并启动调度器"""
    # 注册事件监听器
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    job_count = 0
    db_config_count = 0

    for task in SCHEDULER_TASKS:
        task_id = task["id"]

        # 优先从数据库读取配置
        db_config = _load_task_config_from_db(task_id)

        if db_config:
            # 使用数据库配置
            if not db_config.get("enabled", True):
                logger.info(f"跳过未启用的调度任务（数据库配置）：{task_id}")
                continue
            cron_config = db_config.get("cron", task.get("cron", {}))
            db_config_count += 1
        else:
            # 使用默认配置（scheduler_config.py）
            if not task.get("enabled", True):
                logger.info(f"跳过未启用的调度任务（默认配置）：{task_id}")
                continue
            cron_config = task.get("cron", {})

        try:
            base_callable = _resolve_callable(task)
            job_callable = _wrap_job_callable(base_callable, task)
        except Exception as exc:
            logger.error(f"加载调度任务 {task_id} 失败: {exc}")
            continue

        try:
            scheduler.add_job(
                job_callable,
                "cron",
                id=task_id,
                name=task["name"],
                replace_existing=True,
                **cron_config,
            )
            job_count += 1
        except Exception as exc:
            logger.error(f"注册调度任务 {task_id} 失败: {exc}")

    # 启动调度器
    scheduler.start()
    logger.info(
        f"定时任务调度器已启动（包含{job_count}个预警/定时服务，"
        f"其中{db_config_count}个使用数据库配置）"
    )

    return scheduler


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")


# 注意：应用启动和关闭的钩子在 app/main.py 中定义
