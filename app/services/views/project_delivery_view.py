# -*- coding: utf-8 -*-
"""项目交付关联视图"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session


def get_project_delivery_overview(db: Session, project_id: int) -> Dict[str, Any]:
    """获取项目交付总览"""
    from app.models.project_delivery import ProjectDeliverySchedule, ProjectDeliveryTask
    
    schedules = db.query(ProjectDeliverySchedule).filter(ProjectDeliverySchedule.project_id == project_id).all()
    task_count = 0
    completed_count = 0
    for s in schedules:
        tasks = db.query(ProjectDeliveryTask).filter(ProjectDeliveryTask.schedule_id == s.id).all()
        task_count += len(tasks)
        completed_count += sum(1 for t in tasks if t.status == "COMPLETED")
    
    return {
        "schedules": {"total": len(schedules), "confirmed": sum(1 for s in schedules if s.status == "CONFIRMED")},
        "tasks": {"total": task_count, "completed": completed_count},
    }
