# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 自动化处理服务
包含：进度预测自动应用、依赖巡检自动处理
"""

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.progress import ProgressLog, Task, TaskDependency
from app.models.project import Project
from app.schemas.progress import DependencyIssue, TaskForecastItem
from app.services.sales_reminder import create_notification

logger = logging.getLogger(__name__)


class ProgressAutoService:
    """进度跟踪自动化服务"""

    def __init__(self, db: Session):
        self.db = db

    def apply_forecast_to_tasks(
        self,
        project_id: int,
        forecast_items: List[TaskForecastItem],
        auto_block: bool = False,
        delay_threshold: int = 3
    ) -> Dict[str, any]:
        """
        将进度预测结果自动应用到任务

        Args:
            project_id: 项目ID
            forecast_items: 预测结果列表
            auto_block: 是否自动阻塞延迟任务
            delay_threshold: 延迟阈值（天数），超过此天数的任务会被标记

        Returns:
            处理结果统计
        """
        logger.info(f"开始应用进度预测到项目 {project_id} 的任务")

        task_map = {item.task_id: item for item in forecast_items}
        task_ids = list(task_map.keys())

        # 获取所有任务
        tasks = (
            self.db.query(Task)
            .filter(Task.id.in_(task_ids))
            .all()
        )

        stats = {
            "total": len(tasks),
            "blocked": 0,
            "risk_tagged": 0,
            "deadline_updated": 0,
            "notifications_sent": 0,
            "skipped": 0
        }

        today = date.today()

        for task in tasks:
            forecast = task_map.get(task.id)
            if not forecast:
                continue

            # 1. 自动阻塞严重延迟的任务
            if auto_block and forecast.delay_days and forecast.delay_days > delay_threshold:
                if task.status != "DONE" and task.status != "CANCELLED":
                    task.status = "BLOCKED"
                    task.block_reason = f"预测延迟 {forecast.delay_days} 天，超过阈值 {delay_threshold} 天"
                    stats["blocked"] += 1
                    logger.info(f"任务 {task.task_name} (ID:{task.id}) 已自动阻塞")

            # 2. 为高风险任务添加标签（如果任务有标签字段）
            if forecast.critical and forecast.status == "Delayed":
                # 如果任务有 tags 字段，可以添加风险标签
                # 这里简化处理，创建进度日志记录
                if task.status != "BLOCKED":
                    progress_log = ProgressLog(
                        task_id=task.id,
                        progress_percent=task.progress_percent or 0,
                        update_note=f"高风险预警：预测延迟 {forecast.delay_days} 天，请关注",
                        updated_by=0  # 系统自动
                    )
                    self.db.add(progress_log)
                    stats["risk_tagged"] += 1

            # 3. 更新任务计划截止时间（如果有偏差）
            if forecast.delay_days and forecast.delay_days > 0:
                # 可以选择更新任务的计划结束时间
                # 这里记录到进度日志中，不做实际更新，避免覆盖原计划
                pass

        self.db.commit()
        logger.info(f"进度预测应用完成: {stats}")

        return stats

    def auto_fix_dependency_issues(
        self,
        project_id: int,
        issues: List[DependencyIssue],
        auto_fix_timing: bool = True,
        auto_fix_missing: bool = False
    ) -> Dict[str, any]:
        """
        自动修复依赖问题

        Args:
            project_id: 项目ID
            issues: 依赖问题列表
            auto_fix_timing: 是否自动修复时序冲突
            auto_fix_missing: 是否自动移除缺失依赖

        Returns:
            修复结果统计
        """
        logger.info(f"开始自动修复项目 {project_id} 的依赖问题")

        stats = {
            "total_issues": len(issues),
            "timing_fixed": 0,
            "missing_removed": 0,
            "cycles_skipped": 0,
            "errors": 0
        }

        for issue in issues:
            try:
                # 跳过循环依赖，需要人工处理
                if issue.issue_type == "CYCLE":
                    stats["cycles_skipped"] += 1
                    continue

                # 自动修复时序冲突
                if auto_fix_timing and issue.issue_type == "TIMING_CONFLICT":
                    self._fix_timing_conflict(issue)
                    stats["timing_fixed"] += 1

                # 自动移除缺失依赖
                if auto_fix_missing and issue.issue_type == "MISSING_PREDECESSOR":
                    self._remove_missing_dependency(issue)
                    stats["missing_removed"] += 1

            except Exception as e:
                logger.error(f"修复依赖问题失败: {issue.detail}, 错误: {str(e)}")
                stats["errors"] += 1

        self.db.commit()
        logger.info(f"依赖问题自动修复完成: {stats}")

        return stats

    def _fix_timing_conflict(self, issue: DependencyIssue) -> bool:
        """
        修复时序冲突（自动调整任务日期）

        Returns:
            是否修复成功
        """
        task = self.db.query(Task).filter(Task.id == issue.task_id).first()
        if not task:
            return False

        # 查找该任务的所有前置依赖
        dependencies = (
            self.db.query(TaskDependency)
            .filter(TaskDependency.task_id == issue.task_id)
            .all()
        )

        if not dependencies:
            return False

        # 找到最晚的前置任务完成时间
        latest_pred_finish = None

        for dep in dependencies:
            pred_task = self.db.query(Task).filter(Task.id == dep.depends_on_task_id).first()
            if not pred_task:
                continue

            pred_finish = pred_task.actual_end or pred_task.plan_end
            if pred_finish:
                if latest_pred_finish is None or pred_finish > latest_pred_finish:
                    latest_pred_finish = pred_finish

        # 调整任务开始时间
        if latest_pred_finish:
            lag_days = dependencies[0].lag_days or 0
            new_start = latest_pred_finish + timedelta(days=lag_days)

            # 计算任务持续时间
            original_duration = 0
            if task.plan_start and task.plan_end:
                original_duration = (task.plan_end - task.plan_start).days

            # 更新任务日期
            old_start = task.plan_start
            old_end = task.plan_end
            task.plan_start = new_start
            if original_duration > 0:
                task.plan_end = new_start + timedelta(days=original_duration)

            # 创建进度日志
            progress_log = ProgressLog(
                task_id=task.id,
                progress_percent=task.progress_percent or 0,
                update_note=f"系统自动调整计划时间：原计划 {old_start} - {old_end}，新计划 {new_start} - {task.plan_end}",
                updated_by=0
            )
            self.db.add(progress_log)

            logger.info(f"任务 {task.task_name} 计划时间已调整: {old_start} -> {new_start}")
            return True

        return False

    def _remove_missing_dependency(self, issue: DependencyIssue) -> bool:
        """
        移除缺失的依赖关系

        Returns:
            是否移除成功
        """
        dependencies = (
            self.db.query(TaskDependency)
            .filter(TaskDependency.task_id == issue.task_id)
            .all()
        )

        removed_count = 0
        for dep in dependencies:
            # 检查依赖的任务是否存在
            pred_task = self.db.query(Task).filter(Task.id == dep.depends_on_task_id).first()
            if not pred_task:
                # 记录日志并删除依赖
                progress_log = ProgressLog(
                    task_id=issue.task_id,
                    progress_percent=self._db.query(Task).filter(Task.id == issue.task_id).first().progress_percent or 0 if self._db.query(Task).filter(Task.id == issue.task_id).first() else 0,
                    update_note=f"系统自动移除缺失依赖: 任务ID {dep.depends_on_task_id}",
                    updated_by=0
                )
                self.db.add(progress_log)
                self.db.delete(dep)
                removed_count += 1

        return removed_count > 0

    def send_forecast_notifications(
        self,
        project_id: int,
        project: Project,
        forecast_items: List[TaskForecastItem]
    ) -> Dict[str, any]:
        """
        发送进度预测通知

        Args:
            project_id: 项目ID
            project: 项目对象
            forecast_items: 预测结果列表

        Returns:
            通知发送统计
        """
        logger.info(f"开始发送项目 {project_id} 的进度预测通知")

        # 筛选高风险任务
        critical_tasks = [
            item for item in forecast_items
            if item.critical and item.delay_days and item.delay_days > 0
        ]

        if not critical_tasks:
            return {"total": 0, "sent": 0, "skipped": "no_critical_tasks"}

        # 收集通知接收人
        recipients = set()
        if project.pm_id:
            recipients.add(project.pm_id)

        for item in critical_tasks:
            task = self.db.query(Task).filter(Task.id == item.task_id).first()
            if task and task.owner_id:
                recipients.add(task.owner_id)

        # 避免重复通知（6小时内相同类型的通知）
        window_start = datetime.now(timezone.utc) - timedelta(hours=6)
        notification_sent = 0

        for user_id in recipients:
            existing = (
                self.db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.notification_type == "PROGRESS_FORECAST_ALERT",
                    Notification.source_type == "project",
                    Notification.source_id == project_id,
                    Notification.created_at >= window_start,
                )
                .first()
            )

            if existing:
                continue

            # 创建通知
            critical_count = len(critical_tasks)
            max_delay = max(item.delay_days or 0 for item in critical_tasks)

            create_notification(
                db=self.db,
                user_id=user_id,
                notification_type="PROGRESS_FORECAST_ALERT",
                title=f"项目「{project.project_name}」进度预警",
                content=f"检测到 {critical_count} 个任务存在延期风险，最长预计延迟 {max_delay} 天，请关注任务进度。",
                source_type="project",
                source_id=project_id,
                link_url=f"/projects/{project_id}/progress-forecast",
                priority="HIGH" if max_delay > 7 else "MEDIUM",
                extra_data={
                    "critical_task_count": critical_count,
                    "max_delay_days": max_delay,
                    "task_ids": [item.task_id for item in critical_tasks]
                }
            )
            notification_sent += 1

        self.db.commit()
        logger.info(f"进度预测通知发送完成: {notification_sent} 个用户")

        return {
            "total": len(recipients),
            "sent": notification_sent,
            "critical_task_count": len(critical_tasks)
        }

    def run_auto_processing(
        self,
        project_id: int,
        options: Dict[str, any] = None
    ) -> Dict[str, any]:
        """
        执行完整的自动处理流程（预测应用 + 依赖修复 + 通知）

        Args:
            project_id: 项目ID
            options: 处理选项
                - auto_block: 是否自动阻塞延迟任务
                - delay_threshold: 延迟阈值
                - auto_fix_timing: 是否自动修复时序冲突
                - auto_fix_missing: 是否自动移除缺失依赖
                - send_notifications: 是否发送通知

        Returns:
            完整的处理结果
        """
        if options is None:
            options = {
                "auto_block": False,  # 默认不自动阻塞
                "delay_threshold": 7,
                "auto_fix_timing": False,  # 默认不自动修复
                "auto_fix_missing": True,
                "send_notifications": True
            }

        logger.info(f"开始执行项目 {project_id} 的自动处理流程")

        result = {
            "project_id": project_id,
            "forecast_stats": {},
            "dependency_stats": {},
            "notification_stats": {},
            "success": False
        }

        try:
            # 1. 获取项目信息
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise Exception("项目不存在")

            # 2. 获取所有任务并计算预测
            tasks = (
                self.db.query(Task)
                .options(Task.progress_logs)
                .filter(Task.project_id == project_id)
                .all()
            )

            if not tasks:
                logger.info(f"项目 {project_id} 没有任务，跳过自动处理")
                result["success"] = True
                return result

            # 导入预测函数
            from app.api.v1.endpoints.progress.utils import (
                _analyze_dependency_graph,
                _build_project_forecast,
            )

            # 3. 计算进度预测
            forecast = _build_project_forecast(project, tasks)
            result["forecast_stats"] = {
                "task_count": len(tasks),
                "current_progress": forecast.current_progress,
                "predicted_delay_days": forecast.predicted_delay_days,
                "critical_task_count": len([t for t in forecast.tasks if t.critical])
            }

            # 4. 应用预测到任务
            if options["auto_block"]:
                forecast_stats = self.apply_forecast_to_tasks(
                    project_id=project_id,
                    forecast_items=forecast.tasks,
                    auto_block=options["auto_block"],
                    delay_threshold=options["delay_threshold"]
                )
                result["forecast_stats"]["applied"] = forecast_stats
            else:
                result["forecast_stats"]["applied"] = {"skipped": "auto_block_disabled"}

            # 5. 检查依赖关系
            task_map = {task.id: task for task in tasks}
            dependencies = (
                self.db.query(TaskDependency)
                .filter(TaskDependency.task_id.in_(task_map.keys()))
                .all()
            )

            cycle_paths, issues = _analyze_dependency_graph(task_map, dependencies)
            result["dependency_stats"] = {
                "cycle_count": len(cycle_paths),
                "issue_count": len(issues)
            }

            # 6. 自动修复依赖问题
            if options["auto_fix_timing"] or options["auto_fix_missing"]:
                dep_stats = self.auto_fix_dependency_issues(
                    project_id=project_id,
                    issues=issues,
                    auto_fix_timing=options["auto_fix_timing"],
                    auto_fix_missing=options["auto_fix_missing"]
                )
                result["dependency_stats"]["fixed"] = dep_stats
            else:
                result["dependency_stats"]["fixed"] = {"skipped": "auto_fix_disabled"}

            # 7. 发送通知
            if options["send_notifications"]:
                # 发送预测通知
                notify_stats = self.send_forecast_notifications(
                    project_id=project_id,
                    project=project,
                    forecast_items=forecast.tasks
                )
                result["notification_stats"]["forecast"] = notify_stats

                # 发送依赖风险通知（如果有严重问题）
                high_issues = [i for i in issues if (i.severity or "").upper() in ["HIGH", "URGENT"]]
                if high_issues or cycle_paths:
                    from app.api.v1.endpoints.progress.utils import (
                        _notify_dependency_alerts,
                    )
                    _notify_dependency_alerts(
                        db=self.db,
                        project=project,
                        task_map=task_map,
                        cycle_paths=cycle_paths,
                        issues=issues
                    )
                    result["notification_stats"]["dependency"] = {
                        "sent": len(high_issues) > 0 or len(cycle_paths) > 0
                    }
            else:
                result["notification_stats"]["forecast"] = {"skipped": "notifications_disabled"}

            result["success"] = True
            logger.info(f"项目 {project_id} 自动处理流程完成")

        except Exception as e:
            logger.error(f"项目 {project_id} 自动处理流程失败: {str(e)}", exc_info=True)
            result["error"] = str(e)

        return result
