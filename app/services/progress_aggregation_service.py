# -*- coding: utf-8 -*-
"""
进度聚合服务
任务进度 → 阶段进度 → 项目进度 的实时聚合
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

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

    # 2. 计算项目整体进度（所有任务的加权平均）
    project_tasks = db.query(TaskUnified).filter(
        and_(
            TaskUnified.project_id == project_id,
            TaskUnified.is_active == True,
            TaskUnified.status.notin_(['CANCELLED'])  # 排除已取消任务
        )
    ).all()

    if project_tasks:
        # 加权平均（默认权重为1）
        total_weight = len(project_tasks)
        weighted_progress = sum(t.progress for t in project_tasks)
        project_progress = round(weighted_progress / total_weight, 2) if total_weight > 0 else 0

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

        # 获取该阶段的所有任务
        stage_tasks = db.query(TaskUnified).filter(
            and_(
                TaskUnified.project_id == project_id,
                TaskUnified.stage == stage_code,
                TaskUnified.is_active == True,
                TaskUnified.status.notin_(['CANCELLED'])
            )
        ).all()

        if stage_tasks:
            # 加权平均
            total_weight = len(stage_tasks)
            weighted_progress = sum(t.progress for t in stage_tasks)
            stage_progress = round(weighted_progress / total_weight, 2) if total_weight > 0 else 0

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

    # 统计任务情况
    tasks = db.query(TaskUnified).filter(
        and_(
            TaskUnified.project_id == project_id,
            TaskUnified.is_active == True,
            TaskUnified.status.notin_(['CANCELLED', 'COMPLETED'])
        )
    ).all()

    delayed_count = sum(1 for t in tasks if t.is_delayed)
    overdue_count = sum(1 for t in tasks if t.deadline and t.deadline < datetime.now())

    total_tasks = len(tasks)

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
        print(f"Warning: Could not create progress log: {e}")
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
    # 统计任务
    tasks = db.query(TaskUnified).filter(TaskUnified.project_id == project_id).all()

    total_tasks = len([t for t in tasks if t.status != 'CANCELLED'])
    completed_tasks = len([t for t in tasks if t.status == 'COMPLETED'])
    in_progress_tasks = len([t for t in tasks if t.status == 'IN_PROGRESS'])
    delayed_tasks = len([t for t in tasks if t.is_delayed])
    overdue_tasks = len([t for t in tasks if t.deadline and t.deadline < datetime.now()
                        and t.status not in ['COMPLETED', 'CANCELLED']])

    # 计算整体进度
    overall_progress = sum(t.progress for t in tasks) / len(tasks) if tasks else 0

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
        tasks = db.query(TaskUnified).filter(TaskUnified.project_id == project_id).all()

        # 仅统计处于激活状态且未取消的任务
        active_tasks = [
            task for task in tasks
            if getattr(task, "is_active", True) and (task.status or "").upper() != "CANCELLED"
        ]

        total_tasks = len(active_tasks)
        completed_tasks = len([t for t in active_tasks if (t.status or "").upper() == "COMPLETED"])
        in_progress_tasks = len([
            t for t in active_tasks if (t.status or "").upper() in {"IN_PROGRESS", "ACCEPTED"}
        ])
        pending_approval_tasks = len([
            t for t in active_tasks if (t.status or "").upper() == "PENDING_APPROVAL"
        ])

        total_hours = 0.0
        weighted_progress = 0.0

        for task in active_tasks:
            progress = float(task.progress or 0)
            if task.estimated_hours and float(task.estimated_hours) > 0:
                weight = float(task.estimated_hours)
            else:
                # 没有预估工时时按1小时处理，避免除零
                weight = 1.0
            total_hours += weight
            weighted_progress += progress * weight

        if total_hours > 0:
            overall_progress = weighted_progress / total_hours
        elif total_tasks > 0:
            # 所有任务都缺少工时估计时，退化为简单平均
            overall_progress = sum(float(t.progress or 0) for t in active_tasks) / total_tasks
        else:
            overall_progress = 0.0

        delayed_tasks = len([t for t in active_tasks if getattr(t, "is_delayed", False)])
        overdue_tasks = len([
            t for t in active_tasks
            if t.deadline and t.deadline < datetime.now()
            and (t.status or "").upper() not in {"COMPLETED", "CANCELLED"}
        ])

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
