# -*- coding: utf-8 -*-
"""
资源分配服务 - 资源分配
"""
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .conflicts import detect_resource_conflicts
from .worker import find_available_workers
from .workstation import find_available_workstations


def allocate_resources(
    db: Session,
    project_id: int,
    machine_id: Optional[int],
    suggested_start_date: date,
    suggested_end_date: date
) -> Dict:
    """
    分配资源（工位和人员）

    Args:
        db: 数据库会话
        project_id: 项目ID
        machine_id: 机台ID
        suggested_start_date: 建议开始日期
        suggested_end_date: 建议结束日期

    Returns:
        资源分配结果
    """
    result = {
        'workstations': [],
        'workers': [],
        'conflicts': [],
        'can_allocate': True
    }

    # 1. 检测资源冲突
    conflicts = detect_resource_conflicts(
        db, project_id, machine_id, suggested_start_date, suggested_end_date
    )
    result['conflicts'] = conflicts

    if conflicts:
        result['can_allocate'] = False
        return result

    # 2. 查找可用工位
    available_workstations = find_available_workstations(
        db,
        start_date=suggested_start_date,
        end_date=suggested_end_date
    )
    result['workstations'] = available_workstations[:3]  # 返回前3个

    # 3. 查找可用人员
    available_workers = find_available_workers(
        db,
        start_date=suggested_start_date,
        end_date=suggested_end_date,
        min_available_hours=8.0
    )
    result['workers'] = available_workers[:5]  # 返回前5个

    # 4. 判断是否可以分配
    if not available_workstations:
        result['can_allocate'] = False
        result['reason'] = '无可用工位'
    elif not available_workers:
        result['can_allocate'] = False
        result['reason'] = '无可用人员'
    else:
        result['can_allocate'] = True

    return result
