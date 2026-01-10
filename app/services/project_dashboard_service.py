# -*- coding: utf-8 -*-
"""
项目仪表盘数据聚合服务
"""

from typing import Dict, Any, Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.project import Project, ProjectCost, ProjectMilestone, ProjectStatusLog
from app.models.progress import Task


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
    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    
    total_cost = sum(float(cost.amount or 0) for cost in costs)
    cost_by_type = {}
    cost_by_category = {}
    
    for cost in costs:
        cost_type = cost.cost_type or "其他"
        cost_category = cost.cost_category or "其他"
        amount = float(cost.amount or 0)
        
        cost_by_type[cost_type] = cost_by_type.get(cost_type, 0) + amount
        cost_by_category[cost_category] = cost_by_category.get(cost_category, 0) + amount
    
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
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    task_total = len(tasks)
    task_completed = len([t for t in tasks if t.status == "COMPLETED"])
    task_in_progress = len([t for t in tasks if t.status == "IN_PROGRESS"])
    task_pending = len([t for t in tasks if t.status in ["PENDING", "ACCEPTED"]])
    task_blocked = len([t for t in tasks if t.status == "BLOCKED"])
    
    task_avg_progress = sum(float(t.progress_pct or 0) for t in tasks) / task_total if task_total > 0 else 0
    
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
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()
    
    milestone_total = len(milestones)
    milestone_completed = len([m for m in milestones if m.status == "COMPLETED"])
    milestone_overdue = len([
        m for m in milestones 
        if m.status != "COMPLETED" and m.planned_date and m.planned_date < today
    ])
    milestone_upcoming = len([
        m for m in milestones 
        if m.status != "COMPLETED" and m.planned_date and m.planned_date >= today
    ])
    
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
    except:
        return None


def calculate_issue_stats(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
    """
    计算问题统计
    
    Returns:
        Optional[dict]: 问题统计数据，如果模型不存在则返回None
    """
    try:
        from app.models.issue import Issue
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
    except:
        return None


def calculate_resource_usage(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
    """
    计算资源使用
    
    Returns:
        Optional[dict]: 资源使用数据，如果模型不存在则返回None
    """
    try:
        from app.models.pmo import PmoResourceAllocation
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
    except:
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
