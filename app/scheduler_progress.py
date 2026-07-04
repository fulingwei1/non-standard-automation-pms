# -*- coding: utf-8 -*-
"""
定时任务配置
包含：进度预测自动处理、依赖巡检定时任务
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.dependencies import get_db_session
from app.services.progress_service import ProgressAutoService
from app.utils.scheduler_metrics import record_job_failure, record_job_success

logger = logging.getLogger(__name__)

# 全局调度器
scheduler = BackgroundScheduler()
PROGRESS_AUTO_PROCESSING_JOB_ID = "progress_auto_processing_daily"


def _wrap_progress_job_callable(
    func: Callable[..., Any], job_id: str
) -> Callable[..., Any]:
    """Record second scheduler job runs in the unified scheduler metrics."""

    def _job_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
        except Exception:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            record_job_failure(job_id, duration_ms, datetime.now(timezone.utc).isoformat())
            raise

        duration_ms = round((time.time() - start_time) * 1000, 2)
        record_job_success(job_id, duration_ms, datetime.now(timezone.utc).isoformat())
        return result

    return _job_wrapper


def run_progress_auto_processing_job():
    """
    定时任务：进度预测与依赖巡检自动处理

    执行频率：每天凌晨2点
    处理范围：所有进行中的项目
    """
    logger.info("开始执行进度预测与依赖巡检自动处理任务")

    try:
        with get_db_session() as db:
            from app.models.project import Project
            from app.services.project_status_normalization import project_delivery_scope_expr

            # 查询所有进行中的项目
            in_progress_projects = (
                db.query(Project)
                .filter(project_delivery_scope_expr(Project))
                .all()
            )

            logger.info(f"找到 {len(in_progress_projects)} 个进行中的项目")

            service = ProgressAutoService(db)

            # 默认处理选项
            default_options = {
                "auto_block": False,  # 默认不自动阻塞，只记录预警
                "delay_threshold": 7,  # 7天阈值
                "auto_fix_timing": False,  # 默认不自动修复时序
                "auto_fix_missing": True,  # 自动移除缺失依赖
                "send_notifications": True,  # 发送通知
            }

            success_count = 0
            failed_count = 0
            results = []

            for project in in_progress_projects:
                try:
                    result = service.run_auto_processing(
                        project_id=project.id, options=default_options
                    )

                    if result.get("success"):
                        success_count += 1
                        logger.info(f"项目 {project.project_name} (ID:{project.id}) 自动处理成功")
                    else:
                        failed_count += 1
                        logger.error(
                            f"项目 {project.project_name} (ID:{project.id}) 自动处理失败: "
                            f"{result.get('error', '未知错误')}"
                        )

                    results.append(
                        {
                            "project_id": project.id,
                            "project_name": project.project_name,
                            "success": result.get("success", False),
                        }
                    )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"项目 {project.project_name} (ID:{project.id}) 处理异常: {str(e)}",
                        exc_info=True,
                    )
                    results.append(
                        {
                            "project_id": project.id,
                            "project_name": project.project_name,
                            "success": False,
                            "error": str(e),
                        }
                    )

            logger.info(
                f"进度预测与依赖巡检自动处理任务完成: "
                f"成功 {success_count}, 失败 {failed_count}, 总计 {len(in_progress_projects)}"
            )

    except Exception as e:
        logger.error(f"定时任务执行失败: {str(e)}", exc_info=True)


def start_scheduler():
    """
    启动定时任务调度器
    """
    logger.info("开始启动定时任务调度器")

    try:
        # 添加进度预测与依赖巡检自动处理任务
        # 每天凌晨2点执行
        scheduler.add_job(
            func=_wrap_progress_job_callable(
                run_progress_auto_processing_job, PROGRESS_AUTO_PROCESSING_JOB_ID
            ),
            trigger=CronTrigger(hour=2, minute=0),
            id=PROGRESS_AUTO_PROCESSING_JOB_ID,
            name="进度预测与依赖巡检自动处理（每天凌晨2点）",
            replace_existing=True,
        )

        # 启动调度器
        scheduler.start()

        logger.info("定时任务调度器启动成功")
        logger.info(f"已注册任务数量: {len(scheduler.get_jobs())}")

        # 打印已注册的任务
        for job in scheduler.get_jobs():
            logger.info(f"  - {job.id}: {job.name}")

    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {str(e)}", exc_info=True)


def stop_scheduler():
    """
    停止定时任务调度器
    """
    logger.info("开始停止定时任务调度器")

    if not scheduler.running:
        logger.info("定时任务调度器未运行，跳过停止")
        return

    try:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止定时任务调度器失败: {str(e)}", exc_info=True)
