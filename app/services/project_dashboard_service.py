# -*- coding: utf-8 -*-
"""
项目仪表盘数据聚合服务
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.progress import Task
from app.models.project import Project, ProjectCost, ProjectMilestone, ProjectStatusLog


def build_basic_info(project: Project) -> Dict[str, Any]:
    """
    构建项目基本信息

    Returns:
        dict: 项目基本信息
    """
    return {
        "project_code": project.project_code,
        "project_name": project.project_name,
        "customer_name": project.customer_name,
        "pm_name": project.pm_name,
        "stage": project.stage or "S1",
        "status": project.status or "ST01",
        "health": project.health or "H1",
        "progress_pct": float(project.progress_pct or 0),
        "planned_start_date": project.planned_start_date.isoformat() if project.planned_start_date else None,
        "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
        "actual_start_date": project.actual_start_date.isoformat() if project.actual_start_date else None,
        "actual_end_date": project.actual_end_date.isoformat() if project.actual_end_date else None,
        "contract_amount": float(project.contract_amount or 0),
        "budget_amount": float(project.budget_amount or 0),
    }


def calculate_progress_stats(project: Project, today: date) -> Dict[str, Any]:
    """
    计算进度统计

    Returns:
        dict: 进度统计数据
    """
    # 计算计划进度
    plan_progress = 0
    if project.planned_start_date and project.planned_end_date:
        total_days = (project.planned_end_date - project.planned_start_date).days
        if total_days > 0:
            elapsed_days = (today - project.planned_start_date).days
            plan_progress = min(100, max(0, (elapsed_days / total_days) * 100))

    # 计算进度偏差
    progress_deviation = float(project.progress_pct or 0) - plan_progress

    # 计算时间偏差
    time_deviation_days = 0
    if project.planned_end_date:
        time_deviation_days = (today - project.planned_end_date).days

    return {
        "actual_progress": float(project.progress_pct or 0),
        "plan_progress": plan_progress,
        "progress_deviation": progress_deviation,
        "time_deviation_days": time_deviation_days,
        "is_delayed": time_deviation_days > 0 and project.stage != "S9",
    }


def calculate_cost_stats(db: Session, project_id: int, budget_amount: float) -> Dict[str, Any]:
    """
    计算成本统计

    Returns:
        dict: 成本统计数据
    """
    # 使用聚合函数优化查询
    from sqlalchemy import case, literal_column

    total_cost_result = (
        db.query(func.sum(ProjectCost.amount).label('total'))
        .filter(ProjectCost.project_id == project_id)
        .first()
    )
    total_cost = float(total_cost_result.total or 0)

    # 按类型和类别聚合
    cost_by_type_result = (
        db.query(
            ProjectCost.cost_type,
            func.sum(ProjectCost.amount).label('amount')
        )
        .filter(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_type)
        .all()
    )
    cost_by_type = {ct or "其他": float(amount or 0) for ct, amount in cost_by_type_result}

    cost_by_category_result = (
        db.query(
            ProjectCost.cost_category,
            func.sum(ProjectCost.amount).label('amount')
        )
        .filter(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_category)
        .all()
    )
    cost_by_category = {cc or "其他": float(amount or 0) for cc, amount in cost_by_category_result}

    cost_variance = budget_amount - total_cost if budget_amount > 0 else 0
    cost_variance_rate = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0

    return {
        "total_cost": total_cost,
        "budget_amount": budget_amount,
        "cost_variance": cost_variance,
        "cost_variance_rate": cost_variance_rate,
        "cost_by_type": cost_by_type,
        "cost_by_category": cost_by_category,
        "is_over_budget": total_cost > budget_amount if budget_amount > 0 else False,
    }


def calculate_task_stats(db: Session, project_id: int) -> Dict[str, Any]:
    """
    计算任务统计

    Returns:
        dict: 任务统计数据
    """
    # 使用聚合函数优化查询
    task_total_result = (
        db.query(func.count(Task.id).label('total'))
        .filter(Task.project_id == project_id)
        .first()
    )
    task_total = task_total_result.total or 0

    # 按状态聚合
    status_counts = (
        db.query(Task.status, func.count(Task.id).label('count'))
        .filter(Task.project_id == project_id)
        .group_by(Task.status)
        .all()
    )
    status_dict = {status: count for status, count in status_counts}

    task_completed = status_dict.get("COMPLETED", 0)
    task_in_progress = status_dict.get("IN_PROGRESS", 0)
    task_pending = status_dict.get("PENDING", 0) + status_dict.get("ACCEPTED", 0)
    task_blocked = status_dict.get("BLOCKED", 0)

    # 计算平均进度
    avg_progress_result = (
        db.query(func.avg(Task.progress_pct).label('avg'))
        .filter(Task.project_id == project_id)
        .first()
    )
    task_avg_progress = float(avg_progress_result.avg or 0)

    return {
        "total": task_total,
        "completed": task_completed,
        "in_progress": task_in_progress,
        "pending": task_pending,
        "blocked": task_blocked,
        "completion_rate": (task_completed / task_total * 100) if task_total > 0 else 0,
        "avg_progress": task_avg_progress,
    }


def calculate_milestone_stats(db: Session, project_id: int, today: date) -> Dict[str, Any]:
    """
    计算里程碑统计

    Returns:
        dict: 里程碑统计数据
    """
    # 使用聚合函数优化查询
    milestone_total_result = (
        db.query(func.count(ProjectMilestone.id).label('total'))
        .filter(ProjectMilestone.project_id == project_id)
        .first()
    )
    milestone_total = milestone_total_result.total or 0

    milestone_completed = (
        db.query(func.count(ProjectMilestone.id))
        .filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.status == "COMPLETED"
        )
        .scalar()
    ) or 0

    milestone_overdue = (
        db.query(func.count(ProjectMilestone.id))
        .filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.status != "COMPLETED",
            ProjectMilestone.planned_date < today
        )
        .scalar()
    ) or 0

    milestone_upcoming = (
        db.query(func.count(ProjectMilestone.id))
        .filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.status != "COMPLETED",
            ProjectMilestone.planned_date >= today
        )
        .scalar()
    ) or 0

    return {
        "total": milestone_total,
        "completed": milestone_completed,
        "overdue": milestone_overdue,
        "upcoming": milestone_upcoming,
        "completion_rate": (milestone_completed / milestone_total * 100) if milestone_total > 0 else 0,
    }


def calculate_risk_stats(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
    """
    计算风险统计

    Returns:
        Optional[dict]: 风险统计数据，如果模型不存在则返回None
    """
    try:
        from app.models.pmo import PmoProjectRisk
    except ImportError:
        # 模型未定义，返回 None
        return None

    try:
        risks = db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project_id).all()

        risk_total = len(risks)
        risk_high = len([r for r in risks if r.risk_level == "HIGH" and r.status != "CLOSED"])
        risk_critical = len([r for r in risks if r.risk_level == "CRITICAL" and r.status != "CLOSED"])
        risk_open = len([r for r in risks if r.status != "CLOSED"])

        return {
            "total": risk_total,
            "open": risk_open,
            "high": risk_high,
            "critical": risk_critical,
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"计算风险统计失败: {e}")
        return None


def calculate_issue_stats(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
    """
    计算问题统计

    Returns:
        Optional[dict]: 问题统计数据，如果模型不存在则返回None
    """
    try:
        from app.models.issue import Issue
    except ImportError:
        return None

    try:
        issues = db.query(Issue).filter(Issue.project_id == project_id).all()

        issue_total = len(issues)
        issue_open = len([i for i in issues if i.status == "OPEN"])
        issue_processing = len([i for i in issues if i.status == "PROCESSING"])
        issue_blocking = len([i for i in issues if i.is_blocking])

        return {
            "total": issue_total,
            "open": issue_open,
            "processing": issue_processing,
            "blocking": issue_blocking,
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"计算问题统计失败: {e}")
        return None


def calculate_resource_usage(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
    """
    计算资源使用

    Returns:
        Optional[dict]: 资源使用数据，如果模型不存在则返回None
    """
    try:
        from app.models.pmo import PmoResourceAllocation
    except ImportError:
        return None

    try:
        allocations = db.query(PmoResourceAllocation).filter(
            PmoResourceAllocation.project_id == project_id
        ).all()

        if not allocations:
            return None

        resource_usage = {
            "total_allocations": len(allocations),
            "by_department": {},
            "by_role": {},
        }

        for alloc in allocations:
            dept = alloc.department_name or "未分配"
            role = alloc.role or "未分配"

            resource_usage["by_department"][dept] = resource_usage["by_department"].get(dept, 0) + 1
            resource_usage["by_role"][role] = resource_usage["by_role"].get(role, 0) + 1

        return resource_usage
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"计算资源使用失败: {e}")
        return None


def get_recent_activities(db: Session, project_id: int) -> List[Dict[str, Any]]:
    """
    获取最近活动

    Returns:
        List[Dict]: 最近活动列表
    """
    recent_activities = []

    # 最近的状态变更
    recent_status_logs = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    ).order_by(desc(ProjectStatusLog.changed_at)).limit(5).all()

    for log in recent_status_logs:
        activity = {
            "type": "STATUS_CHANGE",
            "time": log.changed_at.isoformat() if log.changed_at else None,
            "title": f"状态变更：{log.old_status} → {log.new_status}",
            "description": log.change_reason,
        }
        recent_activities.append(activity)

    # 最近的里程碑完成
    recent_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).order_by(desc(ProjectMilestone.actual_date)).limit(3).all()

    for milestone in recent_milestones:
        activity = {
            "type": "MILESTONE",
            "time": milestone.actual_date.isoformat() if milestone.actual_date else None,
            "title": f"里程碑完成：{milestone.milestone_name}",
            "description": None,
        }
        recent_activities.append(activity)

    # 按时间排序
    recent_activities.sort(key=lambda x: x.get("time") or "", reverse=True)
    return recent_activities[:10]


def calculate_key_metrics(
    project: Project,
    progress_deviation: float,
    cost_variance_rate: float,
    task_completed: int,
    task_total: int
) -> Dict[str, float]:
    """
    计算关键指标

    Returns:
        dict: 关键指标数据
    """
    key_metrics = {
        "health_score": 100 if project.health == "H1" else (75 if project.health == "H2" else (50 if project.health == "H3" else 25)),
        "progress_score": float(project.progress_pct or 0),
        "schedule_score": 100 - abs(progress_deviation) if abs(progress_deviation) <= 20 else max(0, 100 - abs(progress_deviation) * 2),
        "cost_score": 100 - abs(cost_variance_rate) if abs(cost_variance_rate) <= 10 else max(0, 100 - abs(cost_variance_rate) * 2),
        "quality_score": (task_completed / task_total * 100) if task_total > 0 else 100,
    }

    # 计算综合得分
    key_metrics["overall_score"] = (
        key_metrics["health_score"] * 0.3 +
        key_metrics["progress_score"] * 0.25 +
        key_metrics["schedule_score"] * 0.2 +
        key_metrics["cost_score"] * 0.15 +
        key_metrics["quality_score"] * 0.1
    )

    return key_metrics
