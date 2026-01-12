# -*- coding: utf-8 -*-
"""
进度聚合服务
任务进度 → 阶段进度 → 项目进度 的实时聚合
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.models.task_center import TaskUnified
from app.models.project import Project, ProjectStage
from app.models.progress import ProgressLog


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
        # 没有活跃任务，保持当前健康度
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


def create_progress_log(
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
        # 检查是否有 ProgressLog 模型
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
        # 如果 ProgressLog 表不存在或其他错误，记录日志但不影响主流程
        db.rollback()
        logger.warning(f"Could not create progress log: {e}")
        return None


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
        # 使用SQL的CASE WHEN来处理estimated_hours为空的情况
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
                ).scalar()
            ) or 0.0

        if total_hours > 0:
            overall_progress = weighted_progress_result / total_hours
        elif total_tasks > 0:
            # 所有任务都缺少工时估计时，退化为简单平均
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
