# -*- coding: utf-8 -*-
"""
资源分配服务 - 冲突检测
"""
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models import Machine, Project


def detect_resource_conflicts(
    db: Session,
    project_id: int,
    machine_id: Optional[int],
    start_date: date,
    end_date: date
) -> List[Dict]:
    """
    检测资源冲突

    Args:
        db: 数据库会话
        project_id: 项目ID
        machine_id: 机台ID（可选）
        start_date: 计划开始日期
        end_date: 计划结束日期

    Returns:
        冲突列表
    """
    conflicts = []

    # 1. 检查机台冲突
    if machine_id:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if machine:
            # 检查是否有其他项目占用该机台
            conflicting_projects = db.query(Project).join(
                Machine, Project.id == Machine.project_id
            ).filter(
                Machine.id == machine_id,
                Project.id != project_id,
                Project.status.in_(['S4', 'S5']),  # 加工制造、装配调试阶段
                or_(
                    and_(
                        Project.planned_start_date.isnot(None),
                        Project.planned_start_date <= end_date
                    ),
                    and_(
                        Project.planned_end_date.isnot(None),
                        Project.planned_end_date >= start_date
                    )
                )
            ).all()

            for cp in conflicting_projects:
                conflicts.append({
                    'type': 'MACHINE',
                    'resource_id': machine_id,
                    'resource_name': machine.machine_code,
                    'conflict_project_id': cp.id,
                    'conflict_project_name': cp.project_name,
                    'conflict_period': f"{cp.planned_start_date or '未知'} 至 {cp.planned_end_date or '未知'}",
                    'severity': 'HIGH'
                })

    return conflicts
