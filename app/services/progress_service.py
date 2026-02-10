# -*- coding: utf-8 -*-
"""
统一进度服务

整合以下模块的功能:
- progress_aggregation_service.py (进度聚合)
- task_progress_service.py (任务进度更新)
- progress_auto_service.py (自动化处理)

保持原有函数签名不变，确保向后兼容。
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.progress import ProgressLog, Task, TaskDependency
from app.models.project import Project, ProjectStage
from app.models.task_center import TaskUnified
from app.schemas.progress import DependencyIssue, TaskForecastItem
from app.services.sales_reminder import create_notification

logger = logging.getLogger(__name__)


# =============================================================================
# 进度更新 (原 task_progress_service.py)
# =============================================================================

def progress_error_to_http(exc: ValueError) -> HTTPException:
    """将服务层 ValueError 映射为 HTTP 异常"""
    msg = str(exc)
    if "任务不存在" in msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    if "只能更新" in msg or "无权" in msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def apply_task_progress_update(
    task: TaskUnified,
    progress: int,
    updater_id: int,
    *,
    actual_hours: Optional[Decimal] = None,
    reject_completed: bool = True,
    enforce_assignee: bool = True,
) -> None:
    """
    仅应用进度更新字段与状态转换，不负责数据库提交。
    用于单个与批量更新逻辑复用。
    """
    if enforce_assignee and task.assignee_id != updater_id:
        raise ValueError("只能更新分配给自己的任务")

    if reject_completed and task.status in ("COMPLETED", "REJECTED", "CANCELLED"):
        raise ValueError("任务已完成或已被拒绝，无法更新进度")

    if progress < 0 or progress > 100:
        raise ValueError("进度必须在0到100之间")

    # 更新字段
    task.progress = progress
    if actual_hours is not None:
        task.actual_hours = actual_hours
    task.updated_by = updater_id
    task.updated_at = datetime.now()

    # 状态与日期
    if progress > 0 and task.status == "ACCEPTED":
        task.status = "IN_PROGRESS"
        if not task.actual_start_date:
            task.actual_start_date = date.today()

    if progress >= 100:
        task.status = "COMPLETED"
        task.actual_end_date = date.today()


def update_task_progress(
    db: Session,
    task_id: int,
    progress: int,
    updater_id: int,
    *,
    actual_hours: Optional[Decimal] = None,
    progress_note: Optional[str] = None,
    reject_completed: bool = True,
    create_progress_log: bool = True,
    run_aggregation: bool = True,
) -> Tuple[TaskUnified, Dict[str, Any]]:
    """
    更新任务进度（核心逻辑）。

    Args:
        db: 数据库会话
        task_id: 任务 ID
        progress: 进度百分比 0-100
        updater_id: 更新人用户 ID
        actual_hours: 实际工时，可选
        progress_note: 进度说明，可选
        reject_completed: 若 True，已完成任务抛出 ValueError
        create_progress_log: 若 True 且 progress_note 有值，写入进度日志
        run_aggregation: 若 True，聚合到项目/阶段

    Returns:
        (更新后的 TaskUnified, 聚合结果 dict)

    Raises:
        ValueError: 任务不存在、无权限、状态不可更新、进度非法
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise ValueError("任务不存在")

    apply_task_progress_update(
        task,
        progress,
        updater_id,
        actual_hours=actual_hours,
        reject_completed=reject_completed,
        enforce_assignee=True,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    aggregation_result: Dict[str, Any] = {}

    if create_progress_log and progress_note:
        create_progress_log_entry(
            db,
            task_id=task.id,
            progress=progress,
            actual_hours=float(actual_hours) if actual_hours is not None else None,
            note=progress_note,
            updater_id=updater_id,
        )

    if run_aggregation:
        aggregation_result = aggregate_task_progress(db, task.id)

    return task, aggregation_result


# =============================================================================
# 进度聚合 (原 progress_aggregation_service.py)
# =============================================================================

def aggregate_task_progress(db: Session, task_id: int) -> dict:
    """
    任务进度聚合到阶段和项目

    Args:
        db: 数据库会话
        task_id: 任务ID

    Returns:
        dict: 聚合结果
    """
    result = {
        'project_progress_updated': False,
        'stage_progress_updated': False,
        'project_id': None,
        'stage_code': None,
        'new_project_progress': None,
        'new_stage_progress': None
    }

    # 1. 获取任务信息
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task or not task.project_id:
        return result

    project_id = task.project_id
    result['project_id'] = project_id

    # 2. 计算项目整体进度（使用聚合函数优化）
    base_filter = and_(
        TaskUnified.project_id == project_id,
        TaskUnified.is_active == True,
        TaskUnified.status.notin_(['CANCELLED'])
    )

    total_tasks_result = (
        db.query(func.count(TaskUnified.id))
        .filter(base_filter)
        .scalar()
    )

    if total_tasks_result:
        # 使用SQL聚合计算加权平均
        weighted_progress_result = (
            db.query(func.sum(TaskUnified.progress))
            .filter(base_filter)
            .scalar()
        )
        project_progress = round(float(weighted_progress_result or 0) / total_tasks_result, 2)

        # 更新项目进度
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.progress_pct = project_progress
            project.updated_at = datetime.now()
            db.commit()

            result['project_progress_updated'] = True
            result['new_project_progress'] = project_progress

    # 3. 如果任务关联了阶段，计算阶段进度
    if hasattr(task, 'stage') and task.stage:
        stage_code = task.stage
        result['stage_code'] = stage_code

        # 获取该阶段的所有任务（使用聚合函数优化）
        stage_filter = and_(
            TaskUnified.project_id == project_id,
            TaskUnified.stage == stage_code,
            TaskUnified.is_active == True,
            TaskUnified.status.notin_(['CANCELLED'])
        )

        total_stage_tasks_result = (
            db.query(func.count(TaskUnified.id))
            .filter(stage_filter)
            .scalar()
        )

        if total_stage_tasks_result:
            weighted_stage_progress_result = (
                db.query(func.sum(TaskUnified.progress))
                .filter(stage_filter)
                .scalar()
            )
            stage_progress = round(float(weighted_stage_progress_result or 0) / total_stage_tasks_result, 2)

            # 更新阶段进度
            project_stage = db.query(ProjectStage).filter(
                and_(
                    ProjectStage.project_id == project_id,
                    ProjectStage.stage_code == stage_code
                )
            ).first()

            if project_stage:
                project_stage.progress_pct = stage_progress
                project_stage.updated_at = datetime.now()
                db.commit()

                result['stage_progress_updated'] = True
                result['new_stage_progress'] = stage_progress

    # 4. 检查并更新健康度
    _check_and_update_health(db, project_id)

    return result


def _check_and_update_health(db: Session, project_id: int):
    """
    检查并更新项目健康度

    基于以下因素：
    - 延期任务数量
    - 逾期任务数量
    - 整体进度落后情况
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return

    # 使用聚合查询统计任务情况
    active_filter = and_(
        TaskUnified.project_id == project_id,
        TaskUnified.is_active == True,
        TaskUnified.status.notin_(['CANCELLED', 'COMPLETED'])
    )

    total_tasks = (
        db.query(func.count(TaskUnified.id))
        .filter(active_filter)
        .scalar()
    ) or 0

    # 统计延期和逾期任务
    delayed_count = (
        db.query(func.count(TaskUnified.id))
        .filter(and_(active_filter, TaskUnified.is_delayed == True))
        .scalar()
    ) or 0

    overdue_count = (
        db.query(func.count(TaskUnified.id))
        .filter(and_(
            active_filter,
            TaskUnified.deadline < datetime.now()
        ))
        .scalar()
    ) or 0

    # 健康度判断逻辑
    if total_tasks == 0:
        return

    delayed_ratio = delayed_count / total_tasks if total_tasks > 0 else 0
    overdue_ratio = overdue_count / total_tasks if total_tasks > 0 else 0

    # H1: 正常（绿色） - 延期<10%，逾期<5%
    # H2: 有风险（黄色） - 延期10-25%，或逾期5-15%
    # H3: 阻塞（红色） - 延期>25%，或逾期>15%

    new_health = 'H1'  # 默认正常

    if delayed_ratio > 0.25 or overdue_ratio > 0.15:
        new_health = 'H3'  # 阻塞
    elif delayed_ratio > 0.10 or overdue_ratio > 0.05:
        new_health = 'H2'  # 有风险

    # 只有当健康度需要变化时才更新
    if project.health != new_health:
        project.health = new_health
        project.updated_at = datetime.now()
        db.commit()


def create_progress_log_entry(
    db: Session,
    task_id: int,
    progress: int,
    actual_hours: Optional[float],
    note: Optional[str],
    updater_id: int
):
    """
    创建进度日志

    Args:
        db: 数据库会话
        task_id: 任务ID
        progress: 进度百分比
        actual_hours: 实际工时
        note: 进度说明
        updater_id: 更新人ID
    """
    try:
        progress_log = ProgressLog(
            task_id=task_id,
            progress_percent=progress,
            update_note=note or f"进度更新至 {progress}%",
            updated_by=updater_id,
            updated_at=datetime.now()
        )
        db.add(progress_log)
        db.commit()
        db.refresh(progress_log)
        return progress_log
    except Exception as e:
        db.rollback()
        logger.warning(f"Could not create progress log: {e}")
        return None


# 别名，保持兼容性
create_progress_log = create_progress_log_entry


def get_project_progress_summary(db: Session, project_id: int) -> dict:
    """
    获取项目进度汇总

    Args:
        db: 数据库会话
        project_id: 项目ID

    Returns:
        dict: 进度汇总信息
    """
    # 使用聚合查询优化
    base_filter = TaskUnified.project_id == project_id

    # 统计任务总数
    total_tasks = (
        db.query(func.count(TaskUnified.id))
        .filter(and_(base_filter, TaskUnified.status != 'CANCELLED'))
        .scalar()
    ) or 0

    # 按状态聚合
    status_counts = (
        db.query(TaskUnified.status, func.count(TaskUnified.id).label('count'))
        .filter(base_filter)
        .group_by(TaskUnified.status)
        .all()
    )
    status_dict = {status: count for status, count in status_counts}

    completed_tasks = status_dict.get('COMPLETED', 0)
    in_progress_tasks = status_dict.get('IN_PROGRESS', 0)

    # 统计延期任务
    delayed_tasks = (
        db.query(func.count(TaskUnified.id))
        .filter(and_(base_filter, TaskUnified.is_delayed == True))
        .scalar()
    ) or 0

    # 统计逾期任务
    overdue_tasks = (
        db.query(func.count(TaskUnified.id))
        .filter(and_(
            base_filter,
            TaskUnified.deadline < datetime.now(),
            TaskUnified.status.notin_(['COMPLETED', 'CANCELLED'])
        ))
        .scalar()
    ) or 0

    # 计算整体进度
    overall_progress_result = (
        db.query(func.avg(TaskUnified.progress))
        .filter(base_filter)
        .scalar()
    )
    overall_progress = float(overall_progress_result or 0)

    return {
        'project_id': project_id,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'delayed_tasks': delayed_tasks,
        'overdue_tasks': overdue_tasks,
        'overall_progress': round(overall_progress, 2),
        'completion_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
    }


class ProgressAggregationService:
    """
    项目进度聚合服务

    提供基于任务数据的聚合能力，用于快速计算项目整体进度。
    前端和自动化测试都依赖该类，请保持接口稳定。
    """

    @staticmethod
    def aggregate_project_progress(project_id: int, db: Session) -> Dict[str, Any]:
        """
        计算项目整体进度（按任务预估工时加权）

        Args:
            project_id: 项目ID
            db: 数据库会话

        Returns:
            dict: 聚合后的进度指标
        """
        # 使用聚合函数优化查询
        base_filter = and_(
            TaskUnified.project_id == project_id,
            TaskUnified.is_active == True,
            TaskUnified.status.notin_(['CANCELLED'])
        )

        # 统计任务总数
        total_tasks = (
            db.query(func.count(TaskUnified.id))
            .filter(base_filter)
            .scalar()
        ) or 0

        # 按状态聚合
        status_counts = (
            db.query(TaskUnified.status, func.count(TaskUnified.id).label('count'))
            .filter(base_filter)
            .group_by(TaskUnified.status)
            .all()
        )
        status_dict = {status.upper(): count for status, count in status_counts}

        completed_tasks = status_dict.get('COMPLETED', 0)
        in_progress_tasks = status_dict.get('IN_PROGRESS', 0) + status_dict.get('ACCEPTED', 0)
        pending_approval_tasks = status_dict.get('PENDING_APPROVAL', 0)

        # 计算加权平均进度（按预估工时加权）
        total_hours_result = (
            db.query(
                func.sum(
                    case(
                        (TaskUnified.estimated_hours.isnot(None), TaskUnified.estimated_hours),
                        else_=1.0
                    )
                ).label('total_weight')
            )
            .filter(base_filter)
            .scalar()
        ) or 0.0

        weighted_progress_result = (
            db.query(
                func.sum(
                    TaskUnified.progress *
                    case(
                        (TaskUnified.estimated_hours.isnot(None), TaskUnified.estimated_hours),
                        else_=1.0
                    )
                ).label('weighted_sum')
            )
            .filter(base_filter)
            .scalar()
        ) or 0.0

        if total_hours_result > 0:
            overall_progress = weighted_progress_result / total_hours_result
        elif total_tasks > 0:
            avg_progress_result = (
                db.query(func.avg(TaskUnified.progress))
                .filter(base_filter)
                .scalar()
            )
            overall_progress = float(avg_progress_result or 0)
        else:
            overall_progress = 0.0

        # 统计延期和逾期任务
        delayed_tasks = (
            db.query(func.count(TaskUnified.id))
            .filter(and_(base_filter, TaskUnified.is_delayed == True))
            .scalar()
        ) or 0

        overdue_tasks = (
            db.query(func.count(TaskUnified.id))
            .filter(and_(
                base_filter,
                TaskUnified.deadline < datetime.now()
            ))
            .scalar()
        ) or 0

        return {
            "project_id": project_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_approval_tasks": pending_approval_tasks,
            "delayed_tasks": delayed_tasks,
            "overdue_tasks": overdue_tasks,
            "overall_progress": round(overall_progress, 2),
            "calculated_at": datetime.now().isoformat(),
        }


# =============================================================================
# 自动化处理 (原 progress_auto_service.py)
# =============================================================================

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
            delay_threshold: 延迟阈值（天数）

        Returns:
            处理结果统计
        """
        logger.info(f"开始应用进度预测到项目 {project_id} 的任务")

        task_map = {item.task_id: item for item in forecast_items}
        task_ids = list(task_map.keys())

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

            # 2. 为高风险任务添加标签
            if forecast.critical and forecast.status == "Delayed":
                if task.status != "BLOCKED":
                    progress_log = ProgressLog(
                        task_id=task.id,
                        progress_percent=task.progress_percent or 0,
                        update_note=f"高风险预警：预测延迟 {forecast.delay_days} 天，请关注",
                        updated_by=0
                    )
                    self.db.add(progress_log)
                    stats["risk_tagged"] += 1

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
                if issue.issue_type == "CYCLE":
                    stats["cycles_skipped"] += 1
                    continue

                if auto_fix_timing and issue.issue_type == "TIMING_CONFLICT":
                    self._fix_timing_conflict(issue)
                    stats["timing_fixed"] += 1

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
        """修复时序冲突"""
        task = self.db.query(Task).filter(Task.id == issue.task_id).first()
        if not task:
            return False

        dependencies = (
            self.db.query(TaskDependency)
            .filter(TaskDependency.task_id == issue.task_id)
            .all()
        )

        if not dependencies:
            return False

        latest_pred_finish = None

        for dep in dependencies:
            pred_task = self.db.query(Task).filter(Task.id == dep.depends_on_task_id).first()
            if not pred_task:
                continue

            pred_finish = pred_task.actual_end or pred_task.plan_end
            if pred_finish:
                if latest_pred_finish is None or pred_finish > latest_pred_finish:
                    latest_pred_finish = pred_finish

        if latest_pred_finish:
            lag_days = dependencies[0].lag_days or 0
            new_start = latest_pred_finish + timedelta(days=lag_days)

            original_duration = 0
            if task.plan_start and task.plan_end:
                original_duration = (task.plan_end - task.plan_start).days

            old_start = task.plan_start
            old_end = task.plan_end
            task.plan_start = new_start
            if original_duration > 0:
                task.plan_end = new_start + timedelta(days=original_duration)

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
        """移除缺失的依赖关系"""
        dependencies = (
            self.db.query(TaskDependency)
            .filter(TaskDependency.task_id == issue.task_id)
            .all()
        )

        removed_count = 0
        for dep in dependencies:
            pred_task = self.db.query(Task).filter(Task.id == dep.depends_on_task_id).first()
            if not pred_task:
                task = self.db.query(Task).filter(Task.id == issue.task_id).first()
                progress_log = ProgressLog(
                    task_id=issue.task_id,
                    progress_percent=task.progress_percent if task else 0,
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
        """发送进度预测通知"""
        logger.info(f"开始发送项目 {project_id} 的进度预测通知")

        critical_tasks = [
            item for item in forecast_items
            if item.critical and item.delay_days and item.delay_days > 0
        ]

        if not critical_tasks:
            return {"total": 0, "sent": 0, "skipped": "no_critical_tasks"}

        recipients = set()
        if project.pm_id:
            recipients.add(project.pm_id)

        for item in critical_tasks:
            task = self.db.query(Task).filter(Task.id == item.task_id).first()
            if task and task.owner_id:
                recipients.add(task.owner_id)

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

        Returns:
            完整的处理结果
        """
        if options is None:
            options = {
                "auto_block": False,
                "delay_threshold": 7,
                "auto_fix_timing": False,
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
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise Exception("项目不存在")

            tasks = (
                self.db.query(Task)
                .filter(Task.project_id == project_id)
                .all()
            )

            if not tasks:
                logger.info(f"项目 {project_id} 没有任务，跳过自动处理")
                result["success"] = True
                return result

            from app.api.v1.endpoints.progress.utils import (
                _analyze_dependency_graph,
                _build_project_forecast,
            )

            forecast = _build_project_forecast(project, tasks)
            result["forecast_stats"] = {
                "task_count": len(tasks),
                "current_progress": forecast.current_progress,
                "predicted_delay_days": forecast.predicted_delay_days,
                "critical_task_count": len([t for t in forecast.tasks if t.critical])
            }

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

            if options["send_notifications"]:
                notify_stats = self.send_forecast_notifications(
                    project_id=project_id,
                    project=project,
                    forecast_items=forecast.tasks
                )
                result["notification_stats"]["forecast"] = notify_stats

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
